from langchain_core.messages import HumanMessage, AIMessage
from app.graph.graph_builder import agent_graph
from app.db import db_models
from app.db.database import SessionLocal
from typing import Optional, List, Dict, Any

def save_chat_message(user_id: int, content: str, sender_type: str, attachement: Optional[str] = None):
    """Guarda un mensaje en la base de datos."""
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
    """Carga el historial para el contexto de LangChain (objetos Message)."""
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
    Carga el historial formateado para la API (Lista de diccionarios).
    """
    db = SessionLocal()
    try:
        message_count = db.query(db_models.ChatMessage)\
            .filter(db_models.ChatMessage.user_id == user_id).count()
        
        if message_count == 0:
            # Mensaje de bienvenida por defecto si es nuevo usuario
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
                        .limit(20).all() # Traemos los últimos 20 para el frontend
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
        
async def run_agent_graph(user_info: Dict[str, Any], user_query: str, image_base64: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Ejecuta el grafo de agentes.
    
    Args:
        user_info (dict): Diccionario con datos del usuario (id, username, parcels, etc.)
        user_query (str): La pregunta del usuario.
        image_base64 (str): Imagen opcional.
        
    Returns:
        list: Historial de chat actualizado (formato API).
    """
    try:
        # Extraemos el ID del diccionario
        user_id = user_info.get("id")
        
        # 1. Cargar historial previo
        chat_history = load_chat_history(user_id=user_id)
        
        # 2. Preparar estado inicial
        initial_state = {
            "messages": chat_history + [HumanMessage(content=user_query)],
            "user_id": user_id,
            "image_base64": image_base64,
            "reasoning": None,
            "info_next_agent": None,
            "agent_history": [],
        }
        
        # 3. Ejecutar el grafo
        final_state = await agent_graph.ainvoke(initial_state)
        
        # 4. Obtener la respuesta final de la IA
        final_response_message = next((msg for msg in reversed(final_state["messages"]) if isinstance(msg, AIMessage)), None)
        final_response = final_response_message.content if final_response_message else "No se pudo generar una respuesta."
        
        # 5. Guardar mensajes en DB
        save_chat_message(user_id, user_query, 'user', image_base64)
        save_chat_message(user_id, final_response, 'ai', None)
        
        # 6. Devolver historial actualizado para el frontend
        return load_chat_history_api(user_id=user_id)
        
    except Exception as e:
        print(f"Error al ejecutar el grafo de agentes: {e}")
        import traceback
        traceback.print_exc() # Esto nos ayudará a ver dónde falló exactamente dentro del try
        
        # --- CORRECCIÓN AQUÍ ---
        # Usamos user_info que viene como argumento de la función, no una variable local indefinida.
        # Y usamos .get() por seguridad.
        safe_user_id = user_info.get("id") if user_info else None
        
        if safe_user_id:
            return load_chat_history_api(user_id=safe_user_id)
        else:
            # Si no tenemos ID de usuario, devolvemos lista vacía para no romper nada
            return []