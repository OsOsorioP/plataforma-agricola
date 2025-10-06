from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from app.core.config import GOOGLE_API_KEY
from app.agents.graph_builder import agent_graph
from app.db import db_models
from app.db.database import SessionLocal

from typing import Optional

from sqlalchemy.orm import Session

def save_chat_message(user_id: int, message_text: str, sender_type: str):
    """Esta funcion guarda el chat history a la base de datos.

    Args:
        user_id (int): El ID del usuario
        message_text (str): El mensaje o texto del usuario o ia
        sender_type (str): El tipo de remitente user o ai
    """
    db = SessionLocal()
    try:
        db_message = db_models.ChatMessage(
            user_id=user_id,
            message=message_text,
            sender_type=sender_type
        )
        db.add(db_message)
        db.commit()
    finally:
        db.close()

def load_chat_history(user_id: int):
    """Esta funcion carga el chat history de la base de datos, luego lo transforma de mensaje humano o de ia para el modelo.

    Args:
        user_id (int): El ID del usuario

    Returns:
        history (list): el historial con los mensajes tranformados para transmitirlos al modelo
    """
    db = SessionLocal()
    try:
        db_messages = db.query(db_models.ChatMessage)\
            .filter(db_models.ChatMessage.user_id == user_id)\
                .order_by(db_models.ChatMessage.timestamp.desc())\
                    .limit(10).all()
        db_messages.reverse()
        
        history = []
        for msg in db_messages:
            if msg.sender_type == 'user':
                history.append(HumanMessage(content=msg.message))
            else:
                history.append(AIMessage(content=msg.message))
        return history
    finally:
        db.close()
        
async def run_agent_graph(user_id: int, user_query: str, image_base64: Optional[str] = None) -> str:
    """
    Ejecuta el grafo de agentes con la consulta del usuario.
    
    Args:
        user_id (int): El ID del usuario
        user_query (str): La pregunta o mensaje del usuario
        
    Returns:
        final_state (dict[str, Any]): respuesta del agente
    """
    try:
        chat_history = load_chat_history(user_id=user_id)
        
        initial_state = {
            "user_id": user_id,
            "user_query": user_query,
            "chat_history": chat_history,
            "recommendation_draft": "",
            "agent_response": "",
            "image_base64": image_base64,
        }
        
        final_state = await  agent_graph.ainvoke(initial_state)
        final_response = final_state.get("agent_response", "No se pudo obtener una respuesta.")
        
        save_chat_message(user_id, user_query, 'user')
        save_chat_message(user_id, final_response, 'ai')
        
        return final_response
        
    except Exception as e:
        print(f"Error al ejecutar el grafo de agentes: {e}")
        return "Lo siento, he tenido un problema para procesar tu solicitud a través del sistema de agentes."

async def get_ai_response(user_query: str) -> str:
    """
    Función simple para obtener una respuesta de Gemini a una consulta.
    
    Args:
        user_query (str): La pregunta o mensaje del usuario
        
    Returns:
        content (str | list[str | dict]): respuesta de la ia
    """
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=GOOGLE_API_KEY)
        
        response = await llm.invoke(user_query)
        
        return response.content
        
    except Exception as e:
        print(f"Error al interactuar con la API de Gemini: {e}")
        return "Lo siento, he tenido un problema para procesar tu solicitud."