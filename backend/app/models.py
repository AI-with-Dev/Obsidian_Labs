from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ApiError] = None

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        return cls(success=True, data=data, error=None)

    @classmethod
    def fail(cls, code: str, message: str) -> "ApiResponse[None]":
        return cls(success=False, data=None, error=ApiError(code=code, message=message))


from typing import List


class ItemPayload(BaseModel):
    name: str = ""
    amount: float = 0.0
    quantity: Optional[float] = 1.0
    unitPrice: Optional[float] = None


class ReceiptUpdatePayload(BaseModel):
    vendor: Optional[str] = None
    date: Optional[str] = None
    currency: Optional[str] = "INR"
    items: Optional[List[ItemPayload]] = None
    total: Optional[float] = None
    category: Optional[str] = None
    type: Optional[str] = None
    transactionType: Optional[str] = None
    invoiceNumber: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    discount: Optional[float] = None
    paymentMethod: Optional[str] = None
    notes: Optional[str] = None

