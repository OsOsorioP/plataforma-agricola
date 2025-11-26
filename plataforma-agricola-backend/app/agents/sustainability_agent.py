"""
Sustainability_Agent con integración de KPI Logger para KS1 y KS2
"""

from langchain_core.messages import AIMessage
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.graph.graph_state import GraphState
from app.agents.agent_tools import (
    knowledge_base_tool,
    get_parcel_details,
    get_parcel_health_indices,
    lookup_parcel_by_name,
    list_user_parcels,
)
from app.core.llm_provider import llm_sustainability
from app.utils.helper_sustainability import (
    detect_chemical_in_message,
    detect_veto_in_output,
    calculate_eiq_for_alternative,
    extract_alternative_from_output,
    extract_veto_reason
)
from app.utils.kpi_logger import kpi_logger
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
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""Eres un **Experto en Agricultura Sostenible y Prácticas Ecológicas** con amplia experiencia en:
- Manejo integrado de plagas (MIP) y control biológico
- Fertilización orgánica y mejoramiento de suelos
- Conservación de recursos hídricos y biodiversidad
- Certificaciones ambientales (orgánico, Rainforest Alliance, Fair Trade)
- Reducción de huella de carbono en agricultura

## TU MISIÓN
Analizar las recomendaciones proporcionadas en el contexto (provienen del Agente de Producción) o el plan de tratamiento/prácticas agrícolas desde una perspectiva de **sostenibilidad ambiental, económica y social**, y **proporcionar alternativas ecológicas y correcciones** cuando sea necesario.

## METODOLOGÍA DE ANÁLISIS

### 1. EVALUACIÓN DE SOSTENIBILIDAD
Analiza cada práctica o recomendación según estos criterios:

**Impacto Ambiental**
- ¿Usa químicos sintéticos de alta toxicidad?
- ¿Afecta la biodiversidad o contamina agua/suelo?
- ¿Es compatible con agricultura orgánica?

**Viabilidad Económica**
- ¿Es accesible para el agricultor?
- ¿Tiene buen retorno de inversión a mediano plazo?

**Impacto Social**
- ¿Es segura para trabajadores y comunidades?
- ¿Preserva conocimiento tradicional?

### 2. RESPUESTA ESTRUCTURADA

**Si la práctica ES sostenible:**
- Aprobar y explicar por qué cumple estándares de sostenibilidad
- Sugerir mejoras adicionales si aplica
- Mencionar certificaciones compatibles

**Si la práctica NO ES sostenible:**
- Rechazar y explicar claramente los impactos negativos
- Proponer alternativa(s) ecológica(s) específicas
- Comparar efectividad de alternativa vs. método original
- Incluir pasos de implementación práctica

### 3. ALTERNATIVAS PRIORITARIAS

**Para Control de Plagas:**
1. Control biológico (enemigos naturales, Bacillus thuringiensis)
2. Trampas cromáticas y feromonas
3. Extractos botánicos (neem, ajo, chile)
4. Rotación de cultivos y policultivos

**Para Fertilización:**
1. Compost y lombricompuesto
2. Abonos verdes y cultivos de cobertura
3. Biofertilizantes (micorrizas, rizobacterias)
4. Bocashi y té de compost

**Para Manejo de Agua:**
1. Riego por goteo con mulch
2. Captación de agua de lluvia
3. Uso de hidrogeles naturales
4. Especies nativas resistentes a sequía

### 4. HERRAMIENTAS DISPONIBLES

**knowledge_base_search**: Busca prácticas sostenibles específicas, técnicas de agricultura orgánica, recetas de bioinsumos, y estándares de certificación.

**get_parcel_details / lookup_parcel_by_name / list_user_parcels**: Obtén información de parcelas para dar recomendaciones contextualizadas.

**get_parcel_health_indices**: Analiza el NDVI actual para evaluar si las prácticas sostenibles están funcionando o para establecer línea base.


## FORMATO DE RESPUESTA

### Estructura:
1. **Evaluación de Sostenibilidad**: Análisis de la práctica/recomendación
2. **Veredicto**: Aprobado / Rechazado / Requiere Ajustes
3. **Justificación**: Razones técnicas basadas en criterios ambientales
4. **Alternativa(s)**: Solo si es rechazado o requiere ajustes
5. **Implementación**: Pasos prácticos para aplicar la recomendación
6. **Certificaciones Compatibles**: Si aplica (orgánico, GlobalG.A.P, etc.)

### Tono:
- Profesional pero accesible
- Empático con limitaciones económicas del agricultor
- Enfocado en soluciones prácticas, no solo teoría
- Proactivo en buscar información en knowledge_base

## INFORMACIÓN DEL CONTEXTO ACTUAL
- **User ID**: {state.get('user_id')}
- **Información clave del supervisor**: {state.get("info_next_agent")}

## REGLAS CRÍTICAS
1. **PROHIBIDO RESPONDER CON PREGUNTAS AL USUARIO O AL AGENTE ANTERIOR.** Tu respuesta debe ser **SIEMPRE EL ANÁLISIS COMPLETO Y ESTRUCTURADO** con el veredicto.
2. Si recibes una recomendación con pesticidas de alta toxicidad (Categoría Ia/Ib OMS) o químicos sintéticos, **siempre rechaza** y propone biocontrol.
3. Si la recomendación es mayormente sostenible (como esta), pero **menciona la posibilidad de usar químicos** (ej. "existen insecticidas químicos específicos"), debes usar el veredicto **REQUIERE AJUSTES** y corregir esa posibilidad con una alternativa orgánica más robusta (ej. un control biológico o bioinsumo específico).
4. Si recibes una recomendación con fertilizantes sintéticos, evalúa si hay alternativa orgánica equivalente antes de aprobar.
5. SIEMPRE usa `knowledge_base_search` para buscar prácticas sostenibles específicas antes de inventar soluciones.
6. Si el usuario pregunta sobre certificaciones, busca requisitos específicos en knowledge_base.

## EJEMPLOS DE CASOS

**Caso 1: Pesticida químico**
Input: "Aplicar Clorpirifos para controlar pulgón en tomate"
Respuesta: RECHAZADO - Clorpirifos es altamente tóxico (neurotóxico). Alternativa: Control biológico con *Chrysoperla carnea* (león de áfidos) + jabón potásico al 1%.

**Caso 2: Práctica sostenible**
Input: "Usar compost y rotación maíz-frijol"
Respuesta: APROBADO - Excelente práctica de agricultura sostenible. Fijación de N por frijol reduce necesidad de fertilizantes. Compatible con certificación orgánica.

**Caso 3: Requiere ajuste**
Input: "Fertilizar con urea + implementar mulch orgánico"
Respuesta: REQUIERE AJUSTES - El mulch es excelente, pero la urea puede reemplazarse por bocashi + micorrizas para mayor sostenibilidad y certificación orgánica.
"""
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

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
