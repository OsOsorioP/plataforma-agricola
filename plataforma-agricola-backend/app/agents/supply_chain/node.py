from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import AIMessage

from app.graph.state import GraphState
from app.agents.common.tools import (
    get_parcel_details,
    list_user_parcels,
)
from app.agents.supply_chain.tools import get_market_price

from app.core.llm import llm_supply_chain
from app.prompts.loader import load_prompt

supply_chain_tools = [
    get_market_price,
    get_parcel_details,
    list_user_parcels,
]

async def supply_chain_agent_node(state: GraphState) -> dict:
    """Agente de Cadena de Suministro mejorado."""
    print("-- Node ejecutándose: supply_chain_agent --")

    user_id = state.get("user_id", "N/A")
    info_next_agent = state.get("info_next_agent", "Sin información")
    
    prompt_template = ChatPromptTemplate.from_messages([(
        "system",
        load_prompt("supply", "system.md")
    ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    prompt = prompt_template.partial(
        user_id=user_id,
        info_next_agent=info_next_agent
    )

    agent = create_tool_calling_agent(llm_supply_chain, supply_chain_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=supply_chain_tools,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )

    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})

        print(f"-- Respuesta supply_chain: {response["output"][0]["text"]}... --\n")

        return {
            "messages": [AIMessage(content=response["output"][0]["text"], name="supply_chain")],
            "agent_history": state.get("agent_history", []) + ["supply_chain"]
        }
    except Exception as e:
        print(f"-- ERROR supply_chain: {e} --")
        return {
            "messages": [AIMessage(
                content="Error al consultar información de mercado. Por favor, especifica el producto.",
                name="supply_chain"
            )],
            "agent_history": state.get("agent_history", []) + ["supply_chain"]
        }