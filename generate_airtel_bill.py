#!/usr/bin/env python3
"""Airtel receipt generator — exact replica of airtel_receipt_july_2026.pdf.

Only the invoice date, month, and invoice number are changeable.
"""

import argparse
import calendar
import sys
from pathlib import Path

import pymupdf

TEMPLATE = Path(__file__).with_name("airtel_receipt_template.pdf")
if not TEMPLATE.exists():
    TEMPLATE = Path.home() / "Downloads" / "airtel_receipt_july_2026.pdf"

# Card background under the editable fields
CARD_BG = (0.992157, 0.992157, 0.992157)

# Right edge for right-aligned header/total text (page points)
RIGHT = 529.506

# Editable-field geometry (page points, y from top)
REDACT_RECTS = [
    pymupdf.Rect(465.5, 114, 532, 128),  # invoice number value (label ends ~464.9)
    pymupdf.Rect(478.5, 130, 532, 144),  # date value (label ends ~477.5)
    pymupdf.Rect(178, 230, 350, 247),    # billed period value
    pymupdf.Rect(70, 352, 315, 371),     # table description
]

MONTHS = {
    1: ("Jan", "January"), 2: ("Feb", "February"), 3: ("Mar", "March"),
    4: ("Apr", "April"), 5: ("May", "May"), 6: ("Jun", "June"),
    7: ("Jul", "July"), 8: ("Aug", "August"), 9: ("Sep", "September"),
    10: ("Oct", "October"), 11: ("Nov", "November"), 12: ("Dec", "December"),
}


def parse_month(value: str) -> int:
    v = value.strip().lower().rstrip(".")
    if v.isdigit():
        m = int(v)
        if 1 <= m <= 12:
            return m
    for num, (abbr, full) in MONTHS.items():
        if v in (abbr.lower(), full.lower()):
            return num
    raise SystemExit(f"Invalid month: {value!r} (use 1-12, Jul, July, ...)")


def parse_date(value: str) -> tuple[int, int, int]:
    try:
        d, m, y = (int(p) for p in value.strip().split("-"))
    except ValueError:
        raise SystemExit(f"Invalid date: {value!r} (use DD-MM-YYYY)")
    if not (1 <= m <= 12):
        raise SystemExit(f"Invalid month in date: {value!r}")
    if not (1 <= d <= calendar.monthrange(y, m)[1]):
        raise SystemExit(f"Invalid day in date: {value!r}")
    return d, m, y


def insert(page, x, y, text, size, font, color, right=None, center=None):
    if right is not None:
        x = right - pymupdf.get_text_length(text, fontname=font, fontsize=size)
    elif center is not None:
        x = center - pymupdf.get_text_length(text, fontname=font, fontsize=size) / 2
    page.insert_text((x, y), text, fontsize=size, fontname=font, color=color)


def generate(date: str, month: str, invoice_no: str, out_path: str) -> str:
    if not TEMPLATE.exists():
        raise SystemExit(f"Template not found: {TEMPLATE}")

    day, date_month, year = parse_date(date)
    month_num = parse_month(month)
    abbr, full = MONTHS[month_num]
    last_day = calendar.monthrange(year, month_num)[1]

    billed_period = f"01-{abbr}-{year} to {last_day}-{abbr}-{year}"
    description = f"Prepaid Recharge - Airtel {full}"
    date_str = f"{day:02d}-{date_month:02d}-{year:04d}"

    doc = pymupdf.open(TEMPLATE)
    page = doc[0]

    for rect in REDACT_RECTS:
        page.add_redact_annot(rect, fill=CARD_BG)
    page.apply_redactions(
        images=pymupdf.PDF_REDACT_IMAGE_NONE,
        graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
        text=pymupdf.PDF_REDACT_TEXT_REMOVE,
    )

    # Invoice No value (regular 9.5, #555555), right-aligned
    insert(page, 0, 123.7, f" {invoice_no}", 9.5, "helv", (0.333, 0.333, 0.333), right=RIGHT)
    # Date value (regular 9.5, #555555), right-aligned
    insert(page, 0, 139.5, f" {date_str}", 9.5, "helv", (0.333, 0.333, 0.333), right=RIGHT)
    # Billed Period value (regular 10, #222222), left at x=181.70
    insert(page, 181.70, 239.7, billed_period, 10, "helv", (0.133, 0.133, 0.133))
    # Table description (regular 10, #333333), left at x=73.30
    insert(page, 73.30, 362.7, description, 10, "helv", (0.2, 0.2, 0.2))

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out, garbage=3, deflate=True)
    doc.close()
    return str(out)


def main():
    p = argparse.ArgumentParser(description="Generate the Airtel receipt PDF (editable date/month/invoice no only).")
    p.add_argument("--date", default="17-07-2026", help="Invoice date DD-MM-YYYY (default: 17-07-2026)")
    p.add_argument("--month", default="Jul", help="Billing month: 7, Jul, July (default: Jul)")
    p.add_argument("--invoice", default="INV19600133-", help="Invoice number (default: INV19600133-)")
    p.add_argument("-o", "--out", default="airtel_receipt.pdf", help="Output PDF path")
    args = p.parse_args()
    path = generate(args.date, args.month, args.invoice, args.out)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
