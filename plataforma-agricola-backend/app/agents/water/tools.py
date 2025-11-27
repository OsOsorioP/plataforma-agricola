from langchain.tools import tool

from app.db.session import SessionLocal
from app.db.models.parcel import Parcel
from app.core.config import OPENWEATHER_API_KEY
from app.services.agronomy import calculate_eto_penman_simplified
from app.utils.helper import _safe_json_response, _extract_coordinates

from datetime import datetime, timedelta
import requests

@tool
def calculate_water_requirements(
    parcel_id: int, 
    crop_type: str, 
    growth_stage: str,
    temperature_c: float,            
    humidity_percent: float,
    wind_speed_ms: float,
    effective_precipitation_mm: float = 0.0,
) -> str:
    """
    Calcula requerimientos hídricos usando método FAO-56 (simplificado).

    Parámetros:
    - parcel_id: ID de la parcela
    - crop_type: 'maiz', 'cafe', 'arroz', etc.
    - growth_stage: Etapa fenológica (ej. 'crecimiento', 'floracion')
    - temperature_c: Temperatura actual en Celsius (de get_weather_forecast)
    - humidity_percent: Humedad actual en porcentaje (de get_weather_forecast)
    - wind_speed_ms: Velocidad del viento en m/s (de get_weather_forecast)
    - effective_precipitation_mm: Precipitación efectiva en mm/día (de get_precipitation_data)
    """
    
    stage_mapping = {
        'preparacion': 'inicial',
        'siembra': 'inicial',
        'germinacion': 'inicial',
        'crecimiento': 'desarrollo',
        'floracion': 'maduracion',
        'maduracion': 'maduracion',
        'cosecha': 'cosecha',
    }
    
    # Coeficientes Kc por cultivo y etapa (FAO-56)
    kc_values = {
        'maiz': {'inicial': 0.3, 'desarrollo': 0.7, 'maduracion': 1.15, 'cosecha': 0.6},
        'cafe': {'inicial': 0.85, 'desarrollo': 0.95, 'maduracion': 1.0, 'cosecha': 0.95},
        'arroz': {'inicial': 1.05, 'desarrollo': 1.15, 'maduracion': 1.2, 'cosecha': 0.95},
        'papa': {'inicial': 0.5, 'desarrollo': 0.8, 'maduracion': 1.15, 'cosecha': 0.75},
        'tomate': {'inicial': 0.6, 'desarrollo': 0.9, 'maduracion': 1.15, 'cosecha': 0.8},
        'platano': {'inicial': 0.5, 'desarrollo': 1.05, 'maduracion': 1.15, 'cosecha': 1.1},
    }

    db = SessionLocal()
    try:
        parcel = db.query(Parcel.Parcel).filter(
            Parcel.Parcel.id == parcel_id
        ).first()

        if not parcel:
            return _safe_json_response(False, error=f"Parcela {parcel_id} no encontrada")

        crop_lower = crop_type.lower()
        stage_lower = growth_stage.lower()
        
        fao_stage = stage_mapping.get(stage_lower)
        
        if not fao_stage:
            return _safe_json_response(False,
                                       error=f"Etapa '{growth_stage}' no se pudo mapear a una etapa FAO válida.",
                                       data={"valid_stages": list(stage_mapping.keys())})

        if crop_lower not in kc_values:
            return _safe_json_response(False,
                                       error=f"Cultivo '{crop_type}' no reconocido",
                                       data={"available_crops": list(kc_values.keys())})

        kc = kc_values[crop_lower][fao_stage]

        # ETo usando Penman-Monteith simplificado
        try:
            eto_estimated = calculate_eto_penman_simplified(temperature_c, humidity_percent, wind_speed_ms)
        except Exception:
            eto_estimated = 4.5  # mm/día (Valor generalizado)

        # ETc = ETo × Kc (Evapotranspiración del Cultivo)
        etc_base = eto_estimated * kc
        
        irrigation_type = parcel.irrigation_type.lower() if parcel.irrigation_type else 'secano'
        soil_type = parcel.soil_type.lower() if parcel.soil_type else 'franco'
        
        percolation_loss = 0.0
        evaporation_loss = 0.0
        is_inundation = False
        
        # Caso especial: Arroz con inundación
        if crop_lower == 'arroz' and irrigation_type == 'inundacion':
            is_inundation = True
            evaporation_loss = 3.0  # mm/día
            
            if 'arcilloso' in soil_type or 'pesado' in soil_type:
                percolation_loss = 4.0  # mm/día
            elif 'arenoso' in soil_type or 'ligero' in soil_type:
                percolation_loss = 8.0  # mm/día
            else:
                percolation_loss = 5.0  # mm/día
                 
            etc_base += percolation_loss + evaporation_loss
        
        # ETc total (bruto, sin considerar lluvia)
        etc_total_mm_day = etc_base
        
        # ===== CÁLCULO DE NECESIDAD NETA (LO QUE FALTABA) =====
        # Necesidad neta = ETc - Precipitación Efectiva
        net_requirement_mm_day = max(0.0, etc_total_mm_day - effective_precipitation_mm)
        
        # Conversión a litros
        area_m2 = parcel.area * 10000
        
        # Volumen bruto (ETc sin lluvia)
        water_liters_day_gross = etc_total_mm_day * area_m2
        
        # Volumen neto (ETc - P_eff) - ESTE ES EL QUE EL AGENTE DEBE RECOMENDAR
        water_liters_day_net = net_requirement_mm_day * area_m2

        # Eficiencia de riego
        efficiency = 0.75
        water_needed_with_losses_gross = water_liters_day_gross / efficiency
        water_needed_with_losses_net = water_liters_day_net / efficiency

        # ===== RECOMENDACIÓN ACTUALIZADA =====
        if net_requirement_mm_day == 0:
            recommendation_text = (
                f"No se requiere riego suplementario. "
                f"La precipitación efectiva ({effective_precipitation_mm:.1f} mm/día) "
                f"cubre la demanda del cultivo (ETc = {etc_total_mm_day:.1f} mm/día)."
            )
        else:
            recommendation_text = (
                f"Aplicar {int(water_liters_day_net)} litros/día (neto después de lluvia), "
                f"o {int(water_needed_with_losses_net)} litros/día considerando pérdidas del sistema. "
                f"ETc total: {etc_total_mm_day:.1f} mm/día. "
                f"Precipitación efectiva: {effective_precipitation_mm:.1f} mm/día. "
                f"Déficit: {net_requirement_mm_day:.1f} mm/día."
            )

        return _safe_json_response(True, {
            "parcel_id": parcel_id,
            "parcel_name": parcel.name,
            "area_hectares": parcel.area,
            "area_m2": area_m2,
            "crop_type": crop_type,
            "growth_stage": growth_stage,
            "fao_stage": fao_stage,
            "kc_coefficient": kc,
            "eto_mm_day": round(eto_estimated, 2),
            "etc_mm_day": round(etc_total_mm_day, 2),  # ETc bruto
            "effective_precipitation_mm_day": round(effective_precipitation_mm, 2),
            "net_requirement_mm_day": round(net_requirement_mm_day, 2),  # NUEVO
            "water_requirements": {
                # Valores BRUTOS (sin restar lluvia - para referencia)
                "gross_ideal_liters_per_day": round(water_liters_day_gross, 2),
                "gross_with_losses_liters_per_day": round(water_needed_with_losses_gross, 2),
                
                # Valores NETOS (restando lluvia - ESTOS SON LOS IMPORTANTES)
                "net_ideal_liters_per_day": round(water_liters_day_net, 2),  # ESTE ES V_AGENTE
                "net_with_losses_liters_per_day": round(water_needed_with_losses_net, 2),
                
                # Proyecciones semanales/mensuales NETAS
                "net_per_week_liters": round(water_liters_day_net * 7, 2),
                "net_per_month_liters": round(water_liters_day_net * 30, 2)
            },
            "efficiency_assumed": f"{efficiency * 100}%",
            "is_inundation_model": is_inundation,
            "percolation_mm_day": percolation_loss,
            "evaporation_loss_mm_day": evaporation_loss,
            "recommendation": recommendation_text
        })

    except Exception as e:
        return _safe_json_response(False, error=f"Error en cálculo: {str(e)}")
    finally:
        db.close()
        
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
        parcel = db.query(Parcel.Parcel).filter(
            Parcel.Parcel.id == parcel_id
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
        parcel = db.query(Parcel.Parcel).filter(
            Parcel.Parcel.id == parcel_id
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





















