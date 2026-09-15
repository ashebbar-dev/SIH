"""Bounded stdlib HTTP server for the local NISHAN browser demonstration."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
import time
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pymupdf as fitz
from PIL import Image, ImageOps

from .engine import MAX_UPLOAD_BYTES, DemoEngine, InputError


STATIC_ROOT = Path(__file__).with_name("static")
STATIC_ROUTES = {
    "/": (STATIC_ROOT / "index.html", "text/html; charset=utf-8"),
    "/mobile": (STATIC_ROOT / "mobile.html", "text/html; charset=utf-8"),
    "/static/app.js": (STATIC_ROOT / "app.js", "text/javascript; charset=utf-8"),
    "/static/style.css": (STATIC_ROOT / "style.css", "text/css; charset=utf-8"),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DemoHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, engine: DemoEngine, max_completed: int = 20):
        self.engine = engine
        self.max_completed = max_completed
        self.request_token = secrets.token_urlsafe(32)
        self.jobs: OrderedDict[str, dict] = OrderedDict()
        self.job_files: dict[str, dict[str, Path]] = {}
        self.latest_job_id: str | None = None
        self._active_job: str | None = None
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="nishan-demo")
        self.files_root = engine.state_dir / "http-files"
        self.files_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.files_root, 0o700)
        super().__init__(address, DemoRequestHandler)

    def server_close(self) -> None:
        super().server_close()
        self._executor.shutdown(wait=True, cancel_futures=True)

    def submit_analysis(self, body: bytes, filename: str, mode: str) -> str | None:
        with self._lock:
            if self._active_job is not None:
                return None
            job_id = uuid.uuid4().hex
            upload = self.files_root / f"{job_id}.upload"
            descriptor = os.open(upload, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(body)
            job = {
                "job_id": job_id,
                "type": "analysis",
                "status": "queued",
                "mode": mode,
                "filename": filename,
                "created_at": _utc_now(),
                "result": None,
                "error": None,
                "preview_url": None,
                "report_url": None,
            }
            self.jobs[job_id] = job
            self.job_files[job_id] = {"upload": upload}
            self.latest_job_id = job_id
            self._active_job = job_id
            self._executor.submit(self._run_analysis, job_id, upload, mode)
            return job_id

    def submit_prepare(self) -> str | None:
        with self._lock:
            if self._active_job is not None:
                return None
            job_id = uuid.uuid4().hex
            self.jobs[job_id] = {
                "job_id": job_id,
                "type": "prepare",
                "status": "queued",
                "mode": "signed",
                "filename": None,
                "created_at": _utc_now(),
                "result": None,
                "error": None,
                "preview_url": None,
                "report_url": None,
            }
            self.job_files[job_id] = {}
            self.latest_job_id = job_id
            self._active_job = job_id
            self._executor.submit(self._run_prepare, job_id)
            return job_id

    def _begin(self, job_id: str) -> float:
        started = time.perf_counter()
        with self._lock:
            self.jobs[job_id]["status"] = "running"
            self.jobs[job_id]["started_at"] = _utc_now()
        return started

    def _run_analysis(self, job_id: str, upload: Path, mode: str) -> None:
        started = self._begin(job_id)
        try:
            result = self.engine.analyze(upload, mode)
            report = self.files_root / f"{job_id}-report.json"
            self._write_private(report, json.dumps(result, indent=2, sort_keys=True).encode() + b"\n")
            preview = self._make_preview(upload, job_id)
            with self._lock:
                self.job_files[job_id]["report"] = report
                if preview is not None:
                    self.job_files[job_id]["preview"] = preview
                job = self.jobs[job_id]
                job["result"] = result
                job["preview_url"] = f"/api/jobs/{job_id}/preview" if preview else None
                job["report_url"] = f"/api/jobs/{job_id}/report"
                job["status"] = "done"
        except Exception as error:
            with self._lock:
                self.jobs[job_id]["status"] = "error"
                self.jobs[job_id]["error"] = (
                    str(error) if isinstance(error, (InputError, RuntimeError, ValueError))
                    else "Analysis failed. Inspect the local terminal for details."
                )
        finally:
            self._finish(job_id, started)

    def _run_prepare(self, job_id: str) -> None:
        started = self._begin(job_id)
        try:
            result = self.engine.prepare_signed()
            with self._lock:
                self.jobs[job_id]["result"] = result
                self.jobs[job_id]["status"] = "done"
        except Exception as error:
            with self._lock:
                self.jobs[job_id]["status"] = "error"
                self.jobs[job_id]["error"] = str(error)
        finally:
            self._finish(job_id, started)

    def _finish(self, job_id: str, started: float) -> None:
        with self._lock:
            job = self.jobs[job_id]
            job["completed_at"] = _utc_now()
            job["duration_seconds"] = round(time.perf_counter() - started, 3)
            self._active_job = None
            completed = [key for key, value in self.jobs.items() if value["status"] in {"done", "error"}]
            while len(completed) > self.max_completed:
                expired = completed.pop(0)
                self.jobs.pop(expired, None)
                for path in self.job_files.pop(expired, {}).values():
                    try:
                        path.unlink()
                    except FileNotFoundError:
                        pass

    @staticmethod
    def _write_private(path: Path, data: bytes) -> None:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)

    def _make_preview(self, source: Path, job_id: str) -> Path | None:
        output = self.files_root / f"{job_id}-preview.jpg"
        try:
            try:
                with fitz.open(source) as document:
                    if document.is_pdf and document.page_count:
                        pixmap = document[0].get_pixmap(matrix=fitz.Matrix(1.3, 1.3), alpha=False)
                        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                    else:
                        raise fitz.FileDataError("not a PDF")
            except (fitz.FileDataError, RuntimeError, ValueError):
                with Image.open(source) as opened:
                    image = ImageOps.exif_transpose(opened).convert("RGB")
            image.thumbnail((1400, 1800), Image.Resampling.LANCZOS)
            image.save(output, "JPEG", quality=86, optimize=True)
            os.chmod(output, 0o600)
            return output
        except Exception:
            return None

    def public_job(self, job_id: str) -> dict | None:
        with self._lock:
            job = self.jobs.get(job_id)
            return None if job is None else json.loads(json.dumps(job))


class DemoRequestHandler(BaseHTTPRequestHandler):
    server: DemoHTTPServer

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def _headers(self, status: int, content_type: str, length: int, *, attachment: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        if attachment:
            self.send_header("Content-Disposition", f'attachment; filename="{attachment}"')
        self.end_headers()

    def _send(self, status: int, data: bytes, content_type: str = "application/json; charset=utf-8", *, attachment: str | None = None) -> None:
        self._headers(status, content_type, len(data), attachment=attachment)
        self.wfile.write(data)

    def _json(self, status: int, value: dict) -> None:
        self._send(status, json.dumps(value, separators=(",", ":")).encode())

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def _host_valid(self) -> bool:
        raw = self.headers.get("Host", "")
        try:
            parsed = urlsplit(f"//{raw}")
            host = parsed.hostname
            port = parsed.port
        except ValueError:
            return False
        if not host or port not in {None, self.server.server_address[1]}:
            return False
        bound = self.server.server_address[0]
        if bound in {"127.0.0.1", "::1", "localhost"}:
            return host in {"127.0.0.1", "::1", "localhost"}
        if bound in {"0.0.0.0", "::"}:
            return host == "localhost" or all(part.isdigit() for part in host.split(".")) or ":" in host
        return host == bound

    def _mutation_allowed(self) -> bool:
        if not secrets.compare_digest(
            self.headers.get("X-Nishan-Token", ""), self.server.request_token
        ):
            return False
        origin = self.headers.get("Origin")
        if not origin:
            return True
        try:
            parsed = urlsplit(origin)
        except ValueError:
            return False
        return parsed.scheme == "http" and parsed.netloc == self.headers.get("Host")

    def do_GET(self) -> None:
        if not self._host_valid():
            self._error(HTTPStatus.FORBIDDEN, "Host is not permitted for this local server.")
            return
        path = unquote(urlsplit(self.path).path)
        if path in STATIC_ROUTES:
            file_path, content_type = STATIC_ROUTES[path]
            try:
                self._send(HTTPStatus.OK, file_path.read_bytes(), content_type)
            except FileNotFoundError:
                self._error(HTTPStatus.NOT_FOUND, "UI asset not found.")
            return
        if path == "/api/status":
            self._json(HTTPStatus.OK, {
                "capabilities": self.server.engine.capabilities(),
                "fixtures": self.server.engine.fixtures(),
                "latest_job_id": self.server.latest_job_id,
                "active_job_id": self.server._active_job,
                "request_token": self.server.request_token,
                "max_upload_bytes": MAX_UPLOAD_BYTES,
            })
            return
        pieces = path.strip("/").split("/")
        if len(pieces) == 3 and pieces[:2] == ["api", "jobs"]:
            job = self.server.public_job(pieces[2])
            if job is None:
                self._error(HTTPStatus.NOT_FOUND, "Unknown job.")
            else:
                self._json(HTTPStatus.OK, job)
            return
        if len(pieces) == 4 and pieces[:2] == ["api", "jobs"] and pieces[3] in {"preview", "report"}:
            kind = pieces[3]
            path_to_file = self.server.job_files.get(pieces[2], {}).get(kind)
            if path_to_file is None or not path_to_file.is_file():
                self._error(HTTPStatus.NOT_FOUND, "Job asset is not available.")
                return
            content_type = "image/jpeg" if kind == "preview" else "application/json; charset=utf-8"
            attachment = "nishan-evidence.json" if kind == "report" else None
            self._send(HTTPStatus.OK, path_to_file.read_bytes(), content_type, attachment=attachment)
            return
        if len(pieces) == 3 and pieces[:2] == ["api", "fixtures"]:
            fixture_id = pieces[2]
            if not fixture_id or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in fixture_id):
                self._error(HTTPStatus.BAD_REQUEST, "Invalid fixture ID.")
                return
            try:
                fixture = self.server.engine.fixture_path(fixture_id)
            except (KeyError, FileNotFoundError, ValueError):
                self._error(HTTPStatus.NOT_FOUND, "Unknown fixture.")
                return
            media = "application/pdf" if fixture.read_bytes()[:5] == b"%PDF-" else "image/png"
            suffix = ".pdf" if media == "application/pdf" else ".png"
            self._send(HTTPStatus.OK, fixture.read_bytes(), media, attachment=f"nishan-{fixture_id}{suffix}")
            return
        self._error(HTTPStatus.NOT_FOUND, "Route not found.")

    def do_POST(self) -> None:
        if not self._host_valid() or not self._mutation_allowed():
            self._error(HTTPStatus.FORBIDDEN, "A valid local request token and same origin are required.")
            return
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        length_value = self.headers.get("Content-Length")
        if length_value is None:
            self._error(HTTPStatus.LENGTH_REQUIRED, "Content-Length is required.")
            return
        try:
            length = int(length_value)
        except ValueError:
            self._error(HTTPStatus.BAD_REQUEST, "Invalid Content-Length.")
            return
        if length < 0:
            self._error(HTTPStatus.BAD_REQUEST, "Invalid Content-Length.")
            return
        if length > MAX_UPLOAD_BYTES:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Upload exceeds the 25 MiB limit.")
            return
        if path == "/api/prepare":
            if length:
                self._error(HTTPStatus.BAD_REQUEST, "Preparation does not accept a request body.")
                return
            job_id = self.server.submit_prepare()
        elif path == "/api/analyze":
            query = parsed.query
            if query not in {"mode=public", "mode=signed"}:
                self._error(HTTPStatus.BAD_REQUEST, "Mode must be public or signed.")
                return
            if not length:
                self._error(HTTPStatus.BAD_REQUEST, "Upload body is empty.")
                return
            filename = "".join(
                character
                for character in unquote(self.headers.get("X-File-Name", "upload")[:720])[:240]
                if character.isprintable()
            ) or "upload"
            body = self.rfile.read(length)
            if len(body) != length:
                self._error(HTTPStatus.BAD_REQUEST, "Upload body ended early.")
                return
            job_id = self.server.submit_analysis(body, filename, query.split("=", 1)[1])
        else:
            self._error(HTTPStatus.NOT_FOUND, "Route not found.")
            return
        if job_id is None:
            self._error(HTTPStatus.CONFLICT, "Detector is busy; wait for the active job to finish.")
        else:
            self._json(HTTPStatus.ACCEPTED, {"job_id": job_id, "job_url": f"/api/jobs/{job_id}"})


def serve(workspace: Path, state_dir: Path, host: str, port: int) -> None:
    engine = DemoEngine(workspace, state_dir)
    server = DemoHTTPServer((host, port), engine)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
