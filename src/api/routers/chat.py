from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from ...database import schemas, models
from ...auth import get_current_active_user
from ...core.chat_service import ChatService
# from ...core.analysis_service import AnalysisService # Removed to break import cycle
from ..dependencies import get_analysis_service

router = APIRouter()


@router.post("/", response_model=schemas.ChatResponse)
async def chat_with_ai(
    chat_request: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_active_user),
    analysis_service: Any = Depends(get_analysis_service), # Changed to Any
):
    """Handles a conversational chat request with the AI."""
    chat_llm = getattr(analysis_service, "chat_llm_service", None) or analysis_service.llm_service
    if not chat_llm.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The chat model is not available. Please try again later.",
        )

    chat_service = ChatService(chat_llm)

    try:
        response_text = chat_service.process_message(chat_request.history)
        return schemas.ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during the chat session: {e}",
        )