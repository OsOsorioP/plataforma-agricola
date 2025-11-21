from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState
from app.agents.agent_model import SupervisorDecision


llm_supervisor = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", temperature=0, google_api_key=GOOGLE_API_KEY)


async def supervisor_agent_node(state: GraphState) -> dict:
    """
    Supervisor que orquesta el flujo multi-agente.
    Decide si enrutar a otro agente o finalizar con una respuesta al usuario.
    """
    print("-- Node ejecutandose: Supervisor --")

    has_image = bool(state.get('image_base64'))
    last_agent = state.get(
        'agent_history', [])[-1] if state.get('agent_history') else None
    reasoning_prev = state.get('reasoning', 'Ninguno')

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""
            
            ## TU RESPUESTA DEBE SER UN JSON CON ESTA ESTRUCTURA:
            
            "next_agent": "nombre_agente" o "FINISH",
            "reasoning": "explicación de tu decisión",
            "info_for_next_agent": "contexto relevante para el próximo agente",
            "content": "respuesta final SOLO si next_agent es FINISH, de lo contrario vacío"

## PROCESO DE DECISIÓN (en orden):

### 1. PRIORIDAD IMAGEN
- Si hay imagen (`image_base64`: {'Sí' if has_image else 'No'}) y 'vision' NO ha sido ejecutado → ENRUTA a 'vision'

### 2. EVALUAR ÚLTIMA RESPUESTA
Analiza el último mensaje del historial:

**CASO A: Respuesta Completa**
- La información disponible responde totalmente la consulta original
- Acción: `next_agent = "FINISH"`, sintetiza toda la info en `content`

**CASO B: Falta Info que SOLO el usuario puede dar**
- Un agente pidió datos que ningún otro agente puede proporcionar
- Ejemplos: nombre exacto de parcela, etapa de crecimiento no registrada, mejor calidad de imagen
- Acción: `next_agent = "FINISH"`, pregunta clara al usuario en `content`

**CASO C: Se necesita otro agente**
- La respuesta es parcial o requiere expertise de otro dominio
- Acción: Selecciona el agente apropiado, pasa contexto en `info_for_next_agent`

**CASO D: Solicitud entre agentes**
- Un agente pidió datos que OTRO agente SÍ puede proporcionar
- Ejemplo: 'production' necesita clima → enruta a 'water' para obtener weather
- Acción: Enruta al agente que tiene las herramientas necesarias

### 3. PREVENIR BUCLES
- Si el último agente ({last_agent}) devolvió un saludo genérico o pregunta abierta sin nueva info → FINISH
- NO enrutes al mismo agente consecutivamente a menos que el usuario haya dado nueva información

## AGENTES DISPONIBLES Y HERRAMIENTAS

**'vision'** → Análisis de imágenes (enfermedades, plagas)
**'production'** → Rendimiento, fertilizantes, manejo (herramientas: knowledge_base_search)
**'water'** → Gestión hídrica y parcelas (herramientas: list_user_parcels, get_parcel_details, get_weather_forecast, calculate_water_requirements, get_precipitation_data, estimate_soil_moisture_deficit)
**'supply_chain'** → Logística y precios (herramientas: get_market_price)
**'risk'** → Análisis de riesgos climáticos (herramientas: get_historical_weather_summary)
**'sustainability'** → Experto en agricultura sostenible, prácticas ecológicas y certificaciones. (herramientas: knowledge_base_search)
    Debe ser consultado cuando:
    * Usuario menciona palabras clave: "orgánico", "sostenible", "ecológico", "certificación", "bio", "verde"
    * Usuario pregunta por alternativas a químicos: "sin pesticidas", "natural", "no tóxico"
    * Otro agente propone prácticas que requieren validación ambiental
    * Usuario pregunta por: manejo integrado de plagas (MIP/IPM), control biológico, compost, fertilizantes orgánicos
    * Usuario quiere certificar su producción: "certificación orgánica", "sello verde", "fair trade"
    * Consultas sobre impacto ambiental o biodiversidad en fincas
    IMPORTANTE: Si otro agente ya dio una recomendación con químicos sintéticos, SIEMPRE enrutar a 'sustainability' para que evalúe si hay alternativa orgánica antes de finalizar.

## REGLAS CRÍTICAS
1. `content` SOLO se llena cuando `next_agent = "FINISH"`
2. En `info_for_next_agent` incluye: contexto relevante, IDs de parcelas, info previa de agentes, si el usuario lo suministra, sino simplemente entrega nombre de la parcela si lo hay y el usuario habla de ella
3. Si el usuario hace una pregunta inicial sin contexto previo → elige el agente más apropiado
4. Razonamiento anterior: {reasoning_prev}
5. User ID: {state.get('user_id')}
6. No entregues IDs inventados o que no estan en la consulta del usuario

Analiza el historial completo antes de decidir.
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
            print(
                f"-- content (respuesta final): {response.content[:100]}... --\n")
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
        print(f"ERROR en supervisor: {e}")
        error_msg = "Disculpa, ocurrió un error al procesar tu solicitud. Por favor, intenta reformular tu pregunta."
        return {
            "messages": [AIMessage(content=error_msg, name="supervisor")],
            "next": "FINISH"
        }
