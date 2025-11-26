from typing import Optional, Tuple, Dict, List
from app.db.database import SessionLocal
from app.db import db_models
import os
import json
from datetime import datetime
from typing import List, Any
from app.utils.helper_KT1 import normalize_message_content

def _get_parcel_from_db(parcel_id: int) -> Optional[db_models.Parcel]:
    """Helper para obtener una parcela. Centraliza la lógica de consulta."""
    db = SessionLocal()
    try:
        return db.query(db_models.Parcel).filter(
            db_models.Parcel.id == parcel_id
        ).first()
    finally:
        db.close()


def _get_user_from_db(user_id: int) -> Optional[db_models.User]:
    """Helper para obtener un usuario."""
    db = SessionLocal()
    try:
        return db.query(db_models.User).filter(
            db_models.User.id == user_id
        ).first()
    finally:
        db.close()


def _extract_coordinates(location_string: str) -> Tuple[float, float]:
    """
    Extrae coordenadas de un string en formato "lat,lon".
    Raises: ValueError si el formato es inválido.
    """
    try:
        parts = location_string.split(',')
        if len(parts) != 2:
            raise ValueError(f"Formato inválido. Se esperaba 'lat,lon', recibido: '{location_string}'")
        
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        
        # Validar rangos razonables
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitud fuera de rango: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitud fuera de rango: {lon}")
        
        return lat, lon
    except (ValueError, IndexError) as e:
        raise ValueError(f"Error al extraer coordenadas de '{location_string}': {e}")


def _safe_json_response(success: bool, data: Dict = None, error: str = None) -> str:
    """Helper para generar respuestas JSON consistentes."""
    response = {"success": success}
    if data:
        response.update(data)
    if error:
        response["error"] = error
    return json.dumps(response, ensure_ascii=False)

def _generate_climate_recommendations(frost_days: int, heat_days: int, risk: str) -> List[str]:
    """Helper para generar recomendaciones basadas en riesgos climáticos."""
    recs = []
    
    if frost_days > 5:
        recs.append("Alto riesgo de heladas - implementar sistemas de protección (coberturas, calefacción)")
    elif frost_days > 0:
        recs.append("Riesgo moderado de heladas - monitorear pronósticos nocturnos")
    
    if heat_days > 10:
        recs.append("Estrés por calor frecuente - aumentar frecuencia de riego y considerar mallas sombra")
    elif heat_days > 0:
        recs.append("Días calurosos detectados - asegurar riego adecuado en horas tempranas")
    
    if not recs:
        recs.append("Condiciones climáticas dentro de rangos normales")
    
    return recs

def _interpret_ndvi(ndvi_value: float) -> Dict[str, str]:
    """Helper para interpretar valores NDVI."""
    if ndvi_value < 0.2:
        return {
            "status": "Muy pobre",
            "description": "Suelo desnudo o vegetación muy escasa",
            "color": "red",
            "recommendation": "Verificar estado del cultivo urgentemente. Evaluar replantación."
        }
    elif ndvi_value < 0.4:
        return {
            "status": "Baja",
            "description": "Vegetación bajo estrés o en etapa muy temprana",
            "color": "orange",
            "recommendation": "Evaluar: agua, nutrientes, plagas. Ajustar manejo."
        }
    elif ndvi_value < 0.6:
        return {
            "status": "Moderada",
            "description": "Crecimiento aceptable con potencial de mejora",
            "color": "yellow",
            "recommendation": "Optimizar fertilización y riego para maximizar rendimiento."
        }
    elif ndvi_value < 0.8:
        return {
            "status": "Buena",
            "description": "Vegetación saludable y en desarrollo activo",
            "color": "light_green",
            "recommendation": "Mantener prácticas actuales. Monitorear regularmente."
        }
    else:
        return {
            "status": "Excelente",
            "description": "Vegetación muy densa y en óptimas condiciones",
            "color": "dark_green",
            "recommendation": "Condiciones óptimas. Preparar para cosecha según fenología."
        }
        
def save_conversation_log(
    messages: List[Any], 
    user_id: int, 
    agent_history: List[str], 
    conversation_id: str, 
    final_response: str
) -> None:
    """
    Guarda el historial completo de la conversación (mensajes, tools, respuestas) 
    en un archivo JSON legible para depuración y análisis.
    """
    try:
        # 1. Preparar directorio
        log_dir = "logs/conversations"
        os.makedirs(log_dir, exist_ok=True)

        # 2. Estructura base del JSON
        log_data = {
            "meta": {
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "agents_involved": agent_history
            },
            "timeline": []
        }

        # 3. Procesar mensajes
        for msg in messages:
            # Manejo de contenido multimodal (listas) a string
            content_display = msg.content
            if isinstance(content_display, list):
                content_display = str(content_display)

            msg_data = {
                "type": msg.type, # human, ai, tool
                "content": content_display,
                "timestamp": datetime.now().isoformat() # Aproximado al momento de guardado
            }

            # Intentar capturar el nombre del remitente (ej: 'production', 'water')
            if hasattr(msg, "name") and msg.name:
                msg_data["sender"] = msg.name
            
            # Capturar llamadas a herramientas (Tool Calls)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                msg_data["tool_calls"] = [
                    {
                        "name": tc.get("name"), 
                        "args": tc.get("args"),
                        "id": tc.get("id")
                    } 
                    for tc in msg.tool_calls
                ]
            
            # Capturar errores de herramientas si existen
            if hasattr(msg, "tool_call_id"):
                msg_data["is_tool_result"] = True
                msg_data["tool_call_id"] = msg.tool_call_id

            log_data["timeline"].append(msg_data)

        # 4. Agregar la respuesta final del supervisor
        log_data["timeline"].append({
            "type": "ai",
            "sender": "supervisor_final",
            "content": final_response,
            "timestamp": datetime.now().isoformat()
        })

        # 5. Escribir archivo
        filename = f"VAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{conversation_id[:8]}.json"
        filepath = os.path.join(log_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
            
        print(f"-- 📂 Historial JSON guardado: {filename} --")

    except Exception as e:
        print(f"-- ⚠️ Error guardando log JSON: {str(e)} --")
        
def normalize_agent_output(output):
    """
    Convierte la salida compleja de los agentes de Google/LangChain 
    en un único string limpio.
    """
    # Caso 1: Ya es un string simple
    if isinstance(output, str):
        return output
        
    # Caso 2: Es una lista (común en Gemini)
    if isinstance(output, list):
        full_text = []
        for item in output:
            if isinstance(item, str):
                # Si es un string suelto dentro de la lista
                full_text.append(item)
            elif isinstance(item, dict):
                # Si es un diccionario (ej: {'type': 'text', 'text': '...'})
                full_text.append(item.get('text', ''))
        
        # Unir todo el texto
        return "".join(full_text)
    
    # Caso 3: Fallback (convertir lo que sea a string)
    return str(output)

def extract_user_query(messages: list) -> str:
    """Extrae la consulta original del usuario (primer HumanMessage)"""
    for msg in messages:
        if hasattr(msg, 'type') and msg.type == "human":
            return normalize_message_content(msg.content)
    return ""

def get_agent_responses(messages: list) -> list:
    """Extrae todas las respuestas de los agentes (excluyendo supervisor)"""
    agent_responses = []
    for msg in messages:
        if hasattr(msg, 'name') and msg.name and msg.name != "supervisor":
            agent_responses.append({
                "agent": msg.name,
                "content": normalize_message_content(msg.content)
            })
    return agent_responses

def build_synthesis_context(messages: list) -> str:
    """Construye un resumen del flujo de la conversación actual"""
    user_query = extract_user_query(messages)
    agent_responses = get_agent_responses(messages)
    
    if not agent_responses:
        return f"Consulta del usuario: {user_query}\n(No hay respuestas de agentes aún)"
    
    context = f"CONSULTA ORIGINAL DEL USUARIO:\n{user_query}\n\n"
    context += "RESPUESTAS DE AGENTES ESPECIALIZADOS:\n"
    
    for i, resp in enumerate(agent_responses, 1):
        context += f"\n{i}. Agente {resp['agent'].upper()}:\n"
        context += f"{resp['content'][:500]}...\n" if len(resp['content']) > 500 else f"{resp['content']}\n"
    
    return context