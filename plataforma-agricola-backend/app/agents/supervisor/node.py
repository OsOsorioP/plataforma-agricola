from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.state import GraphState
from app.schemas.agent import SupervisorDecision
from app.services.metrics.logger import kpi_logger
from app.services.metrics.orchestration import (
    normalize_message_content,
    calculate_minimum_nodes,
    _should_validate_sustainability,
    classify_query_type
)
from app.utils.helper import extract_user_query, get_agent_responses, build_synthesis_context
from app.prompts.loader import load_prompt

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

    has_image = 'Sí' if bool(state.get('image_base64')) else 'No'
    agent_history = state.get('list_agent', [])
    last_agent = agent_history[-1] if agent_history else None

    current_messages = state.get("messages", [])
    user_query = extract_user_query(current_messages)
    agent_responses = get_agent_responses(current_messages)

    last_message_content = ""
    if current_messages:
        last_msg = current_messages[-1]
        if hasattr(last_msg, 'content'):
            last_message_content = normalize_message_content(last_msg.content)

    chat_history = state.get('chat_history', [])
    has_previous_context = len(chat_history) > 0

    synthesis_context = build_synthesis_context(current_messages)

    prompt_template = ChatPromptTemplate.from_messages([
        (
            "system",
            load_prompt("supervisor", "system.md")
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="chat_history")
    ])
    
    prompt = prompt_template.partial(
        user_id=state["user_id"],
        synthesis_context=synthesis_context,
        has_image=has_image,
        agent_history=agent_history,
        last_agent=last_agent,
        conversation_id=conversation_id,
        agent_responses= len(agent_responses),
        has_previous_context= 'Sí - usa SOLO si el usuario hace referencia' if has_previous_context else 'No'
    )

    structured_llm = prompt | llm_supervisor.with_structured_output(SupervisorDecision)

    try:
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
            print(
                f"-- info_for_next_agent: {response.info_for_next_agent} --\n")
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
