"""
KSP Insight AI — Conversation PDF export
Location: assistant/ai/report_generator.py (new file)

Generates a PDF transcript of a Conversation: officer/station header,
every ChatMessage in order, and — where available — the structured
tool trace (sql_trace/ml_trace/graph trace) so the exported report
carries the same "how I got this answer" transparency as the chat UI,
not just the plain-text answers.

Saves the PDF to MEDIA_ROOT/reports/ and creates a GeneratedReport row
pointing at it. Requires MEDIA_ROOT/MEDIA_URL configured in settings.py
(see setup notes below) — no cloud storage wired in yet, so this is
local-disk for now, consistent with the project's existing
"file_reference is a temporary placeholder" pattern, just made
functional for the demo.

pip install reportlab
"""

import os
import uuid
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib import colors

from assistant.models import ChatMessage, GeneratedReport


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="OfficerMsg", parent=styles["Normal"],
        backColor=colors.HexColor("#eef3fb"), borderPadding=8,
        spaceAfter=10, leftIndent=0,
    ))
    styles.add(ParagraphStyle(
        name="AIMsg", parent=styles["Normal"],
        backColor=colors.HexColor("#f3f3f3"), borderPadding=8,
        spaceAfter=6, leftIndent=0,
    ))
    styles.add(ParagraphStyle(
        name="TraceLabel", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#555555"),
        fontName="Helvetica-Oblique", spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="Meta", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#666666"),
    ))
    return styles


def _format_trace(metadata: dict) -> str:
    """
    Renders whatever structured trace info is present into a short line.
    sql_trace and ml_trace are LISTS of entries (one per call to that
    tool within the turn) — confirmed against real output, not a dict
    as originally guessed. graph_lookup doesn't populate a graph_trace
    key yet (still just the old text-tag trailer) — handled here as an
    optional list too, so it slots in automatically once that's added
    without needing another change to this function.
    """
    if not metadata:
        return ""
    parts = []

    if metadata.get("tools_used"):
        parts.append(f"Tool(s): {', '.join(metadata['tools_used'])}")
    if metadata.get("elapsed_ms") is not None:
        parts.append(f"{metadata['elapsed_ms']}ms")

    for sql_entry in metadata.get("sql_trace") or []:
        if sql_entry.get("executed_sql"):
            parts.append(f"SQL: {sql_entry['executed_sql']}")

    for ml_entry in metadata.get("ml_trace") or []:
        factors = ml_entry.get("top_factors") or []
        if factors:
            factor_str = "; ".join(
                f"{f.get('feature')} (impact {f.get('impact', 0):.2f})"
                for f in factors[:3]
            )
            parts.append(
                f"QuickML [{ml_entry.get('model')}]: {ml_entry.get('prediction')} "
                f"({ml_entry.get('confidence')}%) — top factors: {factor_str}"
            )

    for graph_entry in metadata.get("graph_trace") or []:
        if graph_entry.get("intent"):
            parts.append(f"Graph intent: {graph_entry['intent']}")

    return " · ".join(parts)


def generate_conversation_pdf(conversation) -> GeneratedReport:
    """
    Builds the PDF, saves it under MEDIA_ROOT/reports/, and returns the
    created GeneratedReport row (with file_reference set).
    """
    styles = _build_styles()
    officer = conversation.officer

    reports_dir = os.path.join(settings.MEDIA_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    filename = f"conversation_{conversation.id}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
    )
    story = []

    # --- Header ---
    story.append(Paragraph("KSP Insight AI — Conversation Export", styles["Title"]))
    story.append(Spacer(1, 4))
    header_table = Table([
        ["Officer:", f"{officer.first_name} {officer.last_name} (Badge {officer.badge_number})"],
        ["Station:", officer.police_station.name],
        ["Conversation:", conversation.title or str(conversation.id)],
        ["Case:", conversation.case.case_number if conversation.case else "— (general query, not case-linked)"],
        ["Exported:", datetime.now().strftime("%d %b %Y, %H:%M")],
    ], colWidths=[35 * mm, 130 * mm])
    header_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 16))

    # --- Messages ---
    messages = conversation.messages.order_by("created_at")
    for msg in messages:
        timestamp = timezone.localtime(msg.created_at).strftime("%H:%M:%S")
        if msg.sender == ChatMessage.Sender.USER:
            story.append(Paragraph(f"<b>Officer</b> — {timestamp}", styles["Meta"]))
            story.append(Paragraph(msg.content, styles["OfficerMsg"]))
        else:
            story.append(Paragraph(f"<b>AI Assistant</b> — {timestamp}", styles["Meta"]))
            story.append(Paragraph(msg.content.replace("\n", "<br/>"), styles["AIMsg"]))
            trace_line = _format_trace(msg.metadata or {})
            if trace_line:
                story.append(Paragraph(f"How this answer was generated: {trace_line}", styles["TraceLabel"]))

    # --- Footer note ---
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "This report was generated from an AI-assisted conversation. Every query was "
        "automatically scoped to the requesting officer's role-based access level "
        "(station, district, or state-wide, per KSP Insight AI's RBAC policy). "
        "This export is also independently recorded in the system audit log.",
        styles["Meta"],
    ))

    doc.build(story)

    relative_path = f"reports/{filename}"  # forward slash always, this becomes part of a URL
    report = GeneratedReport.objects.create(
        officer=officer,
        case=conversation.case,
        report_type=GeneratedReport.ReportType.CUSTOM,
        title=f"Conversation Export — {conversation.title or conversation.id}",
        content_summary=f"PDF transcript of conversation with {messages.count()} message(s).",
        file_reference=relative_path,
    )
    return report