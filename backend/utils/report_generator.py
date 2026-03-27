from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from pathlib import Path
import os

REPORTS_DIR = Path("./reports")
REPORTS_DIR.mkdir(exist_ok=True)

PRIORITY_COLORS = {
    "low": colors.HexColor("#4CAF50"),
    "medium": colors.HexColor("#FF9800"),
    "high": colors.HexColor("#F44336"),
    "urgent": colors.HexColor("#9C27B0"),
}


def generate_complaint_report(complaint: dict) -> str:
    """
    Generate a PDF report for a complaint.
    Returns: path to the generated PDF.
    """
    complaint_id = complaint.get("complaint_id", "UNKNOWN")
    filename = REPORTS_DIR / f"complaint_{complaint_id}.pdf"

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Header ---
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#1a237e"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    story.append(Paragraph("GOVERNMENT COMPLAINT MANAGEMENT SYSTEM", header_style))
    story.append(Paragraph("Multilingual Citizen Grievance Portal", sub_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a237e")))
    story.append(Spacer(1, 0.4 * cm))

    # --- Complaint ID + Date ---
    label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    value_style = ParagraphStyle("Value", parent=styles["Normal"], fontSize=11, fontName="Helvetica-Bold")

    priority = complaint.get("priority", "medium")
    priority_color = PRIORITY_COLORS.get(priority, colors.orange)

    meta_data = [
        ["Complaint ID", complaint_id, "Date Filed", datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")],
        ["Category", complaint.get("category", "N/A"), "Department", complaint.get("department", "N/A")],
        ["Priority", priority.upper(), "Status", complaint.get("status", "submitted").upper()],
        ["Original Language", complaint.get("original_language", "Unknown"), "Input Type", complaint.get("input_type", "text").capitalize()],
    ]

    table_style = TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#1a237e")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f5f5f5"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ])

    t = Table(meta_data, colWidths=[3.5 * cm, 7 * cm, 3.5 * cm, 5 * cm])
    t.setStyle(table_style)
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # --- Citizen Info ---
    if complaint.get("citizen_name") or complaint.get("contact"):
        story.append(Paragraph("Citizen Information", styles["Heading2"]))
        citizen_data = [
            ["Name", complaint.get("citizen_name", "Anonymous")],
            ["Contact", complaint.get("contact", "Not provided")],
            ["Location", complaint.get("location", "Not specified")],
        ]
        ct = Table(citizen_data, colWidths=[4 * cm, 15 * cm])
        ct.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(ct)
        story.append(Spacer(1, 0.5 * cm))

    # --- Original Complaint ---
    story.append(Paragraph("Original Complaint (as submitted)", styles["Heading2"]))
    story.append(Paragraph(
        complaint.get("original_text", "No original text available"),
        ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=16,
                       backColor=colors.HexColor("#fffde7"), borderPad=6)
    ))
    story.append(Spacer(1, 0.4 * cm))

    # --- Translated Version ---
    if complaint.get("translated_text") and complaint.get("translated_text") != complaint.get("original_text"):
        story.append(Paragraph("English Translation", styles["Heading2"]))
        story.append(Paragraph(
            complaint.get("translated_text"),
            ParagraphStyle("Trans", parent=styles["Normal"], fontSize=10, leading=16)
        ))
        story.append(Spacer(1, 0.4 * cm))

    # --- AI-Generated Summary ---
    story.append(Paragraph("Official Summary (AI-Generated)", styles["Heading2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        complaint.get("summary", "No summary available"),
        ParagraphStyle("Summary", parent=styles["Normal"], fontSize=11, leading=18,
                       leftIndent=10, rightIndent=10)
    ))
    story.append(Spacer(1, 0.5 * cm))

    # --- Classification Confidence ---
    story.append(Paragraph("AI Classification", styles["Heading2"]))
    conf = complaint.get("confidence", 0)
    class_data = [
        ["Category", complaint.get("category", "N/A")],
        ["Assigned Department", complaint.get("department", "N/A")],
        ["Confidence Score", f"{conf * 100:.1f}%"],
        ["Priority Level", priority.upper()],
    ]
    clf_table = Table(class_data, colWidths=[5 * cm, 14 * cm])
    clf_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (1, 3), (1, 3), priority_color),
        ("FONTNAME", (1, 3), (1, 3), "Helvetica-Bold"),
    ]))
    story.append(clf_table)

    # --- Footer ---
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(
        f"Generated on {datetime.utcnow().strftime('%d %b %Y at %H:%M UTC')} | "
        "Government Complaint Management System | Confidential",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    return str(filename)
