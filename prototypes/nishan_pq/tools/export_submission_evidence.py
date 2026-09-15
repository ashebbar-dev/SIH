#!/usr/bin/env python3
"""Run the NISHAN demo and export only non-secret, submission-safe evidence.

Private recipient keys, the authority watermark secret, and raw validator state stay
inside a temporary directory.  The output is suitable for a slide deck or review.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

import pymupdf as fitz
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "nishan-mpl"))
import matplotlib
import numpy as np
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from nishan.demo import run


NAVY = "#0B1F33"
CYAN = "#15B8A6"
AMBER = "#F4B942"
RED = "#E45B5B"
MUTED = "#75879A"


def _render_first_page(pdf: Path, output: Path, dpi: int = 144) -> np.ndarray:
    document = fitz.open(pdf)
    page = document[0]
    pixmap = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
    image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
        pixmap.height, pixmap.width, 3
    )
    Image.fromarray(image).save(output)
    document.close()
    return image.copy()


def _difference_panel(source: np.ndarray, marked: np.ndarray, output: Path) -> None:
    difference = marked.astype(np.int16) - source.astype(np.int16)
    amplified = np.clip(128 + 24 * difference, 0, 255).astype(np.uint8)
    crop = (80, 70, source.shape[1] - 80, min(source.shape[0] - 70, 720))
    source_image = Image.fromarray(source).crop(crop)
    marked_image = Image.fromarray(marked).crop(crop)
    residual_image = Image.fromarray(amplified).crop(crop)
    canvas = Image.new(
        "RGB",
        (source_image.width * 3 + 32, source_image.height + 64),
        "white",
    )
    for index, (label, image) in enumerate(
        [("SOURCE", source_image), ("MARKED", marked_image), ("24x RESIDUAL", residual_image)]
    ):
        x = index * (source_image.width + 16)
        canvas.paste(image, (x, 48))
        # PIL's default font keeps this script independent of machine fonts.
        from PIL import ImageDraw

        ImageDraw.Draw(canvas).text((x + 8, 16), label, fill=NAVY)
    canvas.save(output)


def _score_chart(demo_root: Path, output: Path) -> None:
    evidence_files = [
        ("JPEG Q55\nBob copy", demo_root / "evidence" / "bob-jpeg.json"),
        ("2-copy average\nAlice + Bob", demo_root / "evidence" / "alice-bob-coalition.json"),
        (
            "3-copy average\nAlice + Bob + Charlie",
            demo_root / "evidence" / "alice-bob-charlie-coalition.json",
        ),
    ]
    recipients = ["alice", "bob", "charlie"]
    labels = ["Alice", "Bob", "Charlie"]
    matrix: list[list[float]] = []
    thresholds: list[float] = []
    for _, path in evidence_files:
        evidence = json.loads(path.read_text())
        thresholds.append(float(evidence["detection_threshold"]))
        by_recipient = {item["recipient_id"]: item["score"] for item in evidence["ranking"]}
        matrix.append([float(by_recipient[name]) for name in recipients])

    figure, axes = plt.subplots(1, 3, figsize=(15.8, 4.6), sharey=True)
    colors = [CYAN, AMBER, MUTED]
    global_max = max(max(values) for values in matrix)
    global_min = min(min(values) for values in matrix)
    y_bottom = min(-450.0, global_min * 1.5)
    y_top = global_max * 1.16
    for axis, (title, _), values, threshold in zip(
        axes, evidence_files, matrix, thresholds, strict=True
    ):
        bars = axis.bar(labels, values, color=colors, width=0.64)
        axis.axhline(threshold, color=RED, linestyle="--", linewidth=1.5)
        axis.text(
            0.98,
            (threshold - y_bottom) / (y_top - y_bottom) + 0.025,
            f"Tardos threshold = {threshold:,.0f}",
            ha="right",
            transform=axis.transAxes,
            color=RED,
            fontsize=9,
        )
        axis.set_title(title, color=NAVY, weight="bold", fontsize=12, pad=10)
        axis.set_ylim(y_bottom, y_top)
        axis.grid(axis="y", alpha=0.16)
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.tick_params(axis="y", length=0, labelsize=9)
        for bar, value in zip(bars, values, strict=True):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                value + (230 if value >= 0 else -230),
                f"{value:,.0f}",
                ha="center",
                va="bottom" if value >= 0 else "top",
                fontsize=10,
                weight="bold",
                color=NAVY,
            )
    axes[0].set_ylabel("Tardos accusation score", color=NAVY)
    figure.suptitle(
        "Measured attribution: 52,500-symbol Tardos code · all 1,000 roster rows scored",
        fontsize=14,
        weight="bold",
        color=NAVY,
        y=0.98,
    )
    figure.subplots_adjust(left=0.07, right=0.99, bottom=0.16, top=0.76, wspace=0.20)
    figure.savefig(output, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def _write_public_result(summary: dict[str, object], output: Path) -> None:
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


def export(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nishan-evidence-") as directory:
        demo_root = Path(directory) / "demo"
        summary = run(demo_root)

        _write_public_result(summary, destination / "measured-results.json")
        shutil.copy2(demo_root / "source.pdf", destination / "synthetic-source.pdf")
        shutil.copy2(
            demo_root / "released" / "bob.pdf",
            destination / "bob-marked-live-text.pdf",
        )
        shutil.copy2(demo_root / "attacks" / "bob-jpeg-q55.jpg", destination / "bob-jpeg-q55.jpg")
        shutil.copy2(
            demo_root / "attacks" / "alice-bob-average.png",
            destination / "alice-bob-average.png",
        )
        shutil.copy2(
            demo_root / "attacks" / "alice-bob-charlie-average.png",
            destination / "alice-bob-charlie-average.png",
        )
        for filename in [
            "alice-overlay-removed.pdf",
            "alice-layout-normalized.pdf",
            "alice-both-carriers-removed.pdf",
            "alice-visual-on-bob-layout.pdf",
        ]:
            shutil.copy2(demo_root / "attacks" / filename, destination / filename)
        shutil.copy2(
            demo_root / "evidence" / "bob-jpeg.json",
            destination / "bob-jpeg-evidence.json",
        )
        shutil.copy2(
            demo_root / "evidence" / "alice-bob-coalition.json",
            destination / "alice-bob-coalition-evidence.json",
        )
        shutil.copy2(
            demo_root / "evidence" / "alice-bob-charlie-coalition.json",
            destination / "alice-bob-charlie-coalition-evidence.json",
        )
        for source_name, destination_name in [
            ("alice-direct-pdf.json", "alice-direct-pdf-evidence.json"),
            ("alice-overlay-removed.json", "alice-overlay-removed-evidence.json"),
            ("alice-layout-normalized.json", "alice-layout-normalized-evidence.json"),
            (
                "alice-both-carriers-removed.json",
                "alice-both-carriers-removed-evidence.json",
            ),
            ("visual-transplant-conflict.json", "visual-transplant-conflict-evidence.json"),
        ]:
            shutil.copy2(
                demo_root / "evidence" / source_name,
                destination / destination_name,
            )

        source = _render_first_page(demo_root / "source.pdf", destination / "source-page.png")
        marked = _render_first_page(
            demo_root / "released" / "bob.pdf", destination / "bob-marked-page.png"
        )
        _difference_panel(source, marked, destination / "imperceptibility-panel.png")
        _score_chart(demo_root, destination / "attribution-scores.png")

    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"submission-safe evidence written to {destination}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/nishan"),
        help="directory for public evidence (default: artifacts/nishan)",
    )
    args = parser.parse_args()
    export(args.output.resolve())


if __name__ == "__main__":
    main()
