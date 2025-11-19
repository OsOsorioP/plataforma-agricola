from fastapi import APIRouter, Depends, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import run_agent_graph, load_chat_history_api
from app.auth import get_current_user
from app.db import db_models

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def handle_chat(request: ChatRequest, current_user: db_models.User = Depends(get_current_user)):
    """
    Recibe un mensaje del usuario y devuelve una respuesta generada por la IA.
    """
    chat_history_updated = await run_agent_graph(
        user_info={
            "id":current_user.id, 
            "username":current_user.full_name, 
            "parcels":current_user.parcels,
            "email":current_user.email
        }, 
        user_query=request.message,
        image_base64=request.image_base64,
    )
    
    return chat_history_updated

@router.get("/history")
def handle_chat_history(current_user: db_models.User = Depends(get_current_user)):
    """
    Carga el historial de chat para el usuario autenticado.
    """
    return load_chat_history_api(current_user.id)