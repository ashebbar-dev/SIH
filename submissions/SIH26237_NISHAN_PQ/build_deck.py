#!/usr/bin/env python3
"""Build the six-slide SIH26237 submission from the official SIH template."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from deck_evidence import load_physical, speaker_notes, validate_safeguard_evidence


NAVY = "0B1F33"
BLUE = "24557A"
TEAL = "15B8A6"
TEAL_DARK = "087E73"
AMBER = "F4B942"
RED = "D95555"
INK = "172A3A"
MUTED = "617386"
PALE = "F3F7F9"
PALE_TEAL = "E8F7F4"
PALE_AMBER = "FFF6DE"
PALE_RED = "FDECEC"
WHITE = "FFFFFF"
GREY = "DCE5EA"
FONT = "Liberation Sans"


def rgb(value: str) -> RGBColor:
    return RGBColor.from_string(value)


def remove_shape(shape) -> None:
    element = shape._element
    element.getparent().remove(element)


def clear_slide_body(slide, *, title_slide: bool = False) -> None:
    """Keep official background/footer/logo; remove template body placeholders."""
    for shape in list(slide.shapes):
        text = getattr(shape, "text", "").strip()
        top = shape.top / 914400
        is_logo = shape.shape_type == 13 and shape.left / 914400 > 10.2 and top < 1.3
        is_footer = top > 6.85
        is_background = shape.left == 0 and shape.top == 0 and shape.width >= 12190000
        keep_header = title_slide and text == "SMART INDIA HACKATHON 2026"
        if is_logo or is_footer or is_background or keep_header:
            continue
        remove_shape(shape)


def box(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str = WHITE,
    line: str | None = GREY,
    radius: bool = True,
    line_width: float = 1.0,
):
    shape_type = (
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if radius else MSO_AUTO_SHAPE_TYPE.RECTANGLE
    )
    shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(line_width)
    return shape


def text(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    value: str,
    *,
    size: float = 16,
    color: str = INK,
    bold: bool = False,
    align=PP_ALIGN.LEFT,
    valign=MSO_ANCHOR.TOP,
    margin: float = 0.04,
    font: str = FONT,
):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(margin)
    frame.margin_right = Inches(margin)
    frame.margin_top = Inches(margin)
    frame.margin_bottom = Inches(margin)
    frame.vertical_anchor = valign
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    paragraph.space_before = Pt(0)
    paragraph.space_after = Pt(0)
    paragraph.line_spacing = 1.0
    run = paragraph.add_run()
    run.text = value
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = rgb(color)
    return shape


def rich_text(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    runs: list[tuple[str, float, str, bool]],
    *,
    margin: float = 0.04,
    valign=MSO_ANCHOR.TOP,
):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(margin)
    frame.margin_right = Inches(margin)
    frame.margin_top = Inches(margin)
    frame.margin_bottom = Inches(margin)
    frame.vertical_anchor = valign
    paragraph = frame.paragraphs[0]
    paragraph.space_before = Pt(0)
    paragraph.space_after = Pt(0)
    for value, size, color, bold in runs:
        run = paragraph.add_run()
        run.text = value
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = rgb(color)
    return shape


def bullet_list(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    items: list[str],
    *,
    size: float = 13,
    color: str = INK,
    bullet_color: str = TEAL,
    gap: float = 3,
):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.02)
    frame.margin_right = Inches(0.02)
    frame.margin_top = Inches(0.02)
    frame.margin_bottom = Inches(0.02)
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.space_before = Pt(0)
        paragraph.space_after = Pt(gap)
        paragraph.line_spacing = 1.0
        run_bullet = paragraph.add_run()
        run_bullet.text = "●  "
        run_bullet.font.name = FONT
        run_bullet.font.size = Pt(max(size - 2, 8))
        run_bullet.font.color.rgb = rgb(bullet_color)
        run_text = paragraph.add_run()
        run_text.text = item
        run_text.font.name = FONT
        run_text.font.size = Pt(size)
        run_text.font.color.rgb = rgb(color)
    return shape


def pill(slide, x, y, w, label, *, fill=PALE_TEAL, color=TEAL_DARK, size=10.5):
    box(slide, x, y, w, 0.34, fill=fill, line=None)
    text(
        slide,
        x,
        y + 0.01,
        w,
        0.3,
        label,
        size=size,
        color=color,
        bold=True,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
        margin=0,
    )


def section_header(slide, title_value: str, team_name: str, number: int) -> None:
    text(slide, 0.62, 0.20, 9.55, 0.60, title_value, size=27, color=NAVY, bold=True)
    display_name = "[TEAM NAME]" if team_name.startswith("[") else team_name
    pill(slide, 0.62, 0.83, 1.52, display_name, fill=PALE_TEAL, color=TEAL_DARK, size=9)


def arrow(slide, x: float, y: float, w: float = 0.25, h: float = 0.34, color: str = TEAL):
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.CHEVRON, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(color)
    shape.line.fill.background()
    return shape


def small_card(slide, x, y, w, h, number, title_value, body, *, accent=TEAL):
    box(slide, x, y, w, h, fill=WHITE, line=GREY)
    circle = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.OVAL, Inches(x + 0.13), Inches(y + 0.14), Inches(0.34), Inches(0.34)
    )
    circle.fill.solid()
    circle.fill.fore_color.rgb = rgb(accent)
    circle.line.fill.background()
    text(
        slide,
        x + 0.13,
        y + 0.14,
        0.34,
        0.34,
        str(number),
        size=10,
        color=WHITE,
        bold=True,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
        margin=0,
    )
    text(slide, x + 0.55, y + 0.10, w - 0.67, 0.40, title_value, size=11.4, color=NAVY, bold=True)
    text(slide, x + 0.14, y + 0.55, w - 0.28, h - 0.64, body, size=9.4, color=MUTED)


def draw_document_hero(slide) -> None:
    box(slide, 7.95, 1.33, 4.58, 4.92, fill=PALE, line=None)
    doc = box(slide, 9.00, 1.73, 2.18, 2.92, fill=WHITE, line=BLUE, radius=False, line_width=1.6)
    # folded corner
    fold = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RIGHT_TRIANGLE, Inches(10.60), Inches(1.73), Inches(0.58), Inches(0.58)
    )
    fold.rotation = 180
    fold.fill.solid()
    fold.fill.fore_color.rgb = rgb(PALE_TEAL)
    fold.line.color.rgb = rgb(BLUE)
    text(slide, 9.30, 2.30, 1.58, 0.40, "RESTRICTED", size=11.5, color=RED, bold=True, align=PP_ALIGN.CENTER)
    for i, width in enumerate([1.25, 1.48, 1.05, 1.38]):
        bar = box(slide, 9.34, 2.92 + i * 0.28, width, 0.065, fill=GREY, line=None, radius=False)
    # fingerprint-like rings
    for i in range(4):
        ring = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ARC,
            Inches(9.64 - i * 0.08),
            Inches(3.24 - i * 0.08),
            Inches(0.72 + i * 0.16),
            Inches(0.90 + i * 0.16),
        )
        ring.fill.background()
        ring.line.color.rgb = rgb(TEAL)
        ring.line.width = Pt(2.2)
    # ledger validators around document
    positions = [(8.35, 2.00), (11.47, 2.02), (8.38, 4.95), (11.45, 4.92)]
    for index, (x, y) in enumerate(positions, 1):
        node = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL, Inches(x), Inches(y), Inches(0.54), Inches(0.54))
        node.fill.solid()
        node.fill.fore_color.rgb = rgb(NAVY if index < 4 else MUTED)
        node.line.fill.background()
        text(slide, x, y, 0.54, 0.54, f"V{index}", size=9, color=WHITE, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)
    pill(slide, 8.64, 5.55, 3.26, "RESEARCH PROTOTYPE", fill=NAVY, color=WHITE, size=10)


def slide_one(prs: Presentation, team_id: str, team_name: str) -> None:
    slide = prs.slides[0]
    clear_slide_body(slide, title_slide=True)
    text(slide, 0.70, 1.14, 6.72, 0.62, "NISHAN-PQ", size=34, color=NAVY, bold=True)
    text(
        slide,
        0.72,
        1.78,
        6.70,
        0.84,
        "Accountable decryption.\nVerifiable source-copy evidence.",
        size=19,
        color=TEAL_DARK,
        bold=True,
    )
    text(
        slide,
        0.72,
        2.67,
        6.52,
        0.54,
        "When a protected copy leaks, connect it to a signed release session—or return inconclusive.",
        size=14.2,
        color=INK,
        bold=True,
    )
    box(slide, 0.68, 3.28, 6.72, 2.91, fill=WHITE, line=GREY)
    fields = [
        ("Problem Statement ID", "SIH26237"),
        (
            "Problem Statement Title",
            "Cryptographic Attribution and Immutable Decryption Provenance for Multi-Recipient Encrypted Document Distribution",
        ),
        ("Theme", "Blockchain & Cybersecurity"),
        ("PS Category", "Software"),
        ("Team ID", team_id),
        ("Team Name (Registered on portal)", team_name),
    ]
    y = 3.52
    for index, (label, value) in enumerate(fields):
        height = 0.71 if index == 1 else 0.39
        text(slide, 0.95, y, 2.30, height, label.upper(), size=8.8, color=MUTED, bold=True)
        value_color = RED if value.startswith("[") else INK
        text(slide, 3.22, y - 0.01, 3.82, height, value, size=10.4 if index == 1 else 11.8, color=value_color, bold=index != 1)
        y += height
    draw_document_hero(slide)
    pill(slide, 8.34, 6.00, 3.84, "FRESH SAFEGUARDS · 12/12 · REAL PQC", fill=PALE_AMBER, color="7A5100", size=8.6)
    text(slide, 8.58, 6.37, 3.34, 0.25, "Evidence status · 12 September 2026", size=8.5, color=MUTED, align=PP_ALIGN.CENTER)


def digital_summary(
    measured: dict,
    tardos_benchmark: dict,
    tardos_trials: dict,
    end_to_end_trials: dict,
) -> dict[str, int | float]:
    """Derive every displayed experimental count from the saved JSON inputs."""
    trial_summaries = tardos_trials["summary"]
    metrics = tardos_benchmark["carrier"]["metrics_by_user"]
    if not metrics:
        raise ValueError("Tardos benchmark has no released-PDF metrics")
    pages_per_pdf = {int(item["released_document"]["pages"]) for item in metrics}
    if len(pages_per_pdf) != 1:
        raise ValueError(f"Tardos benchmark has inconsistent PDF page counts: {sorted(pages_per_pdf)}")
    issued_trials = end_to_end_trials["trials"]
    issued_rows = [int(item["tardos_user_index"]) for item in issued_trials]
    if not issued_rows:
        raise ValueError("end-to-end JPEG evidence has no issued sessions")
    other_scores = [item.get("maximum_other_issued_score") for item in issued_trials]
    layout_symbols = int(
        measured["dual_carrier_attack_decisions"]
        ["alice_visual_transplanted_onto_bob_layout"]
        ["layout_observation"]
        ["encoded_bits"]
    )
    return {
        "jpeg_exact": int(end_to_end_trials["summary"]["exact_session_attributions"]),
        "jpeg_trials": int(end_to_end_trials["parameters"]["trials"]),
        "jpeg_false": int(end_to_end_trials["summary"]["false_accused_codebook_rows_total"]),
        "jpeg_mean": float(end_to_end_trials["summary"]["expected_score_mean"]),
        "jpeg_sd": float(end_to_end_trials["summary"]["expected_score_population_sd"]),
        "roster_rows": int(end_to_end_trials["parameters"]["roster_rows_scored_per_trial"]),
        "issued_session_count": len(issued_trials),
        "issued_row_min": min(issued_rows),
        "issued_row_max": max(issued_rows),
        "other_score_null": sum(value is None for value in other_scores),
        "other_score_nonnull": sum(value is not None for value in other_scores),
        "attack_cases": int(tardos_benchmark["attack_count"]),
        "codebooks": int(tardos_trials["parameters"]["trials"]),
        "strategy_count": len(trial_summaries),
        "code_cases": sum(int(item["trials"]) for item in trial_summaries.values()),
        "code_all_five": sum(
            int(item["all_colluders_recovered"]) for item in trial_summaries.values()
        ),
        "pdf_count": len(metrics),
        "pages_per_pdf": next(iter(pages_per_pdf)),
        "psnr_mean": sum(
            float(item["released_document"]["psnr_db"]) for item in metrics
        )
        / len(metrics),
        "layout_symbols": layout_symbols,
    }


def slide_two(
    prs: Presentation,
    team_name: str,
    physical: dict,
    digital: dict,
) -> None:
    slide = prs.slides[1]
    clear_slide_body(slide)
    section_header(slide, "IDEA TITLE / PROPOSED SOLUTION", team_name, 2)
    text(
        slide,
        2.30,
        0.84,
        8.00,
        0.38,
        "One encrypted source. Signed, session-specific releases.",
        size=15.2,
        color=TEAL_DARK,
        bold=True,
    )
    capabilities = [
        (
            "01",
            "Session-specific release",
            "Serialized row + session allocation. Marked output is signed before publication.",
            TEAL,
        ),
        (
            "02",
            "Commit before release",
            "ML-DSA receipt enters the local 3-of-4 log. Configured mode checks signed witness state under a caller-provisioned key pin.",
            BLUE,
        ),
        (
            "03",
            "Conservative trace",
            "Clean PDFs need two-channel agreement. Missing evidence produces a lead or inconclusive result.",
            AMBER,
        ),
    ]
    for index, (number, title_value, body, accent) in enumerate(capabilities):
        x = 0.66 + index * 4.12
        box(slide, x, 1.48, 3.82, 2.13, fill=WHITE, line=accent, line_width=1.4)
        text(slide, x + 0.20, 1.68, 0.54, 0.40, number, size=19, color=accent, bold=True)
        text(slide, x + 0.86, 1.71, 2.70, 0.34, title_value, size=14.4, color=NAVY, bold=True)
        text(slide, x + 0.22, 2.25, 3.36, 1.03, body, size=13.0, color=INK)

    box(slide, 0.66, 3.92, 12.06, 1.55, fill=PALE, line=None)
    text(slide, 0.90, 4.14, 11.58, 0.30, "CONTROLLED RELEASE → EVIDENCE", size=11.2, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
    flow = [
        ("Encrypt once", "AES-256-GCM"),
        ("Wrap key", "ML-KEM-768"),
        ("Mark", "visual + layout"),
        ("Sign + commit", "ML-DSA-65"),
        ("Trace", "attribute / abstain"),
    ]
    x = 0.90
    for index, (title_value, body) in enumerate(flow):
        box(slide, x, 4.57, 2.05, 0.60, fill=WHITE, line=GREY)
        text(slide, x + 0.08, 4.64, 1.89, 0.22, title_value, size=10.8, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        text(slide, x + 0.08, 4.89, 1.89, 0.18, body, size=8.7, color=MUTED, align=PP_ALIGN.CENTER)
        x += 2.33
        if index < len(flow) - 1:
            arrow(slide, x - 0.22, 4.73, w=0.16, h=0.25)
    box(slide, 0.66, 5.77, 12.06, 0.49, fill=PALE_TEAL, line=None)
    text(
        slide,
        0.86,
        5.88,
        11.66,
        0.24,
        "Outcome: verifiable source-copy evidence—not a claim about which human disclosed the file.",
        size=12.1,
        color=TEAL_DARK,
        bold=True,
        align=PP_ALIGN.CENTER,
    )


def architecture_node(slide, x, y, w, title_value, body, *, fill=WHITE, accent=TEAL):
    box(slide, x, y, w, 1.08, fill=fill, line=accent, line_width=1.3)
    text(slide, x + 0.10, y + 0.10, w - 0.20, 0.30, title_value, size=11.2, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    text(slide, x + 0.10, y + 0.45, w - 0.20, 0.48, body, size=8.9, color=MUTED, align=PP_ALIGN.CENTER)


def slide_three(prs: Presentation, team_name: str) -> None:
    slide = prs.slides[2]
    clear_slide_body(slide)
    section_header(slide, "TECHNICAL APPROACH", team_name, 3)
    text(slide, 2.30, 0.84, 9.80, 0.34, "Commit and witness before release (configured mode)", size=15.2, color=TEAL_DARK, bold=True)
    box(slide, 0.58, 1.32, 12.18, 3.72, fill=PALE, line=None)
    pill(slide, 0.82, 1.51, 2.78, "MANAGED-PROCESS TRUST BOUNDARY", fill=NAVY, color=WHITE, size=8.5)
    pill(slide, 9.02, 1.51, 3.24, "CO-LOCATED VALIDATORS + WITNESS", fill=PALE_AMBER, color="7A5100", size=8.0)
    nodes = [
        (0.82, 2.08, 1.72, "Validate", "package + ledger\n+ pinned state"),
        (2.80, 2.08, 1.72, "Allocate + mark", "serialized row/session\nvisual + layout"),
        (4.78, 2.08, 1.72, "Recipient sign", "ML-DSA-65\nrelease receipt"),
        (6.76, 2.08, 1.72, "Quorum append", "3-of-4 local log\nthen re-audit"),
        (8.74, 2.08, 1.72, "Checkpoint", "verify actual key pin\n+ signed head"),
        (10.72, 2.08, 1.72, "Publish", "atomic replace\nmarked copy"),
    ]
    for index, (x, y, w, title_value, body) in enumerate(nodes):
        architecture_node(slide, x, y, w, title_value, body, fill=WHITE, accent=TEAL if index < 5 else AMBER)
        if index < len(nodes) - 1:
            arrow(slide, x + w + 0.07, y + 0.38, w=0.16, h=0.28)
    box(slide, 1.50, 3.55, 10.36, 0.93, fill=WHITE, line=GREY)
    text(slide, 1.76, 3.72, 2.30, 0.28, "TRACE PATH · READ ONLY", size=11.2, color=NAVY, bold=True)
    text(slide, 4.00, 3.68, 7.54, 0.45, "retained source + suspect → PDF type guard → visual/layout agreement → signed session  |  otherwise INCONCLUSIVE", size=11.4, color=INK, bold=True)

    box(slide, 0.62, 5.28, 7.15, 0.93, fill=PALE_TEAL, line=None)
    text(slide, 0.86, 5.44, 2.10, 0.27, "FAIL-CLOSED NOW", size=11.3, color=TEAL_DARK, bold=True)
    text(slide, 2.72, 5.40, 4.77, 0.48, "wrong pin (release) · rollback (release + trace) · raster/low-capacity attribution · checkpoint publication", size=10.8, color=NAVY, bold=True)
    box(slide, 7.98, 5.28, 4.76, 0.93, fill=PALE_AMBER, line=None)
    text(slide, 8.22, 5.44, 1.52, 0.27, "BOUNDARY", size=11.3, color="8A5D00", bold=True)
    text(slide, 9.58, 5.38, 2.88, 0.51, "keys + replicas remain under one local administrator", size=11.2, color=NAVY, bold=True)


def metric_badge(slide, x, y, w, number, caption, *, fill=PALE_TEAL, accent=TEAL_DARK):
    box(slide, x, y, w, 0.86, fill=fill, line=None)
    text(slide, x + 0.06, y + 0.08, w - 0.12, 0.34, number, size=18, color=accent, bold=True, align=PP_ALIGN.CENTER)
    text(slide, x + 0.08, y + 0.48, w - 0.16, 0.25, caption, size=8.5, color=MUTED, bold=True, align=PP_ALIGN.CENTER)


def risk_row(slide, y, title_value, truth, gate, severity="HIGH"):
    box(slide, 6.06, y, 6.54, 0.94, fill=WHITE, line=GREY)
    fill = PALE_RED if severity == "HIGH" else PALE_AMBER
    color = RED if severity == "HIGH" else "9A6900"
    pill(slide, 6.22, y + 0.15, 0.72, severity, fill=fill, color=color, size=8.4)
    text(slide, 7.10, y + 0.10, 1.50, 0.28, title_value, size=10.4, color=NAVY, bold=True)
    text(slide, 8.58, y + 0.10, 3.78, 0.28, truth, size=9.0, color=MUTED)
    text(slide, 7.10, y + 0.49, 5.24, 0.29, "UNRESOLVED  ·  " + gate, size=8.9, color=TEAL_DARK, bold=True)


def slide_four(
    prs: Presentation,
    team_name: str,
    physical: dict,
    digital: dict,
    safeguards: dict,
) -> None:
    slide = prs.slides[3]
    clear_slide_body(slide)
    section_header(slide, "FEASIBILITY AND VIABILITY", team_name, 4)
    text(slide, 2.30, 0.84, 9.80, 0.34, "Fresh safeguards first; historical visual results and physical evidence stay separate.", size=14.5, color=TEAL_DARK, bold=True)

    box(slide, 0.62, 1.37, 6.22, 4.81, fill=PALE_TEAL, line=None)
    text(slide, 0.91, 1.62, 2.18, 0.31, "FRESH · CURRENT CODE", size=12.2, color=NAVY, bold=True)
    text(slide, 0.91, 2.00, 2.20, 0.58, f"{len(safeguards['cases'])}/12", size=31, color=TEAL_DARK, bold=True)
    text(slide, 2.35, 2.03, 4.05, 0.55, "safeguard scenarios passed\n59/59 final-code tests · real PQC · 19 hashes verified", size=11.8, color=INK, bold=True)
    controls = [
        "Serialized release: concurrent rows differ; next release succeeds",
        "Pinned mode: wrong pin blocks release; rollback blocks release + trace",
        "Checkpoint failure publishes nothing; existing output is preserved",
        "Clean PDF corroborates; raster and low-capacity PDF abstain",
    ]
    bullet_list(slide, 0.92, 2.80, 5.62, 2.13, controls, size=12.2, gap=7)
    text(slide, 0.92, 5.05, 5.62, 0.25, "Six-person team · existing offline laptop prototype · repeatable saved evidence", size=10.4, color=TEAL_DARK, bold=True, align=PP_ALIGN.CENTER)
    pill(slide, 0.92, 5.45, 5.62, "SYNTHETIC OFFLINE SCENARIOS · NOT POPULATION EXPERIMENTS", fill=NAVY, color=WHITE, size=8.2)

    box(slide, 7.05, 1.37, 5.67, 2.18, fill=PALE_AMBER, line=None)
    text(slide, 7.33, 1.62, 5.12, 0.31, "HISTORICAL VISUAL FIXTURES", size=12.2, color=NAVY, bold=True)
    text(slide, 7.33, 2.08, 5.12, 0.52, f"{digital['jpeg_exact']}/{digital['jpeg_trials']} JPEG-Q55 visual-channel trials", size=17.2, color="8A5D00", bold=True)
    text(slide, 7.33, 2.66, 5.12, 0.60, f"One document/codebook; repeated sessions. {digital['pdf_count']} one-page PDFs retained text; mean PSNR {digital['psnr_mean']:.2f} dB.", size=11.5, color=INK)

    box(slide, 7.05, 3.76, 5.67, 2.42, fill=WHITE, line=GREY)
    text(slide, 7.33, 4.01, 5.12, 0.52, "Physical recovery remains experimental: 0/4 at the shipped threshold", size=14.0, color=RED, bold=True)
    text(slide, 7.33, 4.63, 5.12, 0.66, "Exploratory profiles recover the same 1/4 capture. No added capture; no robust physical claim.", size=12.0, color=INK, bold=True)
    text(slide, 7.33, 5.45, 5.12, 0.42, "Digital PDF corroboration; raster-only matches are research leads", size=11.3, color=TEAL_DARK, bold=True)


def benefit_card(slide, x, y, w, title_value, body, *, number=None, accent=TEAL):
    box(slide, x, y, w, 1.16, fill=WHITE, line=GREY)
    if number:
        text(slide, x + 0.14, y + 0.12, 0.62, 0.38, number, size=17, color=accent, bold=True)
        title_x = x + 0.78
        title_w = w - 0.92
    else:
        title_x = x + 0.16
        title_w = w - 0.32
    text(slide, title_x, y + 0.13, title_w, 0.30, title_value, size=11.5, color=NAVY, bold=True)
    text(slide, x + 0.16, y + 0.53, w - 0.32, 0.48, body, size=9.2, color=MUTED)


def slide_five(prs: Presentation, team_name: str) -> None:
    slide = prs.slides[4]
    clear_slide_body(slide)
    section_header(slide, "IMPACT AND BENEFITS", team_name, 5)
    text(slide, 2.30, 0.84, 9.92, 0.34, "A five-minute judge demo shows both the useful answer and the refusal to overclaim.", size=14.4, color=TEAL_DARK, bold=True)
    box(slide, 0.62, 1.37, 7.05, 4.84, fill=PALE, line=None)
    text(slide, 0.91, 1.62, 6.49, 0.31, "JUDGE-DRIVEN DEMO · OFFLINE LAPTOP", size=12.4, color=NAVY, bold=True)
    demo_steps = [
        ("01", "Issue", "Alice + Bob + repeated session → distinct rows and signed copy hashes"),
        ("02", "Associate", "Clean PDF → two channels agree on one signed source copy"),
        ("03", "Abstain", "Rendered transplant / short PDF → inconclusive; research lead retained"),
        ("04", "Block", "Wrong pin blocks release; rollback blocks release + trace; checkpoint fail publishes nothing"),
    ]
    y = 2.05
    for number, title_value, body in demo_steps:
        box(slide, 0.91, y, 6.47, 0.79, fill=WHITE, line=GREY)
        text(slide, 1.08, y + 0.16, 0.48, 0.30, number, size=14.5, color=TEAL_DARK, bold=True)
        text(slide, 1.67, y + 0.14, 1.07, 0.29, title_value, size=12.3, color=NAVY, bold=True)
        text(slide, 2.71, y + 0.12, 4.45, 0.48, body, size=11.2, color=INK)
        y += 0.91
    pill(slide, 0.93, 5.78, 6.43, "VALUE: A DEFENSIBLE SESSION LEAD—OR A DEFENSIBLE INCONCLUSIVE", fill=NAVY, color=WHITE, size=8.3)

    box(slide, 7.89, 1.37, 4.83, 2.14, fill=PALE_TEAL, line=None)
    text(slide, 8.17, 1.62, 4.27, 0.31, "OPERATIONAL BENEFIT", size=12.3, color=NAVY, bold=True)
    bullet_list(slide, 8.17, 2.06, 4.27, 1.10, [
        "Air-gapped workflow; no cloud KMS or public chain",
        "Evidence tied to a release session, not a vague access log",
        "Explicit refusal when high-assurance evidence is missing",
    ], size=11.4, gap=6)

    box(slide, 7.89, 3.72, 4.83, 2.49, fill=PALE_AMBER, line=None)
    text(slide, 8.17, 3.97, 4.27, 0.31, "NARROW SECOND-ROUND ROADMAP", size=12.0, color=NAVY, bold=True)
    bullet_list(slide, 8.17, 4.40, 4.27, 1.34, [
        "Independent administrator + key custody",
        "Larger multi-recipient, multi-page corpus",
        "Representative held-out print / camera tests",
        "Portable independent evidence verifier",
    ], size=11.2, gap=5, bullet_color=AMBER)
    text(slide, 8.17, 5.83, 4.27, 0.20, "No GPU or ESP32 required for the measured demo.", size=9.1, color=MUTED, bold=True)


def reference_item(slide, y, number, title_value, link_label):
    circle = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL, Inches(0.72), Inches(y), Inches(0.28), Inches(0.28))
    circle.fill.solid()
    circle.fill.fore_color.rgb = rgb(TEAL)
    circle.line.fill.background()
    text(slide, 0.72, y, 0.28, 0.28, str(number), size=8.5, color=WHITE, bold=True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0)
    text(slide, 1.12, y - 0.02, 5.47, 0.23, title_value, size=9.6, color=NAVY, bold=True)
    text(slide, 1.12, y + 0.22, 5.47, 0.22, link_label, size=7.8, color=MUTED)


def slide_six(prs: Presentation, team_name: str, repository_url: str) -> None:
    slide = prs.slides[5]
    clear_slide_body(slide)
    section_header(slide, "RESEARCH AND REFERENCES", team_name, 6)
    text(slide, 0.68, 1.17, 5.92, 0.30, "PRIMARY SOURCES & PRIOR ART", size=13.3, color=NAVY, bold=True)
    references = [
        ("Official SIH26237 problem statement", "sih.gov.in/sih2026PS"),
        ("NIST FIPS 203 / 204 — ML-KEM / ML-DSA", "csrc.nist.gov/pubs/fips/203/final · /fips/204/final"),
        ("FontCode — established glyph perturbation", "cs.columbia.edu/cg/fontcode/"),
        ("PQFabric — prior permissioned PQ ledger work", "arXiv:2010.06571"),
        ("Tardos fingerprint codes", "renyi.hu/~tardos/fingerprint.pdf"),
        ("Saved fresh + historical evidence", "demo/results.json · artifacts/nishan/*.json · scores.json"),
        ("Public repository", repository_url),
    ]
    y = 1.62
    for index, (title_value, link) in enumerate(references, 1):
        reference_item(slide, y, index, title_value, link)
        y += 0.64

    box(slide, 6.84, 1.19, 5.83, 4.92, fill=PALE, line=None)
    text(slide, 7.12, 1.49, 5.26, 0.33, "DIFFERENTIATED INTEGRATION", size=14.0, color=NAVY, bold=True)
    box(slide, 7.12, 1.98, 5.28, 1.45, fill=WHITE, line=GREY)
    text(slide, 7.34, 2.18, 4.84, 0.29, "ESTABLISHED COMPONENTS", size=10.3, color=MUTED, bold=True)
    text(slide, 7.34, 2.61, 4.84, 0.51, "PQC standards, traitor-tracing codes, document marks and permissioned ledgers all have prior art.", size=12.0, color=INK, bold=True)
    arrow(slide, 9.53, 3.54, w=0.36, h=0.29, color=AMBER)
    box(slide, 7.12, 3.95, 5.28, 1.63, fill=PALE_TEAL, line=None)
    text(slide, 7.34, 4.16, 4.84, 0.29, "ENGINEERING CONTRIBUTION", size=10.3, color=TEAL_DARK, bold=True)
    text(slide, 7.34, 4.55, 4.84, 0.84, "Tested integration of PQ-signed marked release, configured pinned-checkpoint gating and conservative two-channel PDF evidence.", size=12.4, color=NAVY, bold=True)
    pill(slide, 7.14, 5.72, 5.22, "INTEGRATION CLAIM · NOT A FIRST-EVER CLAIM", fill=NAVY, color=WHITE, size=8.4)


def delete_last_slide(prs: Presentation) -> None:
    slide_id = prs.slides._sldIdLst[-1]
    prs.part.drop_rel(slide_id.rId)
    prs.slides._sldIdLst.remove(slide_id)


def build(
    template: Path,
    evidence_chart: Path,
    metrics_path: Path,
    tardos_benchmark_path: Path,
    tardos_trials_path: Path,
    end_to_end_trials_path: Path,
    output: Path,
    team_id: str,
    team_name: str,
    *,
    physical_path: Path | None = None,
    safeguard_path: Path | None = None,
    repository_url: str = "[INSERT PUBLIC REPOSITORY LINK BEFORE UPLOAD]",
) -> None:
    """Build the deck.

    ``evidence_chart`` remains in the positional API for compatibility with the
    archived builder and existing callers. Slide 2 now uses editable evidence
    cards, so that image path is intentionally not read.
    """
    prs = Presentation(template)
    measured = json.loads(metrics_path.read_text())
    tardos_benchmark = json.loads(tardos_benchmark_path.read_text())
    tardos_trials = json.loads(tardos_trials_path.read_text())
    end_to_end_trials = json.loads(end_to_end_trials_path.read_text())
    if physical_path is None:
        physical_path = (
            Path(__file__).resolve().parents[2]
            / "research"
            / "evidence"
            / "nishan-bias-physical-2026-09-10"
            / "scores.json"
        )
    if safeguard_path is None:
        safeguard_path = (
            Path(__file__).resolve().parents[2]
            / "research"
            / "evidence"
            / "nishan-selection-2026-09-12"
            / "demo"
            / "results.json"
        )
    physical = load_physical(physical_path)
    safeguards = validate_safeguard_evidence(json.loads(safeguard_path.read_text()))
    digital = digital_summary(
        measured,
        tardos_benchmark,
        tardos_trials,
        end_to_end_trials,
    )
    if len(prs.slides) != 7:
        raise ValueError(f"expected 7-slide official template, got {len(prs.slides)}")
    delete_last_slide(prs)
    slide_one(prs, team_id, team_name)
    slide_two(
        prs,
        team_name,
        physical,
        digital,
    )
    slide_three(prs, team_name)
    slide_four(
        prs,
        team_name,
        physical,
        digital,
        safeguards,
    )
    slide_five(prs, team_name)
    slide_six(prs, team_name, repository_url)
    notes = speaker_notes(
        physical,
        team_id=team_id,
        team_name=team_name,
        repository_url=repository_url,
        digital=digital,
        safeguards=safeguards,
    )
    for slide, note in zip(prs.slides, notes, strict=True):
        slide.notes_slide.notes_text_frame.text = note
    prs.core_properties.title = "NISHAN-PQ — SIH26237 Idea Submission"
    prs.core_properties.subject = "Smart India Hackathon 2026"
    prs.core_properties.author = team_name
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output)
    notes_path = output.with_name(f"{output.stem}_speaker_notes.md")
    notes_path.write_text(
        "# NISHAN-PQ speaker notes and audit record\n\n"
        + "\n\n".join(f"## Slide {index}\n\n{note}" for index, note in enumerate(notes, 1))
        + "\n"
    )
    print(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--template",
        type=Path,
        default=Path("resources/SIH2026-IDEA-Presentation-Format.pptx"),
    )
    parser.add_argument(
        "--evidence-chart",
        type=Path,
        default=Path("artifacts/nishan/attribution-scores.png"),
        help="compatibility-only legacy argument; the current deck uses editable evidence cards",
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("artifacts/nishan/measured-results.json"),
    )
    parser.add_argument(
        "--tardos-benchmark",
        type=Path,
        default=Path("artifacts/nishan/tardos-pdf-benchmark.json"),
    )
    parser.add_argument(
        "--tardos-trials",
        type=Path,
        default=Path("artifacts/nishan/tardos-independent-codebook-study.json"),
    )
    parser.add_argument(
        "--end-to-end-trials",
        type=Path,
        default=Path("artifacts/nishan/end-to-end-jpeg-trials.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx"),
    )
    parser.add_argument("--team-id", default="[ENTER TEAM ID]")
    parser.add_argument("--team-name", default="[ENTER REGISTERED TEAM NAME]")
    parser.add_argument(
        "--physical-evidence",
        type=Path,
        default=None,
        help="validated physical score JSON; defaults to the fixed documented evidence",
    )
    parser.add_argument(
        "--repository-url",
        default="[INSERT PUBLIC REPOSITORY LINK BEFORE UPLOAD]",
    )
    parser.add_argument(
        "--safeguard-evidence",
        type=Path,
        default=None,
        help="fresh validated 12-scenario safeguard report; defaults to the reviewed demo",
    )
    args = parser.parse_args()
    build(
        args.template.resolve(),
        args.evidence_chart.resolve(),
        args.metrics.resolve(),
        args.tardos_benchmark.resolve(),
        args.tardos_trials.resolve(),
        args.end_to_end_trials.resolve(),
        args.output.resolve(),
        args.team_id,
        args.team_name,
        physical_path=args.physical_evidence.resolve() if args.physical_evidence else None,
        safeguard_path=args.safeguard_evidence.resolve() if args.safeguard_evidence else None,
        repository_url=args.repository_url,
    )


if __name__ == "__main__":
    main()
