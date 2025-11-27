from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.state import GraphState
from app.services.metrics.logger import kpi_logger
from app.services.metrics.vision import (
    extract_diagnosis_from_output,
    analyze_image_conditions
)
from app.prompts.loader import load_prompt

import time

llm_vision = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
    google_api_key=GOOGLE_API_KEY
)

async def vision_agent_node(state: GraphState) -> dict:
    """
    Agente de Visión mejorado.
    Analiza imágenes para detectar enfermedades, plagas, deficiencias.
    """
    print("-- Node ejecutándose: vision_agent --")
    
    
    prompt_template = load_prompt("vision", "system.md")
    

    # Medir tiempo de inicio
    start_time = time.time()
    
    if state.get("image_base64"):
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_template},
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{state['image_base64']}"
                },
            ]
        )
        image_base64 = state['image_base64']
    elif state.get("audio_base64"):
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_template},
                {
                    "type": "media",
                    "data": f"{state['audio_base64']}",
                    "mime_type": "audio/mpeg"
                },
            ]
        )
        image_base64 = None
    else:
        return {
            "messages": [AIMessage(
                content="No se proporcionó ninguna imagen para analizar. Por favor, sube una foto del cultivo.", 
                name="vision"
            )],
            "list_agent": state.get("list_agent", []) + ["vision"]
        }
    
    try:
        response = await llm_vision.ainvoke([message])
        
        response_content = response.content
        
        processing_time = time.time() - start_time
        
        try:
            if image_base64: 
                
                diagnosis_data = extract_diagnosis_from_output(response_content)
                
                image_conditions = analyze_image_conditions(image_base64)
                
                if diagnosis_data['diagnosis']:
                    kpi_logger.log_diagnosis(
                        user_id=state.get("user_id"),
                        diagnosis=diagnosis_data['diagnosis'],
                        confidence=diagnosis_data['confidence'],
                        processing_time=processing_time,
                        image_size_kb=image_conditions['size_kb'],
                        image_conditions=image_conditions,
                        parcel_id=state.get("parcel_id") if state.get("parcel_id") else None,
                        ground_truth=None
                    )
                    
                    print(f"[KPI] ✓ Diagnóstico registrado: {diagnosis_data['diagnosis']}")
                    print(f"[KPI]   Confianza: {diagnosis_data['confidence']:.0%}")
                    print(f"[KPI]   Tiempo: {processing_time:.2f}s")
                else:
                    print("[KPI-WARNING] No se pudo extraer diagnóstico del output")
        
        except Exception as e:
            print(f"[KPI-WARNING] Error al registrar diagnóstico: {e}")
        
        # ====================================================================
        
        print(f"-- Respuesta vision: {response_content}... --\n")
        
        return {
            "messages": [AIMessage(content=response_content, name="vision")],
            "list_agent": state.get("list_agent", []) + ["vision"]
        }
        
    except Exception as e:
        print(f"-- ERROR vision: {e} --")
        return {
            "messages": [AIMessage(
                content=f"Error al analizar la imagen: {str(e)}. Por favor, intenta con una imagen más clara.",
                name="vision"
            )],
            "list_agent": state.get("list_agent", []) + ["vision"]
        }