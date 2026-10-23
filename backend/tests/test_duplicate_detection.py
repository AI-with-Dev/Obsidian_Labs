import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Use an isolated database for each test."""
    test_db = tmp_path / "test_shopledger.db"
    test_uploads = tmp_path / "uploads"
    test_uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.app.config.settings.DATABASE_PATH", str(test_db))
    monkeypatch.setattr("backend.app.config.settings.UPLOAD_DIR", str(test_uploads))
    init_db(str(test_db))


client = TestClient(app)


def test_exact_sha256_duplicate_detection():
    """Uploading identical content must flag the second receipt as exact duplicate."""
    file_bytes = b"Sample receipt content for SHA256 test"

    # First upload
    res1 = client.post(
        "/api/receipts/upload",
        files={"file": ("receipt1.jpg", io.BytesIO(file_bytes), "image/jpeg")},
    )
    assert res1.status_code == 200
    id1 = res1.json()["data"]["id"]

    # Verify first upload is 'uploaded' / 'draft'
    detail1 = client.get(f"/api/receipts/{id1}").json()["data"]
    assert detail1["status"] == "draft"
    assert detail1["duplicateOfId"] is None

    # Second upload with identical bytes
    res2 = client.post(
        "/api/receipts/upload",
        files={"file": ("receipt2.jpg", io.BytesIO(file_bytes), "image/jpeg")},
    )
    assert res2.status_code == 200
    id2 = res2.json()["data"]["id"]

    # Verify second upload is flagged as duplicate
    detail2 = client.get(f"/api/receipts/{id2}").json()["data"]
    assert detail2["status"] == "duplicate"
    assert detail2["duplicateOfId"] == id1
    assert "duplicate" in detail2["flags"]


def test_similar_duplicate_detection():
    """Receipt matching confirmed vendor + date + total must be flagged as similar duplicate."""
    # 1. Create and confirm original receipt
    res1 = client.post(
        "/api/receipts/upload",
        files={"file": ("orig.png", io.BytesIO(b"orig file 1"), "image/png")},
    )
    id1 = res1.json()["data"]["id"]

    client.patch(
        f"/api/receipts/{id1}",
        json={
            "vendor": "National Stationery Mart",
            "date": "2026-10-18",
            "currency": "INR",
            "total": 1250.0,
            "category": "inventory",
            "items": [{"name": "Registers", "amount": 1250.0, "quantity": 5, "unitPrice": 250.0}],
        },
    )
    client.post(f"/api/receipts/{id1}/confirm")

    # 2. Upload a second file with DIFFERENT content
    res2 = client.post(
        "/api/receipts/upload",
        files={"file": ("scan2.png", io.BytesIO(b"different scan file 2"), "image/png")},
    )
    id2 = res2.json()["data"]["id"]

    # Save draft on second receipt matching vendor (case-insensitive), date, and total
    patch_res = client.patch(
        f"/api/receipts/{id2}",
        json={
            "vendor": "national stationery mart",
            "date": "2026-10-18",
            "currency": "INR",
            "total": 1250.0,
            "category": "inventory",
            "items": [{"name": "Registers copy", "amount": 1250.0}],
        },
    )
    assert patch_res.status_code == 200


def test_discard_duplicate_action():
    """Discarding a duplicate receipt marks it as discarded and excludes it from ledger."""
    file_bytes = b"duplicate receipt bytes"
    id1 = client.post("/api/receipts/upload", files={"file": ("r1.jpg", io.BytesIO(file_bytes), "image/jpeg")}).json()["data"]["id"]
    id2 = client.post("/api/receipts/upload", files={"file": ("r2.jpg", io.BytesIO(file_bytes), "image/jpeg")}).json()["data"]["id"]

    # Discard second receipt
    discard_res = client.post(f"/api/receipts/{id2}/discard-duplicate")
    assert discard_res.status_code == 200

    # Ensure it no longer appears in pending or confirmed ledger
    pending_list = client.get("/api/receipts?status=pending").json()["data"]
    assert all(r["id"] != id2 for r in pending_list)

    confirmed_list = client.get("/api/receipts?status=confirmed").json()["data"]
    assert all(r["id"] != id2 for r in confirmed_list)


def test_keep_separate_action():
    """Keeping a duplicate receipt separate clears duplicate status and allows confirmation."""
    file_bytes = b"same bytes for keep separate test"
    id1 = client.post("/api/receipts/upload", files={"file": ("k1.jpg", io.BytesIO(file_bytes), "image/jpeg")}).json()["data"]["id"]
    id2 = client.post("/api/receipts/upload", files={"file": ("k2.jpg", io.BytesIO(file_bytes), "image/jpeg")}).json()["data"]["id"]

    # Check initially duplicate
    assert client.get(f"/api/receipts/{id2}").json()["data"]["status"] == "duplicate"

    # Action: keep separate
    keep_res = client.post(f"/api/receipts/{id2}/keep-separate")
    assert keep_res.status_code == 200
    kept_data = keep_res.json()["data"]

    assert kept_data["status"] == "draft"
    assert kept_data["duplicateOfId"] is None
    assert "duplicate" not in kept_data["flags"]

    # Verify receipt can now be edited and confirmed
    client.patch(
        f"/api/receipts/{id2}",
        json={
            "vendor": "Separate Purchase Shop",
            "date": "2026-10-19",
            "currency": "INR",
            "total": 350.0,
            "category": "packaging",
        },
    )
    conf_res = client.post(f"/api/receipts/{id2}/confirm")
    assert conf_res.status_code == 200
    assert conf_res.json()["data"]["status"] == "confirmed"


def test_new_frontend_fields_persistence():
    """Validate persistence of invoiceNumber, tax, discount, paymentMethod, notes, and item unitPrice."""
    res = client.post("/api/receipts/upload", files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")})
    rid = res.json()["data"]["id"]

    payload = {
        "vendor": "Apex Paper Mills",
        "date": "2026-10-21",
        "currency": "INR",
        "category": "inventory",
        "invoiceNumber": "INV-2026-904",
        "subtotal": 1500.0,
        "tax": 270.0,
        "discount": 50.0,
        "total": 1720.0,
        "paymentMethod": "UPI",
        "notes": "Delivered to store front",
        "items": [
            {"name": "Chart Paper 100pk", "amount": 1000.0, "quantity": 2, "unitPrice": 500.0},
            {"name": "Sketch Pens 50pk", "amount": 500.0, "quantity": 5, "unitPrice": 100.0},
        ],
    }

    save_res = client.patch(f"/api/receipts/{rid}", json=payload)
    assert save_res.status_code == 200
    data = save_res.json()["data"]

    assert data["vendor"] == "Apex Paper Mills"
    assert data["invoiceNumber"] == "INV-2026-904"
    assert data["tax"] == 270.0
    assert data["discount"] == 50.0
    assert data["paymentMethod"] == "UPI"
    assert data["notes"] == "Delivered to store front"
    assert data["total"] == 1720.0
    assert len(data["items"]) == 2
    assert data["items"][0]["quantity"] == 2.0
    assert data["items"][0]["unitPrice"] == 500.0
    assert data["items"][1]["quantity"] == 5.0
    assert data["items"][1]["unitPrice"] == 100.0
