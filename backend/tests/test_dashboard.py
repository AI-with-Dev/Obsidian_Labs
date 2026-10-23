import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import get_db, init_db


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Use an isolated database for each test."""
    test_db = tmp_path / "test_dashboard.db"
    test_uploads = tmp_path / "uploads"
    test_uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.app.config.settings.DATABASE_PATH", str(test_db))
    monkeypatch.setattr("backend.app.config.settings.UPLOAD_DIR", str(test_uploads))
    init_db(str(test_db))


client = TestClient(app)


def test_empty_dashboard():
    """Empty database should report 0.0 spend, 0 confirmed, 0 review, and empty lists."""
    res_summary = client.get("/api/dashboard/summary")
    assert res_summary.status_code == 200
    summary = res_summary.json()["data"]
    assert summary["totalSpent"] == 0.0
    assert summary["totalBalance"] == 0.0
    assert summary["confirmedCount"] == 0
    assert summary["reviewCount"] == 0
    assert summary["topVendors"] == []

    res_cats = client.get("/api/dashboard/categories")
    assert res_cats.status_code == 200
    assert res_cats.json()["data"] == []


def test_dashboard_excludes_unconfirmed_and_discarded():
    """Unconfirmed and discarded receipts must NEVER affect totalSpent or confirmedCount."""
    # 1. Uploaded receipt (pending review)
    res1 = client.post("/api/receipts/upload", files={"file": ("r1.jpg", io.BytesIO(b"file 1"), "image/jpeg")})
    id1 = res1.json()["data"]["id"]
    client.patch(f"/api/receipts/{id1}", json={"vendor": "Shop A", "date": "2026-10-10", "total": 999.0, "category": "inventory"})

    # 2. Duplicate receipt (pending owner decision)
    res2 = client.post("/api/receipts/upload", files={"file": ("r2.jpg", io.BytesIO(b"file 1"), "image/jpeg")})
    id2 = res2.json()["data"]["id"]

    # 3. Discarded duplicate receipt
    res3 = client.post("/api/receipts/upload", files={"file": ("r3.jpg", io.BytesIO(b"file 1"), "image/jpeg")})
    id3 = res3.json()["data"]["id"]
    client.post(f"/api/receipts/{id3}/discard-duplicate")

    # Assert summary state
    summary = client.get("/api/dashboard/summary").json()["data"]
    assert summary["totalSpent"] == 0.0
    assert summary["confirmedCount"] == 0
    # id1 (needs_review) + id2 (duplicate) = 2 waiting reviews; id3 (discarded) excluded
    assert summary["reviewCount"] == 2
    assert summary["topVendors"] == []

    cats = client.get("/api/dashboard/categories").json()["data"]
    assert cats == []


def test_dashboard_aggregations_and_precision():
    """Validate accurate confirmed spending, category totals, and top vendor ranking."""
    # Receipt 1: Vikas Stationery, ₹1,800.50, inventory
    r1 = client.post("/api/receipts/upload", files={"file": ("r1.png", io.BytesIO(b"f1"), "image/png")}).json()["data"]["id"]
    client.patch(f"/api/receipts/{r1}", json={"vendor": "Vikas Stationery", "date": "2026-10-10", "total": 1800.50, "category": "inventory"})
    client.post(f"/api/receipts/{r1}/confirm")

    # Receipt 2: Vikas Stationery, ₹199.50, packaging
    r2 = client.post("/api/receipts/upload", files={"file": ("r2.png", io.BytesIO(b"f2"), "image/png")}).json()["data"]["id"]
    client.patch(f"/api/receipts/{r2}", json={"vendor": "Vikas Stationery", "date": "2026-10-11", "total": 199.50, "category": "packaging"})
    client.post(f"/api/receipts/{r2}/confirm")

    # Receipt 3: Navneet Publications, ₹5,000.00, inventory
    r3 = client.post("/api/receipts/upload", files={"file": ("r3.png", io.BytesIO(b"f3"), "image/png")}).json()["data"]["id"]
    client.patch(f"/api/receipts/{r3}", json={"vendor": "Navneet Publications", "date": "2026-10-12", "total": 5000.00, "category": "inventory"})
    client.post(f"/api/receipts/{r3}/confirm")

    # 1 unconfirmed receipt (should not affect totals)
    r4 = client.post("/api/receipts/upload", files={"file": ("r4.png", io.BytesIO(b"f4"), "image/png")}).json()["data"]["id"]
    client.patch(f"/api/receipts/{r4}", json={"vendor": "Pending Store", "date": "2026-10-13", "total": 9999.00, "category": "transport"})

    # Check summary
    summary = client.get("/api/dashboard/summary").json()["data"]
    assert summary["totalSpent"] == 7000.0  # 1800.50 + 199.50 + 5000.00 = 7000.00 exact
    assert summary["confirmedCount"] == 3
    assert summary["reviewCount"] == 1

    # Check top vendors (sorted descending by spend)
    assert len(summary["topVendors"]) == 2
    assert summary["topVendors"][0]["vendor"] == "Navneet Publications"
    assert summary["topVendors"][0]["amount"] == 5000.0
    assert summary["topVendors"][1]["vendor"] == "Vikas Stationery"
    assert summary["topVendors"][1]["amount"] == 2000.0  # 1800.50 + 199.50

    # Check categories (sorted descending by spend)
    cats = client.get("/api/dashboard/categories").json()["data"]
    assert len(cats) == 2
    assert cats[0]["category"] == "inventory"
    assert cats[0]["amount"] == 6800.50  # 1800.50 + 5000.00
    assert cats[1]["category"] == "packaging"
    assert cats[1]["amount"] == 199.50


def test_dashboard_separates_received_income_from_spending():
    """Dashboard balance is confirmed income minus confirmed expenses."""
    income_id = client.post(
        "/api/receipts/upload",
        files={"file": ("sale.png", io.BytesIO(b"income receipt"), "image/png")},
    ).json()["data"]["id"]
    client.patch(
        f"/api/receipts/{income_id}",
        json={
            "vendor": "Customer",
            "date": "2026-10-20",
            "total": 750.0,
            "category": "retail_sales",
        },
    )
    client.post(f"/api/receipts/{income_id}/confirm")
    with get_db() as conn:
        conn.execute(
            "UPDATE receipts SET transaction_type = 'income' WHERE id = ?;",
            (income_id,),
        )

    expense_id = client.post(
        "/api/receipts/upload",
        files={"file": ("purchase.png", io.BytesIO(b"expense receipt"), "image/png")},
    ).json()["data"]["id"]
    client.patch(
        f"/api/receipts/{expense_id}",
        json={
            "vendor": "Paper Supplier",
            "date": "2026-10-21",
            "total": 300.0,
            "category": "inventory",
        },
    )
    client.post(f"/api/receipts/{expense_id}/confirm")

    summary = client.get("/api/dashboard/summary").json()["data"]
    assert summary["totalSpent"] == 300.0
    assert summary["totalReceived"] == 750.0
    assert summary["totalBalance"] == 450.0
    assert summary["confirmedCount"] == 2
