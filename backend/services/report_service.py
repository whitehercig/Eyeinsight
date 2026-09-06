"""Generate a compact, non-diagnostic technical session PDF."""

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
    "en": {
        "title": "Visual attention session report",
        "session": "Session",
        "quality": "Data quality",
        "attention": "Technical attention proxy",
        "usable": "Usable frames",
        "face": "Face visibility",
        "tracking": "Tracking quality",
        "latency": "Estimated response latency",
        "phases": "Phase comparison",
        "heatmap": "Estimated gaze distribution",
        "status": "Technical processing completed. No clinical risk score was generated.",
        "notice": "Research prototype only. This report is not a diagnosis, a validated medical test, or a basis for clinical decisions.",
        "proxy": "Attention, gaze alignment, heatmap and response latency are uncalibrated camera-based proxy estimates.",
        "phase": "Phase", "phase_attention": "Attention proxy", "alignment": "Target alignment", "response": "Response",
        "footer": "EyeInsight MVP · technical prototype report",
        "demo": "SYNTHETIC DEMO — no person was recorded and no personal data was used.",
    },
    "ru": {
        "title": "Технический отчёт сессии визуального внимания",
        "session": "Сессия",
        "quality": "Качество данных",
        "attention": "Технический прокси внимания",
        "usable": "Пригодные кадры",
        "face": "Видимость лица",
        "tracking": "Качество отслеживания",
        "latency": "Оценочная задержка реакции",
        "phases": "Сравнение фаз",
        "heatmap": "Оценочное распределение взгляда",
        "status": "Техническая обработка завершена. Клиническая оценка риска не формировалась.",
        "notice": "Только исследовательский прототип. Отчёт не является диагнозом, валидированным медицинским тестом или основанием для клинического решения.",
        "proxy": "Внимание, выравнивание взгляда, тепловая карта и задержка реакции — некалиброванные камерные прокси-оценки.",
        "phase": "Фаза", "phase_attention": "Прокси внимания", "alignment": "Совпадение со стимулом", "response": "Реакция",
        "footer": "EyeInsight MVP · технический отчёт прототипа",
        "demo": "СИНТЕТИЧЕСКОЕ ДЕМО — человек не записывался, персональные данные не использовались.",
    },
    "kz": {
        "title": "Көрнекі зейін сессиясының техникалық есебі",
        "session": "Сессия",
        "quality": "Деректер сапасы",
        "attention": "Зейіннің техникалық проксиі",
        "usable": "Жарамды кадрлар",
        "face": "Беттің көрінуі",
        "tracking": "Бақылау сапасы",
        "latency": "Бағаланған реакция кідірісі",
        "phases": "Кезеңдерді салыстыру",
        "heatmap": "Көзқарастың бағаланған таралуы",
        "status": "Техникалық өңдеу аяқталды. Клиникалық тәуекел бағасы жасалмады.",
        "notice": "Тек зерттеу прототипі. Бұл есеп диагноз, валидацияланған медициналық тест немесе клиникалық шешімнің негізі емес.",
        "proxy": "Зейін, көзқарас сәйкестігі, жылу картасы және реакция кідірісі — калибрленбеген камералық прокси-бағалар.",
        "phase": "Кезең", "phase_attention": "Зейін проксиі", "alignment": "Стимулға сәйкестік", "response": "Реакция",
        "footer": "EyeInsight MVP · прототиптің техникалық есебі",
        "demo": "СИНТЕТИКАЛЫҚ ДЕМО — адам жазылмады және жеке деректер пайдаланылмады.",
    },
}

PHASE_COPY = {
    "en": {"center_focus": "Center focus", "horizontal_tracking": "Horizontal tracking", "vertical_tracking": "Vertical tracking", "social_face": "Face stimulus", "attention_shift": "Attention shift", "final_center": "Final center"},
    "ru": {"center_focus": "Фиксация в центре", "horizontal_tracking": "Движение по горизонтали", "vertical_tracking": "Движение по вертикали", "social_face": "Стимул с лицом", "attention_shift": "Переключение внимания", "final_center": "Финальная фиксация"},
    "kz": {"center_focus": "Орталық фиксация", "horizontal_tracking": "Көлденең бақылау", "vertical_tracking": "Тік бақылау", "social_face": "Бет стимулы", "attention_shift": "Зейінді ауыстыру", "final_center": "Соңғы фиксация"},
}


def create_session_report(output_path: Path, session_id: str, result: dict[str, Any], features: dict[str, Any], phases: list[dict[str, Any]], language: str) -> Path:
    labels = COPY.get(language, COPY["ru"])
    phase_labels = PHASE_COPY.get(language, PHASE_COPY["ru"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font = _font()
    canvas = Canvas(str(output_path), pagesize=A4)
    width, height, margin = *A4, 42
    canvas.setFillColor(colors.HexColor("#0F172A")); canvas.rect(0, height - 74, width, 74, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#2DD4BF")); canvas.setFont(font, 19); canvas.drawString(margin, height - 42, "EyeInsight")
    canvas.setFillColor(colors.white); canvas.setFont(font, 9); canvas.drawRightString(width - margin, height - 40, f"{labels['session']} #{session_id[:8]}")
    cursor = height - 105
    canvas.setFillColor(colors.HexColor("#111827")); canvas.setFont(font, 14); canvas.drawString(margin, cursor, labels["title"]); cursor -= 24
    canvas.setFillColor(colors.HexColor("#0F766E")); cursor = _wrap(canvas, labels["status"], margin, cursor, width - margin * 2, font, 8.5); cursor -= 10
    if result.get("is_demo"):
        canvas.setFillColor(colors.HexColor("#B45309")); cursor = _wrap(canvas, labels["demo"], margin, cursor, width - margin * 2, font, 8.5); cursor -= 7
    cards = (
        (labels["quality"], f"{result['quality_score']:.0f}/100"),
        (labels["attention"], _score(features.get("attention_score"))),
        (labels["usable"], _percent(features.get("overall_usable_frames"))),
        (labels["face"], _percent(features.get("overall_face_visibility"))),
        (labels["tracking"], _percent(features.get("overall_tracking_quality"))),
        (labels["latency"], _latency(features)),
    )
    card_width = (width - margin * 2 - 18) / 2
    for index, (label, value) in enumerate(cards):
        x, y = margin + (index % 2) * (card_width + 18), cursor - (index // 2) * 60
        canvas.setFillColor(colors.HexColor("#F1F5F9")); canvas.roundRect(x, y - 44, card_width, 47, 7, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#64748B")); canvas.setFont(font, 8); canvas.drawString(x + 10, y - 14, label)
        canvas.setFillColor(colors.HexColor("#0F766E")); canvas.setFont(font, 14); canvas.drawString(x + 10, y - 32, value)
    cursor -= 205
    canvas.setFillColor(colors.HexColor("#111827")); canvas.setFont(font, 11); canvas.drawString(margin, cursor, labels["phases"]); cursor -= 17
    header_x = (margin, margin + 195, margin + 300, margin + 420)
    canvas.setFillColor(colors.HexColor("#E2E8F0")); canvas.rect(margin, cursor - 13, width - margin * 2, 18, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#334155")); canvas.setFont(font, 7)
    for x, value in zip(header_x, (labels["phase"], labels["phase_attention"], labels["alignment"], labels["response"])): canvas.drawString(x + 5, cursor - 7, value)
    cursor -= 25
    for phase in phases[:6]:
        phase_code = str(phase.get("phase", ""))
        values = (phase_labels.get(phase_code, phase_code.replace("_", " ")), f"{float(phase.get('attention_ratio') or 0) * 100:.0f}%", f"{float(phase.get('target_alignment_ratio') or 0) * 100:.0f}%", _phase_latency(phase))
        canvas.setFillColor(colors.HexColor("#111827")); canvas.setFont(font, 7)
        for x, value in zip(header_x, values): canvas.drawString(x + 5, cursor, value)
        canvas.setStrokeColor(colors.HexColor("#E2E8F0")); canvas.line(margin, cursor - 6, width - margin, cursor - 6); cursor -= 21
    heatmap = features.get("visualization_data", {}).get("gaze_heatmap", [])
    if heatmap and any(float(value or 0) > 0 for row in heatmap for value in row):
        cursor -= 4
        canvas.setFillColor(colors.HexColor("#111827")); canvas.setFont(font, 9); canvas.drawString(margin, cursor, labels["heatmap"])
        cursor = _draw_heatmap(canvas, heatmap, margin, cursor - 112, 96) - 12
    canvas.setFillColor(colors.HexColor("#64748B")); cursor = _wrap(canvas, labels["proxy"], margin, cursor - 9, width - margin * 2, font, 7.5); _wrap(canvas, labels["notice"], margin, cursor - 7, width - margin * 2, font, 7.5)
    canvas.setFillColor(colors.HexColor("#94A3B8")); canvas.setFont(font, 7); canvas.drawRightString(width - margin, 24, labels["footer"])
    canvas.save()
    return output_path


def _font() -> str:
    for candidate in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"):
        if os.path.isfile(candidate):
            pdfmetrics.registerFont(TTFont("EyeInsightUnicode", candidate)); return "EyeInsightUnicode"
    return "Helvetica"


def _score(value: Any) -> str:
    return f"{float(value):.0f}/100" if value is not None else "—"


def _percent(value: Any) -> str:
    return f"{float(value) * 100:.0f}%" if value is not None else "—"


def _latency(features: dict[str, Any]) -> str:
    value = features.get("estimated_response_latency_ms")
    return f"{float(value):.0f} ms" if value is not None else "not available"


def _phase_latency(phase: dict[str, Any]) -> str:
    value = phase.get("estimated_response_latency_ms")
    return f"{float(value):.0f} ms" if value is not None else "-"


def _draw_heatmap(canvas: Canvas, heatmap: list[list[Any]], x: float, y: float, size: float) -> float:
    rows = len(heatmap)
    columns = max((len(row) for row in heatmap), default=0)
    if not rows or not columns:
        return y
    maximum = max((float(value or 0) for row in heatmap for value in row), default=1.0) or 1.0
    cell_width, cell_height = size / columns, size / rows
    for row_index, row in enumerate(heatmap):
        for column_index, value in enumerate(row):
            intensity = max(0.0, min(1.0, float(value or 0) / maximum))
            canvas.setFillColor(colors.Color(0.94 - 0.86 * intensity, 0.98 - 0.26 * intensity, 0.97 - 0.32 * intensity))
            canvas.rect(x + column_index * cell_width, y + (rows - row_index - 1) * cell_height, cell_width + 0.2, cell_height + 0.2, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor("#CBD5E1")); canvas.rect(x, y, size, size, fill=0, stroke=1)
    return y


def _wrap(canvas: Canvas, text: str, x: float, y: float, max_width: float, font: str, size: float) -> float:
    canvas.setFont(font, size); line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and canvas.stringWidth(candidate, font, size) > max_width:
            canvas.drawString(x, y, line); y -= size + 3; line = word
        else: line = candidate
    if line: canvas.drawString(x, y, line); y -= size + 3
    return y
