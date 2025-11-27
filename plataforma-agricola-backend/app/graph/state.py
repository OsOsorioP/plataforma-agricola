from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class GraphState(TypedDict):
    """
    Representa el estado de nuestro grafo de agentes.

    Atributos:
        messages: La lista de mensajes que componen la conversación.
                  LangGraph se encargará de añadir nuevos mensajes a esta lista.
        chat_history: Lista de mensajes en el historial de chat.
        user_id: El ID del usuario que inició la conversación.
        image_base64: La imagen opcional enviada por el usuario.
        reasoning: Razonamiento del supervisor
        info_next_agent: Información para el siguiente agente.
        list_agent: Historial de los agentes usados por el supervisor.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    chat_history: List[BaseMessage]
    user_id: int
    image_base64: Optional[str]
    reasoning: Optional[str]
    info_next_agent: Optional[str]
    list_agent: List[str]
    total_start_time: float
    time_breakdown: dict