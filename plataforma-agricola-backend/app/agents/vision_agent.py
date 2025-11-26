from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import GOOGLE_API_KEY
from app.graph.graph_state import GraphState
from app.utils.kpi_logger import kpi_logger
from app.utils.helper_KT2 import (
    extract_diagnosis_from_output,
    analyze_image_conditions
)

import time


llm_vision = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # Modelo específico para visión
    temperature=0.1,
    google_api_key=GOOGLE_API_KEY
)

async def vision_agent_node(state: GraphState) -> dict:
    """
    Agente de Visión mejorado.
    Analiza imágenes para detectar enfermedades, plagas, deficiencias.
    """
    print("-- Node ejecutándose: vision_agent --")
    
    prompt = """Eres un **Fitopatólogo y Entomólogo Agrícola Especialista** con amplia experiencia en:
- Diagnóstico visual de enfermedades de plantas (hongos, bacterias, virus)
- Identificación de plagas (insectos, ácaros, moluscos)
- Detección de deficiencias nutricionales
- Daños abióticos (clima, herbicidas, estrés hídrico)
- Evaluación del estado fenológico de cultivos

## TU MISIÓN
Analizar la imagen proporcionada y generar un diagnóstico preciso, detallado y accionable.

## PROTOCOLO DE ANÁLISIS

### 1. OBSERVACIÓN SISTEMÁTICA
Analiza la imagen en este orden:

**a) Identificación del Cultivo**
- ¿Qué planta es? (familia, especie si es posible)
- ¿En qué etapa fenológica está? (plántula, vegetativa, floración, fructificación)

**b) Órgano Afectado**
- ¿Hojas? (viejas vs jóvenes, haz vs envés)
- ¿Tallo/ramas?
- ¿Frutos?
- ¿Raíces? (si visible)

**c) Patrón de Daño**
- Distribución: ¿Localizado o generalizado?
- Progresión: ¿Desde dónde avanza?
- Síntomas asociados: clorosis, necrosis, deformaciones

**d) Presencia de Agentes**
- ¿Se ven insectos, ácaros, caracoles?
- ¿Hay signos de hongos? (micelio, esporas, manchas circulares)
- ¿Excreciones, telarañas, galerías?

### 2. DIAGNÓSTICO DIFERENCIAL
Considera estas categorías:
- **ENFERMEDADES FÚNGICAS**: manchas circulares con halos, mildiu, oídio
- **ENFERMEDADES BACTERIANAS**: manchas angulares, exudados
- **ENFERMEDADES VIRALES**: mosaicos, deformaciones
- **PLAGAS**: perforaciones, presencia del insecto
- **DEFICIENCIAS NUTRICIONALES**: clorosis interveinal
- **DAÑOS ABIÓTICOS**: quemaduras uniformes, fitotoxicidad

### 3. NIVEL DE CONFIANZA
Indica siempre tu nivel de certeza:
- ALTA CONFIANZA (90-100%): Síntomas muy característicos
- CONFIANZA MODERADA (70-89%): Síntomas compatibles con 2-3 causas
- CONFIANZA BAJA (<70%): Síntomas ambiguos

### 4. ESTRUCTURA DE RESPUESTA
```
ANÁLISIS DE IMAGEN - Diagnóstico Fitosanitario

Observaciones:
- Cultivo identificado: [nombre]
- Órgano afectado: [hoja/tallo/fruto]
- Etapa fenológica: [plántula/vegetativa/etc.]

DIAGNÓSTICO PRINCIPAL:
[Nombre del problema] - Confianza: [] [%]

Descripción: [Explicación técnica pero accesible del problema]
Agente causal: [Hongo/Bacteria/Insecto/Deficiencia específica]

Información Adicional Necesaria (si confianza <80%):
- [Foto del envés de la hoja]
- [Foto de toda la planta]
```

## REGLAS CRÍTICAS
1. **SÉ HONESTO** sobre tu nivel de confianza
2. **NUNCA** diagnostiques con certeza si la imagen es de baja calidad
3. **SIEMPRE** menciona diagnósticos diferenciales si hay ambigüedad
4. Si la imagen no muestra el problema claramente, **PIDE MÁS FOTOS**
5. Usa **NOMBRES TÉCNICOS** pero explica en lenguaje accesible
6. Tu salida simplemente tiene que ser el diagnostico visual, no tienes que recomendar nada. SOLAMENTE entregar el diagnostico visual
"""

    # Medir tiempo de inicio
    start_time = time.time()
    
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
        image_base64 = state['image_base64']
    elif state.get("audio_base64"):
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
        
        # Medir tiempo de procesamiento
        processing_time = time.time() - start_time
        
        try:
            if image_base64:  # Solo registrar si hay imagen
                # Extraer diagnóstico y confianza
                diagnosis_data = extract_diagnosis_from_output(response_content)
                
                # Analizar condiciones de imagen
                image_conditions = analyze_image_conditions(image_base64)
                
                if diagnosis_data['diagnosis']:
                    # REGISTRAR DIAGNÓSTICO (KT2)
                    kpi_logger.log_diagnosis(
                        user_id=state.get("user_id"),
                        diagnosis=diagnosis_data['diagnosis'],
                        confidence=diagnosis_data['confidence'],
                        processing_time=processing_time,
                        image_size_kb=image_conditions['size_kb'],
                        image_conditions=image_conditions,
                        parcel_id=state.get("parcel_id") if state.get("parcel_id") else None,
                        ground_truth=None  # Se llenará después con validación manual
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