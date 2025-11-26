from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState
from app.agents.agent_model import SupervisorDecision
from app.utils.kpi_logger import kpi_logger
from app.utils.helper_KT1 import (
    normalize_message_content,
    calculate_minimum_nodes,
    _should_validate_sustainability,
    _contains_chemical_recommendation,
    classify_query_type
)
from app.utils.helper import extract_user_query, get_agent_responses, build_synthesis_context

import uuid
import time

from app.utils.helper import save_conversation_log

llm_supervisor = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)

# ============================================================================
# NODO DEL SUPERVISOR
# ============================================================================


async def supervisor_agent_node(state: GraphState) -> dict:
    """
    Supervisor que orquesta el flujo multi-agente.
    Decide si enrutar a otro agente o finalizar con una respuesta al usuario.
    """
    print("\n-- Node ejecutándose: Supervisor --")

    supervisor_start_time = time.time()

    if not state.get("conversation_id"):
        state["conversation_id"] = str(uuid.uuid4())

    conversation_id = state["conversation_id"]

    # Extraer contexto de la CONVERSACIÓN ACTUAL
    has_image = bool(state.get('image_base64'))
    agent_history = state.get('list_agent', [])
    last_agent = agent_history[-1] if agent_history else None
    
    # Obtener MENSAJES de la conversación ACTUAL
    current_messages = state.get("messages", [])
    user_query = extract_user_query(current_messages)
    agent_responses = get_agent_responses(current_messages)
    
    # Último mensaje del último agente
    last_message_content = ""
    if current_messages:
        last_msg = current_messages[-1]
        if hasattr(last_msg, 'content'):
            last_message_content = normalize_message_content(last_msg.content)
    
    # Contexto del historial ANTERIOR (para recordar nombre, consultas previas, etc.)
    chat_history = state.get('chat_history', [])
    has_previous_context = len(chat_history) > 0

    # Construir síntesis para decisión
    synthesis_context = build_synthesis_context(current_messages)

    # Construir prompt con contexto dinámico
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""Eres el **Supervisor Orquestador** de un sistema multi-agente agrícola. 

## TU MISIÓN EN ESTA CONVERSACIÓN

Estás orquestando una CONSULTA ESPECÍFICA del usuario. Tienes acceso a:

1. **CONVERSACIÓN ACTUAL** (messages): La consulta del usuario + respuestas de agentes especializados
2. **HISTORIAL PREVIO** (chat_history): Conversaciones anteriores (SOLO para contexto si el usuario hace referencia)

---

## RESPUESTA JSON REQUERIDA

Tu respuesta SIEMPRE debe tener esta estructura:


  "next_agent": "nombre_agente" o "FINISH" NUNCA DEBE SER NONE,
  "reasoning": "por qué tomaste esta decisión",
  "info_for_next_agent": "contexto para el siguiente agente (vacío si FINISH)",
  "content": "RESPUESTA FINAL SINTETIZADA (solo si FINISH, vacío si no)"


---

## RESUMEN DE LA CONVERSACIÓN ACTUAL

{synthesis_context}

---

## PROCESO DE DECISIÓN (ORDEN ESTRICTO)

### 1 PRIORIDAD IMAGEN
**SI HAY IMAGEN** (`{has_image}`) **Y 'vision' NO ESTÁ EN**: {agent_history}
→ **next_agent = "vision"**
→ **info_for_next_agent = "Analizar imagen adjunta por el usuario"**

### 2 VALIDACIÓN DE SOSTENIBILIDAD (CRÍTICO)
**SI el último agente** (`{last_agent}`) **recomendó químicos sintéticos** **Y 'sustainability' NO ESTÁ EN**: {agent_history}
→ **next_agent = "sustainability"**
→ **info_for_next_agent = "Validar químicos recomendados por {last_agent} y proponer alternativas orgánicas"**

### 3 EVALUAR COMPLETITUD DE LA RESPUESTA

Analiza las respuestas de los agentes:

**CASO A: RESPUESTA COMPLETA** 
- Todas las respuestas de los agentes juntas responden la consulta original
- No hay información faltante
- No se necesita más análisis

→ **next_agent = "FINISH"**
→ **content = [SÍNTESIS UNIFICADA]** (VER REGLAS ABAJO)

**CASO B: INFORMACIÓN FALTANTE QUE SOLO EL USUARIO PUEDE DAR**
- Un agente pidió datos específicos (ej: "¿En qué etapa está tu cultivo?")
- Ningún otro agente puede proporcionar esa info

→ **next_agent = "FINISH"**
→ **content = [Pregunta clara al usuario]**

**CASO C: SE NECESITA OTRO AGENTE**
- La respuesta es parcial
- Hay un agente que puede complementar la información

→ **next_agent = "[nombre_agente]"**
→ **info_for_next_agent = "Qué necesitas que haga"**

**CASO D: COORDINACIÓN ENTRE AGENTES** 
- El agente de vision cuando da su diagnostico se enruta luego a production
- Un agente pidió datos que OTRO agente SÍ puede calcular/obtener

→ **next_agent = "[agente_con_herramientas]"**

### 4 PREVENIR BUCLES INFINITOS

**ANTI-BUCLE:**
- Si el mismo agente aparece 2+ veces seguidas → **FINISH**
- Si un agente dice "no puedo ayudar" → **FINISH** (explicar limitación)
- Si ya visitaste 5+ agentes → **FINISH** (sintetizar lo que hay)

**Último agente**: {last_agent}
**Historial**: {agent_history}

---

## AGENTES DISPONIBLES

- **vision**: Análisis de imágenes (enfermedades, plagas, deficiencias)
- **production**: Rendimiento, Producción, fertilizantes, manejo (herramientas: knowledge_base_search)
- **water**: Riego, precipitación, necesidades hídricas Gestión hídrica y parcelas (herramientas: list_user_parcels, get_parcel_details, get_weather_forecast, calculate_water_requirements, get_precipitation_data, estimate_soil_moisture_deficit)
- **risk**: Alertas, planes de contingencia, análisis de riesgos climáticos (herramientas: get_historical_weather_summary)
- **supply_chain**: Precios de mercado, comercialización
- **sustainability** → Experto en agricultura sostenible, prácticas ecológicas y certificaciones. (herramientas: knowledge_base_search)
    Debe ser consultado cuando:
    * Usuario menciona palabras clave: "orgánico", "sostenible", "ecológico", "certificación", "bio", "verde"
    * Usuario pregunta por alternativas a químicos: "sin pesticidas", "natural", "no tóxico"
    * Otro agente propone prácticas que requieren validación ambiental
    * Usuario pregunta por: manejo integrado de plagas (MIP/IPM), control biológico, compost, fertilizantes orgánicos
    * Usuario quiere certificar su producción: "certificación orgánica", "sello verde", "fair trade"
    * Consultas sobre impacto ambiental o biodiversidad en fincas
    IMPORTANTE: Si otro agente ya dio una recomendación con químicos sintéticos, SIEMPRE enrutar a 'sustainability' para que evalúe si hay alternativa orgánica antes de finalizar.

---

## REGLAS PARA SÍNTESIS FINAL (cuando next_agent = FINISH)

Cuando decidas **FINISH**, tu `content` debe ser una **respuesta unificada** que:

1. **COMBINA** todas las respuestas de los agentes de forma coherente
2. **ELIMINA** redundancias y contradicciones
3. **ORGANIZA** la información de forma lógica
4. **USA UN TONO** natural, directo y útil
5. **INCLUYE** recomendaciones accionables si las hay

**ESTRUCTURA SUGERIDA:**

[Resumen del diagnóstico/análisis si aplica]

Recomendaciones:
- [Punto 1]
- [Punto 2]

Advertencias importantes: [si las hay]

Próximos pasos: [si aplica]

**NO HAGAS:**
- Listar "el agente X dijo..., el agente Y dijo..."
- Repetir información idéntica de múltiples agentes
- Dar respuestas genéricas tipo "consulta con un experto"
- Incluir tecnicismos innecesarios

---

## CONTEXTO ADICIONAL

- **User ID**: {state.get('user_id')}
- **Conversation ID**: {conversation_id}
- **Imagen**: {'Sí' if has_image else 'No'}
- **Agentes consultados**: {agent_history}
- **Total respuestas**: {len(agent_responses)}
- **Tiene historial previo**: {'Sí - usa SOLO si el usuario hace referencia' if has_previous_context else 'No'}

---

## IMPORTANTE

- Los mensajes en `messages` son la CONVERSACIÓN ACTUAL
- El `chat_history` es SOLO para contexto si el usuario dice "como me llamo" o "qué me dijiste antes"
- Tu respuesta final debe SINTETIZAR las respuestas de LOS AGENTES, no inventar información nueva
- Si un agente no pudo responder algo, reconócelo y explica por qué

Analiza cuidadosamente y decide.
"""
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="chat_history")
    ])

    # Invocar LLM con estructura
    structured_llm = prompt | llm_supervisor.with_structured_output(
        SupervisorDecision)

    try:
        # Validación de sostenibilidad forzada si es necesario
        if _should_validate_sustainability(last_agent, last_message_content, agent_history):
            print(
                f"-- VALIDACIÓN FORZADA: Enrutando a sustainability para revisar químicos --")

            supervisor_time = time.time() - supervisor_start_time

            return {
                "next": "sustainability",
                "reasoning": f"El agente {last_agent} recomendó químicos sintéticos. Validación de sostenibilidad requerida.",
                "info_next_agent": f"El agente {last_agent} hizo recomendaciones que incluyen químicos sintéticos. Evaluar si existen alternativas orgánicas equivalentes antes de aprobar.",
                "time_breakdown": state.get("time_breakdown", {}) | {"supervisor": supervisor_time}
            }

        # Invocar LLM para decisión
        response = await structured_llm.ainvoke({"messages": state["messages"], "chat_history": state["chat_history"]})

        supervisor_time = time.time() - supervisor_start_time

        print(f"-- next_agent: {response.next_agent} --")
        print(f"-- reasoning: {response.reasoning} --")

        # ====================================================================
        # CAPTURA DE KPI: KT1 - EFICIENCIA DE ORQUESTACIÓN
        # ====================================================================

        if response.next_agent == 'FINISH':
            try:
                # Calcular nodos visitados
                nodes_visited = ["supervisor"] + \
                    agent_history + ["supervisor", "FINISH"]
                nodes_count = len(nodes_visited)

                # Clasificar tipo de consulta
                query_type = classify_query_type(user_query, has_image)

                # Calcular nodos mínimos necesarios
                nodes_minimum = calculate_minimum_nodes(query_type, has_image)

                # REGISTRAR ORQUESTACIÓN (KT1)
                kpi_logger.log_orchestration(
                    user_id=state.get("user_id"),
                    conversation_id=conversation_id,
                    query_text=user_query[:500],  # Limitar longitud
                    nodes_visited=nodes_visited,
                    nodes_minimum=nodes_minimum,
                    query_type=query_type,
                    has_image=has_image
                )

                g_eff = nodes_minimum / nodes_count if nodes_count > 0 else 0

                print(f"[KPI-KT1] ✓ Orquestación registrada")
                print(f"[KPI-KT1]   Tipo: {query_type}")
                print(
                    f"[KPI-KT1]   Nodos: {nodes_count} (mínimo: {nodes_minimum})")
                print(f"[KPI-KT1]   G_eff: {g_eff:.2f}")

            except Exception as e:
                print(f"[KPI-WARNING] Error al registrar orquestación: {e}")

            # ==============================================================
            # CAPTURA DE KPI: KA3 - LATENCIA DE INFERENCIA
            # ==============================================================

            try:
                # Calcular tiempo total
                total_time = state.get("total_start_time")
                if total_time:
                    total_elapsed = time.time() - total_time

                    # Obtener desglose de tiempos
                    time_breakdown = state.get("time_breakdown", {})
                    time_breakdown["supervisor"] = time_breakdown.get(
                        "supervisor", 0) + supervisor_time

                    # REGISTRAR LATENCIA (KA3)
                    kpi_logger.log_latency(
                        user_id=state.get("user_id"),
                        conversation_id=conversation_id,
                        total_time=total_elapsed,
                        time_breakdown=time_breakdown,
                        has_image=has_image
                    )

                    threshold = 10.0 if has_image else 5.0
                    status = "✓" if total_elapsed <= threshold else "✗"

                    print(
                        f"[KPI-KA3] {status} Latencia registrada: {total_elapsed:.2f}s")
                    print(f"[KPI-KA3]   Threshold: {threshold}s")
                    print(f"[KPI-KA3]   Desglose: {time_breakdown}")

            except Exception as e:
                print(f"[KPI-WARNING] Error al registrar latencia: {e}")

            # ==============================================================
            
            save_conversation_log(
                messages=state["messages"],
                user_id=state.get("user_id", 0),
                agent_history=agent_history,
                conversation_id=conversation_id,
                final_response=response.content
            )

            return {
                "next": response.next_agent,
                "reasoning": response.reasoning,
                "info_next_agent": response.info_for_next_agent,
                "list_agent": state["list_agent"],
                "messages": [AIMessage(content=response.content, name="supervisor")]
            }

        else:
            print(f"-- info_for_next_agent: {response.info_for_next_agent} --\n")
            # No es FINISH, continuar orquestación
            time_breakdown = state.get("time_breakdown", {})
            time_breakdown["supervisor"] = time_breakdown.get(
                "supervisor", 0) + supervisor_time
            return {
                "next": response.next_agent,
                "reasoning": response.reasoning,
                "info_next_agent": response.info_for_next_agent,
                "time_breakdown": time_breakdown
            }

    except Exception as e:
        print(f"ERROR en supervisor: {e}")

        supervisor_time = time.time() - supervisor_start_time
        time_breakdown = state.get("time_breakdown", {})
        time_breakdown["supervisor"] = time_breakdown.get(
            "supervisor", 0) + supervisor_time

        error_msg = "Disculpa, ocurrió un error al procesar tu solicitud. Por favor, intenta reformular tu pregunta."

        return {
            "messages": [AIMessage(content=error_msg, name="supervisor")],
            "next": "FINISH",
            "time_breakdown": time_breakdown
        }