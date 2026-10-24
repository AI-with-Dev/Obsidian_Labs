import csv
import io
import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db, init_db
from backend.app.main import app
from backend.app.routers.export import sanitize_csv_cell
from conftest import ensure_test_owner


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Ensure an isolated database for each test so dev database is never affected."""
    test_db = tmp_path / "test_csv_export.db"
    test_uploads = tmp_path / "uploads"
    test_uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.app.config.settings.DATABASE_PATH", str(test_db))
    monkeypatch.setattr("backend.app.config.settings.UPLOAD_DIR", str(test_uploads))
    init_db(str(test_db))
    ensure_test_owner(str(test_db))


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
    """Test CSV export when no confirmed ledger entries exist."""
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "vyapar-mitra-ledger.csv" in response.headers["content-disposition"]
    
    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0] == ["Party/Vendor", "Date", "Type", "Currency", "Total"]


def test_export_confirmed_income_and_expense_entries(client):
    """Export confirmed income and expenses while excluding unconfirmed receipts."""
    with get_db() as conn:
        # Confirmed expense
        conn.execute(
            """
            INSERT INTO receipts (id, owner_id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_1', 1, 'confirmed', 'Gupta Papers', '2026-10-12', 'inventory', 'INR', 45000, 'path1.jpg', 'r1.jpg', 'hash1', 'image/jpeg');
            """
        )
        # Confirmed expense
        conn.execute(
            """
            INSERT INTO receipts (id, owner_id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_2', 1, 'confirmed', 'Sharma Book Depot', '2026-10-15', 'inventory', 'INR', 125000, 'path2.jpg', 'r2.jpg', 'hash2', 'image/jpeg');
            """
        )
        # Confirmed income
        conn.execute(
            """
            INSERT INTO receipts (id, owner_id, status, vendor, receipt_date, category, currency, total_paise, transaction_type, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_income', 1, 'confirmed', 'Ramu Kaka', '2026-10-16', 'retail_sales', 'INR', 10000, 'income', 'path_income.jpg', 'income.jpg', 'hash_income', 'image/jpeg');
            """
        )
        # Needs review (draft)
        conn.execute(
            """
            INSERT INTO receipts (id, owner_id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_draft', 1, 'needs_review', 'Draft Vendor', '2026-10-14', 'packaging', 'INR', 20000, 'path3.jpg', 'r3.jpg', 'hash3', 'image/jpeg');
            """
        )
        # Duplicate
        conn.execute(
            """
            INSERT INTO receipts (id, owner_id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_dup', 1, 'duplicate', 'Duplicate Vendor', '2026-10-14', 'inventory', 'INR', 45000, 'path4.jpg', 'r4.jpg', 'hash4', 'image/jpeg');
            """
        )
        # Discarded
        conn.execute(
            """
            INSERT INTO receipts (id, owner_id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_disc', 1, 'discarded_duplicate', 'Discarded Vendor', '2026-10-10', 'repairs', 'INR', 30000, 'path5.jpg', 'r5.jpg', 'hash5', 'image/jpeg');
            """
        )
        conn.commit()

    response = client.get("/api/export/csv")
    assert response.status_code == 200
    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)

    # 1 header + 3 confirmed entries
    assert len(rows) == 4
    assert rows[0] == ["Party/Vendor", "Date", "Type", "Currency", "Total"]
    # Entries are sorted by date descending and include both income and expenses.
    assert rows[1] == ["Ramu Kaka", "2026-10-16", "income", "INR", "100.00"]
    assert rows[2] == ["Sharma Book Depot", "2026-10-15", "expense", "INR", "1250.00"]
    assert rows[3] == ["Gupta Papers", "2026-10-12", "expense", "INR", "450.00"]


def test_export_formula_injection_and_rfc4180_escaping(client):
    """Test formula injection characters in vendor/category and quotes/commas."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO receipts (id, owner_id, status, vendor, receipt_date, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_inj1', 1, 'confirmed', '=SUM(1,2)', '2026-10-10', 'inventory', 'INR', 5000, 'p1.jpg', 'r1.jpg', 'h1', 'image/jpeg');
            """
        )
        conn.execute(
            """
            INSERT INTO receipts (id, owner_id, status, vendor, receipt_date, transaction_type, category, currency, total_paise, file_path, file_name, file_hash, mime_type)
            VALUES ('rec_inj2', 1, 'confirmed', '@Attacker, "Special" Books', '2026-10-09', '+income', '+packaging', 'INR', 8500, 'p2.jpg', 'r2.jpg', 'h2', 'image/jpeg');
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
    # and a formula-like transaction type should also be neutralized.
    assert rows[2][0] == '\'@Attacker, "Special" Books'
    assert rows[2][2] == "'+income"
    assert rows[2][4] == "85.00"
