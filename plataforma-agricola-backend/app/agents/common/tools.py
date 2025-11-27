from typing import Optional
from langchain.tools import tool

from app.db.session import SessionLocal
from app.db.models.parcel import Parcel
from app.db.models.user import User 
from app.db.models.kpi import KPIMetric

from app.core.config import DATOS_GOV_API_KEY
from app.utils.helper import _safe_json_response


from datetime import datetime
import requests
import json

# ============================================================================
# HERRAMIENTAS DE BASE DE DATOS
# ============================================================================

@tool
def get_parcel_details(parcel_id: int) -> str:
    """
    Obtiene detalles COMPLETOS de una parcela incluyendo información del cultivo,
    suelo, riego y estado actual de salud.
    """
    db = SessionLocal()
    try:
        parcel = db.query(Parcel).filter(
            Parcel.id == parcel_id
        ).first()

        if not parcel:
            return _safe_json_response(False, error=f"Parcela {parcel_id} no encontrada")

        # Calcular días desde siembra si existe
        days_since_planting = None
        if parcel.planting_date:
            days_since_planting = (datetime.now() - parcel.planting_date).days

        # Información completa estructurada
        parcel_data = {
            # Información básica
            "parcel_id": parcel.id,
            "name": parcel.name,
            "coordinates": parcel.location,
            "area_hectares": parcel.area,
            "area_m2": parcel.area * 10000,
            "geojson": parcel.geometry,
            "owner_id": parcel.owner_id,

            # Información del cultivo
            "crop_info": {
                "crop_type": parcel.crop_type,
                "development_stage": parcel.development_stage,
                "planting_date": parcel.planting_date.isoformat() if parcel.planting_date else None,
                "days_since_planting": days_since_planting
            },

            # Características del suelo
            "soil_info": {
                "soil_type": parcel.soil_type if parcel.soil_type else None,
                "soil_ph": parcel.soil_ph if parcel.soil_ph else None
            },

            # Sistema de riego
            "irrigation_info": {
                "irrigation_type": parcel.irrigation_type if parcel.irrigation_type else None
            },

            # Estado actual de salud
            "health_info": {
                "health_status": parcel.health_status,
                "current_issues": parcel.current_issues
            }
        }

        return _safe_json_response(True, parcel_data)

    except Exception as e:
        return _safe_json_response(False, error=f"Error al obtener detalles: {str(e)}")
    finally:
        db.close()

@tool
def update_parcel_info(
    parcel_id: int,
    crop_type: Optional[str] = None,
    development_stage: Optional[str] = None,
    soil_type: Optional[str] = None,
    soil_ph: Optional[float] = None,
    irrigation_type: Optional[str] = None,
    health_status: Optional[str] = None,
    current_issues: Optional[str] = None
) -> str:
    """
    Actualiza información de la parcela. Los agentes pueden usar esto para:
    - Actualizar el estado de salud detectado por análisis
    - Registrar problemas identificados
    - Actualizar la etapa de desarrollo del cultivo
    - Registrar observaciones importantes
    
    Solo actualiza los campos que se proporcionen (los demás quedan sin cambios).
    """
    db = SessionLocal()
    try:
        parcel = db.query(Parcel).filter(
            Parcel.id == parcel_id
        ).first()
        
        if not parcel:
            return _safe_json_response(False, error=f"Parcela {parcel_id} no encontrada")
        
        # Actualizar solo los campos proporcionados
        updated_fields = []
        
        if crop_type is not None:
            parcel.crop_type = crop_type
            updated_fields.append("crop_type")
            
        if development_stage is not None:
            parcel.development_stage = development_stage
            updated_fields.append("development_stage")
            
        if soil_type is not None:
            parcel.soil_type = soil_type
            updated_fields.append("soil_type")
            
        if soil_ph is not None:
            if 0 <= soil_ph <= 14:
                parcel.soil_ph = soil_ph
                updated_fields.append("soil_ph")
            else:
                return _safe_json_response(False, error="pH debe estar entre 0 y 14")
        
        if irrigation_type is not None:
            parcel.irrigation_type = irrigation_type
            updated_fields.append("irrigation_type")
            
        if health_status is not None:
            parcel.health_status = health_status
            updated_fields.append("health_status")
            
        if current_issues is not None:
            # Si ya hay issues, agregarlos con timestamp
            if parcel.current_issues:
                timestamp = datetime.now().strftime("%Y-%m-%d")
                parcel.current_issues += f"\n[{timestamp}] {current_issues}"
            else:
                parcel.current_issues = current_issues
            updated_fields.append("current_issues")
        
        if not updated_fields:
            return _safe_json_response(False, error="No se proporcionaron campos para actualizar")
        
        db.commit()
        db.refresh(parcel)
        
        return _safe_json_response(True, {
            "parcel_id": parcel_id,
            "parcel_name": parcel.name,
            "updated_fields": updated_fields,
            "message": f"Parcela actualizada exitosamente. Campos actualizados: {', '.join(updated_fields)}"
        })
        
    except Exception as e:
        db.rollback()
        return _safe_json_response(False, error=f"Error al actualizar: {str(e)}")
    finally:
        db.close()

@tool
def list_user_parcels(user_id: int) -> str:
    """
    Lista todas las parcelas del usuario con su información de cultivo y estado actual.
    Útil para dar una visión general de todas las parcelas del agricultor.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.id == user_id
        ).first()
        
        if not user:
            return _safe_json_response(False, error=f"Usuario {user_id} no encontrado")
        
        if not user.parcels:
            return _safe_json_response(True, {
                "user_id": user_id,
                "email": user.email,
                "parcels": [],
                "total_parcels": 0,
                "message": "Este usuario no tiene parcelas registradas"
            })
        
        parcels_data = []
        for p in user.parcels:
            # Calcular días desde siembra si existe
            days_since_planting = None
            if p.planting_date:
                days_since_planting = (datetime.now() - p.planting_date).days
            
            parcel_info = {
                "id": p.id,
                "name": p.name,
                "location": p.location,
                "area_hectares": p.area,
                
                # Información del cultivo
                "crop_type": p.crop_type,
                "development_stage": p.development_stage,
                "days_since_planting": days_since_planting,
                
                # Estado actual
                "health_status": p.health_status,
                "has_current_issues": bool(p.current_issues),
                "current_issues_summary": p.current_issues[:100] + "..." if p.current_issues and len(p.current_issues) > 100 else p.current_issues
            }
            parcels_data.append(parcel_info)
        
        return _safe_json_response(True, {
            "user_id": user_id,
            "email": user.email,
            "total_parcels": len(parcels_data),
            "parcels": parcels_data,
            "summary": f"El usuario tiene {len(parcels_data)} parcela(s) registrada(s)"
        })
        
    except Exception as e:
        return _safe_json_response(False, error=f"Error al listar parcelas: {str(e)}")
    finally:
        db.close()


@tool
def get_parcel_geojson(parcel_id: int) -> Optional[str]:
    """Consulta la DB y retorna el string GeoJSON de la parcela."""
    db = SessionLocal()
    try:
        parcel = db.query(Parcel).filter(
            Parcel.id == parcel_id).first()
        if parcel:
            return parcel.geometry
        return f'No se encontró ninguna parcela con el ID {parcel_id}.'
    finally:
        db.close()


@tool
def get_parcel_location_by_id(parcel_id: int) -> str:
    """
    Útil para obtener la latitud y longitud de una parcela específica cuando se conoce su ID.
    Devuelve un string JSON con 'latitude' y 'longitude'.
    """
    db = SessionLocal()
    try:
        parcel = db.query(Parcel).filter(
            Parcel.id == parcel_id).first()
        if not parcel:
            return f'No se encontró ninguna parcela con el ID {parcel_id}.'

        # Asumiendo que la ubicación es un campo JSON o se puede parsear a coordenadas
        # Si 'location' es un string de texto, esto debe ser ajustado a cómo se guardan las coordenadas.
        # Por simplicidad, asumimos que podemos obtener Lat/Lon.
        # Si la DB no guarda Lat/Lon directamente, se debe usar la geometría (GeoJSON) para calcular el centroide.

        # **NOTA:** Si la ubicación es un string de texto (ej. 'Bogotá, CO'), se debe usar una API de geocodificación.
        # Si la DB tiene campos lat/lon, úsalos. Aquí asumo que la DB tiene `latitude` y `longitude`.
        if hasattr(parcel, 'latitude') and hasattr(parcel, 'longitude'):
            return json.dumps({"latitude": parcel.latitude, "longitude": parcel.longitude})
        else:
            # Si no hay campos directos, se devuelve la ubicación textual para el agente de clima
            return json.dumps({"location_name": parcel.location})

    finally:
        db.close()

@tool
def get_kpi_summary(parcel_id: int, kpi_name: str) -> str:
    """
    Obtiene resumen y análisis de evolución de un KPI específico.
    Ejemplo: kpi_name='SOIL_HEALTH_NDVI'
    """
    db = SessionLocal()
    try:
        metrics = db.query(KPIMetric).filter(
            KPIMetric.parcel_id == parcel_id,
            KPIMetric.kpi_name == kpi_name
        ).order_by(KPIMetric.timestamp.asc()).all()

        if not metrics:
            return _safe_json_response(False,
                                       error=f"No hay datos para KPI '{kpi_name}' en parcela {parcel_id}")

        latest = metrics[-1]
        initial = metrics[0]

        result = {
            "parcel_id": parcel_id,
            "kpi_name": kpi_name,
            "total_records": len(metrics),
            "latest_value": round(latest.value, 4),
            "latest_date": latest.timestamp.strftime('%Y-%m-%d'),
            "first_value": round(initial.value, 4),
            "first_date": initial.timestamp.strftime('%Y-%m-%d')
        }

        if len(metrics) > 1:
            change = latest.value - initial.value
            percentage_change = (change / initial.value) * \
                100 if initial.value != 0 else 0

            if abs(percentage_change) < 1:
                trend = "estable"
            elif change > 0:
                trend = "mejora"
            else:
                trend = "declive"

            result.update({
                "change": round(change, 4),
                "percentage_change": round(percentage_change, 2),
                "trend": trend
            })

        return _safe_json_response(True, result)

    except Exception as e:
        return _safe_json_response(False, error=f"Error al obtener KPI: {str(e)}")
    finally:
        db.close()


@tool
def lookup_parcel_by_name(name_query: str, user_id: int) -> str:
    """
    Busca una parcela por su nombre (búsqueda parcial, insensible a mayúsculas).
    Útil cuando el usuario menciona el nombre pero no el ID.
    """
    db = SessionLocal()
    try:
        parcel = db.query(Parcel).filter(
            Parcel.owner_id == user_id,
            Parcel.name.ilike(f"%{name_query}%")
        ).first()

        if not parcel:
            return _safe_json_response(False,
                                       error=f"No se encontró parcela con nombre '{name_query}' para usuario {user_id}")

        return _safe_json_response(True, {
            "parcel_id": parcel.id,
            "name": parcel.name,
            "location": parcel.location,
            "area_hectares": parcel.area,
            "area_m2": parcel.area * 10000
        })
    except Exception as e:
        return _safe_json_response(False, error=f"Error en búsqueda: {str(e)}")
    finally:
        db.close()

# ============================================================================
# HERRAMIENTAS DE DATOS EXTERNOS
# ============================================================================

@tool
def get_data_agromy(departamento: str, producto: str, limite: int = 100) -> str:
    """
    Recupera datos agrícolas de la API del gobierno colombiano.

    Parámetros:
    - departamento: Nombre del departamento (ej. 'Arauca', 'Cundinamarca')
    - producto: Nombre del producto (ej. 'Maíz', 'Café')
    - limite: Máximo de registros (por defecto 100)
    """
    if limite > 1000:
        return _safe_json_response(False, error="Límite máximo: 1000 registros")

    where_clause = f"departamento='{departamento}' AND producto='{producto}'"

    params = {
        "$where": where_clause,
        "$limit": limite,
        "$select": "municipio,fecha,valor,unidad_de_medida,rendimiento"
    }

    headers = {
        "X-App-Token": DATOS_GOV_API_KEY,
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            "https://www.datos.gov.co/resource/vgsd-2dyp.json",
            params=params,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            return _safe_json_response(False,
                                       error=f"No se encontraron datos para {producto} en {departamento}",
                                       data={
                                           "suggestion": "Verificar nombres de departamento y producto"
                                       })

        # Procesar y resumir datos
        total_records = len(data)
        avg_value = sum(float(d.get('valor', 0)) for d in data if d.get(
            'valor')) / total_records if total_records > 0 else 0

        return _safe_json_response(True, {
            "departamento": departamento,
            "producto": producto,
            "total_records": total_records,
            "average_value": round(avg_value, 2),
            "unit": data[0].get('unidad_de_medida', 'N/A') if data else 'N/A',
            "municipalities": list(set(d.get('municipio', 'N/A') for d in data)),
            "data_preview": data[:5]  # Primeros 5 registros
        })

    except requests.exceptions.Timeout:
        return _safe_json_response(False, error="Timeout al consultar datos.gov.co")
    except requests.exceptions.RequestException as e:
        return _safe_json_response(False, error=f"Error de API: {str(e)}")
    except json.JSONDecodeError:
        return _safe_json_response(False, error="Respuesta inválida de la API")
    except Exception as e:
        return _safe_json_response(False, error=f"Error inesperado: {str(e)}")