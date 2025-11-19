from langchain_core.messages import HumanMessage, AIMessage
from app.agents.graph_builder import agent_graph
from app.db import db_models
from app.db.database import SessionLocal

from typing import Optional

def save_chat_message(user_id: int, content: str, sender_type: str, attachement: Optional[str] = None):
    """Esta funcion guarda el chat history a la base de datos.

    Args:
        user_id (int): El ID del usuario
        content (str): El mensaje o texto del usuario o ia
        sender_type (str): El tipo de remitente user o ai
        attachement (str): La imagen en base64
    """
    db = SessionLocal()
    try:
        db_message = db_models.ChatMessage(
            user_id=user_id,
            content=content,
            sender_type=sender_type,
            attachement=attachement
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
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
                history.append(HumanMessage(content=msg.content))
            else:
                history.append(AIMessage(content=msg.content))
        return history
    finally:
        db.close()
        
def load_chat_history_api(user_id: int):
    """
    Carga el historial de chat para la API. 
    Si no hay mensajes, inserta el mensaje de bienvenida y lo devuelve.
    """
    db = SessionLocal()
    try:
        message_count = db.query(db_models.ChatMessage)\
            .filter(db_models.ChatMessage.user_id == user_id).count()
        
        if message_count == 0:
            welcome_message = { 
                "content": "¡Hola! Soy tu asistente Agrosmi. ¿En qué puedo ayudarte hoy?", 
                "sender_type": "ai"
            }
            
            db_welcome_message = db_models.ChatMessage(
                user_id=user_id,
                content=welcome_message["content"],
                sender_type=welcome_message["sender_type"],
            )
            db.add(db_welcome_message)
            db.commit()
            db.refresh(db_welcome_message)
            
            db_messages = [db_welcome_message]
        else:
            db_messages = db.query(db_models.ChatMessage)\
                .filter(db_models.ChatMessage.user_id == user_id)\
                    .order_by(db_models.ChatMessage.timestamp.desc())\
                        .limit(10).all()
            db_messages.reverse()
        
        history = []
        for msg in db_messages:
            is_me = msg.sender_type == 'user'
            history.append({
                "id": msg.id, 
                "content": msg.content, 
                "sender": msg.sender_type, 
                "isMe": is_me,
                "attachement": msg.attachement
            })
        return history
    finally:
        db.close()
        
async def run_agent_graph(user_id: dict, user_query: str, image_base64: Optional[str] = None) -> str:
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
            "messages": chat_history + [HumanMessage(content=user_query)],
            "user_info": {"id":user_id,"username":""},
            "image_base64": image_base64,
            "reasoning": None,
            "info_next_agent": None,
            "agent_history": [],
        }
        
        final_state = await  agent_graph.ainvoke(initial_state)
        final_response_message = next((msg for msg in reversed(final_state["messages"]) if isinstance(msg, AIMessage)), None)
        final_response = final_response_message.content if final_response_message else "No se pudo generar una respuesta."
        
        save_chat_message(user_id, user_query, 'user', image_base64)
        save_chat_message(user_id, final_response, 'ai', None)
        
        return load_chat_history_api(user_id=user_id)
        
    except Exception as e:
        print(f"Error al ejecutar el grafo de agentes: {e}")
        return "Lo siento, he tenido un problema para procesar tu solicitud a través del sistema de agentes."