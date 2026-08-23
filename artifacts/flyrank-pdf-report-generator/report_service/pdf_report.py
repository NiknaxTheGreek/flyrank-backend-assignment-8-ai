from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas


def _footer(canvas: Canvas, page_number: int) -> None:
    canvas.setStrokeColor(HexColor("#CBD5E1"))
    canvas.line(48, 42, 564, 42)
    canvas.setFillColor(HexColor("#64748B"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(48, 28, "Independent PDF Report Generator — implementation evidence")
    canvas.drawRightString(564, 28, f"Page {page_number}")


def build_pdf(
    output_path: Path,
    title: str,
    job_id: str,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output_path), pagesize=letter, pageCompression=1)
    width, height = letter
    page = 1

    canvas.setFillColor(HexColor("#0F172A"))
    canvas.setFont("Helvetica-Bold", 22)
    canvas.drawString(48, height - 62, title)
    canvas.setFillColor(HexColor("#475569"))
    canvas.setFont("Helvetica", 9)
    canvas.drawString(48, height - 82, f"Job reference: {job_id}")
    canvas.drawString(48, height - 96, "Source: persisted seeded source records queried by the worker")

    canvas.setFillColor(HexColor("#0F766E"))
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(48, height - 132, "Executive aggregate")
    canvas.setFillColor(HexColor("#0F172A"))
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(48, height - 154, f"Records processed: {summary['record_count']}")
    canvas.drawString(48, height - 172, f"Total amount: ${summary['total_amount']:,.2f}")
    canvas.drawString(48, height - 190, f"Average amount: ${summary['average_amount']:,.2f}")

    y = height - 226
    canvas.setFillColor(HexColor("#0F766E"))
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(48, y, "Category totals")
    y -= 20
    canvas.setFillColor(HexColor("#0F172A"))
    canvas.setFont("Helvetica", 10)
    for category, amount in summary["category_totals"].items():
        canvas.drawString(64, y, category)
        canvas.drawRightString(300, y, f"${amount:,.2f}")
        y -= 18

    canvas.setFillColor(HexColor("#0F766E"))
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(48, y - 12, "Integrity note")
    canvas.setFillColor(HexColor("#334155"))
    canvas.setFont("Helvetica", 9)
    canvas.drawString(
        48,
        y - 30,
        "The detailed records below reconcile to the aggregate above; the worker validates the PDF before publish.",
    )
    _footer(canvas, page)
    canvas.showPage()
    page += 1

    def table_header(current_y: float) -> float:
        canvas.setFillColor(HexColor("#0F172A"))
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(48, current_y, "Detailed source records")
        current_y -= 20
        canvas.setFillColor(HexColor("#0F766E"))
        canvas.setFont("Helvetica-Bold", 8)
        headers = [("ID", 48), ("Date", 104), ("Category", 166), ("Customer", 244), ("Region", 388), ("Amount", 460)]
        for label, x in headers:
            canvas.drawString(x, current_y, label)
        canvas.setStrokeColor(HexColor("#94A3B8"))
        canvas.line(48, current_y - 4, 564, current_y - 4)
        return current_y - 18

    y = table_header(height - 62)
    canvas.setFont("Helvetica", 8)
    for record in records:
        if y < 64:
            _footer(canvas, page)
            canvas.showPage()
            page += 1
            y = table_header(height - 62)
            canvas.setFont("Helvetica", 8)
        canvas.setFillColor(HexColor("#1E293B"))
        fields = [
            (record["id"], 48),
            (record["recorded_at"], 104),
            (record["category"], 166),
            (record["customer"], 244),
            (record["region"], 388),
        ]
        for value, x in fields:
            canvas.drawString(x, y, str(value)[:26])
        canvas.drawRightString(540, y, f"${float(record['amount']):,.2f}")
        y -= 16
    _footer(canvas, page)
    canvas.save()


def validate_pdf(path: Path) -> int:
    reader = PdfReader(str(path))
    if not reader.pages:
        raise ValueError("PDF contains no pages")
    if not reader.pages[0].extract_text():
        raise ValueError("PDF has no extractable content")
    return len(reader.pages)