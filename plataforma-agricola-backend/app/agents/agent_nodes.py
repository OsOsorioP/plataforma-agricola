from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import GOOGLE_API_KEY
from app.agents.graph_state import GraphState
from app.agents.agent_model import SupervisorDecision
from app.agents.agent_tools import (
    get_parcel_details, list_user_parcels, 
    knowledge_base_tool, 
    get_weather_forecast,
    get_market_price,
    get_historical_weather_summary,
    get_parcel_health_indices,
    save_recommendation,
    get_kpi_summary
)

tools = [get_parcel_details, list_user_parcels]
production_tools = [knowledge_base_tool, get_parcel_health_indices]
water_tools = [get_weather_forecast, get_parcel_health_indices, save_recommendation]
supply_tools = [knowledge_base_tool,get_market_price]
risk_tools = [knowledge_base_tool, get_historical_weather_summary]
kpi_tools = [get_kpi_summary]

llm_supervisor = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=GOOGLE_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0, google_api_key=GOOGLE_API_KEY)

async def supervisor_agent_node(state: GraphState)->dict:
    """
    Supervisor principal que orquesta todos los agentes.
    Analiza la consulta del usuario, el historial y las respuestas intermedias para decidir el siguiente agente o finalizar.
    """
    print("-- Node ejecutandose: Supervisor --")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""Eres el orquestador principal (Supervisor) de un sistema multi-agente para agricultura. Tu rol es analizar y dirigir el flujo de la conversación y la ejecución de tareas.
    
            Tarea: Analizar la última consulta del usuario, el historial de conversación (`messages`), y el contexto de los agentes anteriores (`reasoning`, `agent_history`) para decidir el siguiente paso.
        
            Objetivo: Proporcionar una respuesta completa, precisa y consolidada al usuario, utilizando la secuencia de agentes más eficiente.
            
            Instrucciones para la toma de decisiones:
            1.  Prioridad de Imagen: Si hay una `image_base64` y el agente 'vision' no ha sido utilizado, el primer paso DEBE ser enrutar al agente 'vision'.
            2.  Evaluación de Respuestas: Después de que un agente ha respondido, evalúa si esa respuesta, junto con el contexto, satisface la consulta original del usuario.
            3.  Encadenamiento de Agentes: Si la consulta requiere información de múltiples especialidades, encadena los agentes apropiados. Por ejemplo, una pregunta sobre "rendimiento y gestión del agua" podría ir a 'production' y luego a 'water'.
            4.  Falta de información: Si un agente necesita información pero ningun agente podría brindar esa información, más que solamente el usuario podría brindarla, debes devolver en `next_agent` un 'FINISH'.
            4.  Finalización: Si la consulta está completamente resuelta o si no hay un agente adecuado para continuar, devuelve 'FINISH', ten en cuenta que un agente no entre en un bucle, por lo tanto un agente no puede devolver la misma información, al menos que el la pida
                - REGLA DE SALUDO: Si el ÚLTIMO mensaje en el historial es una respuesta de bienvenida o una pregunta abierta (ej. '¿En qué puedo ayudarte hoy?'), y el usuario aún no ha formulado una pregunta específica, DEBES devolver 'FINISH' para pasar el control al usuario.
                - REGLA DE REPETICIÓN: Un agente no puede devolver la misma información o el mismo tipo de mensaje (ej. una bienvenida) que el mensaje anterior, al menos que el usuario lo pida explícitamente. Tampoco un agente puede volver a entrar seguidamente. Si se repite un saludo o una pregunta genérica, devuelve 'FINISH'.
            5.  Formato de Salida: Debes devolver un JSON con `next_agent` (el nombre del agente o 'FINISH'), `reasoning` (tu explicación de la decisión), `info_for_next_agent` (información necesaria para el agente, si lo requiere), y `content` (aquí solamente va la respuesta completa, clara y concisa al usuario recopilada de la respuesta de todos los agentes para la consulta del usuario, realizala solamente cuando finalice todo un 'FINISH').

            Tu decisión actual debe ser sobre el siguiente agente a ejecutar o si la tarea está completada.
        
            Aquí están los agentes especializados disponibles:
            - 'general': Equipo de soporte general que puede responder preguntas sobre datos de parcelas o temas no cubiertos por los especialistas como conversación en general con el usuario.
            - 'production': Expertos en maximizar el rendimiento de los cultivos, sugerir prácticas de manejo, fertilizantes, etc.
            - 'water': Expertos en riego, clima, gestión y conservación del agua.
            - 'supply_chain': Expertos en logística, inventario, transporte y venta de productos.
            - 'risk': Expertos en analizar riesgos climáticos (heladas, sequías) y proponer planes de contingencia.
            - 'sustainability' : Experto en prácticas agrícolas sostenibles, impacto ambiental, certificaciones, etc.
            - 'vision' : Experto en analisar imagenes, para detectar enfermedades y todo lo que tenga que ver con imagenes.
            - 'kpi': Experto en analizar la evolución de los Indicadores Clave de Desempeño (KPIs) para medir el impacto de las acciones en una parcela.
            
            Recuerda usar FINISH, si la consulta del usuario ha sido completamente satisfecha o si no se necesita más información.
        
            Contexto actual:
            - Imagen adjunta: {'Sí' if state.get('image_base64') else 'No'}
            - Razón anterior: {state.get('reasoning')}
            - Lista de agentes usados: {state.get('agent_history', 'Ninguno')}
            - Información del usuario: {state.get('user_info')}
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
     
    structured_llm = prompt | llm_supervisor.with_structured_output(SupervisorDecision)

    try:
        response = await structured_llm.ainvoke({"messages": state["messages"]})
        print(f"-- next_agent: {response.next_agent} --")
        print(f"-- reasoning: {response.reasoning} --")
        print(f"-- info_for_next_agent: {response.info_for_next_agent} --\n")
        if response.next_agent == 'FINISH':
            print(f"-- info_for_next_agent: {response.content} --\n")
            return {
                "next": response.next_agent, 
                "reasoning":response.reasoning, 
                "info_next_agent":response.info_for_next_agent,
                "agent_history": [],
                "messages": [AIMessage(content=response.content, name="supervisor_agent")]
            }
        else:
            return {
                "next": response.next_agent, 
                "reasoning":response.reasoning, 
                "info_next_agent":response.info_for_next_agent
            }
    except Exception as e:
        return {"next": "FINISH"}

async def general_tool_agent_node(state: GraphState) -> dict:
    """
    Nodo del agente general, se encarga de proporcionar información de parcelas o tener una charla con el usuario.
    
    Args:
        state: El estado actual del grafo.
        
    Returns:
        Un diccionario con las actualizaciones para el estado.
    """
    print("-- Node ejecutandose: General --")
    
    prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        f"""Eres un asistente de IA especializado en agricultura, diseñado para ayudar a los agricultores con información general y específica de sus parcelas.
        
        Tarea: Generar una respuesta útil y precisa para el agricultor.
        
        Instrucciones:
        1. Analiza la intención del usuario: Determina si la pregunta es de conocimiento general o si requiere datos específicos del sistema.
        2. Uso de Herramientas (Datos del Sistema): Si la pregunta es específicamente sobre datos guardados en el sistema (ej. 'dame los detalles de mi parcela', 'lista mis campos', '¿qué datos tienes de la parcela con ID 2?', 'crea una nueva parcela'), DEBES usar las herramientas que tienes disponibles para obtener o gestionar la información más actualizada y precisa.
        3. Respuesta Clara y en Español: Responde siempre en español. Sé conciso, amigable y profesional.
        4. Manejo de Información Faltante: Si una herramienta requiere información adicional del usuario (ej. un ID de parcela), pídesela de forma clara y específica. Si una herramienta no devuelve resultados relevantes, informa al usuario de la situación y ofrécele otras opciones.
        
        Contexto:
        {state.get("info_next_agent") | state["messages"][-1].content}"""
    ),
    MessagesPlaceholder(variable_name="messages"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})
        return {
            "messages": [AIMessage(content=response["output"], name="general_agent")],
            "agent_history": state.get("agent_history", []) + ["general_agent"]
        }
    except Exception as e:
        return {"messages": [AIMessage(content=e, name="general_agent")]}

async def sustainability_agent_node(state: GraphState) -> dict:
    """
    Nodo del Agente de Sostenibilidad. Revisa las recomendaciones o el plan de tratamiento..
    """
    print("-- Node ejecutandose: sustainability --")
    prompt = f"""Eres un experto en agricultura sostenible y prácticas ecológicas.
    
    Tarea: Revisar recomendaciones agrícola o planes de tratamiento propuesto.

    Analízala desde una perspectiva de sostenibilidad.
    - Si la recomendación o plan ya es sostenible, apruébala y explica brevemente por qué.
    - Si NO es sostenible (ej. sugiere un pesticida químico fuerte), recházala y propón una alternativa orgánica o de bajo impacto.
    
    Contexto:
    {state.get("info_next_agent") | state["messages"][-1].content}
    """
    
    response = await llm.ainvoke(prompt)
    
    print(response.content)
    
    return {
        "messages": [AIMessage(content=response.content, name="sustainability")],
        "agent_history": state.get("agent_history", []) + ["sustainability_agent"]
    }

async def production_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Optimización de la Producción. Ahora puede recibir un diagnóstico."""
    print("-- Node ejecutandose: Production --")

    prompt = ChatPromptTemplate.from_messages([
        ("system","""Eres un agrónomo experto en optimización de la producción y análisis de salud de cultivos.
         
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
    agent_executor = AgentExecutor(agent=agent, tools=production_tools, verbose=True)
    
    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})
        return {
            "messages": [AIMessage(content=response["output"], name="production_agent")],
            "agent_history": state.get("agent_history", []) + ["production_agent"]
        }
    except Exception as e:
        return {"messages": [AIMessage(content=e, name="production_agent")]}

async def water_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Gestión de Recursos Hídricos."""
    print("-- Node ejecutandose: Water --")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """Eres un hidrólogo experto en gestión del agua para la agricultura. 
            
            Tarea: Proporcionar recomendaciones de riego y analizar el estrés hídrico.

            Instrucciones:
            1.  Pronóstico del Tiempo: Si la pregunta incluye una ubicación, **DEBES** usar la herramienta `get_weather_forecast` para obtener el clima actual y futuro.
            2.  Análisis de Estrés Hídrico: Si la pregunta es sobre el estado del riego o estrés hídrico de una parcela, usa la herramienta `get_parcel_health_indices` para obtener el NDVI, que es un indicador clave de la necesidad de agua.
            3.  Basa tu recomendación de riego en la combinación del pronóstico del tiempo y el estado de salud (NDVI).
            4.  **ACCIÓN FINAL:** Después de dar una recomendación clara al usuario, **DEBES** usar la herramienta `save_recommendation` para registrar tu consejo en el sistema. Debes proporcionar el `parcel_id`, tu nombre de agente ('water_agent') y el texto de la recomendación.
            5.  Si no se proporciona la información necesaria (ubicación, ID de parcela, fechas), pídesela al usuario.
            6.  Responde siempre en español.
        """
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, water_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=water_tools, verbose=True)
    
    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})
        return {
            "messages": [AIMessage(content=response["output"], name="water_agent")],
            "agent_history": state.get("agent_history", []) + ["water_agent"]
        }
    except Exception as e:
        return {"messages": [AIMessage(content=e, name="water_agent")]}

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
    agent_executor = AgentExecutor(agent=agent, tools=supply_tools, verbose=True)
    
    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})
        return {
            "messages": [AIMessage(content=response["output"], name="supply_chain_agent")],
            "agent_history": state.get("agent_history", []) + ["supply_chain_agent"]
        }
    except Exception as e:
        return {"messages": [AIMessage(content=e, name="supply_chain_agent")]}

async def vision_agent_node(state: GraphState) -> dict:
    """Nodo del Agente de Visión. Ahora produce un diagnóstico para otros agentes."""
    print("-- Node ejecutandose: vision --")
    prompt = f"""
    Eres un fitopatólogo experto (especialista en enfermedades de plantas).
    Analiza la siguiente imagen de un cultivo junto con la pregunta del usuario.
    1. Identifica la planta en la imagen.
    2. Diagnostica cualquier posible enfermedad, plaga o deficiencia nutricional visible.
    3. Proporciona una recomendación clara y práctica para tratar el problema.
    4. Si no puedes hacer un diagnóstico claro, explícalo y sugiere qué tipo de información adicional o fotos necesitarías.
    """
    # 3. Tu salida debe ser únicamente el nombre del problema identificado.
    # 3. Proporciona una recomendación clara y práctica para tratar el problema.
    # 4. Si no puedes hacer un diagnóstico claro, explícalo y sugiere qué tipo de información adicional o fotos necesitarías.
    if state.get("image_base64"):
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{state['image_base64']}"
                },
            ]
        )
    elif(state.get("audio_base64")):
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "media",
                    "data": f"{state['audio_base64']}",
                    "mime_type": "audio/mpeg"
                },
            ]
        )
    
    response = await llm.ainvoke([message])
    print(response.content)
    return {
        "messages": [AIMessage(content=response.content, name="vision_agent")],
        "agent_history": state.get("agent_history", []) + ["vision_agent"]
    }

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
        return {
            "messages": [AIMessage(content=e, name="risk_agent")],
            "agent_history": state.get("agent_history", []) + ["risk_agent"]
        }
          
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
    agent_executor = AgentExecutor(agent=agent, tools=kpi_tools, verbose=True)
    
    try:
        response = await agent_executor.ainvoke({"messages": state["messages"]})
        return {
            "messages": [AIMessage(content=response["output"], name="kpi_agent")],
            "agent_history": state.get("agent_history", []) + ["kpi_agent"]
        }
    except Exception as e:
        return {"messages": [AIMessage(content=e, name="kpi_agent")]}