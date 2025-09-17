from langgraph.graph import StateGraph, END
from app.agents.graph_state import GraphState
from app.agents.agent_nodes import monitoring_agent_node

workflow = StateGraph(GraphState)

workflow.add_node("monitoring_agent", monitoring_agent_node)

workflow.add_edge("monitoring_agent", END)

workflow.set_entry_point("monitoring_agent")

agent_graph = workflow.compile()