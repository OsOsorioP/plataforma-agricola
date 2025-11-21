import os
from langgraph.graph import StateGraph, END

from app.graph.graph_state import GraphState

from app.agents import (supervisor_agent, supply_agent, sustainability_agent,
                        production_agent, water_agent, vision_agent, risk_agent)

workflow = StateGraph(GraphState)

# Añadir los nodos al grafo
workflow.add_node("supervisor_agent", supervisor_agent.supervisor_agent_node)
workflow.add_node("production_agent", production_agent.production_agent_node)
workflow.add_node("water_agent", water_agent.water_agent_node)
workflow.add_node("supply_chain_agent", supply_agent.supply_chain_agent_node)
workflow.add_node("risk_agent", risk_agent.risk_agent_node)
workflow.add_node("vision_agent", vision_agent.vision_agent_node)
workflow.add_node("sustainability_agent",
                  sustainability_agent.sustainability_agent_node)

# Punto de entrada
workflow.set_entry_point("supervisor_agent")

# Aristas condicionales
workflow.add_conditional_edges(
    "supervisor_agent",
    lambda state: state["next"],
    {
        "production": "production_agent",
        "water": "water_agent",
        "supply_chain": "supply_chain_agent",
        "risk": "risk_agent",
        "sustainability": "sustainability_agent",
        "vision": "vision_agent",
        "FINISH": END
    }
)

# Nodos especializados para terminar el flujo de trabajo
workflow.add_edge("production_agent", "supervisor_agent")
workflow.add_edge("risk_agent", "supervisor_agent")
workflow.add_edge("supply_chain_agent", "supervisor_agent")
workflow.add_edge("sustainability_agent", "supervisor_agent")
workflow.add_edge("vision_agent", "supervisor_agent")
workflow.add_edge("water_agent", "supervisor_agent")

# Se compila el grafo
agent_graph = workflow.compile()


def workflow_img():
    graph_image_bytes = agent_graph.get_graph().draw_mermaid_png()
    image_path = os.path.join(os.path.dirname(
        "app/assets/img/"), "workflow_graph.png")
    with open(image_path, "wb") as f:
        f.write(graph_image_bytes)
