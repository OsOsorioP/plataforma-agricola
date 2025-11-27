from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.llm import llm_water
from app.prompts.loader import load_prompt
from app.graph.state import GraphState

from app.agents.common.tools import (
    list_user_parcels,
    get_parcel_details,
    lookup_parcel_by_name,
    update_parcel_info
)
from app.agents.water.tools import get_weather_forecast, get_precipitation_data, calculate_water_requirements, estimate_soil_moisture_deficit
from app.agents.production.tools import get_parcel_health_indices

from app.services.metrics.water_calc import _calculation_kpi_ks3
from app.utils.helper import normalize_agent_output

water_tools = [
    list_user_parcels,
    lookup_parcel_by_name,
    get_parcel_details,
    get_weather_forecast,
    get_precipitation_data,
    calculate_water_requirements,
    estimate_soil_moisture_deficit,
    get_parcel_health_indices,
    update_parcel_info,
]


async def water_agent_node(state: GraphState) -> dict:
    """Agente de Gestión Hídrica.

    Args:
        state (GraphState): es el estado del grafo

    Returns:
        dict: devuelve un diccionario para actualizar los estados
    """

    print("-- Node ejecutándose: water_agent --")

    user_id = state.get("user_id", "N/A")
    info_next_agent = state.get("info_next_agent", "Sin información específica")

    prompt_template = ChatPromptTemplate.from_messages([(
        "system",
        load_prompt("water", "system.md")
    ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    prompt = prompt_template.partial(
        user_id=user_id,
        info_next_agent=info_next_agent,
    )

    agent = create_tool_calling_agent(
        llm=llm_water,
        tools=water_tools,
        prompt=prompt
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=water_tools,
        verbose=True,
        max_iterations=8,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )

    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})

        response_content = normalize_agent_output(response["output"])
        intermediate_steps = response.get("intermediate_steps", [])

        _calculation_kpi_ks3(
            intermediate_steps=intermediate_steps,
            user_id=user_id,
            response_content=response_content
        )

        print(f"-- Respuesta water: {response_content}... --\n")

        return {
            "messages": [AIMessage(content=response_content, name="water")],
            "list_agent": state.get("list_agent", []) + ["water"]
        }
    except Exception as e:
        print(f"-- ERROR water: {e} --")
        return {
            "messages": [AIMessage(
                content="Error al analizar gestión hídrica. Por favor, especifica la parcela y el cultivo.",
                name="water"
            )],
            "list_agent": state.get("list_agent", []) + ["water"]
        }
