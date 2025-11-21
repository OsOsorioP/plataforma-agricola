from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState
from app.agents.agent_tools import (
    knowledge_base_tool, get_parcel_health_indices, get_parcel_details, list_user_parcels, lookup_parcel_by_name, save_recommendation)

production_tools = [
    knowledge_base_tool,
    get_parcel_details,
    list_user_parcels,
    lookup_parcel_by_name,
    get_parcel_health_indices,
    save_recommendation,
]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", temperature=0, google_api_key=GOOGLE_API_KEY)


async def production_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Optimización de la Producción. Ahora puede recibir un diagnóstico."""
    print("-- Node ejecutandose: Production --")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un agrónomo experto en optimización de la producción y análisis de salud de cultivos.
         
        Tarea: Responder a consultas sobre rendimiento, salud vegetal, diagnóstico de problemas y prácticas de manejo.

        Instrucciones:
        1.  Análisis Geoespacial (Salud del Cultivo): Si la pregunta del usuario es sobre la **salud actual del cultivo, estrés hídrico, o la condición del suelo** en una parcela específica (ej. '¿Cómo está mi parcela 101?'), **DEBES** usar la herramienta `get_parcel_health_indices`. Esta herramienta requiere el `parcel_id`, una `start_date` y una `end_date` (generalmente un rango de 30 días o el último mes). Si faltan las fechas o el ID, pídelos al usuario.
        2.  Base de Conocimiento (Prácticas): Si la pregunta es sobre **prácticas de manejo, fertilizantes, control de plagas o mejora de rendimiento**, usa tu herramienta `knowledge_base_search`.
        3.  Respuesta Consolidada: Combina la información obtenida (NDVI, RAG) para dar una respuesta completa, clara y concisa al agricultor.
        4.  Responde siempre en español.
        
        contexto:"""),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, production_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, tools=production_tools, verbose=True)

    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})
        return {
            "messages": [AIMessage(content=response["output"], name="production_agent")],
            "agent_history": state.get("agent_history", []) + ["production_agent"]
        }
    except Exception as e:
        print(f"ERROR en el agente PRODUCTION: {e}")
        error_message = f"Ocurrió un error al procesar tu solicitud: {str(e)}"
        return {"messages": [AIMessage(content=error_message, name="production_agent")]}
