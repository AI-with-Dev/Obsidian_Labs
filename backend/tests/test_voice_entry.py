import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db
from conftest import ensure_test_owner


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Use an isolated database and upload directory for each test."""
    test_db = tmp_path / "test_voice.db"
    test_uploads = tmp_path / "uploads"
    test_uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.app.config.settings.DATABASE_PATH", str(test_db))
    monkeypatch.setattr("backend.app.config.settings.UPLOAD_DIR", str(test_uploads))
    init_db(str(test_db))
    ensure_test_owner(str(test_db))


client = TestClient(app)


def test_voice_quick_entry_success_under_1000():
    """Valid voice entry under ₹1,000 immediately confirms and sets the data column."""
    payload = {
        "spoken_text": "Tea and biscuits 60 rupees",
        "amount": 60.0,
        "vendor": "Chai Corner",
        "category": "utilities",
        "data": "Spoken: Tea and biscuits 60 rupees (Calculated: ₹60.00)",
    }
    res = client.post("/api/receipts/voice-quick-entry", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["status"] == "confirmed"
    assert data["total"] == 60.0
    assert data["vendor"] == "Chai Corner"
    assert data["category"] == "utilities"
    assert data["data"] == "Spoken: Tea and biscuits 60 rupees (Calculated: ₹60.00)"
    assert data["type"] == "income"
    assert len(data["items"]) == 1
    assert data["items"][0]["amount"] == 60.0

    # Verify retrieval
    res_get = client.get(f"/api/receipts/{data['id']}")
    assert res_get.status_code == 200
    assert res_get.json()["data"]["data"] == payload["data"]
    assert res_get.json()["data"]["type"] == "income"

    # Verify SVG file voucher is readable
    res_file = client.get(f"/api/receipts/{data['id']}/file")
    assert res_file.status_code == 200
    assert "VOICE MONEY ADDED VOUCHER" in res_file.text
    assert "+ INR 60.00" in res_file.text

    # Verify dashboard reflects confirmed receipt
    summary = client.get("/api/dashboard/summary").json()["data"]
    assert summary["totalSpent"] == 0.0
    assert summary["totalReceived"] == 60.0
    assert summary["totalBalance"] == 60.0
    assert summary["confirmedCount"] == 1
    assert summary["reviewCount"] == 0


def test_voice_quick_entry_allows_large_amounts_and_rejects_zero():
    """Quick voice audio entry allows amounts >= ₹1,000 as money added, but rejects <= 0."""
    # 1500 rupees succeeds as money added
    res_1500 = client.post(
        "/api/receipts/voice-quick-entry",
        json={"spoken_text": "Cash received 1500", "amount": 1500.0, "vendor": "Counter Sales"},
    )
    assert res_1500.status_code == 200
    data_1500 = res_1500.json()["data"]
    assert data_1500["total"] == 1500.0
    assert data_1500["type"] == "income"

    # 0 or negative must be rejected
    res_zero = client.post(
        "/api/receipts/voice-quick-entry",
        json={"spoken_text": "Zero", "amount": 0.0},
    )
    assert res_zero.status_code == 400


def test_voice_entry_calculation_breakdown():
    """Voice entry with item sums under ₹1,000 persists correctly in the data column."""
    payload = {
        "spoken_text": "2 notebooks 40 rupees each and 1 pen 10 rupees",
        "amount": 90.0,
        "vendor": "Stationery Items",
        "category": "inventory",
        "data": "2x40 + 10 = ₹90.00",
    }
    res = client.post("/api/receipts/voice-quick-entry", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 90.0
    assert data["data"] == "2x40 + 10 = ₹90.00"


def test_voice_voucher_escapes_user_content_as_xml():
    res = client.post(
        "/api/receipts/voice-quick-entry",
        json={
            "spoken_text": "<script>alert(1)</script>",
            "amount": 25.0,
            "vendor": "<img src=x>",
        },
    )
    assert res.status_code == 200

    voucher = client.get(f"/api/receipts/{res.json()['data']['id']}/file")
    assert voucher.status_code == 200
    assert "<script>" not in voucher.text
    assert "&lt;script&gt;" in voucher.text
    assert "&lt;img src=x&gt;" in voucher.text


def test_voice_entry_high_concurrency_load():
    """Verify backend handles rapid concurrent voice requests without lock timeouts or deadlocks."""
    import concurrent.futures

    def post_entry(idx: int):
        return client.post(
            "/api/receipts/voice-quick-entry",
            json={
                "spoken_text": f"Customer {idx} payment {10 + idx}",
                "amount": float(10 + idx),
                "vendor": f"Customer {idx}",
                "data": f"Stress test item {idx}",
            },
        )

    # 40 concurrent workers posting simultaneous requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(post_entry, i) for i in range(40)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for r in results:
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "confirmed"
        assert r.json()["data"]["type"] == "income"

    # Verify all 40 receipts exist in database
    confirmed = client.get("/api/receipts?status=confirmed").json()["data"]
    stress_entries = [r for r in confirmed if "Stress test item" in (r.get("data") or "")]
    assert len(stress_entries) == 40
