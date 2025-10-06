from pydantic.v1 import BaseModel, Field
from app.agents.graph_state import GraphState

class RouteQuery(BaseModel):
    """Enruta una consulta de usuario a un agente especialista."""
    destination: str = Field(
        description="El nombre del agente especialista al que se debe enrutar la consulta. Debe ser uno de: ['vision', 'production', 'water', 'supply_chain', 'risk', 'general']"
    )

def router_node(state: GraphState) -> str:
    """
    Enrutador que decide el siguiente paso.
    """
    next_agent = state.get("next_agent", "FINISH")
    print(f"-- Agente enrutando: {next_agent} --")
    valid_agents = [
        "production", "water", "supply_chain", "risk", "sustainability",
        "vision", "general", "end"
    ]
    
    if next_agent in valid_agents:
        print(f"-- Node enrutador: Decisión ir a {next_agent} --")
        return next_agent
    else:
        return "end"