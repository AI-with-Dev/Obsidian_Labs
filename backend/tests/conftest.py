import sys
from pathlib import Path

import pytest

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.main import app
from backend.app.routers.auth import require_authenticated_owner


_LEGACY_AUTHENTICATED_MODULES = {
    "test_extraction",
    "test_review_confirmation",
    "test_review_confirm",
    "test_upload",
}


@pytest.fixture(autouse=True)
def authenticate_existing_api_workflows(request):
    if request.module.__name__.rsplit(".", 1)[-1] not in _LEGACY_AUTHENTICATED_MODULES:
        yield
        return

    app.dependency_overrides[require_authenticated_owner] = lambda: {"id": 1}
    try:
        yield
    finally:
        app.dependency_overrides.pop(require_authenticated_owner, None)
