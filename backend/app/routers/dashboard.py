from fastapi import APIRouter
from backend.app.database import get_db
from backend.app.models import ApiResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=ApiResponse[dict])
async def get_dashboard_summary():
    """Calculate dashboard summaries strictly from confirmed receipts in backend application code."""
    with get_db() as conn:
        spent_row = conn.execute(
            """
            SELECT COALESCE(SUM(total_paise), 0) AS total_paise,
                   COUNT(*) AS confirmed_count
            FROM receipts
            WHERE status = 'confirmed';
            """
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
            SELECT vendor, COALESCE(SUM(total_paise), 0) AS vendor_paise
            FROM receipts
            WHERE status = 'confirmed' AND vendor != ''
            GROUP BY vendor
            ORDER BY vendor_paise DESC
            LIMIT 5;
            """
        )

        top_vendors = [
            {
                "vendor": row["vendor"],
                "amount": row["vendor_paise"] / 100.0,
            }
            for row in vendors_cursor.fetchall()
        ]

        total_spent = (spent_row["total_paise"] or 0) / 100.0
        confirmed_count = spent_row["confirmed_count"] or 0
        review_count = review_row["review_count"] or 0

        return ApiResponse.ok({
            "totalSpent": total_spent,
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
            SELECT category, COALESCE(SUM(total_paise), 0) AS category_paise
            FROM receipts
            WHERE status = 'confirmed' AND category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY category_paise DESC;
            """
        )

        categories = [
            {
                "category": row["category"],
                "amount": row["category_paise"] / 100.0,
            }
            for row in cursor.fetchall()
        ]

        return ApiResponse.ok(categories)
