from fastapi import APIRouter, Depends, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import run_agent_graph
from app.auth import get_current_user
from app.db import db_models

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def handle_chat(request: ChatRequest, current_user: db_models.User = Depends(get_current_user)):
    """
    Recibe un mensaje del usuario y devuelve una respuesta generada por la IA.
    """
    ai_reply = await run_agent_graph(
        user_id=current_user.id, 
        user_query=request.message,
        image_base64=request.image_base64)
    return ChatResponse(reply=ai_reply)