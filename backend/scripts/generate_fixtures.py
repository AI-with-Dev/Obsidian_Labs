import json
import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = BASE_DIR / "backend/data/test_fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


def create_receipt_image(
    filename: str,
    vendor: str,
    date_str: str,
    items: list,
    total_str: str,
    category: str,
    is_blurry: bool = False,
    is_faint: bool = False,
    omit_vendor: bool = False,
    omit_total: bool = False,
) -> Path:
    """Generate a realistic synthetic stationery receipt image."""
    width, height = 500, 700
    bg_color = (250, 248, 242) if not is_faint else (255, 255, 255)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Receipt border
    draw.rectangle([15, 15, width - 15, height - 15], outline=(200, 195, 185), width=2)
    draw.rectangle([25, 25, width - 25, height - 25], outline=(230, 225, 215), width=1)

    text_color = (40, 35, 30) if not is_faint else (160, 160, 160)
    sub_color = (100, 95, 90) if not is_faint else (180, 180, 180)

    # Header / Vendor
    y = 50
    if not omit_vendor:
        draw.text((width // 2, y), vendor.upper(), fill=text_color, anchor="mm")
        y += 25
        draw.text((width // 2, y), "STATIONERY & OFFICE SUPPLIES", fill=sub_color, anchor="mm")
        y += 20
        draw.text((width // 2, y), "TAX INVOICE / CASH MEMO", fill=sub_color, anchor="mm")
    else:
        y += 30
        draw.text((width // 2, y), "[ CASH MEMO ]", fill=sub_color, anchor="mm")

    y += 25
    draw.line([(40, y), (width - 40, y)], fill=(180, 175, 165), width=2)
    y += 15

    # Date
    draw.text((45, y), f"Date: {date_str}", fill=text_color)
    draw.text((width - 45, y), f"Cat: {category}", fill=sub_color, anchor="ra")
    y += 25
    draw.line([(40, y), (width - 40, y)], fill=(220, 215, 205), width=1)
    y += 20

    # Column header
    draw.text((45, y), "ITEM DESCRIPTION", fill=sub_color)
    draw.text((width - 45, y), "AMOUNT (INR)", fill=sub_color, anchor="ra")
    y += 20
    draw.line([(40, y), (width - 40, y)], fill=(200, 195, 185), width=1)
    y += 15

    # Items
    for name, amt in items:
        draw.text((45, y), str(name), fill=text_color)
        draw.text((width - 45, y), f"₹{amt:,.2f}", fill=text_color, anchor="ra")
        y += 24

    y = max(y + 20, 520)
    draw.line([(40, y), (width - 40, y)], fill=(150, 145, 135), width=2)
    y += 25

    # Total
    if not omit_total:
        draw.text((45, y), "TOTAL AMOUNT", fill=(20, 20, 20))
        draw.text((width - 45, y), f"₹{total_str}", fill=(10, 120, 80), anchor="ra")
    else:
        draw.text((45, y), "[ TOTAL TORN OFF / UNREADABLE ]", fill=(200, 50, 50))

    y += 40
    draw.line([(40, y), (width - 40, y)], fill=(180, 175, 165), width=1)
    y += 25
    draw.text((width // 2, y), "Thank You • Please Visit Again", fill=sub_color, anchor="mm")

    # Apply blur if requested
    if is_blurry:
        img = img.filter(ImageFilter.GaussianBlur(radius=1.8))

    target_path = FIXTURES_DIR / filename
    img.save(target_path, "PNG")
    return target_path


def create_receipt_pdf(filename: str, vendor: str, invoice_no: str, date_str: str, items: list, total_val: float) -> Path:
    """Generate a standard compliant single-page PDF receipt."""
    content_lines = [
        f"BT /F1 16 Tf 50 780 Td ({vendor}) Tj ET",
        "BT /F1 10 Tf 50 760 Td (TAX INVOICE - WHOLESALE STATIONERY SUPPLY) Tj ET",
        f"BT /F1 10 Tf 50 735 Td (Invoice No: {invoice_no}     Date: {date_str}     Currency: INR) Tj ET",
        "BT /F1 11 Tf 50 700 Td (ITEM DESCRIPTION                                         AMOUNT) Tj ET",
    ]

    y = 675
    for name, amt in items:
        line_desc = f"{name:<50} INR {amt:,.2f}"
        content_lines.append(f"BT /F1 10 Tf 50 {y} Td ({line_desc}) Tj ET")
        y -= 22

    content_lines.append(f"BT /F1 14 Tf 50 {y - 20} Td (TOTAL INVOICE AMOUNT: INR {total_val:,.2f}) Tj ET")
    content_lines.append(f"BT /F1 9 Tf 50 {y - 60} Td (Payment Terms: Bank Transfer / UPI Verified) Tj ET")

    stream_data = "\n".join(content_lines)
    stream_bytes = stream_data.encode("latin1")
    stream_len = len(stream_bytes)

    pdf_text = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj
4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
5 0 obj
<< /Length {stream_len} >>
stream
{stream_data}
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000318 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
{400 + stream_len}
%%EOF"""

    target_path = FIXTURES_DIR / filename
    target_path.write_bytes(pdf_text.encode("latin1"))
    return target_path


def generate_all_fixtures():
    fixtures_metadata = []

    # 1. 8 Clear Images
    clear_specs = [
        ("fixture_01_clear.png", "Sharma Wholesale Traders", "2026-10-03", [("Classmate Notebooks (50 Pcs)", 6500.0), ("Reynolds Pens (5 Boxes)", 2950.0), ("A4 Copier Paper (6 Reams)", 3000.0)], "12,450.00", 12450.0, "inventory"),
        ("fixture_02_clear.png", "JK Paper Mart", "2026-10-08", [("JK Sparkle A4 75GSM (10 Reams)", 3500.0), ("Executive Bond Paper (2 Boxes)", 700.0)], "4,200.00", 4200.0, "inventory"),
        ("fixture_03_clear.png", "Ganesh Packaging", "2026-10-06", [("Cardboard Shipping Boxes (50 pcs)", 1200.0), ("Brown Packing Tape (6 Rolls)", 660.0)], "1,860.00", 1860.0, "packaging"),
        ("fixture_04_clear.png", "City Goods Transport", "2026-10-09", [("Stationery Consignment Freight Delivery", 2400.0)], "2,400.00", 2400.0, "transport"),
        ("fixture_05_clear.png", "Rajasthan Power Vidyut", "2026-10-12", [("Shop Electricity Bill (Oct 2026)", 3120.0)], "3,120.00", 3120.0, "utilities"),
        ("fixture_06_clear.png", "Mahalaxmi Stationery Hub", "2026-10-11", [("Fluorescent Highlighters (4 Packs)", 800.0), ("Waterproof Gel Pens (15 Boxes)", 1350.0)], "2,150.00", 2150.0, "inventory"),
        ("fixture_07_clear.png", "Super Office Supplies", "2026-10-13", [("Lever Arch Files (20 Pcs)", 2600.0), ("Clear Display Folders (25 Pcs)", 1250.0)], "3,850.00", 3850.0, "inventory"),
        ("fixture_08_clear.png", "Apex Cartridges & Ink", "2026-10-14", [("HP Laser Printer Toner Refill", 950.0), ("Printer Roller Service & Cleaning", 500.0)], "1,450.00", 1450.0, "repairs"),
    ]

    for fname, vendor, d, items, t_str, t_val, cat in clear_specs:
        create_receipt_image(fname, vendor, d, items, t_str, cat)
        fixtures_metadata.append({
            "filename": fname,
            "type": "clear_image",
            "expected": {
                "vendor": vendor,
                "date": d,
                "currency": "INR",
                "total": t_val,
                "category": cat,
                "items_count": len(items),
                "uncertainty_flags": [],
            },
        })

    # 2. 4 Short PDFs
    pdf_specs = [
        ("fixture_09_pdf.pdf", "Navneet Publications India", "INV-2026-901", "2026-10-04", [("School Exercise Books (100 Pcs)", 5000.0), ("Drawing Books & Scrapbooks", 3500.0)], 8500.0, "inventory"),
        ("fixture_10_pdf.pdf", "Kokuyo Camlin Limited", "INV-2026-902", "2026-10-07", [("Geometry Boxes (30 Pcs)", 3600.0), ("Oil Pastels & Poster Colors", 2700.0)], 6300.0, "inventory"),
        ("fixture_11_pdf.pdf", "Pidilite Wholesale Distributor", "INV-2026-903", "2026-10-10", [("Fevicol MR Squeeze Bottles (50 Pcs)", 1750.0), ("Fevikwik Display Cards (10 Cards)", 1500.0)], 3250.0, "inventory"),
        ("fixture_12_pdf.pdf", "Bharat Heavy Freight Carriers", "INV-2026-904", "2026-10-13", [("Interstate Consignment Freight Delivery", 4500.0)], 4500.0, "transport"),
    ]

    for fname, vendor, inv, d, items, t_val, cat in pdf_specs:
        create_receipt_pdf(fname, vendor, inv, d, items, t_val)
        fixtures_metadata.append({
            "filename": fname,
            "type": "short_pdf",
            "expected": {
                "vendor": vendor,
                "date": d,
                "currency": "INR",
                "total": t_val,
                "category": cat,
                "items_count": len(items),
                "uncertainty_flags": [],
            },
        })

    # 3. 3 Blurry / Ambiguous Images
    create_receipt_image("fixture_13_blurry.png", "Ravi General Store", "2026-10-10", [("White Board Markers (10 Pcs)", 450.0), ("Duster (2 Pcs)", 330.0)], "780.00", "inventory", is_blurry=True)
    fixtures_metadata.append({
        "filename": "fixture_13_blurry.png",
        "type": "blurry_image",
        "expected": {
            "vendor": "Ravi General Store",
            "date": "2026-10-10",
            "currency": "INR",
            "total": 780.0,
            "category": "inventory",
            "uncertainty_flags": ["total"],
            "notes": "Blurry thermal print requiring owner verification",
        },
    })

    create_receipt_image("fixture_14_blurry.png", "Gupta Stationers", "04/05/2026", [("Permanent Markers (12 Pcs)", 360.0), ("White Fluid Correction Pens", 240.0)], "600.00", "inventory", is_faint=True)
    fixtures_metadata.append({
        "filename": "fixture_14_blurry.png",
        "type": "ambiguous_date_image",
        "expected": {
            "vendor": "Gupta Stationers",
            "date": "2026-05-04",  # or 2026-04-05
            "currency": "INR",
            "total": 600.0,
            "category": "inventory",
            "uncertainty_flags": ["date"],
            "notes": "Ambiguous slash date format 04/05/2026",
        },
    })

    create_receipt_image("fixture_15_blurry.png", "City Hardware & Locksmith", "2026-10-14", [("Shop Shutter Padlock & 3 Keys", 940.0)], "940.00", "repairs", is_faint=True)
    fixtures_metadata.append({
        "filename": "fixture_15_blurry.png",
        "type": "faint_header_image",
        "expected": {
            "vendor": "City Hardware & Locksmith",
            "date": "2026-10-14",
            "currency": "INR",
            "total": 940.0,
            "category": "repairs",
            "uncertainty_flags": ["vendor"],
            "notes": "Faint receipt header banner",
        },
    })

    # 4. 3 Duplicate-Related Receipts
    # Exact duplicate: copy of fixture_03_clear.png
    shutil.copyfile(FIXTURES_DIR / "fixture_03_clear.png", FIXTURES_DIR / "fixture_16_exact_dup.png")
    fixtures_metadata.append({
        "filename": "fixture_16_exact_dup.png",
        "type": "exact_sha256_duplicate",
        "expected": {
            "duplicate_of": "fixture_03_clear.png",
            "vendor": "Ganesh Packaging",
            "total": 1860.0,
            "category": "packaging",
            "flag": "duplicate",
        },
    })

    create_receipt_image("fixture_17_fuzzy_dup1.png", "Sharma Wholesale Traders", "2026-10-03", [("Classmate Notebooks (50 Pcs)", 6500.0), ("Reynolds Pens (5 Boxes)", 2950.0), ("A4 Copier Paper (6 Reams)", 3000.0)], "12,450.00", "inventory")
    fixtures_metadata.append({
        "filename": "fixture_17_fuzzy_dup1.png",
        "type": "fuzzy_duplicate_same_vendor_date_total",
        "expected": {
            "vendor": "Sharma Wholesale Traders",
            "date": "2026-10-03",
            "total": 12450.0,
            "category": "inventory",
            "conflict_with": "Sharma Wholesale Traders 2026-10-03",
        },
    })

    create_receipt_image("fixture_18_fuzzy_dup2.png", "JK Paper Mart", "2026-10-08", [("JK Sparkle A4 75GSM (10 Reams)", 3500.0), ("Executive Bond Paper (2 Boxes)", 700.0)], "4,200.00", "inventory")
    fixtures_metadata.append({
        "filename": "fixture_18_fuzzy_dup2.png",
        "type": "fuzzy_duplicate_same_vendor_date_total",
        "expected": {
            "vendor": "JK Paper Mart",
            "date": "2026-10-08",
            "total": 4200.0,
            "category": "inventory",
            "conflict_with": "JK Paper Mart 2026-10-08",
        },
    })

    # 5. 2 Incomplete Receipts
    create_receipt_image("fixture_19_torn_total.png", "Modern Book Depot", "2026-10-15", [("A4 Spiral Registers (10 Pcs)", 600.0), ("Ballpoint Pen Packs (5 Pcs)", 250.0)], "", "inventory", omit_total=True)
    fixtures_metadata.append({
        "filename": "fixture_19_torn_total.png",
        "type": "incomplete_missing_total",
        "expected": {
            "vendor": "Modern Book Depot",
            "date": "2026-10-15",
            "total": None,
            "category": "inventory",
            "uncertainty_flags": ["total"],
            "notes": "Bottom edge torn, total missing",
        },
    })

    create_receipt_image("fixture_20_missing_vendor.png", "", "2026-10-16", [("Assorted Paper Clips & Pins", 180.0), ("Rubber Bands Box (500g)", 220.0)], "400.00", "inventory", omit_vendor=True)
    fixtures_metadata.append({
        "filename": "fixture_20_missing_vendor.png",
        "type": "incomplete_missing_vendor",
        "expected": {
            "vendor": None,
            "date": "2026-10-16",
            "total": 400.0,
            "category": "inventory",
            "uncertainty_flags": ["vendor"],
            "notes": "Generic cash memo without vendor header",
        },
    })

    # Save ground_truth.json
    ground_truth_path = FIXTURES_DIR / "ground_truth.json"
    with open(ground_truth_path, "w", encoding="utf-8") as f:
        json.dump(fixtures_metadata, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(fixtures_metadata)} synthetic receipt fixtures and ground_truth.json!")


if __name__ == "__main__":
    generate_all_fixtures()
