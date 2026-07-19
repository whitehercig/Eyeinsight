"""Generate a compact, non-diagnostic clinician summary PDF."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


COPY = {
    "en": ("Visual Attention Screening Summary", "Data quality", "Attention score", "Screening indicator", "Estimated response latency", "Phase comparison", "AI-assisted screening support only. This report is not a diagnosis and is not the sole basis for clinical decisions.", "Gaze alignment and response latency are uncalibrated screen-gaze proxy estimates."),
    "ru": ("Сводка скрининга визуального внимания", "Качество данных", "Показатель внимания", "Скрининговый индикатор", "Оценочная задержка реакции", "Сравнение фаз", "Только AI-assisted поддержка скрининга. Отчёт не является диагнозом и не может быть единственным основанием для клинического решения.", "Выравнивание взгляда и задержка реакции являются некалиброванными proxy-оценками экранного взгляда."),
    "kz": ("Көрнекі зейін скринингі бойынша қорытынды", "Деректер сапасы", "Зейін көрсеткіші", "Скрининг индикаторы", "Бағаланған реакция кідірісі", "Кезеңдерді салыстыру", "Есеп диагноз емес және клиникалық шешімнің жалғыз негізі болмауы тиіс.", "Көзқарасты теңестіру мен реакция кідірісі калибрленбеген proxy-бағалар болып табылады."),
}


def create_clinical_report(output_path: Path, session_id: str, result: dict[str, Any], features: dict[str, Any], phases: list[dict[str, Any]], language: str) -> Path:
    labels = COPY.get(language, COPY["ru"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font = _font()
    canvas = Canvas(str(output_path), pagesize=A4)
    width, height, margin = *A4, 42
    canvas.setFillColor(colors.HexColor("#0F172A")); canvas.rect(0, height - 74, width, 74, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#2DD4BF")); canvas.setFont(font, 19); canvas.drawString(margin, height - 42, "EyeInsight")
    canvas.setFillColor(colors.white); canvas.setFont(font, 9); canvas.drawRightString(width - margin, height - 40, f"Session #{session_id[:8]}")
    cursor = height - 105
    canvas.setFillColor(colors.HexColor("#111827")); canvas.setFont(font, 14); canvas.drawString(margin, cursor, labels[0]); cursor -= 32
    cards = ((labels[1], f"{result['quality_score']:.0f}/100"), (labels[2], f"{float(features.get('attention_score', 0)):.0f}/100"), (labels[3], _indicator(result)), (labels[4], _latency(features)))
    card_width = (width - margin * 2 - 18) / 2
    for index, (label, value) in enumerate(cards):
        x, y = margin + (index % 2) * (card_width + 18), cursor - (index // 2) * 60
        canvas.setFillColor(colors.HexColor("#F1F5F9")); canvas.roundRect(x, y - 44, card_width, 47, 7, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#64748B")); canvas.setFont(font, 8); canvas.drawString(x + 10, y - 14, label)
        canvas.setFillColor(colors.HexColor("#0F766E")); canvas.setFont(font, 14); canvas.drawString(x + 10, y - 32, value)
    cursor -= 145
    canvas.setFillColor(colors.HexColor("#111827")); canvas.setFont(font, 11); canvas.drawString(margin, cursor, labels[5]); cursor -= 17
    header_x = (margin, margin + 195, margin + 300, margin + 420)
    canvas.setFillColor(colors.HexColor("#E2E8F0")); canvas.rect(margin, cursor - 13, width - margin * 2, 18, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#334155")); canvas.setFont(font, 7)
    for x, value in zip(header_x, ("Phase", "Attention", "Target alignment", "Response")): canvas.drawString(x + 5, cursor - 7, value)
    cursor -= 25
    for phase in phases[:6]:
        values = (str(phase.get("phase", "")).replace("_", " "), f"{float(phase.get('attention_ratio') or 0) * 100:.0f}%", f"{float(phase.get('target_alignment_ratio') or 0) * 100:.0f}%", _phase_latency(phase))
        canvas.setFillColor(colors.HexColor("#111827")); canvas.setFont(font, 7)
        for x, value in zip(header_x, values): canvas.drawString(x + 5, cursor, value)
        canvas.setStrokeColor(colors.HexColor("#E2E8F0")); canvas.line(margin, cursor - 6, width - margin, cursor - 6); cursor -= 21
    canvas.setFillColor(colors.HexColor("#64748B")); cursor = _wrap(canvas, labels[7], margin, cursor - 9, width - margin * 2, font, 7.5); _wrap(canvas, labels[6], margin, cursor - 7, width - margin * 2, font, 7.5)
    canvas.setFillColor(colors.HexColor("#94A3B8")); canvas.setFont(font, 7); canvas.drawRightString(width - margin, 24, "EyeInsight MVP - not for diagnostic use")
    canvas.save()
    return output_path


def _font() -> str:
    for candidate in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"):
        if os.path.isfile(candidate):
            pdfmetrics.registerFont(TTFont("EyeInsightUnicode", candidate)); return "EyeInsightUnicode"
    return "Helvetica"


def _indicator(result: dict[str, Any]) -> str:
    return "not generated" if result.get("risk_score") is None else f"{result['risk_score']:.0f}/100 ({result.get('risk_level', 'n/a')})"


def _latency(features: dict[str, Any]) -> str:
    value = features.get("estimated_response_latency_ms")
    return f"{float(value):.0f} ms" if value is not None else "not available"


def _phase_latency(phase: dict[str, Any]) -> str:
    value = phase.get("estimated_response_latency_ms")
    return f"{float(value):.0f} ms" if value is not None else "-"


def _wrap(canvas: Canvas, text: str, x: float, y: float, max_width: float, font: str, size: float) -> float:
    canvas.setFont(font, size); line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and canvas.stringWidth(candidate, font, size) > max_width:
            canvas.drawString(x, y, line); y -= size + 3; line = word
        else: line = candidate
    if line: canvas.drawString(x, y, line); y -= size + 3
    return y
