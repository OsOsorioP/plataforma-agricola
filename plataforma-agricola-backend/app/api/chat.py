from fastapi import APIRouter
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import get_ai_response

router = APIRouter()

@router.post("/", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    """
    Recibe un mensaje del usuario y devuelve una respuesta generada por la IA.
    """
    ai_reply = get_ai_response(request.message)
    return ChatResponse(reply=ai_reply)