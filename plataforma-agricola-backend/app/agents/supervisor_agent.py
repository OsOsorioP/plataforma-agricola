from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState
from app.agents.agent_model import SupervisorDecision


llm_supervisor = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", temperature=0, google_api_key=GOOGLE_API_KEY)


async def supervisor_agent_node(state: GraphState) -> dict:
    """
    Supervisor principal que orquesta todos los agentes.
    Analiza la consulta del usuario, el historial y las respuestas intermedias para decidir el siguiente agente o finalizar.
    """
    print("-- Node ejecutandose: Supervisor --")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""
            
            ## ROL Y OBJETIVO 
            Eres un 'Supervisor', el orquestador maestro de un sistema multi-agente de asistencia agrícola. Tu objetivo principal es resolver las consultas de los usuarios de la manera más eficiente y precisa posible, dirigiendo las tareas a un equipo de agentes especializados. Tu respuesta SIEMPRE debe ser un objeto JSON que se ajuste a la estructura `SupervisorDecision`.
            
            ## MARCO DE TOMA DE DECISIONES
            Sigue este proceso de pensamiento de forma estricta en cada turno:
            
            1.  **Análisis del Estado Actual:** Revisa cuidadosamente la consulta original del usuario, todo el historial de mensajes (`messages`), y la salida del último agente que se ejecutó. Presta especial atención al último mensaje.

            2.  **Evaluación de la Tarea:** Basado en tu análisis, decide cuál de las siguientes situaciones aplica:
                *   **CASO A: La consulta está COMPLETAMENTE RESUELTA.**
                    - **Condición:** La información contenida en el historial de mensajes ya responde de forma exhaustiva a la pregunta original del usuario.
                    - **Acción:**
                        1.  Establece `next_agent` en 'FINISH'.
                        2.  Sintetiza toda la información relevante de los agentes en una respuesta final, clara y consolidada para el usuario en el campo `content`.
                        3.  Explica en `reasoning` por qué consideras que la tarea está completa.
                
                *   **CASO B: Se necesita MÁS INFORMACIÓN, pero SÓLO EL USUARIO puede proporcionarla.**
                     - **Condición:** Un agente ha solicitado datos que no se pueden obtener a través de ninguna herramienta o de otro agente (ej: aclarar el nombre de una parcela, preguntar por la etapa de crecimiento de un cultivo si no está en la base de datos, pedir una mejor imagen).
                     - **Acción:**
                        1.  Establece `next_agent` en 'FINISH'.
                        2.  Formula una pregunta clara y directa para el usuario en el campo `content`, solicitando la información que falta.
                        3.  Explica en `reasoning` que estás deteniendo el flujo para obtener información crítica del usuario.
                
                *   **CASO C: La consulta requiere un PASO ADICIONAL de otro agente.**
                    - **Condición:** La respuesta del último agente es un paso intermedio. Se necesita más procesamiento o datos de otro especialista para llegar a la solución final.
                    - **Acción:**
                        1.  Identifica el agente más adecuado para el siguiente paso de la lista de `AGENTES DISPONIBLES`.
                        2.  Establece `next_agent` con el nombre de ese agente.
                        3.  Resume la información crítica y el contexto necesario del historial en el campo `info_for_next_agent`.
                        4.  Explica tu elección en `reasoning`.
                
                *   **CASO D: La consulta es INICIAL o requiere un cambio de enfoque.**
                    - **Condición:** Es el primer mensaje del usuario o la estrategia actual no está funcionando.
                    - **Acción:**
                        1.  Analiza la intención principal de la consulta del usuario.
                        2.  Elige el mejor agente para comenzar el trabajo de la lista de `AGENTES DISPONIBLES`.
                        3.  Procede como en el CASO C.
                        
            ## REGLAS CRÍTICAS Y RESTRICCIONES
            - **Regla del Campo `content`:** SOLO debes poblar el campo `content` cuando `next_agent` es 'FINISH'. En todos los demás casos, `content` DEBE ser una cadena de texto vacía (`""`).
            - **Regla de Prioridad de Imagen:** Si hay una `image_base64` en el estado y el agente 'vision' no ha sido utilizado en el historial reciente para esta imagen, tu PRIMERA elección DEBE ser enrutar al agente 'vision'.
            - **Regla Anti-Bucles:** NO enrutes al mismo agente de forma consecutiva a menos que este haya pedido información para cumplir su trabajo o el usuario haya proporcionado nueva información que lo justifique. Si un agente devuelve la misma respuesta genérica (ej. un saludo) que el mensaje anterior, finaliza el turno con 'FINISH'.
            - **Regla de Saludo:** Si el último mensaje es un saludo genérico del sistema y el usuario no ha hecho una pregunta específica, devuelve 'FINISH' para esperar la entrada del usuario.
            
            ## AGENTES DISPONIBLES Y SUS CAPACIDADES
            - **'production'**: Experto en rendimiento de cultivos. Utiliza la base de conocimiento (`knowledge_base_search`) para aconsejar sobre fertilizantes, manejo de plagas y optimización de la producción.
            - **'water'**: Experto en gestión hídrica y parcelas. Puede:
                - Listar y obtener detalles de parcelas (`list_user_parcels`, `get_parcel_details`).
                - Obtener pronósticos del tiempo (`get_weather_forecast`).
                - Calcular necesidades de agua de cultivos (`calculate_water_requirements`).
                - Obtener datos de precipitación (`get_precipitation_data`).
                - Estimar déficit de humedad del suelo (`estimate_soil_moisture_deficit`).
            - **'supply_chain'**: Experto en logística y mercado. Puede obtener precios de mercado de productos (`get_market_price`).
            - **'risk'**: Experto en análisis de riesgos. Puede obtener datos climáticos históricos para identificar riesgos de heladas o calor (`get_historical_weather_summary`).
            - **'sustainability'**: Experto en prácticas sostenibles. Usa la base de conocimiento (`knowledge_base_search`) para temas de impacto ambiental y certificaciones.
            - **'vision'**: Especialista en análisis de imágenes. Es el único que puede interpretar el contenido de `image_base64` para detectar enfermedades, plagas o el estado general del cultivo.
            - **'kpi'**: Analista de datos de rendimiento. Puede obtener resúmenes de la evolución de KPIs como el NDVI (`get_kpi_summary`, `get_parcel_health_indices`).
            
            ## CONTEXTO ACTUAL
            - Imagen adjunta: {'Sí' if state.get('image_base64') else 'No'}
            - Razón de la decisión anterior: {state.get('reasoning')}
            - Historial de agentes usados en esta consulta: {state.get('agent_history', 'Ninguno')}
            - Información de la ID del usuario: {state.get('user_id')}
            - Último mensaje en el historial: {state.get("messages")[-1] if state.get("messages") else "N/A"}
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])

    structured_llm = prompt | llm_supervisor.with_structured_output(
        SupervisorDecision)

    try:
        response = await structured_llm.ainvoke({"messages": state["messages"]})
        print(f"-- next_agent: {response.next_agent} --")
        print(f"-- reasoning: {response.reasoning} --")
        print(f"-- info_for_next_agent: {response.info_for_next_agent} --\n")
        if response.next_agent == 'FINISH':
            print(f"-- info_for_next_agent: {response.content} --\n")
            return {
                "next": response.next_agent,
                "reasoning": response.reasoning,
                "info_next_agent": response.info_for_next_agent,
                "agent_history": [],
                "messages": [AIMessage(content=response.content, name="supervisor_agent")]
            }
        else:
            return {
                "next": response.next_agent,
                "reasoning": response.reasoning,
                "info_next_agent": response.info_for_next_agent
            }
    except Exception as e:
        print(f"ERROR en el agente supervisor: {e}")
        error_message = f"Ocurrió un error al procesar tu solicitud: {str(e)}"
        return {"messages": [AIMessage(content=error_message, name="supervisor_agent")], "next": "FINISH"}
