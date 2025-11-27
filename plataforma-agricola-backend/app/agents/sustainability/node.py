from langchain_core.messages import AIMessage
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.llm import llm_sustainability
from app.graph.state import GraphState
from app.prompts.loader import load_prompt
from app.agents.common.tools import (
    get_parcel_details,
    lookup_parcel_by_name,
    list_user_parcels,
)
from app.agents.production.tools import knowledge_base_tool, get_parcel_health_indices
from app.services.metrics.sustainability import (
    detect_chemical_in_message,
    detect_veto_in_output,
    calculate_eiq_for_alternative,
    extract_alternative_from_output,
    extract_veto_reason
)
from app.services.metrics.logger import kpi_logger
from app.utils.helper import normalize_agent_output

sustainability_tools = [
    knowledge_base_tool,
    get_parcel_details,
    lookup_parcel_by_name,
    get_parcel_health_indices,
    list_user_parcels
]

async def sustainability_agent_node(state: GraphState) -> dict:
    """
    Nodo del Agente de Sostenibilidad. Revisa las recomendaciones o el plan de tratamiento..
    """

    print("-- Node ejecutandose: sustainability --")
    
    prompt_template = ChatPromptTemplate.from_messages([(
        "system",
        load_prompt("sustainability", "system.md")
    ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    prompt = prompt_template.partial(
        user_id=state["user_id"],
        info_next_agent=state["info_next_agent"]
    )

    agent = create_tool_calling_agent(
        llm=llm_sustainability, 
        tools=sustainability_tools, 
        prompt=prompt
    )
    agent_executor = AgentExecutor(
        agent=agent,
        tools=sustainability_tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )

    try:
        response = await agent_executor.ainvoke({
            "messages": state["messages"]
        })

        response_content = normalize_agent_output(response["output"])
        
        detected_parcel_id = None
        
        if "intermediate_steps" in response:
            for action, _ in reversed(response["intermediate_steps"]):
                
                tools_with_id = ["get_parcel_details", "get_parcel_health_indices"]
                
                if action.tool in tools_with_id:
                    tool_input = action.tool_input

                    if isinstance(tool_input, dict) and "parcel_id" in tool_input:
                        detected_parcel_id = tool_input["parcel_id"]
                        break
                    
                    elif isinstance(tool_input, str):
                        try:
                            import json
                            input_clean = tool_input.replace("'", '"')
                            input_dict = json.loads(input_clean)
                            if "parcel_id" in input_dict:
                                detected_parcel_id = input_dict["parcel_id"]
                                break
                        except:
                            pass
        final_parcel_id = detected_parcel_id if detected_parcel_id else None

        try:
            last_message = state["messages"][-1].content if state["messages"] else ""
            detected_chemicals  = detect_chemical_in_message(response_content)
            was_vetoed = detect_veto_in_output(response_content)

            if detected_chemicals and was_vetoed:
                
                total_eiq_base = sum(c['eiq'] for c in detected_chemicals)
                
                alternatives = extract_alternative_from_output(response_content)
                
                eiq_alternatives_list = [calculate_eiq_for_alternative(alt) for alt in alternatives]
                
                total_eiq_alternative = max(eiq_alternatives_list) if eiq_alternatives_list else 0.0
                
                if total_eiq_base == 0:
                    total_eiq_alternative = 0.0
                
                veto_reason = extract_veto_reason(response_content)
                agent_history = state.get("list_agent", [])
                agent_source = agent_history[-1] if agent_history else "unknown"
                
                kpi_logger.log_intervention(
                    user_id=state.get("user_id"),
                    agent_source=agent_source,
                    chemical_name=", ".join([c['name'] for c in detected_chemicals]),
                    chemical_category=", ".join(set(c['category'] for c in detected_chemicals)),
                    was_vetoed=True,
                    veto_reason=veto_reason,
                    eiq_base=total_eiq_base,
                    eiq_alternative=total_eiq_alternative,
                    alternative_proposed=", ".join(alternatives),
                    parcel_id=final_parcel_id,
                )
                eiq_reduction_percent = 0
                
                if total_eiq_base > 0:
                    eiq_reduction_percent = ((total_eiq_base - total_eiq_alternative) / total_eiq_base) * 100
                    print(f"[KPI] ✓ Intervención GRUPAL registrada: VETO de {len(detected_chemicals)} químicos en parcela {final_parcel_id}")
                    print(f"[KPI]   EIQ: {total_eiq_base:.1f} → {total_eiq_alternative:.1f} (Reducción: {eiq_reduction_percent:.1f}%)")
                
            elif detected_chemicals and not was_vetoed:
                total_eiq_base = sum(c['eiq'] for c in detected_chemicals)
                
                agent_history = state.get("list_agent", [])
                agent_source = agent_history[-1] if agent_history else "unknown"
                
                kpi_logger.log_intervention(
                    user_id=state.get("user_id"),
                    agent_source=agent_source,
                    chemical_name=", ".join([c['name'] for c in detected_chemicals]),
                    chemical_category=", ".join(set(c['category'] for c in detected_chemicals)),
                    was_vetoed=False,
                    veto_reason="Fallo del Agente de Sostenibilidad en aplicar veto a químico tóxico.",
                    eiq_base=total_eiq_base,
                    eiq_alternative=total_eiq_base,
                    alternative_proposed="Ninguna (Químico aprobado por error)",
                    parcel_id=final_parcel_id
                )
                print(f"[KPI-WARNING] Error al registrar intervención: {", ".join([c['name'] for c in detected_chemicals])}")
        except Exception as e:
            # No fallar si hay error en logging
            print(f"[KPI-WARNING] Error al registrar intervención: {e}")
            
        print(f"\n-- Respuesta sustainability: {response_content}... --\n")    
        
        if response_content:
            return {
                "messages": [AIMessage(content=response_content, name="sustainability")],
                "list_agent": state.get("list_agent", []) + ["sustainability"]
            }
        else:
            print(f"\n-- ERROR: No hay contenido en la respuesta del sustainability --\n")
            return
        
    except Exception as e:
        error_message = f"Error en agente de sostenibilidad: {str(e)}"
        print(f"\n-- ERROR: {error_message} --\n")

        return {
            "messages": [AIMessage(
                content="Disculpa, ocurrió un error al analizar la sostenibilidad. Por favor, intenta reformular tu consulta.",
                name="sustainability"
            )],
            "list_agent": state.get("list_agent", []) + ["sustainability"]
        }
