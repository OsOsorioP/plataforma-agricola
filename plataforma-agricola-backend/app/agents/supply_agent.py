from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState
from app.agents.agent_tools import (
    knowledge_base_tool,
    get_market_price,
)

supply_tools = [knowledge_base_tool, get_market_price]


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", temperature=0, google_api_key=GOOGLE_API_KEY)


async def supply_chain_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Optimización de la Cadena de Suministro."""
    print("-- Node ejecutandose: Supply --")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """Eres un experto en logística y comercialización agrícola. }
            
            Tienes dos herramientas principales:
            1. `knowledge_base_search`: Úsala para responder preguntas sobre regulaciones, estándares de calidad, empaquetado y logística.
            2. `get_market_price`: Úsala para obtener el precio de mercado actual de un producto.

            Instrucciones: 
            1. Analiza la pregunta del usuario y utiliza la herramienta más apropiada para responder.
            2. Si la pregunta es sobre calidad o regulaciones, usa la base de conocimiento.
            3. Si la pregunta es sobre precios, usa la herramienta de precios de mercado.
            4. Responde siempre en español.
        """
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, supply_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, tools=supply_tools, verbose=True)

    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})
        return {
            "messages": [AIMessage(content=response["output"], name="supply_chain_agent")],
            "agent_history": state.get("agent_history", []) + ["supply_chain_agent"]
        }
    except Exception as e:
        print(f"ERROR en el agente supply_chain_agent: {e}")
        error_message = f"Ocurrió un error al procesar tu solicitud: {str(e)}"
        return {"messages": [AIMessage(content=error_message, name="supply_chain_agent")]}
