import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "backend/data/shopledger.db"
UPLOAD_DIR = BASE_DIR / "backend/data/uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def create_sample_svg(filename: str, vendor: str, total_str: str, date_str: str) -> Path:
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="640" viewBox="0 0 480 640">
  <rect width="480" height="640" fill="#faf8f5" stroke="#d5d0c7" stroke-width="2"/>
  <rect x="20" y="20" width="440" height="600" fill="#ffffff" stroke="#e8e4dc" stroke-width="1" rx="4"/>
  <text x="240" y="70" font-family="system-ui, -apple-system, sans-serif" font-size="22" font-weight="bold" fill="#1c1917" text-anchor="middle">{vendor}</text>
  <text x="240" y="100" font-family="monospace" font-size="14" fill="#78716c" text-anchor="middle">RECEIPT / INVOICE</text>
  <line x1="50" y1="120" x2="430" y2="120" stroke="#e7e5e4" stroke-width="2" stroke-dasharray="4 4"/>
  <text x="50" y="150" font-family="system-ui, sans-serif" font-size="14" fill="#78716c">Date:</text>
  <text x="430" y="150" font-family="system-ui, sans-serif" font-size="14" font-weight="600" fill="#1c1917" text-anchor="end">{date_str}</text>
  <line x1="50" y1="170" x2="430" y2="170" stroke="#e7e5e4" stroke-width="1"/>
  <text x="50" y="200" font-family="system-ui, sans-serif" font-size="15" fill="#44403c">Stationery Supplies &amp; Services</text>
  <text x="430" y="200" font-family="system-ui, sans-serif" font-size="15" font-weight="bold" fill="#1c1917" text-anchor="end">{total_str}</text>
  <line x1="50" y1="480" x2="430" y2="480" stroke="#1c1917" stroke-width="2"/>
  <text x="50" y="520" font-family="system-ui, sans-serif" font-size="18" font-weight="bold" fill="#1c1917">TOTAL AMOUNT</text>
  <text x="430" y="520" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" fill="#047857" text-anchor="end">{total_str}</text>
  <text x="240" y="580" font-family="system-ui, sans-serif" font-size="12" fill="#a8a29e" text-anchor="middle">ShopLedger Verified Expense</text>
</svg>"""
    file_path = UPLOAD_DIR / filename
    file_path.write_text(svg_content, encoding="utf-8")
    return file_path


def seed_database():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Clean previous records
    conn.execute("DELETE FROM receipt_events;")
    conn.execute("DELETE FROM receipt_items;")
    conn.execute("DELETE FROM receipts;")

    receipts_data = [
        {
            "id": "rec_sharma_01",
            "vendor": "Sharma Wholesale Traders",
            "receipt_date": "2026-10-03",
            "category": "inventory",
            "currency": "INR",
            "total_paise": 1245000,
            "status": "confirmed",
            "confirmed_at": "2026-10-03 14:30:00",
            "file_name": "sharma_invoice_oct.svg",
            "file_hash": "hash_sharma_01",
            "mime_type": "image/svg+xml",
            "flags": [],
            "duplicate_of_id": None,
            "items": [
                ("Classmate Notebooks (50 Pcs)", 1.0, 650000, 650000),
                ("Reynolds Fine Ball Pens (5 Boxes)", 5.0, 295000, 59000),
                ("A4 Copier Paper (6 Reams)", 6.0, 300000, 50000),
            ],
        },
        {
            "id": "rec_ganesh_02",
            "vendor": "Ganesh Packaging",
            "receipt_date": "2026-10-06",
            "category": "packaging",
            "currency": "INR",
            "total_paise": 186000,
            "status": "confirmed",
            "confirmed_at": "2026-10-06 17:15:00",
            "file_name": "ganesh_pack_oct06.svg",
            "file_hash": "hash_ganesh_02",
            "mime_type": "image/svg+xml",
            "flags": [],
            "duplicate_of_id": None,
            "items": [
                ("Cardboard Shipping Boxes (50 pcs)", 50.0, 120000, 2400),
                ("Brown Packaging Tape (6 Rolls)", 6.0, 66000, 11000),
            ],
        },
        {
            "id": "rec_citytrans_03",
            "vendor": "City Goods Transport",
            "receipt_date": "2026-10-09",
            "category": "transport",
            "currency": "INR",
            "total_paise": 240000,
            "status": "confirmed",
            "confirmed_at": "2026-10-09 11:20:00",
            "file_name": "transport_oct09.svg",
            "file_hash": "hash_citytrans_03",
            "mime_type": "image/svg+xml",
            "flags": [],
            "duplicate_of_id": None,
            "items": [
                ("Stationery Consignment Freight Delivery", 1.0, 240000, 240000),
            ],
        },
        {
            "id": "rec_power_04",
            "vendor": "Rajasthan Power Vidyut",
            "receipt_date": "2026-10-12",
            "category": "utilities",
            "currency": "INR",
            "total_paise": 312000,
            "status": "confirmed",
            "confirmed_at": "2026-10-12 16:45:00",
            "file_name": "power_bill_oct12.svg",
            "file_hash": "hash_power_04",
            "mime_type": "image/svg+xml",
            "flags": [],
            "duplicate_of_id": None,
            "items": [
                ("Shop Electricity Bill (Oct 2026)", 1.0, 312000, 312000),
            ],
        },
        {
            "id": "rec_locksmith_05",
            "vendor": "Mahalaxmi Hardware",
            "receipt_date": "2026-10-14",
            "category": "repairs",
            "currency": "INR",
            "total_paise": 94000,
            "status": "needs_review",
            "confirmed_at": None,
            "file_name": "hardware_receipt.svg",
            "file_hash": "hash_hardware_05",
            "mime_type": "image/svg+xml",
            "flags": ["date"],
            "duplicate_of_id": None,
            "items": [
                ("Shop Shutter Padlock & 3 Keys", 1.0, 94000, 94000),
            ],
        },
        {
            "id": "rec_ganesh_dup_06",
            "vendor": "Ganesh Packaging",
            "receipt_date": "2026-10-06",
            "category": "packaging",
            "currency": "INR",
            "total_paise": 186000,
            "status": "duplicate",
            "confirmed_at": None,
            "file_name": "ganesh_duplicate.svg",
            "file_hash": "hash_ganesh_02",
            "mime_type": "image/svg+xml",
            "flags": ["duplicate"],
            "duplicate_of_id": "rec_ganesh_02",
            "items": [
                ("Cardboard Shipping Boxes (50 pcs)", 50.0, 120000, 2400),
                ("Brown Packaging Tape (6 Rolls)", 6.0, 66000, 11000),
            ],
        },
    ]

    for r in receipts_data:
        file_path = create_sample_svg(
            r["file_name"],
            r["vendor"],
            f"₹{r['total_paise'] / 100.0:,.2f}",
            r["receipt_date"],
        )

        conn.execute(
            """
            INSERT INTO receipts (
                id, vendor, receipt_date, category, currency, total_paise,
                status, confirmed_at, file_path, file_name, file_hash, mime_type,
                flags_json, duplicate_of_receipt_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                r["id"],
                r["vendor"],
                r["receipt_date"],
                r["category"],
                r["currency"],
                r["total_paise"],
                r["status"],
                r["confirmed_at"],
                str(file_path),
                r["file_name"],
                r["file_hash"],
                r["mime_type"],
                json.dumps(r["flags"]),
                r["duplicate_of_id"],
            ),
        )

        for idx, item in enumerate(r["items"]):
            conn.execute(
                """
                INSERT INTO receipt_items (receipt_id, item_order, description, quantity, line_total_paise, unit_price_paise)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (r["id"], idx, item[0], item[1], item[2], item[3]),
            )

        event_name = "CONFIRMED" if r["status"] == "confirmed" else "UPLOADED"
        conn.execute(
            """
            INSERT INTO receipt_events (receipt_id, event_type, details_json)
            VALUES (?, ?, ?);
            """,
            (r["id"], event_name, json.dumps({"note": "Seed demo receipt"})),
        )

    conn.commit()
    conn.close()
    print("Database successfully seeded with realistic stationery shop expenses!")


if __name__ == "__main__":
    seed_database()
