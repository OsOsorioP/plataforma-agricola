from typing import TypedDict, Optional, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class GraphState(TypedDict):
    """
    Representa el estado de nuestro grafo de agentes.
    
    Atributos:
        user_id: ID del usuario actual.
        user_query: La consulta de texto del usuario.
        image_base64: La ruta local de la imagen enviada por el usuario (NUEVO).
        chat_history: Lista de mensajes en el historial de chat.
        next_agent: El agente especializado elegido por el supervisor
        recommendation_draft: Borrador de la recomendación del agente.
        agent_response: La respuesta final del agente.
        # Aquí se van añadir más campos a futuro.
        # parcel_id: ID de la parcelas para el contexto
        diagnosis: Diagnóstico de una enfermedad.
        # recommendations: Lista de recomendaciones.
        treatment_plan: Plan del agente de producción
    """
    user_id: int
    user_query: str
    chat_history: List[BaseMessage]
    next_agent: str
    recommendation_draft: str
    agent_response: str
    image_base64: Optional[str]
    diagnosis: Optional[str]
    treatment_plan: Optional[str]
    