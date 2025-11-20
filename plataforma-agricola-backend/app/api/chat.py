from fastapi import APIRouter, Depends
from app.models.chat import ChatRequest, MessageResponse
from app.services.chat_service import run_agent_graph, load_chat_history_api
from app.auth import get_current_user
from typing import List
from app.db import db_models

router = APIRouter()

@router.post("/", response_model=List[MessageResponse])
async def handle_chat(request: ChatRequest, current_user: db_models.User = Depends(get_current_user)):
    """
    Recibe un mensaje y devuelve el historial completo (Lista).
    """
    chat_history_updated = await run_agent_graph(
        user_info={
            "id": current_user.id, 
            "username": current_user.full_name, 
            "parcels": [p.name for p in current_user.parcels],
            "email": current_user.email
        }, 
        user_query=request.message,
        image_base64=request.image_base64,
    )
    
    return chat_history_updated

@router.get("/history", response_model=List[MessageResponse])
def handle_chat_history(current_user: db_models.User = Depends(get_current_user)):
    """
    Carga el historial de chat para el usuario autenticado.
    """
    return load_chat_history_api(current_user.id)