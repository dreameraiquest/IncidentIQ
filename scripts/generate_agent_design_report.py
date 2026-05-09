from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "IncidentIQ_Agent_Design_Report.md"
TARGET = ROOT / "docs" / "IncidentIQ_Agent_Design_Report.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "TitleX",
            parent=styles["Title"],
            fontSize=24,
            leading=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1f2b3d"),
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            "BodyX",
            parent=styles["BodyText"],
            fontSize=9.8,
            leading=13.5,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "H1X",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#223d63"),
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            "H2X",
            parent=styles["Heading2"],
            fontSize=12.5,
            leading=16,
            textColor=colors.HexColor("#32577a"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "BulletX",
            parent=styles["BodyText"],
            fontSize=9.6,
            leading=13.2,
            leftIndent=14,
            firstLineIndent=-8,
            spaceAfter=3,
        )
    )
    return styles


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(0.55 * inch, 0.4 * inch, "IncidentIQ Agent Design Report")
    canvas.drawRightString(7.72 * inch, 0.4 * inch, f"Page {doc.page}")
    canvas.restoreState()


def parse_lines(text: str):
    styles = build_styles()
    flow = [
        Paragraph("IncidentIQ Agent Design Report", styles["TitleX"]),
        Spacer(1, 0.08 * inch),
    ]

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            flow.append(Spacer(1, 0.06 * inch))
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            flow.append(Paragraph(line[3:], styles["H1X"]))
            continue
        if line.startswith("### "):
            flow.append(Paragraph(line[4:], styles["H2X"]))
            continue
        if line.startswith("- "):
            flow.append(Paragraph(f"• {line[2:]}", styles["BulletX"]))
            continue
        if line[0].isdigit() and ". " in line[:4]:
            flow.append(Paragraph(line, styles["BulletX"]))
            continue
        flow.append(Paragraph(line, styles["BodyX"]))
    return flow


def main():
    text = SOURCE.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(TARGET),
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.65 * inch,
        title="IncidentIQ Agent Design Report",
        author="IncidentIQ Team",
    )
    doc.build(parse_lines(text), onFirstPage=footer, onLaterPages=footer)
    print(TARGET)


if __name__ == "__main__":
    main()
