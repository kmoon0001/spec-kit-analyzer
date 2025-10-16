from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from requests.exceptions import HTTPError

from ...auth import get_current_active_user
from ...core.chat_service import ChatService
from ...database import models, schemas
from ..dependencies import get_analysis_service

router = APIRouter()


@router.post("/", response_model=schemas.ChatResponse)
async def chat_with_ai(
    chat_request: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_active_user),
    analysis_service: Any = Depends(get_analysis_service),  # Changed to Any
):
    """Handles a conversational chat request with the AI."""
    chat_llm = getattr(analysis_service, "chat_llm_service", None) or analysis_service.llm_service
    if not chat_llm.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The chat model is not available. Please try again later.",
        )

    chat_service = ChatService(llm_service=chat_llm)

    try:
        history_payload = [message.model_dump() for message in chat_request.history]
        response_text = chat_service.process_message(history_payload)
        return schemas.ChatResponse(response=response_text)
    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred during the chat session: {e}"
        ) from e
