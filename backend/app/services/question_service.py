import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from google import genai
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.services.receipt_service import get_receipt_details

logger = logging.getLogger("shopledger.questions")

UNSUPPORTED_MSG_EN = (
    "I can answer simple questions about your confirmed expenses. "
    "I cannot calculate profit because sales revenue is not recorded."
)

UNSUPPORTED_MSG_HI = (
    "मैं आपके सत्यापित खर्चों के बारे में सरल प्रश्नों के उत्तर दे सकता हूँ। "
    "मैं लाभ (profit) की गणना नहीं कर सकता क्योंकि बिक्री का रिकॉर्ड नहीं रखा जाता है।"
)

CATEGORY_NAMES = {
    "inventory": {"en": "inventory", "hi": "इन्वेंट्री / माल"},
    "packaging": {"en": "packaging", "hi": "पैकेजिंग सामग्री"},
    "transport": {"en": "transport", "hi": "परिवहन / भाड़ा"},
    "utilities": {"en": "utilities", "hi": "बिजली / उपयोगिताएँ"},
    "rent": {"en": "rent", "hi": "दुकान का किराया"},
    "repairs": {"en": "repairs", "hi": "मरम्मत व रखरखाव"},
    "other": {"en": "other expenses", "hi": "अन्य खर्च"},
}


class QuestionIntent(BaseModel):
    intent: str = Field(
        description="One of: TOTAL_SPEND, CATEGORY_SPEND, TOP_VENDOR, DATE_RANGE, WAITING_REVIEW, UNSUPPORTED"
    )
    category: Optional[str] = Field(
        default=None,
        description="If CATEGORY_SPEND, one of: inventory, packaging, transport, utilities, rent, repairs, other",
    )
    start_date: Optional[str] = Field(default=None, description="If DATE_RANGE, YYYY-MM-DD start date")
    end_date: Optional[str] = Field(default=None, description="If DATE_RANGE, YYYY-MM-DD end date")


def classify_intent_deterministic(question: str) -> Optional[Tuple[str, Dict]]:
    """Fast deterministic intent detection for common queries and unsupported queries."""
    q = question.lower().strip()

    # 1. Unsupported queries (profit, sales, revenue, turnover, loss, tax calculation)
    unsupported_terms = [
        "profit", "revenue", "sales", "turnover", "margin", "income", "gain",
        "loss", "how much did i earn", "earnings", "net income", "gst filing",
        "मुनाफा", "बिक्री", "कमाई", "लाभ", "टर्नओवर", "फायदा"
    ]
    if any(term in q for term in unsupported_terms):
        return "UNSUPPORTED", {}

    # 2. Waiting review intent
    if any(k in q for k in ["waiting", "pending", "review", "बाकी", "समीक्षा", "लंबित"]):
        if any(w in q for w in ["receipt", "bill", "invoice", "रसीद", "बिल"]):
            return "WAITING_REVIEW", {}

    # 3. Top vendor intent
    if any(k in q for k in ["highest", "top vendor", "most spent", "which vendor", "which shop", "max spend", "सबसे ज्यादा", "सबसे अधिक", "किस विक्रेता"]):
        return "TOP_VENDOR", {}

    # 4. Category spend intent
    for cat in ["inventory", "packaging", "transport", "utilities", "rent", "repairs"]:
        if cat in q:
            return "CATEGORY_SPEND", {"category": cat}
    if "इन्वेंट्री" in q or "माल" in q or "स्टॉक" in q or "stock" in q:
        return "CATEGORY_SPEND", {"category": "inventory"}
    if "पैकिंग" in q or "पैकेजिंग" in q or "packing" in q:
        return "CATEGORY_SPEND", {"category": "packaging"}
    if "भाड़ा" in q or "किराया" in q and "rent" not in q:
        return "CATEGORY_SPEND", {"category": "transport"}
    if "बिजली" in q or "electricity" in q:
        return "CATEGORY_SPEND", {"category": "utilities"}

    # 5. Total spend intent
    if any(k in q for k in ["overall", "total spend", "total expense", "total spent", "how much have i spent", "कुल खर्च", "कुल कितना", "खर्चा"]):
        return "TOTAL_SPEND", {}

    return None


def classify_question_intent(question: str) -> Tuple[str, Dict]:
    """Classify user question using deterministic rules, falling back to Gemini."""
    fast_match = classify_intent_deterministic(question)
    if fast_match:
        return fast_match

    # If Gemini key is available, classify intent using Gemini
    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = f"""You are a question intent classifier for Vyapar Mitra, an expense tracking system for a small shop.
Classify the following user query into exactly ONE of the allowed intents:
- TOTAL_SPEND: queries asking about overall confirmed spending or receipt count
- CATEGORY_SPEND: queries asking about spending on a specific category (inventory, packaging, transport, utilities, rent, repairs, other)
- TOP_VENDOR: queries asking about the highest spend vendor, shop, or supplier
- DATE_RANGE: queries asking about spending between specific dates or time periods
- WAITING_REVIEW: queries asking about receipts waiting for review or pending receipts
- UNSUPPORTED: queries asking about profit, revenue, sales, taxes, non-expense topics, or general talk

User query: "{question}"
"""
            resp = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": QuestionIntent,
                    "temperature": 0.0,
                },
            )
            data = json.loads(resp.text or "{}")
            intent = data.get("intent", "UNSUPPORTED")
            params = {}
            if intent == "CATEGORY_SPEND" and data.get("category"):
                params["category"] = data["category"].lower()
            if intent == "DATE_RANGE":
                params["start_date"] = data.get("start_date")
                params["end_date"] = data.get("end_date")
            return intent, params
        except Exception as e:
            logger.warning("Gemini intent classification fallback: %s", e)

    return "TOTAL_SPEND", {}


def format_money_rupees(amount: float) -> str:
    """Format standard Indian Rupee representation with commas."""
    return f"₹{amount:,.2f}"


def execute_question_answer(question: str, lang: str = "en") -> dict:
    """Execute fixed safe query in application code, calculate numbers, and format answer."""
    intent, params = classify_question_intent(question)
    is_hi = (lang == "hi")

    # Handle unsupported intent
    if intent == "UNSUPPORTED":
        return {
            "answer": UNSUPPORTED_MSG_HI if is_hi else UNSUPPORTED_MSG_EN,
            "supported": False,
            "receipts": [],
        }

    receipt_ids = []
    answer_text = ""

    with get_db() as conn:
        if intent == "TOTAL_SPEND":
            row = conn.execute(
                """
                SELECT COALESCE(SUM(total_paise), 0) AS total_paise, COUNT(*) AS count
                FROM receipts
                WHERE status = 'confirmed' AND transaction_type = 'expense';
                """
            ).fetchone()
            tot = (row["total_paise"] or 0) / 100.0
            cnt = row["count"] or 0

            rows = conn.execute(
                "SELECT id FROM receipts WHERE status = 'confirmed' AND transaction_type = 'expense' ORDER BY receipt_date DESC LIMIT 10;"
            ).fetchall()
            receipt_ids = [r["id"] for r in rows]

            if is_hi:
                answer_text = f"आपने {cnt} सत्यापित रसीदों में कुल {format_money_rupees(tot)} खर्च किए हैं।"
            else:
                answer_text = f"You have spent {format_money_rupees(tot)} across {cnt} confirmed receipts."

        elif intent == "CATEGORY_SPEND":
            cat = params.get("category") or "inventory"
            cat_label = CATEGORY_NAMES.get(cat, {}).get("hi" if is_hi else "en", cat)

            row = conn.execute(
                """
                SELECT COALESCE(SUM(total_paise), 0) AS total_paise, COUNT(*) AS count
                FROM receipts
                WHERE status = 'confirmed' AND transaction_type = 'expense'
                  AND LOWER(TRIM(category)) = ?;
                """,
                (cat,),
            ).fetchone()
            tot = (row["total_paise"] or 0) / 100.0
            cnt = row["count"] or 0

            rows = conn.execute(
                """
                SELECT id FROM receipts
                WHERE status = 'confirmed' AND transaction_type = 'expense'
                  AND LOWER(TRIM(category)) = ?
                ORDER BY receipt_date DESC LIMIT 10;
                """,
                (cat,),
            ).fetchall()
            receipt_ids = [r["id"] for r in rows]

            if is_hi:
                answer_text = f"आपने {cat_label} पर {cnt} सत्यापित रसीदों में {format_money_rupees(tot)} खर्च किए हैं।"
            else:
                answer_text = f"You have spent {format_money_rupees(tot)} on {cat_label} across {cnt} confirmed receipts."

        elif intent == "TOP_VENDOR":
            row = conn.execute(
                """
                SELECT TRIM(vendor) AS vendor_name, COALESCE(SUM(total_paise), 0) AS total_paise, COUNT(*) AS count
                FROM receipts
                WHERE status = 'confirmed' AND transaction_type = 'expense' AND TRIM(vendor) != ''
                GROUP BY TRIM(vendor)
                ORDER BY total_paise DESC
                LIMIT 1;
                """
            ).fetchone()

            if row:
                v_name = row["vendor_name"]
                tot = (row["total_paise"] or 0) / 100.0
                cnt = row["count"] or 0

                rows = conn.execute(
                    """
                    SELECT id FROM receipts
                    WHERE status = 'confirmed' AND transaction_type = 'expense' AND TRIM(vendor) = ?
                    ORDER BY receipt_date DESC LIMIT 10;
                    """,
                    (v_name,),
                ).fetchall()
                receipt_ids = [r["id"] for r in rows]

                if is_hi:
                    answer_text = f"आपका सबसे अधिक खर्च वाला विक्रेता '{v_name}' है, जहाँ {cnt} रसीदों में कुल {format_money_rupees(tot)} खर्च हुआ है।"
                else:
                    answer_text = f"Your highest-spend vendor is '{v_name}' with a total confirmed spend of {format_money_rupees(tot)} across {cnt} receipts."
            else:
                if is_hi:
                    answer_text = "अभी तक कोई सत्यापित रसीद उपलब्ध नहीं है।"
                else:
                    answer_text = "No confirmed receipts are available yet."

        elif intent == "DATE_RANGE":
            start_date = params.get("start_date") or "2000-01-01"
            end_date = params.get("end_date") or "2099-12-31"

            row = conn.execute(
                """
                SELECT COALESCE(SUM(total_paise), 0) AS total_paise, COUNT(*) AS count
                FROM receipts
                WHERE status = 'confirmed' AND transaction_type = 'expense'
                  AND receipt_date >= ? AND receipt_date <= ?;
                """,
                (start_date, end_date),
            ).fetchone()
            tot = (row["total_paise"] or 0) / 100.0
            cnt = row["count"] or 0

            rows = conn.execute(
                """
                SELECT id FROM receipts
                WHERE status = 'confirmed' AND transaction_type = 'expense'
                  AND receipt_date >= ? AND receipt_date <= ?
                ORDER BY receipt_date DESC LIMIT 10;
                """,
                (start_date, end_date),
            ).fetchall()
            receipt_ids = [r["id"] for r in rows]

            if is_hi:
                answer_text = f"{start_date} और {end_date} के बीच, आपने {cnt} सत्यापित रसीदों में {format_money_rupees(tot)} खर्च किए हैं।"
            else:
                answer_text = f"Between {start_date} and {end_date}, you spent {format_money_rupees(tot)} across {cnt} confirmed receipts."

        elif intent == "WAITING_REVIEW":
            row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM receipts
                WHERE status != 'confirmed' AND status != 'discarded_duplicate';
                """
            ).fetchone()
            cnt = row["count"] or 0

            rows = conn.execute(
                """
                SELECT id FROM receipts
                WHERE status != 'confirmed' AND status != 'discarded_duplicate'
                ORDER BY created_at DESC LIMIT 10;
                """
            ).fetchall()
            receipt_ids = [r["id"] for r in rows]

            if cnt == 0:
                answer_text = "सभी रसीदें जाँची जा चुकी हैं! कोई रसीद समीक्षा के लिए बाकी नहीं है।" if is_hi else "All clear! There are no receipts waiting for review."
            else:
                answer_text = f"समीक्षा के लिए {cnt} रसीद(ें) बाकी हैं।" if is_hi else f"You have {cnt} receipt(s) waiting for your review."

    # Fetch receipt details for evidence
    evidence_receipts = [get_receipt_details(rid) for rid in receipt_ids]

    return {
        "answer": answer_text,
        "supported": True,
        "receipts": evidence_receipts,
    }
