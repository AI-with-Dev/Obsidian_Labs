import io
import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db
from backend.app.services import question_service
from conftest import ensure_test_owner


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Use an isolated database for each test."""
    test_db = tmp_path / "test_questions.db"
    test_uploads = tmp_path / "uploads"
    test_uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.app.config.settings.DATABASE_PATH", str(test_db))
    monkeypatch.setattr("backend.app.config.settings.UPLOAD_DIR", str(test_uploads))
    init_db(str(test_db))
    ensure_test_owner(str(test_db))


client = TestClient(app)


def seed_test_receipts():
    """Seed test receipts: 2 confirmed (inventory, packaging) and 1 unconfirmed."""
    # 1. Confirmed Inventory receipt: ₹1,500.00
    r1 = client.post("/api/receipts/upload", files={"file": ("f1.png", io.BytesIO(b"f1"), "image/png")}).json()["data"]["id"]
    client.patch(f"/api/receipts/{r1}", json={"vendor": "Royal Stationery", "date": "2026-10-10", "total": 1500.0, "category": "inventory"})
    client.post(f"/api/receipts/{r1}/confirm")

    # 2. Confirmed Packaging receipt: ₹300.00
    r2 = client.post("/api/receipts/upload", files={"file": ("f2.png", io.BytesIO(b"f2"), "image/png")}).json()["data"]["id"]
    client.patch(f"/api/receipts/{r2}", json={"vendor": "Packers Hub", "date": "2026-10-11", "total": 300.0, "category": "packaging"})
    client.post(f"/api/receipts/{r2}/confirm")

    # 3. Unconfirmed receipt (pending review): ₹5,000.00
    r3 = client.post("/api/receipts/upload", files={"file": ("f3.png", io.BytesIO(b"f3"), "image/png")}).json()["data"]["id"]
    client.patch(f"/api/receipts/{r3}", json={"vendor": "Draft Vendor", "date": "2026-10-12", "total": 5000.0, "category": "inventory"})

    return [r1, r2, r3]


def test_question_total_spend():
    """Overall spend query must calculate confirmed total and return source receipts."""
    seed_test_receipts()

    # English query
    res_en = client.post("/api/questions/ask", json={"question": "What is my total spend overall?", "lang": "en"})
    assert res_en.status_code == 200
    data_en = res_en.json()["data"]
    assert data_en["supported"] is True
    assert "₹1,800.00" in data_en["answer"]
    assert len(data_en["receipts"]) == 2  # Only 2 confirmed receipts

    # Hindi query
    res_hi = client.post("/api/questions/ask", json={"question": "कुल कितना खर्चा हुआ?", "lang": "hi"})
    assert res_hi.status_code == 200
    data_hi = res_hi.json()["data"]
    assert data_hi["supported"] is True
    assert "₹1,800.00" in data_hi["answer"]
    assert "2" in data_hi["answer"]


def test_question_category_spend():
    """Category spend query must filter strictly by category and provide evidence."""
    seed_test_receipts()

    # Query inventory
    res = client.post("/api/questions/ask", json={"question": "How much have I spent on inventory?", "lang": "en"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["supported"] is True
    assert "₹1,500.00" in data["answer"]
    assert len(data["receipts"]) == 1
    assert data["receipts"][0]["vendor"] == "Royal Stationery"

    # Query packaging in Hindi
    res_hi = client.post("/api/questions/ask", json={"question": "पैकेजिंग का खर्च कितना है?", "lang": "hi"})
    assert res_hi.status_code == 200
    data_hi = res_hi.json()["data"]
    assert data_hi["supported"] is True
    assert "₹300.00" in data_hi["answer"]


def test_question_top_vendor():
    """Top vendor query must return the highest spend supplier."""
    seed_test_receipts()

    res = client.post("/api/questions/ask", json={"question": "Who is my highest spend vendor?", "lang": "en"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["supported"] is True
    assert "Royal Stationery" in data["answer"]
    assert "₹1,500.00" in data["answer"]
    assert len(data["receipts"]) == 1


def test_question_waiting_review():
    """Waiting review query must return count and list of unconfirmed receipts."""
    seed_test_receipts()

    res = client.post("/api/questions/ask", json={"question": "How many receipts are waiting for review?", "lang": "en"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["supported"] is True
    assert "1" in data["answer"]
    assert len(data["receipts"]) == 1
    assert data["receipts"][0]["vendor"] == "Draft Vendor"


def test_question_unsupported_queries():
    """Questions asking for profit, revenue, or sales must return supported=False and standard copy."""
    seed_test_receipts()

    # English profit question
    res_en = client.post("/api/questions/ask", json={"question": "What is my net profit this month?", "lang": "en"})
    assert res_en.status_code == 200
    data_en = res_en.json()["data"]
    assert data_en["supported"] is False
    assert "I cannot calculate profit because sales revenue is not recorded." in data_en["answer"]
    assert data_en["receipts"] == []

    # Hindi profit question
    res_hi = client.post("/api/questions/ask", json={"question": "मेरा मुनाफा कितना हुआ?", "lang": "hi"})
    assert res_hi.status_code == 200
    data_hi = res_hi.json()["data"]
    assert data_hi["supported"] is False
    assert "मैं लाभ (profit) की गणना नहीं कर सकता क्योंकि बिक्री का रिकॉर्ड नहीं रखा जाता है।" in data_hi["answer"]

    # Revenue query
    res_rev = client.post("/api/questions/ask", json={"question": "What is our total sales revenue?", "lang": "en"})
    assert res_rev.status_code == 200
    assert res_rev.json()["data"]["supported"] is False


def test_question_money_received_and_borrowed_items():
    """Test Q&A on Money Received (collections) and Borrowed Items (active credit udhar)."""
    # 1. Money received (income): Suresh Bhai ₹500
    r1 = client.post("/api/receipts/upload", files={"file": ("suresh.png", io.BytesIO(b"suresh"), "image/png")}).json()["data"]["id"]
    client.patch(f"/api/receipts/{r1}", json={"vendor": "Suresh Bhai", "date": "2026-10-14", "total": 500.0, "type": "income"})
    client.post(f"/api/receipts/{r1}/confirm")

    # 2. Borrowed / credit udhar (expense): Ramesh ₹20
    r2 = client.post("/api/receipts/upload", files={"file": ("ramesh.png", io.BytesIO(b"ramesh"), "image/png")}).json()["data"]["id"]
    client.patch(f"/api/receipts/{r2}", json={"vendor": "Ramesh", "date": "2026-10-14", "total": 20.0, "type": "expense"})
    client.post(f"/api/receipts/{r2}/confirm")

    # Question about money received in English
    res_inc = client.post("/api/questions/ask", json={"question": "How much total money received?", "lang": "en"})
    assert res_inc.status_code == 200
    data_inc = res_inc.json()["data"]
    assert data_inc["supported"] is True
    assert "₹500.00" in data_inc["answer"]
    assert len(data_inc["receipts"]) == 1
    assert data_inc["receipts"][0]["vendor"] == "Suresh Bhai"

    # Question about borrowed items / udhar in Hindi
    res_bor = client.post("/api/questions/ask", json={"question": "कुल बाकी उधार कितना है?", "lang": "hi"})
    assert res_bor.status_code == 200
    data_bor = res_bor.json()["data"]
    assert data_bor["supported"] is True
    assert "₹20.00" in data_bor["answer"]
    assert len(data_bor["receipts"]) == 1
    assert data_bor["receipts"][0]["vendor"] == "Ramesh"


def test_payment_count_top_payer_and_date_query():
    """Payment questions count and summarize confirmed income, not expense receipts."""
    payment_data = [
        ("Ramu Kaka Aata Becha", 100.00, "2026-10-24"),
        ("Ramesh Kurkura Becha", 5.01, "2026-10-24"),
        ("Earlier Customer", 50.00, "2026-10-23"),
    ]
    payment_ids = []
    for index, (name, amount, receipt_date) in enumerate(payment_data):
        receipt_id = client.post(
            "/api/receipts/upload",
            files={"file": (f"payment-{index}.png", io.BytesIO(b"payment"), "image/png")},
        ).json()["data"]["id"]
        client.patch(
            f"/api/receipts/{receipt_id}",
            json={"vendor": name, "date": receipt_date, "total": amount, "type": "income"},
        )
        client.post(f"/api/receipts/{receipt_id}/confirm")
        payment_ids.append(receipt_id)

    count_response = client.post(
        "/api/questions/ask",
        json={"question": "How many payment entries are recorded?", "lang": "en"},
    )
    assert count_response.status_code == 200
    count_data = count_response.json()["data"]
    assert count_data["supported"] is True
    assert "3 confirmed payment entries" in count_data["answer"]
    assert len(count_data["receipts"]) == 3

    payer_response = client.post(
        "/api/questions/ask",
        json={"question": "Who paid the most, and how much?", "lang": "en"},
    )
    assert payer_response.status_code == 200
    payer_data = payer_response.json()["data"]
    assert payer_data["supported"] is True
    assert "Ramu Kaka Aata Becha" in payer_data["answer"]
    assert "₹100.00" in payer_data["answer"]
    assert [receipt["id"] for receipt in payer_data["receipts"]] == [payment_ids[0]]

    date_response = client.post(
        "/api/questions/ask",
        json={"question": "What payments were received on 2026-10-24?", "lang": "en"},
    )
    assert date_response.status_code == 200
    date_data = date_response.json()["data"]
    assert date_data["supported"] is True
    assert "Ramu Kaka Aata Becha" in date_data["answer"]
    assert "₹100.00" in date_data["answer"]
    assert "Ramesh Kurkura Becha" in date_data["answer"]
    assert "₹5.01" in date_data["answer"]
    assert "Earlier Customer" not in date_data["answer"]
    assert {receipt["id"] for receipt in date_data["receipts"]} == set(payment_ids[:2])


def test_free_form_question_uses_confirmed_ledger_context(monkeypatch):
    """Unmatched questions should be answered from ledger facts, not defaulted to a canned reply."""
    receipt_ids = seed_test_receipts()
    captured_prompt = {}

    class FakeModels:
        def generate_content(self, *, model, contents, config):
            assert model == "test-model"
            if config["response_schema"] is question_service.QuestionIntent:
                return type("Response", (), {"text": '{"intent": "UNSUPPORTED"}'})()
            captured_prompt["contents"] = contents
            assert config["response_schema"] is question_service.LedgerAnswer
            return type(
                "Response",
                (),
                {
                    "text": json.dumps(
                        {
                            "answer": "Royal Stationery is your highest confirmed expense vendor.",
                            "supported": True,
                            "receipt_ids": [receipt_ids[0], "not-a-real-receipt"],
                        }
                    )
                },
            )()

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr(question_service.settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(question_service.settings, "GEMINI_MODEL", "test-model")
    monkeypatch.setattr(question_service.genai, "Client", lambda **kwargs: FakeClient())

    response = client.post(
        "/api/questions/ask",
        json={"question": "What should I notice about these purchase records?", "lang": "en"},
    )
    assert response.status_code == 200
    result = response.json()["data"]

    assert result["supported"] is True
    assert result["answer"] == "Royal Stationery is your highest confirmed expense vendor."
    assert [receipt["id"] for receipt in result["receipts"]] == [receipt_ids[0]]
    assert "Royal Stationery" in captured_prompt["contents"]
    assert "Draft Vendor" not in captured_prompt["contents"]


def test_free_form_question_without_gemini_has_clear_fallback(monkeypatch):
    """Missing AI configuration must not silently turn an arbitrary question into total spend."""
    monkeypatch.setattr(question_service.settings, "GEMINI_API_KEY", "")

    assert question_service.classify_question_intent(
        "Which product do I buy most often?"
    ) == ("LEDGER_QA", {})
    result = question_service.execute_question_answer(
        "Which product do I buy most often?",
        owner_id=1,
    )

    assert result["supported"] is False
    assert "Gemini to be configured" in result["answer"]
    assert "profit" not in result["answer"].lower()
