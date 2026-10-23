from fastapi import APIRouter, Depends
from backend.app.database import get_db
from backend.app.models import ApiResponse
from backend.app.routers.auth import require_authenticated_owner

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(require_authenticated_owner)],
)


@router.get("/summary", response_model=ApiResponse[dict])
async def get_dashboard_summary():
    """Calculate dashboard summaries strictly from confirmed receipts in backend application code."""
    with get_db() as conn:
        spent_row = conn.execute(
            """
            SELECT COALESCE(SUM(total_paise), 0) AS total_paise,
                   COUNT(*) AS confirmed_count
            FROM receipts
            WHERE status = 'confirmed' AND transaction_type = 'expense';
            """
        ).fetchone()

        received_row = conn.execute(
            """
            SELECT COALESCE(SUM(total_paise), 0) AS total_paise
            FROM receipts
            WHERE status = 'confirmed' AND transaction_type = 'income';
            """
        ).fetchone()

        confirmed_row = conn.execute(
            "SELECT COUNT(*) AS confirmed_count FROM receipts WHERE status = 'confirmed';"
        ).fetchone()

        review_row = conn.execute(
            """
            SELECT COUNT(*) AS review_count
            FROM receipts
            WHERE status != 'confirmed' AND status != 'discarded_duplicate';
            """
        ).fetchone()

        vendors_cursor = conn.execute(
            """
            SELECT TRIM(vendor) AS vendor_name, COALESCE(SUM(total_paise), 0) AS vendor_paise
            FROM receipts
            WHERE status = 'confirmed' AND transaction_type = 'expense' AND TRIM(vendor) != ''
            GROUP BY TRIM(vendor)
            ORDER BY vendor_paise DESC
            LIMIT 5;
            """
        )

        top_vendors = [
            {
                "vendor": row["vendor_name"],
                "amount": row["vendor_paise"] / 100.0,
            }
            for row in vendors_cursor.fetchall()
        ]

        total_spent = (spent_row["total_paise"] or 0) / 100.0
        total_received = (received_row["total_paise"] or 0) / 100.0
        total_balance = (
            (received_row["total_paise"] or 0) - (spent_row["total_paise"] or 0)
        ) / 100.0
        confirmed_count = confirmed_row["confirmed_count"] or 0
        review_count = review_row["review_count"] or 0

        return ApiResponse.ok({
            "totalSpent": total_spent,
            "totalReceived": total_received,
            "totalBalance": total_balance,
            "confirmedCount": confirmed_count,
            "reviewCount": review_count,
            "topVendors": top_vendors,
        })


@router.get("/categories", response_model=ApiResponse[list])
async def get_dashboard_categories():
    """Calculate category totals strictly from confirmed receipts in backend application code."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT LOWER(TRIM(category)) AS cat_name, COALESCE(SUM(total_paise), 0) AS category_paise
            FROM receipts
            WHERE status = 'confirmed' AND transaction_type = 'expense'
              AND category IS NOT NULL AND TRIM(category) != ''
            GROUP BY LOWER(TRIM(category))
            ORDER BY category_paise DESC;
            """
        )

        categories = [
            {
                "category": row["cat_name"],
                "amount": row["category_paise"] / 100.0,
            }
            for row in cursor.fetchall()
        ]

        return ApiResponse.ok(categories)
