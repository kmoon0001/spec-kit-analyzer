from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import schemas, models, get_db
from src.core.chat_service import ChatService, ChatHistory
from src.api.routers.auth import get_current_active_user

router = APIRouter()

# In-memory storage for chat histories.
# In a real-world application, this would be a database or a more persistent store.
chat_histories = {}

def get_chat_history(session_id: str) -> ChatHistory:
    """
    Retrieves or creates a chat history for a given session ID.
    """
    if session_id not in chat_histories:
        chat_histories[session_id] = ChatHistory()
    return chat_histories[session_id]

@router.post("/chat", response_model=schemas.ChatMessage)
def post_chat_message(
    chat_input: schemas.ChatInput,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Receives a user's message, gets a response from the AI, and returns it.
    """
    session_id = chat_input.session_id
    history = get_chat_history(session_id)

    # Initialize the chat service with the session's history
    chat_service = ChatService(history=history)

    # Get the AI's response
    response_text = chat_service.get_response(chat_input.message)

    return {"session_id": session_id, "message": response_text, "is_user": False}

@router.get("/chat/history/{session_id}", response_model=List[schemas.ChatMessage])
def get_session_history(
    session_id: str,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieves the full chat history for a given session ID.
    """
    history = get_chat_history(session_id)
    return history.get_messages_as_dicts(session_id)