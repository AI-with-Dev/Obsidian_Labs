import httpx
import pytest

from backend.app.config import settings
from backend.app.database import PostgresConnection, validate_database_url
from backend.app.storage import (
    _url,
    delete_object,
    download_object,
    ensure_storage_bucket,
    upload_object,
    validate_storage_configuration,
)


def test_storage_url_handles_supabase_rest_api_url(monkeypatch):
    monkeypatch.setattr(
        settings,
        "SUPABASE_URL",
        "https://project.supabase.co/rest/v1/",
    )

    assert _url("bucket/receipt-files") == (
        "https://project.supabase.co/storage/v1/bucket/receipt-files"
    )


def test_storage_url_trims_copied_whitespace(monkeypatch):
    monkeypatch.setattr(
        settings,
        "SUPABASE_URL",
        "  https://project.supabase.co\n",
    )

    assert _url("bucket/receipt-files") == (
        "https://project.supabase.co/storage/v1/bucket/receipt-files"
    )


def test_storage_configuration_rejects_internal_url_newlines(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "")
    monkeypatch.setattr(
        settings,
        "SUPABASE_URL",
        "https://project.supabase.co\n/rest/v1",
    )
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "server-only-test-key")

    with pytest.raises(RuntimeError, match="no whitespace or extra path"):
        validate_storage_configuration()


def test_postgres_placeholder_conversion_preserves_quoted_question_marks():
    query = "SELECT '?' AS literal, col FROM table WHERE a = ? AND b = \"?\""
    assert PostgresConnection._postgres_placeholders(query) == (
        "SELECT '?' AS literal, col FROM table WHERE a = %s AND b = \"?\""
    )


def test_database_url_rejects_unescaped_at_in_password():
    with pytest.raises(RuntimeError, match=r"URL-encode reserved characters.*%40"):
        validate_database_url(
            "postgresql://postgres.project:pass@word@aws-0-region.pooler.supabase.com:5432/postgres"
        )


def test_database_url_accepts_percent_encoded_at_in_password():
    validate_database_url(
        "postgresql://postgres.project:pass%40word@aws-0-region.pooler.supabase.com:5432/postgres"
    )


def test_storage_configuration_requires_complete_credentials(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")

    with pytest.raises(RuntimeError, match="Set both SUPABASE_URL"):
        validate_storage_configuration()


def test_supabase_storage_bucket_and_object_operations(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "server-only-test-key")
    monkeypatch.setattr(settings, "SUPABASE_STORAGE_BUCKET", "receipt-files")

    calls = []

    def handle_request(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/bucket/receipt-files") and request.method == "GET":
            if len([call for call in calls if call.method == "GET"]) == 1:
                return httpx.Response(404)
            return httpx.Response(200, json={"id": "receipt-files", "public": False})
        if request.url.path.endswith("/bucket") and request.method == "POST":
            assert request.read()
            return httpx.Response(200, json={"name": "receipt-files", "public": False})
        if request.method == "POST":
            assert request.content == b"receipt bytes"
            assert request.headers["x-upsert"] == "false"
            return httpx.Response(200, json={"Key": "receipt-files/1/receipt.png"})
        if request.method == "GET":
            return httpx.Response(200, content=b"receipt bytes")
        if request.method == "DELETE":
            assert b"1/receipt.png" in request.read()
            return httpx.Response(200, json={"message": "deleted"})
        raise AssertionError(f"Unexpected storage request: {request.method} {request.url}")

    transport = httpx.MockTransport(handle_request)
    client_type = httpx.Client
    monkeypatch.setattr(
        "backend.app.storage.httpx.Client",
        lambda **kwargs: client_type(transport=transport, **kwargs),
    )

    ensure_storage_bucket()
    upload_object("1/receipt.png", b"receipt bytes", "image/png")
    assert download_object("1/receipt.png") == b"receipt bytes"
    delete_object("1/receipt.png")
    assert all(call.headers["apikey"] == "server-only-test-key" for call in calls)
    assert all(
        call.headers["authorization"] == "Bearer server-only-test-key"
        for call in calls
    )


def test_bucket_setup_error_includes_supabase_response(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "server-only-test-key")
    monkeypatch.setattr(settings, "SUPABASE_STORAGE_BUCKET", "receipt-files")

    responses = iter(
        [
            httpx.Response(404, json={"message": "Bucket not found"}),
            httpx.Response(401, json={"message": "Invalid API key"}),
        ]
    )
    transport = httpx.MockTransport(lambda request: next(responses))
    client_type = httpx.Client
    monkeypatch.setattr(
        "backend.app.storage.httpx.Client",
        lambda **kwargs: client_type(transport=transport, **kwargs),
    )

    with pytest.raises(RuntimeError, match=r"HTTP 401.*Invalid API key"):
        ensure_storage_bucket()
