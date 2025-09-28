from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage

from app.core.config import GOOGLE_API_KEY
from app.agents.graph_state import GraphState
from app.agents.agent_tools import (
    get_parcel_details, list_user_parcels, 
    knowledge_base_tool, 
    get_weather_forecast,
    get_market_price,
    get_historical_weather_summary
)

tools = [get_parcel_details, list_user_parcels]
production_tools = [knowledge_base_tool]
water_tools = [get_weather_forecast]
supply_tools = [knowledge_base_tool,get_market_price]
risk_tools = [knowledge_base_tool, get_historical_weather_summary]

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
    
    user_query = state["user_query"]
    user_id = state["user_id"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system","""Eres un agrónomo experto en optimización de la producción. Tu principal habilidad es consultar una base de conocimiento agrícola especializada.

        **Tu proceso de trabajo es estricto:**
        1.  Analiza la pregunta del usuario.
        2.  **SIEMPRE** debes usar la herramienta `knowledge_base_search` para encontrar la información más relevante y precisa en la base de conocimiento. No confíes únicamente en tu conocimiento general.
        3.  Una vez que tengas la información de la herramienta, úsala para construir una respuesta clara y concisa para el agricultor.
        4.  Si la base de conocimiento no devuelve información relevante, entonces y solo entonces, puedes usar tu conocimiento general para responder, pero debes indicar que la información no proviene de la base de conocimiento especializada.
        5.  Responde siempre en español.
        """),
        ("user","{input}"),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    agent = create_tool_calling_agent(llm, production_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=production_tools, verbose=True)
    
    response = agent_executor.invoke({
        "input": f"El usuario con ID {user_id} pregunta: {user_query}",
        "chat_history": state["chat_history"]
    })
    
    return {"agent_response": response["output"]}

def water_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Gestión de Recursos Hídricos."""
    print("-- Node ejecutandose: Water --")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """Eres un hidrólogo experto en gestión del agua para la agricultura. Tu principal habilidad es consultar el pronóstico del tiempo para dar recomendaciones de riego precisas.

            **Proceso de trabajo:**
            1.  Analiza la pregunta del usuario sobre riego.
            2.  Si la pregunta incluye una ubicación, **DEBES** usar la herramienta `get_weather_forecast` para obtener el clima actual y futuro.
            3.  Basa tu recomendación de riego directamente en el pronóstico. Si va a llover, recomienda no regar. Si está seco y caluroso, recomienda regar.
            4.  Si no se proporciona una ubicación, pide al usuario que la especifique.
            5.  Responde siempre en español.
        """
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, water_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=water_tools, verbose=True)
    
    response = agent_executor.invoke({
        "input": state["user_query"],
        "chat_history": state["chat_history"]
    })
    
    return {"agent_response": response["output"]}

def supply_chain_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Optimización de la Cadena de Suministro."""
    print("-- Node ejecutandose: Supply --")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """Eres un experto en logística y comercialización agrícola. Tienes dos herramientas principales:
            1. `knowledge_base_search`: Úsala para responder preguntas sobre regulaciones, estándares de calidad, empaquetado y logística.
            2. `get_market_price`: Úsala para obtener el precio de mercado actual de un producto.

            Analiza la pregunta del usuario y utiliza la herramienta más apropiada para responder.
            Si la pregunta es sobre calidad o regulaciones, usa la base de conocimiento.
            Si la pregunta es sobre precios, usa la herramienta de precios de mercado.
            Responde siempre en español.
        """
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, supply_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=supply_tools, verbose=True)
    
    response = agent_executor.invoke({
        "input": state["user_query"],
        "chat_history": state["chat_history"]
    })
    
    return {"agent_response": response["output"]}

def vision_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Diagnóstico Visual."""
    print("-- Node ejecutandose: vision --")
    prompt = f"""
    Eres un fitopatólogo experto (especialista en enfermedades de plantas).
    Analiza la siguiente imagen de un cultivo junto con la pregunta del usuario.
    1. Identifica la planta en la imagen.
    2. Diagnostica cualquier posible enfermedad, plaga o deficiencia nutricional visible.
    3. Proporciona una recomendación clara y práctica para tratar el problema.
    4. Si no puedes hacer un diagnóstico claro, explícalo y sugiere qué tipo de información adicional o fotos necesitarías.
    
    Pregunta del usuario: {state['user_query']}
    """
    
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{state['image_base64']}"
            },
        ]
    )
    
    response = llm.invoke([message])
    return {"agent_response": response.content}

def risk_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Predicción y Mitigación de Riesgos."""
    print("-- Node ejecutandose: risk --")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """Eres un analista de riesgos agrícolas y estratega. Tu trabajo es identificar riesgos y proponer planes de mitigación.

            **Tu proceso de razonamiento es en dos pasos:**
            1.  **Identificar y Cuantificar el Riesgo:** Usa la herramienta `get_historical_weather_summary` para analizar los datos climáticos históricos de la ubicación del usuario y confirmar la existencia y frecuencia de un riesgo (como heladas o sequías).
            2.  **Proponer Solución:** Una vez confirmado el riesgo, usa la herramienta `knowledge_base_search` para encontrar el plan de contingencia o las acciones de mitigación recomendadas en el manual.

            Combina la información de ambos pasos para dar una respuesta completa y bien fundamentada.
            Responde siempre en español.
            """
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, risk_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=risk_tools, verbose=True)
    
    response = agent_executor.invoke({
        "input": state["user_query"],
        "chat_history": state["chat_history"]
    })
    
    return {"agent_response": response["output"]}
    
