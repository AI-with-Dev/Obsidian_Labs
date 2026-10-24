from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse, Response

from backend.app.routers.auth import require_authenticated_owner
from backend.app.models import ApiResponse
from backend.app.services.receipt_service import (
    delete_receipt,
    get_receipt_file,
    process_and_save_upload,
)

router = APIRouter(
    prefix="/api/receipts",
    tags=["Receipts"],
    dependencies=[Depends(require_authenticated_owner)],
)


@router.post("/upload", response_model=ApiResponse[dict])
async def upload_receipt(
    file: UploadFile = File(...),
    owner: dict = Depends(require_authenticated_owner),
):
    """Upload a receipt image (JPG, PNG) or PDF document."""
    receipt_id = await process_and_save_upload(file, owner["id"])
    return ApiResponse.ok({"id": receipt_id})


@router.get("/{id}/file")
@router.head("/{id}/file")
async def stream_receipt_file(
    id: str,
    owner: dict = Depends(require_authenticated_owner),
):
    """Retrieve and stream the stored receipt image or PDF file."""
    file_path, mime_type, file_name = get_receipt_file(id, owner["id"])
    if isinstance(file_path, bytes):
        return Response(
            content=file_path,
            media_type=mime_type,
            headers={"Content-Disposition": f'inline; filename="{file_name}"'},
        )
    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=file_name,
        content_disposition_type="inline",
    )


from backend.app.services.receipt_service import (
    get_receipt_details,
    perform_receipt_extraction,
)


@router.post("/{id}/extract", response_model=ApiResponse[dict])
async def extract_receipt(id: str, owner: dict = Depends(require_authenticated_owner)):
    """Extract structured data from receipt using Gemini API."""
    data = await perform_receipt_extraction(id, owner.get("businessName", ""), owner["id"])
    return ApiResponse.ok(data)


@router.get("/{id}", response_model=ApiResponse[dict])
async def get_receipt(
    id: str,
    owner: dict = Depends(require_authenticated_owner),
):
    """Retrieve receipt details and line items."""
    data = get_receipt_details(id, owner["id"])
    return ApiResponse.ok(data)


@router.delete("/{id}", response_model=ApiResponse[None])
async def delete_receipt_endpoint(
    id: str,
    owner: dict = Depends(require_authenticated_owner),
):
    """Permanently delete a receipt and its uploaded file."""
    delete_receipt(id, owner["id"])
    return ApiResponse.ok(None)


from typing import Optional
from backend.app.services.receipt_service import list_receipts


@router.get("", response_model=ApiResponse[list])
async def list_all_receipts(
    owner: dict = Depends(require_authenticated_owner),
    q: Optional[str] = None,
    from_: Optional[str] = None,
    to: Optional[str] = None,
    category: Optional[str] = None,
    vendor: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
):
    """List and filter receipts for ledger and dashboard views."""
    data = list_receipts(
        owner_id=owner["id"],
        q=q,
        from_date=from_,
        to_date=to,
        category=category,
        vendor=vendor,
        status_filter=status,
        transaction_type=type,
    )
    return ApiResponse.ok(data)

from backend.app.models import ReceiptUpdatePayload
from backend.app.services.receipt_service import (
    confirm_receipt,
    discard_duplicate,
    keep_separate,
    save_receipt_draft,
)


@router.patch("/{id}", response_model=ApiResponse[dict])
async def update_receipt(
    id: str,
    payload: ReceiptUpdatePayload,
    owner: dict = Depends(require_authenticated_owner),
):
    """Save owner corrections and draft edits for a receipt."""
    data = save_receipt_draft(id, payload, owner["id"])
    return ApiResponse.ok(data)


@router.post("/{id}/confirm", response_model=ApiResponse[dict])
async def confirm_receipt_endpoint(
    id: str,
    owner: dict = Depends(require_authenticated_owner),
):
    """Explicitly confirm and finalize receipt into the trusted ledger."""
    data = confirm_receipt(id, owner["id"])
    return ApiResponse.ok(data)


@router.post("/{id}/discard-duplicate", response_model=ApiResponse[None])
async def discard_duplicate_endpoint(
    id: str,
    owner: dict = Depends(require_authenticated_owner),
):
    """Discard a duplicate upload."""
    discard_duplicate(id, owner["id"])
    return ApiResponse.ok(None)


@router.post("/{id}/keep-separate", response_model=ApiResponse[dict])
async def keep_separate_endpoint(
    id: str,
    owner: dict = Depends(require_authenticated_owner),
):
    """Keep receipt as a separate expense."""
    data = keep_separate(id, owner["id"])
    return ApiResponse.ok(data)


from backend.app.models import VoiceQuickEntryPayload
from backend.app.services.receipt_service import create_voice_quick_entry


@router.post("/voice-quick-entry", response_model=ApiResponse[dict])
def voice_quick_entry_endpoint(
    payload: VoiceQuickEntryPayload,
    owner: dict = Depends(require_authenticated_owner),
):
    """Log an income/added money entry directly from voice dictation into the ledger and data column."""
    data = create_voice_quick_entry(payload, owner["id"])
    return ApiResponse.ok(data)
