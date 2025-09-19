from fastapi import APIRouter, Depends, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import run_agent_graph
from app.auth import get_current_user
from app import db_models

router = APIRouter()

@router.post("/", response_model=ChatResponse)
def handle_chat(request: ChatRequest, current_user: db_models.User = Depends(get_current_user)):
    """
    Recibe un mensaje del usuario y devuelve una respuesta generada por la IA.
    """
    ai_reply = run_agent_graph(current_user.id, request.message)
    return ChatResponse(reply=ai_reply)