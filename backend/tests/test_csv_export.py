import csv
import io
import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db, init_db
from backend.app.main import app
from backend.app.routers.export import sanitize_csv_cell


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Ensure an isolated database for each test so dev database is never affected."""
    test_db = tmp_path / "test_csv_export.db"
    test_uploads = tmp_path / "uploads"
    test_uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.app.config.settings.DATABASE_PATH", str(test_db))
    monkeypatch.setattr("backend.app.config.settings.UPLOAD_DIR", str(test_uploads))
    init_db(str(test_db))


@pytest.fixture
def client():
    return TestClient(app)


def test_sanitize_csv_cell_formula_injection():
    """Test formula injection characters are prepended with a single quote."""
    # Formula injection characters
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert sanitize_csv_cell("+44123456789") == "'+44123456789"
    assert sanitize_csv_cell("-100") == "'-100"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    
    # Safe text
    assert sanitize_csv_cell("Stationery Shop") == "Stationery Shop"
    assert sanitize_csv_cell("2026-10-15") == "2026-10-15"
    assert sanitize_csv_cell("1250.00") == "1250.00"
    assert sanitize_csv_cell("") == ""
    assert sanitize_csv_cell(None) == ""


def test_export_empty_csv(client):
    """Test CSV export when no confirmed receipts exist."""
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "vyapar-mitra-expenses.csv" in response.headers["content-disposition"]
    
    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0] == ["Vendor", "Date", "Category", "Currency", "Total"]


def test_export_only_confirmed_receipts(client):
    """Test that only confirmed receipts are exported, ignoring draft/uploaded/discarded."""
    with get_db() as conn:
        # Confirmed receipt 1
        conn.execute(
            """
            INSERT INTO receipts (id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_1', 'confirmed', 'Gupta Papers', '2026-10-12', 'inventory', 'INR', 45000, 'path1.jpg', 'r1.jpg', 'hash1', 'image/jpeg');
            """
        )
        # Confirmed receipt 2
        conn.execute(
            """
            INSERT INTO receipts (id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_2', 'confirmed', 'Sharma Book Depot', '2026-10-15', 'inventory', 'INR', 125000, 'path2.jpg', 'r2.jpg', 'hash2', 'image/jpeg');
            """
        )
        # Needs review (draft)
        conn.execute(
            """
            INSERT INTO receipts (id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_draft', 'needs_review', 'Draft Vendor', '2026-10-14', 'packaging', 'INR', 20000, 'path3.jpg', 'r3.jpg', 'hash3', 'image/jpeg');
            """
        )
        # Duplicate
        conn.execute(
            """
            INSERT INTO receipts (id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_dup', 'duplicate', 'Duplicate Vendor', '2026-10-14', 'inventory', 'INR', 45000, 'path4.jpg', 'r4.jpg', 'hash4', 'image/jpeg');
            """
        )
        # Discarded
        conn.execute(
            """
            INSERT INTO receipts (id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_disc', 'discarded_duplicate', 'Discarded Vendor', '2026-10-10', 'repairs', 'INR', 30000, 'path5.jpg', 'r5.jpg', 'hash5', 'image/jpeg');
            """
        )
        conn.commit()

    response = client.get("/api/export/csv")
    assert response.status_code == 200
    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)

    # 1 header + 2 confirmed rows
    assert len(rows) == 3
    assert rows[0] == ["Vendor", "Date", "Category", "Currency", "Total"]
    # Check ordering by receipt_date DESC: Sharma (15th) then Gupta (12th)
    assert rows[1] == ["Sharma Book Depot", "2026-10-15", "inventory", "INR", "1250.00"]
    assert rows[2] == ["Gupta Papers", "2026-10-12", "inventory", "INR", "450.00"]


def test_export_formula_injection_and_rfc4180_escaping(client):
    """Test formula injection characters in vendor/category and quotes/commas."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO receipts (id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_inj1', 'confirmed', '=SUM(1,2)', '2026-10-10', 'inventory', 'INR', 5000, 'p1.jpg', 'r1.jpg', 'h1', 'image/jpeg');
            """
        )
        conn.execute(
            """
            INSERT INTO receipts (id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_inj2', 'confirmed', '@Attacker, "Special" Books', '2026-10-09', '+packaging', 'INR', 8500, 'p2.jpg', 'r2.jpg', 'h2', 'image/jpeg');
            """
        )
        conn.commit()

    response = client.get("/api/export/csv")
    assert response.status_code == 200

    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 3

    # Row 1: '=SUM(1,2)' should be neutralized to "'=SUM(1,2)"
    assert rows[1][0] == "'=SUM(1,2)"
    assert rows[1][4] == "50.00"

    # Row 2: '@Attacker, "Special" Books' should be neutralized to "'@Attacker, \"Special\" Books"
    # and '+packaging' should be neutralized to "'+packaging"
    assert rows[2][0] == '\'@Attacker, "Special" Books'
    assert rows[2][2] == "'+packaging"
    assert rows[2][4] == "85.00"
