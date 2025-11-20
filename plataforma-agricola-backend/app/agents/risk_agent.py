from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState
from app.agents.agent_tools import knowledge_base_tool, get_historical_weather_summary

risk_tools = [knowledge_base_tool, get_historical_weather_summary]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", temperature=0, google_api_key=GOOGLE_API_KEY)

async def risk_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Predicción y Mitigación de Riesgos."""
    print("-- Node ejecutandose: risk --")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """Eres un analista de riesgos agrícolas y estratega. 
            
            Tarea: Identificar riesgos y proponer planes de mitigación.

            Instrucciones:
            1. Identificar y Cuantificar el Riesgo: Usa la herramienta `get_historical_weather_summary` para analizar los datos climáticos históricos de la ubicación del usuario y confirmar la existencia y frecuencia de un riesgo (como heladas o sequías).
            2. Proponer Solución: Una vez confirmado el riesgo, usa la herramienta `knowledge_base_search` para encontrar el plan de contingencia o las acciones de mitigación recomendadas en el manual.
            3. Combina la información de ambos pasos para dar una respuesta completa y bien fundamentada.
            4. Responde siempre en español.
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, risk_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=risk_tools, verbose=True)

    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})
        return {
            "messages": [AIMessage(content=response["output"], name="risk_agent")],
            "agent_history": state.get("agent_history", []) + ["risk_agent"]
        }
    except Exception as e:
        print(f"ERROR en el agente RISK: {e}")
        error_message = f"Ocurrió un error al procesar tu solicitud: {str(e)}"
        return {"messages": [AIMessage(content=error_message, name="risk_agent")]}
