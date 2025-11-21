from typing import Optional, Tuple, Dict, List
from app.db.database import SessionLocal
from app.db import db_models
import json

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