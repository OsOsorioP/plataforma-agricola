from langchain.tools import tool

from app.utils.helper import (
    _safe_json_response,
    _generate_climate_recommendations
)

from datetime import datetime, timedelta
import requests


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