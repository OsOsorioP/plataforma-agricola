from fastapi import APIRouter
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import run_agent_graph

router = APIRouter()

@router.post("/", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    """
    Recibe un mensaje del usuario y devuelve una respuesta generada por la IA.
    """
    ai_reply = run_agent_graph(request.message)
    return ChatResponse(reply=ai_reply)