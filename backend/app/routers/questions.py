from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.models import ApiResponse
from backend.app.services.question_service import execute_question_answer

router = APIRouter(prefix="/api/questions", tags=["Questions"])


class AskQuestionPayload(BaseModel):
    question: str
    lang: str = "en"


@router.post("/ask", response_model=ApiResponse[dict])
async def ask_question(payload: AskQuestionPayload):
    """Answer owner questions safely using fixed backend queries, application math, and supporting evidence."""
    data = execute_question_answer(payload.question, payload.lang)
    return ApiResponse.ok(data)
