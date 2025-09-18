from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

from app.core.config import GOOGLE_API_KEY
from app.agents.graph_state import GraphState
from app.agents.agent_tools import get_parcel_details, list_user_parcels

tools = [get_parcel_details, list_user_parcels]

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=GOOGLE_API_KEY)

def monitoring_agent_node(state: GraphState) -> dict:
    """
    Nodo del Agente de Monitoreo, ahora potenciado con herramientas.
    
    Args:
        state: El estado actual del grafo.
        
    Returns:
        Un diccionario con las actualizaciones para el estado.
    """
    user_query = state["user_query"]
    
    prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """Eres un asistente experto en agricultura para la plataforma AgriAgent. Tu objetivo es ayudar a los agricultores.

        Tu proceso de decisión debe ser el siguiente:
        1.  Analiza la pregunta del usuario.
        2.  Si la pregunta es de conocimiento general sobre agricultura (como '¿cuál es la mejor época para plantar X?', '¿qué es el mildiu?', 'recomiéndame fertilizantes orgánicos'), responde directamente usando tu vasto conocimiento.
        3.  Si la pregunta es específicamente sobre datos guardados en el sistema (como 'dame los detalles de mi parcela', 'lista mis campos', '¿qué datos tienes de la parcela con ID 2?'), DEBES usar las herramientas que tienes disponibles para obtener la información más actualizada y precisa.
        4.  Responde siempre en español.
        """
    ),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    response = agent_executor.invoke({
        "input": user_query
    })
    
    return {"agent_response": response["output"]}