from langgraph.graph import StateGraph, END, START
from app.agents.graph_state import GraphState
from app.agents.agent_router import router_node, image_pre_router
from app.agents.agent_nodes import (
    general_tool_agent_node,
    production_agent_node,
    water_agent_node,
    supply_chain_agent_node,
    sustainability_agent_node,
    vision_agent_node
)

workflow = StateGraph(GraphState)

# Añadir los nodos al grafo
workflow.add_node("general_agent", general_tool_agent_node)
workflow.add_node("production_agent", production_agent_node)
workflow.add_node("water_agent", water_agent_node)
workflow.add_node("supply_chain_agent", supply_chain_agent_node)
workflow.add_node("vision_agent", vision_agent_node)
workflow.add_node("router", router_node)
# workflow.add_node("sustainability_agent", sustainability_agent_node)

# Aristas condicionales
workflow.add_conditional_edges(
    START,
    image_pre_router,
    {
        "production": "production_agent",
        "water": "water_agent",
        "supply_chain": "supply_chain_agent",
        "general": "general_agent",
        "vision_agent": "vision_agent",
        "router": "router",
        "end": END
    }
)

# Nodos especializados para terminar el flujo de trabajo
workflow.add_edge("general_agent", END)
workflow.add_edge("production_agent", END)
workflow.add_edge("water_agent", END)
workflow.add_edge("supply_chain_agent", END)
workflow.add_edge("vision_agent", END)

# Se compila el grafo
agent_graph = workflow.compile()