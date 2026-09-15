from __future__ import annotations

import hashlib
import hmac
import io
import math
from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz
import numpy as np
from PIL import Image, ImageFilter


@dataclass
class PreparedScore:
    """A rendered reference/suspect pair ready for many candidate scores.

    Attribution compares one leaked document with every issued session and with a
    decoy population. Rendering the same PDFs for every session both wastes time
    and risks tiny preprocessing differences, so the residual is prepared once.
    """

    residuals: list[np.ndarray]
    residual_norms: list[float]
    shapes: list[tuple[int, int]]


def _seed(secret: bytes, session_id: str, page_index: int) -> int:
    material = f"NISHAN-WATERMARK/v1|{session_id}|{page_index}".encode()
    digest = hmac.new(secret, material, hashlib.sha3_256).digest()
    return int.from_bytes(digest[:16], "big")


def pattern(secret: bytes, session_id: str, page_index: int, shape: tuple[int, int]) -> np.ndarray:
    """Create a keyed, medium-frequency, zero-mean spread-spectrum carrier."""
    height, width = shape
    rng = np.random.default_rng(_seed(secret, session_id, page_index))
    coarse_height = max(24, math.ceil(height / 14))
    coarse_width = max(24, math.ceil(width / 14))
    coarse = rng.standard_normal((coarse_height, coarse_width)).astype(np.float32)
    normalized = np.clip(127.5 + 32.0 * coarse, 0, 255).astype(np.uint8)
    expanded = Image.fromarray(normalized).resize((width, height), Image.Resampling.BICUBIC)
    low = expanded.filter(ImageFilter.GaussianBlur(radius=5))
    carrier = np.asarray(expanded, dtype=np.float32) - np.asarray(low, dtype=np.float32)
    carrier -= float(carrier.mean())
    carrier /= float(carrier.std()) + 1e-8
    return carrier


def _render_pdf(path: Path, dpi: int = 144) -> tuple[list[np.ndarray], list[tuple[float, float]]]:
    document = fitz.open(path)
    pages: list[np.ndarray] = []
    sizes: list[tuple[float, float]] = []
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    for page in document:
        pixmap = page.get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)
        pages.append(
            np.frombuffer(pixmap.samples, dtype=np.uint8)
            .reshape(pixmap.height, pixmap.width, 3)
            .copy()
        )
        sizes.append((page.rect.width, page.rect.height))
    document.close()
    return pages, sizes


def is_pdf_document(path: Path) -> bool:
    """Use the renderer's parser to classify content for the evidence policy.

    A PDF accepted by MuPDF may have a preamble or a different filename suffix.
    Only a separately validated raster may fall back to Pillow when MuPDF
    cannot open it (for example WebP). Unrecognized inputs remain errors.
    """
    try:
        with fitz.open(path) as document:
            return bool(document.is_pdf)
    except fitz.FileDataError:
        with Image.open(path) as image:
            image.verify()
        return False


def load_pages(path: Path, dpi: int = 144) -> tuple[list[np.ndarray], list[tuple[float, float]]]:
    if is_pdf_document(path):
        return _render_pdf(path, dpi=dpi)
    with Image.open(path) as input_image:
        image = input_image.convert("RGB")
        return [np.asarray(image, dtype=np.uint8)], [(float(image.width), float(image.height))]


def _luma(image: np.ndarray) -> np.ndarray:
    rgb = image.astype(np.float32)
    return 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]


def embed_array(image: np.ndarray, carrier: np.ndarray, strength: float) -> np.ndarray:
    ycbcr = Image.fromarray(image).convert("YCbCr")
    channels = np.asarray(ycbcr, dtype=np.float32).copy()
    channels[:, :, 0] = np.clip(channels[:, :, 0] + strength * carrier, 0, 255)
    return np.asarray(Image.fromarray(channels.astype(np.uint8), "YCbCr").convert("RGB"))


def embed_document(
    source: Path,
    destination: Path,
    secret: bytes,
    session_id: str,
    strength: float = 2.2,
    dpi: int = 144,
) -> dict[str, float | int]:
    pages, sizes = load_pages(source, dpi=dpi)
    marked: list[np.ndarray] = []
    squared_error = 0.0
    pixel_values = 0
    for index, page in enumerate(pages):
        carrier = pattern(secret, session_id, index, page.shape[:2])
        result = embed_array(page, carrier, strength)
        difference = result.astype(np.float32) - page.astype(np.float32)
        squared_error += float(np.square(difference).sum())
        pixel_values += difference.size
        marked.append(result)

    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() == ".pdf":
        output = fitz.open()
        for page_image, (width, height) in zip(marked, sizes, strict=True):
            page = output.new_page(width=width, height=height)
            stream = io.BytesIO()
            Image.fromarray(page_image).save(stream, format="PNG", optimize=True)
            page.insert_image(page.rect, stream=stream.getvalue())
        output.save(destination, deflate=True)
        output.close()
    else:
        Image.fromarray(marked[0]).save(destination)

    mse = squared_error / max(pixel_values, 1)
    psnr = float("inf") if mse == 0 else 20.0 * math.log10(255.0 / math.sqrt(mse))
    return {"pages": len(marked), "psnr_db": round(psnr, 3), "strength": strength, "dpi": dpi}


def score_document(
    reference: Path,
    suspect: Path,
    secret: bytes,
    session_id: str,
    dpi: int = 144,
) -> float:
    prepared = prepare_score(reference, suspect, dpi=dpi)
    return score_prepared(prepared, secret, session_id)


def prepare_score(reference: Path, suspect: Path, dpi: int = 144) -> PreparedScore:
    """Prepare non-blind luma residuals for scoring many session carriers."""

    reference_pages, _ = load_pages(reference, dpi=dpi)
    suspect_pages, _ = load_pages(suspect, dpi=dpi)
    residuals: list[np.ndarray] = []
    residual_norms: list[float] = []
    shapes: list[tuple[int, int]] = []
    for index, (original, leaked) in enumerate(zip(reference_pages, suspect_pages, strict=False)):
        if leaked.shape[:2] != original.shape[:2]:
            leaked = np.asarray(
                Image.fromarray(leaked).resize(
                    (original.shape[1], original.shape[0]), Image.Resampling.LANCZOS
                )
            )
        residual = _luma(leaked) - _luma(original)
        residual -= float(residual.mean())
        residuals.append(residual)
        residual_norms.append(math.sqrt(float(np.sum(np.square(residual)))))
        shapes.append(original.shape[:2])
    return PreparedScore(
        residuals=residuals,
        residual_norms=residual_norms,
        shapes=shapes,
    )


def score_prepared(prepared: PreparedScore, secret: bytes, session_id: str) -> float:
    """Score one session against a residual prepared by :func:`prepare_score`."""

    scores: list[float] = []
    for index, (residual, residual_norm, shape) in enumerate(
        zip(
            prepared.residuals,
            prepared.residual_norms,
            prepared.shapes,
            strict=True,
        )
    ):
        carrier = pattern(secret, session_id, index, shape)
        numerator = float(np.sum(residual * carrier))
        denominator = residual_norm * math.sqrt(float(np.sum(np.square(carrier))))
        scores.append(0.0 if denominator == 0 else numerator / denominator)
    return float(np.mean(scores)) if scores else 0.0


def jpeg_attack(source: Path, destination: Path, quality: int = 55, dpi: int = 144) -> None:
    pages, _ = load_pages(source, dpi=dpi)
    buffer = io.BytesIO()
    Image.fromarray(pages[0]).save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)
    Image.open(buffer).convert("RGB").save(destination, format="JPEG", quality=quality)


def average_collusion(sources: list[Path], destination: Path, dpi: int = 144) -> None:
    if len(sources) < 2:
        raise ValueError("collusion simulation needs at least two copies")
    images = [load_pages(path, dpi=dpi)[0][0].astype(np.float32) for path in sources]
    height, width = images[0].shape[:2]
    aligned = [
        image
        if image.shape[:2] == (height, width)
        else np.asarray(
            Image.fromarray(image.astype(np.uint8)).resize((width, height), Image.Resampling.LANCZOS),
            dtype=np.float32,
        )
        for image in images
    ]
    colluded = np.clip(np.mean(aligned, axis=0), 0, 255).astype(np.uint8)
    Image.fromarray(colluded).save(destination, format="PNG")
