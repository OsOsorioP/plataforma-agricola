from typing import Optional
from langchain.tools import tool
from langchain_classic.tools.retriever import create_retriever_tool

from app.services.rag_service import get_retriever
from app.db.database import SessionLocal
from app.db import db_models
from app.core.config import OPENWEATHER_API_KEY, DATOS_GOV_API_KEY, DATOS_GOV_PASSWORD, DATOS_GOV_USER
from app.utils.helper import (_extract_coordinates, _safe_json_response,
                              _generate_climate_recommendations, _interpret_ndvi)
from app.services.sh_service import (
    get_ndvi,
    get_nbr,
    get_bsi,
    get_evi,
    get_fapar,
    get_gci,
    get_lai,
    get_msavi,
    get_ndwi,
    get_savi,
)

from datetime import datetime, timedelta, date
import requests
import json

# ============================================================================
# HERRAMIENTAS DE BASE DE DATOS (CORREGIDAS)
# ============================================================================


@tool
def get_parcel_details(parcel_id: int) -> str:
    """
    Obtiene detalles completos de una parcela específica.
    Devuelve: nombre, coordenadas, área (hectáreas y m²), GeoJSON.
    """
    db = SessionLocal()
    try:
        parcel = db.query(db_models.Parcel).filter(
            db_models.Parcel.id == parcel_id
        ).first()

        if not parcel:
            return _safe_json_response(False, error=f"Parcela {parcel_id} no encontrada")

        return _safe_json_response(True, {
            "parcel_id": parcel.id,
            "name": parcel.name,
            "coordinates": parcel.location,
            "area_hectares": parcel.area,
            "area_m2": parcel.area * 10000,
            "geojson": parcel.geometry,
            "owner_id": parcel.owner_id
        })
    except Exception as e:
        return _safe_json_response(False, error=f"Error al obtener detalles: {str(e)}")
    finally:
        db.close()


@tool
def list_user_parcels(user_id: int) -> str:
    """
    Lista todas las parcelas de un usuario.
    Devuelve: lista con IDs, nombres, ubicaciones y áreas.
    """
    db = SessionLocal()
    try:
        user = db.query(db_models.User).filter(
            db_models.User.id == user_id
        ).first()

        if not user:
            return _safe_json_response(False, error=f"Usuario {user_id} no encontrado")

        if not user.parcels:
            return _safe_json_response(True, {
                "user_id": user_id,
                "email": user.email,
                "parcels": [],
                "message": "Este usuario no tiene parcelas registradas"
            })

        parcels_data = [
            {
                "id": p.id,
                "name": p.name,
                "location": p.location,
                "area_hectares": p.area
            }
            for p in user.parcels
        ]

        return _safe_json_response(True, {
            "user_id": user_id,
            "email": user.email,
            "total_parcels": len(parcels_data),
            "parcels": parcels_data
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
        parcel = db.query(db_models.Parcel).filter(
            db_models.Parcel.id == parcel_id).first()
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
        parcel = db.query(db_models.Parcel).filter(
            db_models.Parcel.id == parcel_id).first()
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
def save_recommendation(parcel_id: int, agent_source: str, recommendation_text: str) -> str:
    """
    Guarda una recomendación generada por un agente en la base de datos.
    Úsala SIEMPRE que des un consejo accionable específico.
    """
    db = SessionLocal()
    try:
        parcel = db.query(db_models.Parcel).filter(
            db_models.Parcel.id == parcel_id
        ).first()

        if not parcel:
            return _safe_json_response(False, error=f"Parcela {parcel_id} no encontrada")

        # Validar que agent_source no esté vacío
        if not agent_source or not agent_source.strip():
            return _safe_json_response(False, error="El nombre del agente es requerido")

        new_recommendation = db_models.Recommendation(
            user_id=parcel.owner_id,
            parcel_id=parcel_id,
            agent_source=agent_source.strip(),
            recommendation_text=recommendation_text.strip(),
        )

        db.add(new_recommendation)
        db.commit()
        db.refresh(new_recommendation)

        return _safe_json_response(True, {
            "recommendation_id": new_recommendation.id,
            "parcel_id": parcel_id,
            "agent_source": agent_source,
            "message": "Recomendación guardada exitosamente"
        })

    except Exception as e:
        db.rollback()
        return _safe_json_response(False, error=f"Error al guardar: {str(e)}")
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
        metrics = db.query(db_models.KPIMetric).filter(
            db_models.KPIMetric.parcel_id == parcel_id,
            db_models.KPIMetric.kpi_name == kpi_name
        ).order_by(db_models.KPIMetric.timestamp.asc()).all()

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
        parcel = db.query(db_models.Parcel).filter(
            db_models.Parcel.owner_id == user_id,
            db_models.Parcel.name.ilike(f"%{name_query}%")
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
# HERRAMIENTAS DE CLIMA Y PRECIPITACIÓN (CORREGIDAS)
# ============================================================================
@tool
def get_weather_forecast(location: str) -> str:
    """
    Obtiene pronóstico del tiempo actual.
    Formatos: '4.65,-74.05' (coordenadas) o 'Bogota,CO' (ciudad).
    """
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "es"
    }

    try:
        # Intentar parsear como coordenadas
        if "," in location:
            try:
                lat, lon = _extract_coordinates(location)
                params["lat"] = lat
                params["lon"] = lon
            except ValueError:
                # Si falla, es nombre de ciudad con país (ej: "Bogota,CO")
                params["q"] = location
        else:
            params["q"] = location

        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return _safe_json_response(True, {
            "location": data.get('name', 'Ubicación'),
            "coordinates": f"{data['coord']['lat']},{data['coord']['lon']}",
            "condition": data['weather'][0]['description'],
            "temperature_c": data['main']['temp'],
            "feels_like_c": data['main']['feels_like'],
            "humidity_percent": data['main']['humidity'],
            "wind_speed_ms": data['wind']['speed'],
            "pressure_hpa": data['main']['pressure'],
            "cloudiness_percent": data['clouds']['all'],
            "summary": (
                f"{data['weather'][0]['description'].capitalize()}, "
                f"{data['main']['temp']}°C (sensación {data['main']['feels_like']}°C), "
                f"humedad {data['main']['humidity']}%"
            )
        })

    except requests.exceptions.Timeout:
        return _safe_json_response(False, error="Timeout al conectar con API de clima")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return _safe_json_response(False, error="API Key inválida para OpenWeather")
        elif e.response.status_code == 404:
            return _safe_json_response(False, error=f"Ubicación '{location}' no encontrada")
        return _safe_json_response(False, error=f"Error HTTP: {e}")
    except Exception as e:
        return _safe_json_response(False, error=f"Error inesperado: {str(e)}")


@tool
def get_precipitation_data(parcel_id: int, days_back: int = 7) -> str:
    """
    Obtiene datos históricos de precipitación para una parcela.
    Parámetros:
    - parcel_id: ID de la parcela
    - days_back: Días hacia atrás (por defecto 7, máximo 16 con API gratuita)
    """
    if days_back > 16:
        return _safe_json_response(False,
                                   error="La API gratuita solo permite hasta 16 días de historial")

    db = SessionLocal()
    try:
        parcel = db.query(db_models.Parcel).filter(
            db_models.Parcel.id == parcel_id
        ).first()

        if not parcel:
            return _safe_json_response(False, error=f"Parcela {parcel_id} no encontrada")

        try:
            lat, lon = _extract_coordinates(parcel.location)
        except ValueError as e:
            return _safe_json_response(False, error=str(e))

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "precipitation_sum,precipitation_hours",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "timezone": "America/Bogota"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        precipitation_data = data['daily']['precipitation_sum']
        precipitation_hours = data['daily'].get(
            'precipitation_hours', [0] * len(precipitation_data))
        dates = data['daily']['time']

        total_precipitation = sum(precipitation_data)
        total_hours = sum(precipitation_hours)

        # Análisis de suficiencia (umbral: 25mm/semana para cultivos)
        days_period = len(precipitation_data)
        weekly_equivalent = (total_precipitation /
                             days_period) * 7 if days_period > 0 else 0

        if weekly_equivalent >= 25:
            interpretation = "Suficiente"
            irrigation_advice = "No se requiere riego suplementario"
        elif weekly_equivalent >= 15:
            interpretation = "Moderado"
            irrigation_advice = "Monitorear humedad del suelo, considerar riego ligero"
        else:
            interpretation = "Insuficiente"
            irrigation_advice = "Riego suplementario recomendado"

        daily_details = [
            {
                "date": date,
                "precipitation_mm": round(precip, 1),
                "hours": int(hours)
            }
            for date, precip, hours in zip(dates, precipitation_data, precipitation_hours)
        ]

        return _safe_json_response(True, {
            "parcel_id": parcel_id,
            "period": f"{start_date} a {end_date}",
            "days_analyzed": days_period,
            "total_precipitation_mm": round(total_precipitation, 2),
            "total_precipitation_hours": total_hours,
            "daily_average_mm": round(total_precipitation / days_period, 2) if days_period > 0 else 0,
            "weekly_equivalent_mm": round(weekly_equivalent, 2),
            "interpretation": interpretation,
            "irrigation_advice": irrigation_advice,
            "daily_data": daily_details
        })

    except requests.exceptions.RequestException as e:
        return _safe_json_response(False, error=f"Error al consultar API: {str(e)}")
    except Exception as e:
        return _safe_json_response(False, error=f"Error inesperado: {str(e)}")
    finally:
        db.close()


@tool
def get_historical_weather_summary(latitude: float, longitude: float, days_back: int = 30) -> str:
    """
    Obtiene resumen de datos meteorológicos históricos.
    Analiza riesgos de heladas y estrés por calor.
    """
    if days_back > 365:
        return _safe_json_response(False, error="Máximo 365 días de historial")

    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)
                      ).strftime('%Y-%m-%d')

        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto"
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        min_temps = [t for t in data['daily']
                     ['temperature_2m_min'] if t is not None]
        max_temps = [t for t in data['daily']
                     ['temperature_2m_max'] if t is not None]
        precip = [p for p in data['daily']
                  ['precipitation_sum'] if p is not None]

        if not min_temps or not max_temps:
            return _safe_json_response(False, error="No hay datos disponibles para el período")

        # Análisis de riesgos
        frost_days = sum(1 for t in min_temps if t <= 2)
        near_frost_days = sum(1 for t in min_temps if 2 < t <= 5)
        heat_stress_days = sum(1 for t in max_temps if t >= 35)
        high_heat_days = sum(1 for t in max_temps if 30 <= t < 35)

        avg_min = sum(min_temps) / len(min_temps)
        avg_max = sum(max_temps) / len(max_temps)
        total_precip = sum(precip)

        # Clasificación de riesgo
        risk_level = "Bajo"
        if frost_days > 5 or heat_stress_days > 10:
            risk_level = "Alto"
        elif frost_days > 0 or heat_stress_days > 0:
            risk_level = "Moderado"

        return _safe_json_response(True, {
            "location": f"{latitude},{longitude}",
            "period": f"{start_date} a {end_date}",
            "days_analyzed": days_back,
            "temperature": {
                "average_min_c": round(avg_min, 1),
                "average_max_c": round(avg_max, 1),
                "absolute_min_c": round(min(min_temps), 1),
                "absolute_max_c": round(max(max_temps), 1)
            },
            "risks": {
                "frost_days": frost_days,
                "near_frost_days": near_frost_days,
                "heat_stress_days": heat_stress_days,
                "high_heat_days": high_heat_days,
                "risk_level": risk_level
            },
            "precipitation": {
                "total_mm": round(total_precip, 2),
                "daily_average_mm": round(total_precip / days_back, 2)
            },
            "recommendations": _generate_climate_recommendations(
                frost_days, heat_stress_days, risk_level
            )
        })

    except Exception as e:
        return _safe_json_response(False, error=f"Error al analizar clima histórico: {str(e)}")


# ============================================================================
# HERRAMIENTAS DE CÁLCULO HÍDRICO (CORREGIDAS)
# ============================================================================
@tool
def calculate_water_requirements(parcel_id: int, crop_type: str, growth_stage: str) -> str:
    """
    Calcula requerimientos hídricos usando método FAO-56 (simplificado).

    Parámetros:
    - parcel_id: ID de la parcela
    - crop_type: 'maiz', 'cafe', 'arroz', 'papa', 'tomate', 'platano'
    - growth_stage: 'inicial', 'desarrollo', 'maduracion', 'cosecha'
    """
    # Coeficientes Kc por cultivo y etapa (FAO-56)
    kc_values = {
        'maiz': {'inicial': 0.3, 'desarrollo': 0.7, 'maduracion': 1.2, 'cosecha': 0.6},
        'cafe': {'inicial': 0.9, 'desarrollo': 0.95, 'maduracion': 0.95, 'cosecha': 0.95},
        'arroz': {'inicial': 1.05, 'desarrollo': 1.1, 'maduracion': 1.2, 'cosecha': 0.9},
        'papa': {'inicial': 0.5, 'desarrollo': 0.75, 'maduracion': 1.15, 'cosecha': 0.75},
        'tomate': {'inicial': 0.6, 'desarrollo': 1.15, 'maduracion': 1.15, 'cosecha': 0.8},
        'platano': {'inicial': 0.5, 'desarrollo': 1.1, 'maduracion': 1.2, 'cosecha': 1.1},
    }

    db = SessionLocal()
    try:
        parcel = db.query(db_models.Parcel).filter(
            db_models.Parcel.id == parcel_id
        ).first()

        if not parcel:
            return _safe_json_response(False, error=f"Parcela {parcel_id} no encontrada")

        crop_lower = crop_type.lower()
        stage_lower = growth_stage.lower()

        if crop_lower not in kc_values:
            return _safe_json_response(False,
                                       error=f"Cultivo '{crop_type}' no reconocido",
                                       data={"available_crops": list(kc_values.keys())})

        if stage_lower not in kc_values[crop_lower]:
            return _safe_json_response(False,
                                       error=f"Etapa '{growth_stage}' inválida",
                                       data={"valid_stages": list(kc_values[crop_lower].keys())})

        kc = kc_values[crop_lower][stage_lower]

        # ETo promedio para Colombia (puede variar por región)
        # Rango típico: 3-5 mm/día
        eto_estimated = 4.0  # mm/día

        # ETc = ETo × Kc
        etc = eto_estimated * kc

        # Conversión a litros (1 mm sobre 1 m² = 1 litro)
        area_m2 = parcel.area * 10000
        water_liters_day = etc * area_m2

        # Eficiencia de riego típica (85% para goteo, 60% para aspersión)
        efficiency = 0.75  # Asumimos valor intermedio
        water_needed_with_losses = water_liters_day / efficiency

        return _safe_json_response(True, {
            "parcel_id": parcel_id,
            "parcel_name": parcel.name,
            "area_hectares": parcel.area,
            "area_m2": area_m2,
            "crop_type": crop_type,
            "growth_stage": growth_stage,
            "kc_coefficient": kc,
            "eto_mm_day": eto_estimated,
            "etc_mm_day": round(etc, 2),
            "water_requirements": {
                "ideal_liters_per_day": round(water_liters_day, 2),
                "with_losses_liters_per_day": round(water_needed_with_losses, 2),
                "per_week_liters": round(water_liters_day * 7, 2),
                "per_month_liters": round(water_liters_day * 30, 2)
            },
            "efficiency_assumed": f"{efficiency * 100}%",
            "recommendation": (
                f"Aplicar {int(water_liters_day)} litros/día ideales, "
                f"o {int(water_needed_with_losses)} litros/día considerando pérdidas del sistema. "
                f"Total semanal: {int(water_liters_day * 7)} litros."
            )
        })

    except Exception as e:
        return _safe_json_response(False, error=f"Error en cálculo: {str(e)}")
    finally:
        db.close()


@tool
def estimate_soil_moisture_deficit(parcel_id: int, crop_type: str, days_since_rain: int) -> str:
    """
    Estima déficit de humedad del suelo (útil sin sensores).

    Parámetros:
    - parcel_id: ID de la parcela
    - crop_type: Tipo de cultivo
    - days_since_rain: Días desde última lluvia significativa (>5mm)
    """
    if days_since_rain < 0:
        return _safe_json_response(False, error="Los días no pueden ser negativos")

    # Tasas de depleción de agua del suelo por cultivo (mm/día)
    # Basado en ETc promedio y tipo de sistema radicular
    depletion_rates = {
        'maiz': 5.0,
        'cafe': 3.5,
        'arroz': 7.0,
        'papa': 4.5,
        'tomate': 5.5,
        'platano': 6.0,
        'default': 4.0
    }

    db = SessionLocal()
    try:
        parcel = db.query(db_models.Parcel).filter(
            db_models.Parcel.id == parcel_id
        ).first()

        if not parcel:
            return _safe_json_response(False, error=f"Parcela {parcel_id} no encontrada")

        rate = depletion_rates.get(
            crop_type.lower(), depletion_rates['default'])
        estimated_deficit = rate * days_since_rain

        # Clasificación de estrés hídrico
        # Capacidad de campo típica: 100-150mm para primeros 50cm de suelo
        if estimated_deficit < 20:
            stress = "Bajo"
            urgency = "baja"
            action = "Continuar monitoreo regular"
            days_until_critical = int((40 - estimated_deficit) / rate)
        elif estimated_deficit < 40:
            stress = "Moderado"
            urgency = "media"
            action = "Planificar riego en 1-2 días"
            days_until_critical = int((60 - estimated_deficit) / rate)
        elif estimated_deficit < 60:
            stress = "Alto"
            urgency = "alta"
            action = "Riego recomendado en las próximas 24 horas"
            days_until_critical = 1
        else:
            stress = "Crítico"
            urgency = "crítica"
            action = "RIEGO URGENTE REQUERIDO - riesgo de pérdidas"
            days_until_critical = 0

        return _safe_json_response(True, {
            "parcel_id": parcel_id,
            "parcel_name": parcel.name,
            "crop_type": crop_type,
            "days_since_rain": days_since_rain,
            "depletion_rate_mm_day": rate,
            "estimated_deficit_mm": round(estimated_deficit, 1),
            "stress_level": stress,
            "urgency": urgency,
            "days_until_critical": days_until_critical,
            "recommended_action": action
        })

    except Exception as e:
        return _safe_json_response(False, error=f"Error en estimación: {str(e)}")
    finally:
        db.close()


# ============================================================================
# HERRAMIENTAS DE ANÁLISIS GEOESPACIAL (CORREGIDAS)
# ============================================================================
@tool
def get_parcel_health_indices(parcel_id: int, start_date: str, end_date: str) -> str:
    """
    Obtiene índices de salud vegetal (NDVI) mediante datos satelitales.

    Parámetros:
    - parcel_id: ID de la parcela
    - start_date: Fecha inicio 'YYYY-MM-DD'
    - end_date: Fecha fin 'YYYY-MM-DD'
    """
    db = SessionLocal()
    try:
        # Validar formato de fechas
        try:
            date_from = date.fromisoformat(start_date)
            date_to = date.fromisoformat(end_date)
        except ValueError:
            return _safe_json_response(False,
                                       error="Fechas inválidas. Usar formato ISO: YYYY-MM-DD",
                                       data={"example": "2024-01-15"})

        # Validar rango temporal
        if date_from > date_to:
            return _safe_json_response(False,
                                       error="La fecha de inicio debe ser anterior a la fecha de fin")

        days_diff = (date_to - date_from).days
        if days_diff > 365:
            return _safe_json_response(False,
                                       error="El rango máximo es 365 días",
                                       data={"days_requested": days_diff})

        # Obtener parcela
        parcel = db.query(db_models.Parcel).filter(
            db_models.Parcel.id == parcel_id
        ).first()

        if not parcel:
            return _safe_json_response(False, error=f"Parcela {parcel_id} no encontrada")

        if not parcel.geometry:
            return _safe_json_response(False,
                                       error=f"La parcela {parcel_id} no tiene geometría definida")

        # Calcular NDVI
        ndvi_results = get_ndvi(parcel.geometry, start_date, end_date)
        ndwi_results = get_ndwi()
        evi_results = get_evi()
        savi_results = get_savi()
        msavi_results = get_msavi()
        bsi_results = get_bsi()
        nbr_results = get_nbr()
        gci_results = get_gci()
        lai_results = get_lai()
        fapar_results = get_fapar()

        return _safe_json_response(True, {
            "parcel_id": parcel_id,
            "parcel_name": parcel.name,
            "date_range": {
                "start": start_date,
                "end": end_date,
                "days": days_diff
            },
            "NDVI_stats": ndvi_results[1],
            "NDWI_stats": ndwi_results[1],
            "EVI_stats": evi_results[1],
            "SAVI_stats": savi_results[1],
            "MSAVI_stats": msavi_results[1],
            "BSI_stats": bsi_results[1],
            "NBR_stats": nbr_results[1],
            "GCI_stats": gci_results[1],
            "LAI_stats": lai_results[1],
            "FAPAR_stats": fapar_results[1]
        })

    except Exception as e:
        return _safe_json_response(False, error=f"Error al calcular índices: {str(e)}")
    finally:
        db.close()


# ============================================================================
# HERRAMIENTAS DE DATOS EXTERNOS (CORREGIDAS)
# ============================================================================

@tool
def get_market_price(product_name: str) -> str:
    """
    Obtiene precio de mercado actual y tendencia para un producto agrícola.
    Nota: Esta es una API mock local. En producción, usar API real de precios.
    """
    try:
        response = requests.get(
            f"http://127.0.0.1:8000/mock/market-prices",
            params={"product_name": product_name},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        return _safe_json_response(True, {
            "product": product_name,
            "price_usd_kg": data['price_usd_kg'],
            "trend": data['trend'],
            "last_update": data.get('last_update', 'N/A'),
            "summary": f"${data['price_usd_kg']} USD/kg - Tendencia: {data['trend']}"
        })

    except requests.exceptions.Timeout:
        return _safe_json_response(False, error="Timeout al consultar precios")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return _safe_json_response(False,
                                       error=f"No hay datos de precios para '{product_name}'")
        return _safe_json_response(False, error=f"Error HTTP: {e}")
    except Exception as e:
        return _safe_json_response(False, error=f"Error al obtener precios: {str(e)}")


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


# ============================================================================
# HERRAMIENTA RAG (BASE DE CONOCIMIENTO)
# ============================================================================
retriever = get_retriever()
knowledge_base_tool = create_retriever_tool(
    retriever,
    "knowledge_base_search",
    "Busca información específica sobre prácticas agrícolas, manejo de cultivos, "
    "fertilizantes, control de plagas, técnicas de siembra, y optimización de producción "
    "en la base de conocimiento especializada."
)
