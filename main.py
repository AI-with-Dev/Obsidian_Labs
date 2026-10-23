"""ASGI entry point for hosting ShopLedger's FastAPI backend."""

from backend.app.main import app

__all__ = ["app"]
