from langgraph.graph import StateGraph, END
from app.agents.graph_state import GraphState
from app.agents.agent_nodes import monitoring_agent_node, sustainability_agent_node

workflow = StateGraph(GraphState)

workflow.add_node("monitoring_agent", monitoring_agent_node)
workflow.add_node("sustainability_agent", sustainability_agent_node)

workflow.set_entry_point("monitoring_agent")

workflow.add_edge("monitoring_agent", "sustainability_agent")

workflow.add_edge("sustainability_agent", END)

agent_graph = workflow.compile()