from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ... import schemas, models
from ...database import get_db
from ...auth import get_current_active_user
from ...core.chat_service import ChatService
from ...core.analysis_service import AnalysisService

router = APIRouter()

# This is a simple way to get a pre-initialized llm_service instance.
analysis_service = AnalysisService()
llm_service = analysis_service.analyzer.llm_service

@router.post("/", response_model=schemas.ChatResponse)
def chat_with_ai(
    chat_request: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Handles a conversational chat request with the AI.
    """
    if not llm_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI model is not available. Please try again later."
        )

    try:
        # The client sends the full history, so we create a new chat service for each turn.
        # The initial "system" message in the history provides the context.
        chat_service = ChatService(llm_service=llm_service, initial_context="")
        chat_service.history = [message.dict() for message in chat_request.history]

        # The last message in the history is the new user message
        user_message = chat_service.history[-1]['content']

        ai_response = chat_service.get_response(user_message)

        return schemas.ChatResponse(response=ai_response)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during the chat session: {e}"
        )
