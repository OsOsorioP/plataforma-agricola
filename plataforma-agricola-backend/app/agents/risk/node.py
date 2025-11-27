from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import AIMessage

from app.core.llm import llm_risk
from app.graph.state import GraphState
from app.agents.common.tools import (
    get_parcel_details,
    list_user_parcels,
    lookup_parcel_by_name
)
from app.agents.water.tools import get_precipitation_data, get_weather_forecast
from app.agents.risk.tools import get_historical_weather_summary
from app.prompts.loader import load_prompt

risk_tools = [
    get_weather_forecast,
    get_historical_weather_summary,
    get_precipitation_data,
    get_parcel_details,
    lookup_parcel_by_name,
    list_user_parcels,
]


async def risk_agent_node(state: GraphState) -> dict:
    """Agente de Análisis de Riesgos mejorado."""
    print("-- Node ejecutándose: risk_agent --")

    user_id = state.get("user_id", "N/A")
    info_next_agent = state.get("info_next_agent", "Sin información")
    
    prompt_template = ChatPromptTemplate.from_messages([(
        "system",
        load_prompt("risk", "system.md")
    ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    prompt = prompt_template.partial(
        user_id=user_id,
        info_next_agent=info_next_agent,
    )

    agent = create_tool_calling_agent(llm_risk, risk_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=risk_tools,
        verbose=True,
        max_iterations=6,
        handle_parsing_errors=True
    )

    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})

        print(f"-- Respuesta risk: {response["output"][0]["text"]}... --\n")

        return {
            "messages": [AIMessage(content=response["output"][0]["text"], name="risk")],
            "list_agent": state.get("list_agent", []) + ["risk"]
        }
    except Exception as e:
        print(f"-- ERROR risk: {e} --")
        return {
            "messages": [AIMessage(
                content="Error al analizar riesgos. Por favor, especifica la parcela y el tipo de riesgo.",
                name="risk"
            )],
            "list_agent": state.get("list_agent", []) + ["risk"]
        }
