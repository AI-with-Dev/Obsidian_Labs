from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from backend.app.models import ApiResponse
from backend.app.services.receipt_service import (
    get_receipt_file,
    process_and_save_upload,
)

router = APIRouter(prefix="/api/receipts", tags=["Receipts"])


@router.post("/upload", response_model=ApiResponse[dict])
async def upload_receipt(file: UploadFile = File(...)):
    """Upload a receipt image (JPG, PNG) or PDF document."""
    receipt_id = await process_and_save_upload(file)
    return ApiResponse.ok({"id": receipt_id})


@router.get("/{id}/file")
@router.head("/{id}/file")
async def stream_receipt_file(id: str):
    """Retrieve and stream the stored receipt image or PDF file."""
    file_path, mime_type, file_name = get_receipt_file(id)
    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=file_name,
    )


from backend.app.services.receipt_service import (
    get_receipt_details,
    perform_receipt_extraction,
)


@router.post("/{id}/extract", response_model=ApiResponse[dict])
async def extract_receipt(id: str):
    """Extract structured data from receipt using Gemini API."""
    data = await perform_receipt_extraction(id)
    return ApiResponse.ok(data)


@router.get("/{id}", response_model=ApiResponse[dict])
async def get_receipt(id: str):
    """Retrieve receipt details and line items."""
    data = get_receipt_details(id)
    return ApiResponse.ok(data)


from typing import Optional
from backend.app.services.receipt_service import list_receipts


@router.get("", response_model=ApiResponse[list])
async def list_all_receipts(
    q: Optional[str] = None,
    from_: Optional[str] = None,
    to: Optional[str] = None,
    category: Optional[str] = None,
    vendor: Optional[str] = None,
    status: Optional[str] = None,
):
    """List and filter receipts for ledger and dashboard views."""
    data = list_receipts(
        q=q,
        from_date=from_,
        to_date=to,
        category=category,
        vendor=vendor,
        status_filter=status,
    )
    return ApiResponse.ok(data)


