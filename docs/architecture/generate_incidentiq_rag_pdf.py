from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "incidentiq_rag_integration_plan.md"
OUTPUT = ROOT / "incidentiq_rag_integration_plan.pdf"


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "IncidentIQ RAG Integration Plan")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            spaceAfter=18,
            textColor=colors.HexColor("#111827"),
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            spaceBefore=14,
            spaceAfter=7,
            textColor=colors.HexColor("#1F2937"),
        ),
        "h3": ParagraphStyle(
            "Heading3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=10,
            spaceAfter=5,
            textColor=colors.HexColor("#374151"),
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            spaceAfter=6,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#111827"),
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            leftIndent=16,
            firstLineIndent=-8,
            spaceAfter=4,
            textColor=colors.HexColor("#111827"),
        ),
        "code": ParagraphStyle(
            "Code",
            fontName="Courier",
            fontSize=8,
            leading=10,
            leftIndent=8,
            rightIndent=8,
            spaceBefore=4,
            spaceAfter=8,
            backColor=colors.HexColor("#F3F4F6"),
            borderColor=colors.HexColor("#E5E7EB"),
            borderWidth=0.5,
            borderPadding=6,
            textColor=colors.HexColor("#111827"),
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            spaceAfter=18,
            textColor=colors.HexColor("#6B7280"),
        ),
    }


def _escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _inline(text):
    out = []
    parts = text.split("`")
    for idx, part in enumerate(parts):
        safe = _escape(part)
        if idx % 2:
            out.append(f'<font name="Courier" backColor="#F3F4F6">{safe}</font>')
        else:
            out.append(safe)
    return "".join(out)


def build_pdf():
    styles = _styles()
    raw_lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story = []
    in_code = False
    code_lines = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            story.append(Preformatted("\n".join(code_lines), styles["code"]))
            code_lines = []

    for line in raw_lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
                code_lines = []
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            story.append(Spacer(1, 4))
            continue

        if stripped.startswith("# "):
            story.append(Paragraph(_inline(stripped[2:]), styles["title"]))
            story.append(
                Paragraph(
                    f"Prepared {datetime.now().strftime('%B %d, %Y')} from the IncidentIQ repository review.",
                    styles["meta"],
                )
            )
            continue

        if stripped.startswith("## "):
            if story and len(story) > 6 and stripped in {"## Pending Work Backlog", "## Recommended Target Architecture"}:
                story.append(PageBreak())
            story.append(Paragraph(_inline(stripped[3:]), styles["h2"]))
            continue

        if stripped.startswith("### "):
            story.append(Paragraph(_inline(stripped[4:]), styles["h3"]))
            continue

        if stripped.startswith("- "):
            story.append(Paragraph(f"- {_inline(stripped[2:])}", styles["bullet"]))
            continue

        if stripped[0:2].isdigit() and ". " in stripped[:4]:
            story.append(Paragraph(_inline(stripped), styles["body"]))
            continue

        story.append(Paragraph(_inline(stripped), styles["body"]))

    flush_code()

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.7 * inch,
        title="IncidentIQ RAG Integration Plan",
        author="Codex",
        subject="Pending work and integration plan for IncidentIQ notebook and RAG code",
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
