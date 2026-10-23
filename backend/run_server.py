import sys
from pathlib import Path

# Add project root to sys.path so 'backend.app' imports resolve cleanly
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import uvicorn
from backend.app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
