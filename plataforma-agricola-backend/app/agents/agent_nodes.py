from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

from app.core.config import GOOGLE_API_KEY
from app.agents.graph_state import GraphState
from app.agents.agent_tools import get_parcel_details, list_user_parcels

tools = [get_parcel_details, list_user_parcels]

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=GOOGLE_API_KEY)

def general_tool_agent_node(state: GraphState) -> dict:
    """
    Nodo del Agente de Monitoreo, ahora potenciado con herramientas.
    
    Args:
        state: El estado actual del grafo.
        
    Returns:
        Un diccionario con las actualizaciones para el estado.
    """
    print("-- Node ejecutandose: General --")
    user_query = state["user_query"]
    user_id = state["user_id"]
    
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
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    input_for_executor = f"El usuario con ID {user_id} pregunta: {user_query}"
    
    response = agent_executor.invoke({
        "input": input_for_executor,
        "chat_history": state["chat_history"]
    })
    
    return {"recommendation_draft": response["output"], "agent_response": response["output"]}

def sustainability_agent_node(state: GraphState) -> dict:
    """
    Nodo del Agente de Sostenibilidad. Revisa las recomendaciones.
    """
    print("-- Node ejecutandose: sustainability --")
    recommendation_draft = state["recommendation_draft"]
    
    prompt = f"""
    Eres un experto en agricultura sostenible y prácticas ecológicas.
    Tu tarea es revisar la siguiente recomendación agrícola:

    "{recommendation_draft}"

    Analízala desde una perspectiva de sostenibilidad.
    - Si la recomendación es sostenible, apruébala y explica brevemente por qué.
    - Si NO es sostenible (ej. sugiere un pesticida químico fuerte), recházala y propón una alternativa orgánica o de bajo impacto.
    - Tu respuesta final será la que vea el agricultor.
    """
    
    response = llm.invoke(prompt)
    
    return {"agent_response": response.content}

def production_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Optimización de la Producción."""
    print("-- Node ejecutandose: Production --")
    prompt = f"""
    Eres un agrónomo experto en optimización de la producción.
    Basado en la siguiente pregunta del usuario y el historial de chat, proporciona una recomendación detallada para maximizar el rendimiento de los cultivos.
    Pregunta: {state['user_query']}
    Historial: {state['chat_history']}
    """
    
    response = llm.invoke(prompt)
    
    return {"agent_response": response.content}

def water_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Gestión de Recursos Hídricos."""
    print("-- Node ejecutandose: Water --")
    prompt = f"""
    Eres un hidrólogo experto en gestión del agua para la agricultura.
    Basado en la siguiente pregunta del usuario y el historial de chat, proporciona una recomendación detallada sobre riego, conservación y calidad del agua.
    Pregunta: {state['user_query']}
    Historial: {state['chat_history']}
    """
    
    response = llm.invoke(prompt)
    
    return {"agent_response": response.content}

def supply_chain_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Optimización de la Cadena de Suministro."""
    print("-- Node ejecutandose: Supply --")
    prompt = f"""
    Eres un experto en logística y cadena de suministro agrícola.
    Basado en la siguiente pregunta del usuario y el historial de chat, proporciona una recomendación detallada sobre inventario, transporte y comercialización.
    Pregunta: {state['user_query']}
    Historial: {state['chat_history']}
    """
    
    response = llm.invoke(prompt)
    
    return {"agent_response": response.content}