from __future__ import annotations

import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from demo_app.engine import DemoEngine
from demo_app.server import DemoHTTPServer


ROOT = Path(__file__).resolve().parents[4]


class ControlledEngine:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.started = threading.Event()
        self.release = threading.Event()
        self.hold = False

    def capabilities(self):
        return {"public": True, "signed": False, "signed_detail": "test engine"}

    def fixtures(self):
        return [{"id": "source", "label": "Original", "mode": "public"}]

    def fixture_path(self, fixture_id):
        if fixture_id != "source":
            raise KeyError(fixture_id)
        return ROOT / "artifacts/nishan/synthetic-source.pdf"

    def analyze(self, path, mode):
        self.started.set()
        if self.hold and not self.release.wait(5):
            raise TimeoutError("test release timed out")
        return {
            "kind": "known_original",
            "title": "Known original — no watermark",
            "summary": "Exact source bytes.",
            "assurance": "exact_file_identity",
            "recipients": [],
            "channels": {},
            "diagnostics": {"input_type": "pdf"},
            "limitations": [],
        }

    def prepare_signed(self):
        return {"run_id": "test", "fixtures": []}


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.engine = ControlledEngine(Path(self.directory.name))
        self.server = DemoHTTPServer(("127.0.0.1", 0), self.engine, max_completed=2)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._close)
        self.host, self.port = self.server.server_address

    def _close(self):
        self.engine.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=8)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response.status, dict(response.getheaders()), payload

    def status(self):
        code, _, payload = self.request("GET", "/api/status")
        self.assertEqual(code, 200)
        return json.loads(payload)

    def post_headers(self, name="sample.pdf"):
        return {
            "Content-Length": "3",
            "Content-Type": "application/octet-stream",
            "X-File-Name": name,
            "X-Nishan-Token": self.status()["request_token"],
            "Origin": f"http://{self.host}:{self.port}",
        }

    def wait_job(self, job_id):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            code, _, payload = self.request("GET", f"/api/jobs/{job_id}")
            self.assertEqual(code, 200)
            job = json.loads(payload)
            if job["status"] in {"done", "error"}:
                return job
            time.sleep(0.01)
        self.fail("job did not complete")

    def test_mutating_requests_require_token_and_same_origin(self) -> None:
        headers = self.post_headers()
        missing = {key: value for key, value in headers.items() if key != "X-Nishan-Token"}
        code, _, _ = self.request("POST", "/api/analyze?mode=public", b"pdf", missing)
        self.assertEqual(code, 403)
        headers["Origin"] = "https://attacker.invalid"
        code, _, _ = self.request("POST", "/api/analyze?mode=public", b"pdf", headers)
        self.assertEqual(code, 403)

    def test_advertised_oversize_rejected_without_reading(self) -> None:
        headers = self.post_headers()
        headers["Content-Length"] = str(25 * 1024 * 1024 + 1)
        code, _, payload = self.request("POST", "/api/analyze?mode=public", b"", headers)
        self.assertEqual(code, 413)
        self.assertIn(b"25 MiB", payload)

    def test_allowlists_reject_unknown_fixtures_and_traversal(self) -> None:
        for path in (
            "/api/fixtures/unknown",
            "/api/fixtures/..%2Fstate%2Fsecret.bin",
            "/api/jobs/..%2Fsecret/report",
            "/state/secret.bin",
        ):
            with self.subTest(path=path):
                code, _, _ = self.request("GET", path)
                self.assertIn(code, {400, 404})

    def test_real_source_job_updates_latest_status(self) -> None:
        source = (ROOT / "artifacts/nishan/synthetic-source.pdf").read_bytes()
        headers = self.post_headers("source.pdf")
        headers["Content-Length"] = str(len(source))
        code, _, payload = self.request("POST", "/api/analyze?mode=public", source, headers)
        self.assertEqual(code, 202)
        job_id = json.loads(payload)["job_id"]
        job = self.wait_job(job_id)
        self.assertEqual(job["status"], "done")
        self.assertEqual(job["result"]["kind"], "known_original")
        self.assertEqual(self.status()["latest_job_id"], job_id)

    def test_busy_response_and_completed_history_limit(self) -> None:
        self.engine.hold = True
        headers = self.post_headers()
        code, _, payload = self.request("POST", "/api/analyze?mode=public", b"pdf", headers)
        self.assertEqual(code, 202)
        first = json.loads(payload)["job_id"]
        self.assertTrue(self.engine.started.wait(2))
        code, _, payload = self.request("POST", "/api/analyze?mode=public", b"pdf", headers)
        self.assertEqual(code, 409)
        self.assertIn(b"busy", payload.lower())
        self.engine.release.set()
        self.wait_job(first)
        self.engine.hold = False
        for _ in range(2):
            code, _, payload = self.request("POST", "/api/analyze?mode=public", b"pdf", headers)
            self.assertEqual(code, 202)
            self.wait_job(json.loads(payload)["job_id"])
        code, _, _ = self.request("GET", f"/api/jobs/{first}")
        self.assertEqual(code, 404)

    def test_host_header_and_static_routes_are_bounded(self) -> None:
        code, _, _ = self.request("GET", "/", headers={"Host": "attacker.invalid"})
        self.assertEqual(code, 403)
        for path in ("/", "/mobile", "/static/app.js", "/static/style.css"):
            code, headers, payload = self.request("GET", path)
            self.assertEqual(code, 200)
            self.assertGreater(len(payload), 20)
            self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")

    def test_frontend_clears_stale_evidence_and_marks_error_jobs_observed(self) -> None:
        script = (ROOT / "prototypes/nishan_pq/demo_app/static/app.js").read_text()
        desktop = (ROOT / "prototypes/nishan_pq/demo_app/static/index.html").read_text()
        mobile = (ROOT / "prototypes/nishan_pq/demo_app/static/mobile.html").read_text()
        self.assertIn("function resetEvidence(job)", script)
        self.assertIn("state.latestJob = jobId", script)
        self.assertIn("scrollIntoView", script)
        self.assertIn("prefers-reduced-motion", script)
        self.assertIn('id="result-context"', desktop)
        self.assertIn('id="result-context"', mobile)
        self.assertIn('rel="icon" href="data:image/svg+xml', desktop)


class RealEngineHTTPIntegrationTests(unittest.TestCase):
    def test_source_bytes_run_through_real_engine_and_become_latest_job(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = DemoEngine(ROOT, Path(directory) / "state")
            server = DemoHTTPServer(("127.0.0.1", 0), engine)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address

            def request(method, path, body=None, headers=None):
                connection = http.client.HTTPConnection(host, port, timeout=8)
                connection.request(method, path, body=body, headers=headers or {})
                response = connection.getresponse()
                value = response.status, response.read()
                connection.close()
                return value

            try:
                code, payload = request("GET", "/api/status")
                self.assertEqual(code, 200)
                token = json.loads(payload)["request_token"]
                source = (ROOT / "artifacts/nishan/synthetic-source.pdf").read_bytes()
                headers = {
                    "Content-Length": str(len(source)),
                    "Content-Type": "application/octet-stream",
                    "X-File-Name": "real-source.pdf",
                    "X-Nishan-Token": token,
                    "Origin": f"http://{host}:{port}",
                }
                code, payload = request("POST", "/api/analyze?mode=public", source, headers)
                self.assertEqual(code, 202)
                job_id = json.loads(payload)["job_id"]
                deadline = time.monotonic() + 8
                while True:
                    code, payload = request("GET", f"/api/jobs/{job_id}")
                    job = json.loads(payload)
                    if job["status"] in {"done", "error"}:
                        break
                    if time.monotonic() >= deadline:
                        self.fail("real engine job did not complete")
                    time.sleep(0.01)
                self.assertEqual(job["status"], "done")
                self.assertEqual(job["result"]["kind"], "known_original")
                code, payload = request("GET", "/api/status")
                self.assertEqual(json.loads(payload)["latest_job_id"], job_id)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(5)


if __name__ == "__main__":
    unittest.main()
