# app/utils/agronomy_helpers.py (Nuevo archivo o helper existente)

def calculate_eto_penman_simplified(temp_c: float, humidity_percent: float, wind_speed_ms: float) -> float:
    """
    Calcula la Evapotranspiración de Referencia (ETo) en mm/día usando una simplificación
    basada en los datos disponibles.

    Se usa una aproximación que pondera la temperatura, humedad y viento.
    (Penman-Monteith simplificado o una regresión lineal robusta).
    """
    
    # 1. Componente de Temperatura (similar a Hargreaves)
    # ETo_T = 0.0023 * (T_avg + 17.8) * (T_max - T_min)^0.5
    # Como solo tenemos T_actual, usamos una regresión lineal simple para T
    eto_temp_factor = 0.25 * temp_c  # Aproximación: 0.25 mm/día por grado C
    
    # 2. Componente de Humedad (penalización por alta humedad)
    # Si la humedad es alta, la ETo es menor.
    humidity_factor = 1.0 - (humidity_percent / 100.0)
    
    # 3. Componente de Viento (aumento de ETo por viento)
    wind_factor = 1.0 + (0.1 * wind_speed_ms) # 10% de aumento por cada m/s
    
    # ETo Simplificado Final (combinación de factores)
    eto = eto_temp_factor * humidity_factor * wind_factor
    
    # Asegurar un valor mínimo y máximo razonable para zonas tropicales
    if eto < 3.0:
        eto = 3.0
    if eto > 7.0:
        eto = 7.0
        
    return round(eto, 2)