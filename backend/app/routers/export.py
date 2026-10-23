import csv
import io
import logging
from typing import Any
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from backend.app.database import get_db
from backend.app.routers.auth import require_authenticated_owner

logger = logging.getLogger("shopledger.export")

router = APIRouter(
    prefix="/api/export",
    tags=["export"],
    dependencies=[Depends(require_authenticated_owner)],
)


def sanitize_csv_cell(value: Any) -> str:
    """
    Neutralize CSV / Formula Injection attacks (CWE-1236).
    If a cell value starts with '=', '+', '-', or '@', prepend a single quote (').
    This prevents spreadsheet software (Excel, LibreOffice, Google Sheets)
    from executing formulas or dynamic data exchange (DDE) payloads.
    """
    if value is None:
        return ""
    s = str(value).strip()
    if s and s[0] in ("=", "+", "-", "@"):
        return f"'{s}"
    return s


@router.get("/csv")
async def export_expenses_csv() -> Response:
    """
    Export confirmed receipts to CSV format.
    Ensures formula injection protection and strictly standard RFC 4180 escaping.
    Only receipts with status = 'confirmed' are included.
    """
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT vendor, receipt_date, category, currency, total_paise
            FROM receipts
            WHERE status = 'confirmed' AND transaction_type = 'expense'
            ORDER BY receipt_date DESC, created_at DESC;
            """
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")

    # CSV Header matching Claude-built frontend mock
    writer.writerow(["Vendor", "Date", "Category", "Currency", "Total"])

    for r in rows:
        vendor = sanitize_csv_cell(r["vendor"])
        date = sanitize_csv_cell(r["receipt_date"])
        category = sanitize_csv_cell(r["category"])
        currency = sanitize_csv_cell(r["currency"] or "INR")
        total_val = (
            f"{r['total_paise'] / 100.0:.2f}"
            if r["total_paise"] is not None
            else "0.00"
        )
        total = sanitize_csv_cell(total_val)

        writer.writerow([vendor, date, category, currency, total])

    csv_text = output.getvalue()

    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="vyapar-mitra-expenses.csv"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
