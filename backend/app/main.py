import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database import get_db, init_db
from backend.app.models import ApiResponse

# Configure server-side logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("shopledger.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for FastAPI."""
    logger.info("Initializing ShopLedger database and storage...")
    init_db()
    settings.upload_dir_resolved.mkdir(parents=True, exist_ok=True)
    logger.info("Backend initialization complete.")
    yield
    logger.info("ShopLedger backend shutting down.")


app = FastAPI(
    title="ShopLedger API",
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


# Routers
from backend.app.routers.receipts import router as receipts_router
from backend.app.routers.dashboard import router as dashboard_router

app.include_router(receipts_router)
app.include_router(dashboard_router)


from fastapi.responses import Response

@app.get("/api/export/csv")
async def export_expenses_csv():
    """Export confirmed receipts to CSV format."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT vendor, receipt_date, category, currency, total_paise
            FROM receipts
            WHERE status = 'confirmed'
            ORDER BY receipt_date DESC, created_at DESC;
            """
        ).fetchall()
        lines = ["Vendor,Date,Category,Currency,Total"]
        for r in rows:
            v = (r["vendor"] or "").replace('"', '""')
            d = r["receipt_date"] or ""
            cat = r["category"] or ""
            cur = r["currency"] or "INR"
            tot = f"{r['total_paise'] / 100.0:.2f}" if r["total_paise"] is not None else "0.00"
            lines.append(f'"{v}",{d},{cat},{cur},{tot}')
        csv_content = "\n".join(lines)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=shopledger-expenses.csv"},
        )


