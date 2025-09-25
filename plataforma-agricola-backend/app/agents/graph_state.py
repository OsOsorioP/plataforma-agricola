from typing import TypedDict, Optional, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class GraphState(TypedDict):
    """
    Representa el estado de nuestro grafo de agentes.
    
    Atributos:
        user_query: La pregunta original del usurio.
        agent_response: La respuesta generada por el agente.
        # Aquí se van añadir más campos a futuro.
        # parcel_id: ID de la parcelas para el contexto
        # diagnosis: Diagnóstico de una enfermedad.
        # recommendations: Lista de recomendaciones.
    """
    user_id: int
    user_query: str
    chat_history: List[BaseMessage]
    recommendation_draft: str
    agent_response: str
    image_base64: Optional[str]