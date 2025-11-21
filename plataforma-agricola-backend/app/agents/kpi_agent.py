from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState
from app.agents.agent_tools import (get_kpi_summary,
                                    get_parcel_health_indices,
                                    get_parcel_details,
                                    list_user_parcels
                                    )

kpi_tools = [
    get_kpi_summary,
    get_parcel_health_indices,
    get_parcel_details,
    list_user_parcels,
]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", temperature=0, google_api_key=GOOGLE_API_KEY)


async def kpi_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Análisis de KPIs."""
    print("-- Node ejecutandose: KPI --")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """Eres un analista de datos especializado en agricultura de precisión.
            
            Tarea: Analizar y reportar la evolución de los KPIs de una parcela.

            Instrucciones:
            1.  Usa la herramienta `get_kpi_summary` para obtener los datos históricos de un KPI específico para una parcela.
            2.  Necesitarás el `parcel_id` y el `kpi_name` (ej. 'SOIL_HEALTH_NDVI'). Si no los tienes, pídelos al usuario.
            3.  Presenta el resumen de forma clara y concisa, explicando la evolución y el estado actual al agricultor.
            4.  Responde siempre en español.
        """
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, kpi_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, tools=kpi_tools, verbose=True)

    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})
        return {
            "messages": [AIMessage(content=response["output"], name="kpi_agent")],
            "agent_history": state.get("agent_history", []) + ["kpi_agent"]
        }
    except Exception as e:
        print(f"ERROR en el agente KPI: {e}")
        error_message = f"Ocurrió un error al procesar tu solicitud: {str(e)}"
        return {"messages": [AIMessage(content=error_message, name="kpi_agent")]}
