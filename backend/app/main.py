import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

repository_root = str(Path(__file__).resolve().parents[2])
if repository_root not in sys.path:
    sys.path.insert(0, repository_root)

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database import get_db, init_db
from backend.app.models import ApiResponse
from backend.app.routers.auth import require_authenticated_owner, router as auth_router

# Configure server-side logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("shopledger.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for FastAPI."""
    logger.info("Initializing Vyapar Mitra database and storage...")
    init_db()
    settings.upload_dir_resolved.mkdir(parents=True, exist_ok=True)
    logger.info("Backend initialization complete.")
    yield
    logger.info("Vyapar Mitra backend shutting down.")


app = FastAPI(
    title="Vyapar Mitra API",
    description="Expense management and receipt extraction backend for Indian small shops.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from starlette.exceptions import HTTPException as StarletteHTTPException

# Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTPException on %s: %s", request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.fail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        ).model_dump(),
    )



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_msg = errors[0]["msg"] if errors else "Invalid request payload."
    logger.warning("Validation error on %s: %s", request.url.path, errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiResponse.fail(
            code="VALIDATION_ERROR",
            message=f"Validation error: {first_msg}",
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse.fail(
            code="INTERNAL_SERVER_ERROR",
            message="Something went wrong on the server. Please try again.",
        ).model_dump(),
    )


# Health Check Endpoint
@app.get("/")
async def root_health_check():
    """Respond to hosting platforms that probe the application root."""
    return {
        "status": "ok",
        "service": "Vyapar Mitra API",
        "frontend": "hosted separately",
    }


@app.get("/script-health-check")
async def streamlit_script_health_check():
    """Respond to Streamlit Community Cloud's script health probe."""
    return {"status": "ok"}


@app.get("/api/health", response_model=ApiResponse[dict])
async def health_check():
    """Verify backend and database health."""
    db_status = "connected"
    try:
        with get_db() as conn:
            conn.execute("SELECT 1;").fetchone()
    except Exception as e:
        logger.error("Health check database failure: %s", e)
        db_status = f"unhealthy: {e}"

    return ApiResponse.ok({
        "status": "ok",
        "database": db_status,
        "version": "0.1.0",
    })


@app.get("/healthz")
async def streamlit_health_check():
    """Provide the plain HTTP health endpoint expected by Streamlit hosting."""
    try:
        with get_db() as conn:
            conn.execute("SELECT 1;").fetchone()
    except Exception as exc:
        logger.error("Streamlit health check database failure: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy"},
        )
    return {"status": "ok"}


# Routers
from backend.app.routers.receipts import router as receipts_router
from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.questions import router as questions_router

from backend.app.routers.export import router as export_router

app.include_router(auth_router)
app.include_router(receipts_router)
app.include_router(dashboard_router)
app.include_router(questions_router)
app.include_router(export_router)


from fastapi.responses import Response

@app.get("/api/export/pdf", dependencies=[Depends(require_authenticated_owner)])
async def export_payments_pdf(owner: dict = Depends(require_authenticated_owner)):
    """Export confirmed customer receipts/payments to official PDF format."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT vendor, receipt_date, category, currency, total_paise, transaction_type
            FROM receipts
            WHERE owner_id = ? AND status = 'confirmed'
            ORDER BY receipt_date DESC, created_at DESC;
            """,
            (owner["id"],),
        ).fetchall()

        total_received = sum(
            r["total_paise"] or 0 for r in rows if r["transaction_type"] == "income"
        ) / 100.0
        total_spent = sum(
            r["total_paise"] or 0 for r in rows if r["transaction_type"] == "expense"
        ) / 100.0

        stream = "BT /F1 16 Tf 50 780 Td (Vyapar Mitra - Official Payment & Collections Summary) Tj\n"
        stream += f"/F2 10 Tf 0 -22 Td (Export Format: Official PDF | Total Records: {len(rows)}) Tj\n"
        stream += f"/F1 12 Tf 0 -24 Td (TOTAL MONEY RECEIVED: (+) INR {total_received:,.2f}) Tj\n"
        stream += f"/F1 10 Tf 0 -18 Td (TOTAL MONEY GIVEN: (-) INR {total_spent:,.2f}) Tj\n"
        stream += "/F1 10 Tf 0 -28 Td (Date         Type      Customer / Vendor                 Amount) Tj\n"
        stream += "/F2 9 Tf 0 -5 Td (--------------------------------------------------------------------------------) Tj\n"

        for r in rows[:30]:
            d = (r["receipt_date"] or "----").ljust(12)
            transaction_type = r["transaction_type"]
            label = "Received" if transaction_type == "income" else "Expense"
            sign = "+" if transaction_type == "income" else "-"
            name = (r["vendor"] or "Unknown")[:32].ljust(34)
            amt = f"({sign}) INR {(r['total_paise'] or 0)/100.0:,.2f}"
            line = f"{d} {label.ljust(9)} {name} {amt}".replace("(", "").replace(")", "").replace("\\", "")
            stream += f"0 -18 Td ({line}) Tj\n"

        stream += "ET"

        o1 = "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        o2 = "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        o3 = "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>\nendobj\n"
        o4 = "4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n"
        o5 = "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        o6 = f"6 0 obj\n<< /Length {len(stream)} >>\nstream\n{stream}\nendstream\nendobj\n"

        header = "%PDF-1.4\n"
        p1 = len(header)
        p2 = p1 + len(o1)
        p3 = p2 + len(o2)
        p4 = p3 + len(o3)
        p5 = p4 + len(o4)
        p6 = p5 + len(o5)
        xref_pos = p6 + len(o6)

        def pad(n: int) -> str:
            return f"{n:010d} 00000 n \n"

        xref = f"xref\n0 7\n0000000000 65535 f \n{pad(p1)}{pad(p2)}{pad(p3)}{pad(p4)}{pad(p5)}{pad(p6)}"
        trailer = f"trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF"

        pdf_bytes = (header + o1 + o2 + o3 + o4 + o5 + o6 + xref + trailer).encode("latin-1")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=vyapar-mitra-payment-summary.pdf"},
        )
