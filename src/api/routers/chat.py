from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ... import schemas, models
from ...database import get_db
from ...auth import get_current_active_user
from ...core.chat_service import ChatService
from ...core.analysis_service import AnalysisService
from ..dependencies import get_analysis_service

router = APIRouter()

@router.post("/", response_model=schemas.ChatResponse)
def chat_with_ai(
    chat_request: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """
    Handles a conversational chat request with the AI.
    """
    llm_service = analysis_service.analyzer.llm_service
    if not llm_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI model is not available. Please try again later.",
        )

    chat_service = ChatService(db=db, user=current_user, llm_service=llm_service)

    response_text = chat_service.process_message(chat_request.message, chat_request.history)

    return schemas.ChatResponse(response=response_text)