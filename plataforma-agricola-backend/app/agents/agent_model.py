from typing import List, Literal, Optional
from pydantic.v1 import BaseModel, Field

class SupervisorDecision(BaseModel):
    """
    Decisión del supervisor sobre el siguiente paso en la orquestación.
    """
    next_agent: Optional[Literal['production', 'water', 'supply_chain', 'risk', 'general', 'sustainability', 'vision', 'FINISH']] = Field(
        description="El nombre del agente especializado al que se debe enrutar la consulta, o 'FINISH' si la consulta está completa. La respuesta nunca debe ser None"
    )
    reasoning: str = Field(
        description="Razonamiento del supervisor para la decisión tomada."
    )
    info_for_next_agent: Optional[str] = Field(None, description="Información clave extraída para el próximo agente.")
    content: str = Field(description="Salida del analisis a las respuestas recopiladas de todos los agentes, para entregar una respuesta completa y precisa al usuario.")