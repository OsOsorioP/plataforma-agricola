from typing import Optional
from langchain.tools import tool
from langchain.tools.retriever import create_retriever_tool

from app.services.rag_service import get_retriever
from app.db.database import SessionLocal
from app.db import db_models
from app.core.config import OPENWEATHER_API_KEY, DATOS_GOV_API_KEY, DATOS_GOV_PASSWORD, DATOS_GOV_USER
from app.utils.geo_calculate import calculate_average_ndvi

from datetime import datetime, timedelta, date
import requests
import json

# Herramientas db
@tool
def get_parcel_details(parcel_id: int)->str:
    """
    Útil para obtener los detalles de una parcela específica cuando se conoce su ID.
    Devuelve el nombre, la ubicación y el área de la parcela.
    """
    db = SessionLocal()
    try:
        parcel = db.query(db_models.Parcel).filter(db_models.Parcel.id == parcel_id).first()
        if not parcel:
            return f'No se encontró ninguna parcela con el ID {parcel_id}.'
        return f'Detalles de la Parcela ID {parcel.id}: Nombre: {parcel.name}, Ubicación: {parcel.location}, Área: {parcel.area} hectáreas.'
    finally:
        db.close()
        
@tool
def list_user_parcels(user_id: int) -> str:
    """
    Útil para listar todas las parcelas que pertenecen a un usuario específico, dado el ID del usuario.
    Devuelve una lista de los nombres y los IDs de las parcelas.
    """

    db = SessionLocal()
    try:
        user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
        if not user:
            return f"No se encontró ningún usuario con el ID {user_id}."
        
        if not user.parcels:
            return f"El usuario {user.email} (ID: {user_id}) no tiene parcelas registradas."

        parcel_list = [f"ID: {p.id}, Nombre: '{p.name}'" for p in user.parcels]
        return f"Parcelas del usuario {user.email} (ID: {user_id}): " + "; ".join(parcel_list)
    finally:
        db.close()
      
@tool
def get_parcel_geojson(parcel_id: int)->Optional[str]:
    """Consulta la DB y retorna el string GeoJSON de la parcela."""
    db = SessionLocal()
    try:
        parcel = db.query(db_models.Parcel).filter(db_models.Parcel.id == parcel_id).first()
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
        parcel = db.query(db_models.Parcel).filter(db_models.Parcel.id == parcel_id).first()
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
    Útil para guardar una recomendación específica generada por un agente en la base de datos.
    Debe usarse siempre que un agente dé un consejo accionable para una parcela.
    Devuelve el ID de la recomendación guardada.
    """
    db = SessionLocal()
    try:
        # Se busca el owner_id a través de la parcela
        parcel = db.query(db_models.Parcel).filter(db_models.Parcel.id == parcel_id).first()
        if not parcel:
            return f"Error: No se encontró la parcela con ID {parcel_id}."

        new_recommendation = db_models.Recommendation(
            user_id=parcel.owner_id,
            parcel_id=parcel_id,
            agent_source=agent_source,
            recommendation_text=recommendation_text,
        )
        db.add(new_recommendation)
        db.commit()
        db.refresh(new_recommendation)
        return f"Recomendación guardada con éxito con ID: {new_recommendation.id}"
    except Exception as e:
        db.rollback()
        return f"Error al guardar la recomendación: {e}"
    finally:
        db.close()        
       
@tool
def get_kpi_summary(parcel_id: int, kpi_name: str) -> str:
    """
    Útil para obtener un resumen y análisis de la evolución de un Indicador Clave de Desempeño (KPI)
    para una parcela específica. Por ejemplo, kpi_name puede ser 'SOIL_HEALTH_NDVI'.
    """
    db = SessionLocal()
    try:
        metrics = db.query(db_models.KPIMetric).filter(
            db_models.KPIMetric.parcel_id == parcel_id,
            db_models.KPIMetric.kpi_name == kpi_name
        ).order_by(db_models.KPIMetric.timestamp.asc()).all()

        if not metrics:
            return f"No se encontraron datos para el KPI '{kpi_name}' en la parcela {parcel_id}."

        latest_metric = metrics[-1]
        summary = f"Resumen para KPI '{kpi_name}' en la parcela {parcel_id}:\n"
        summary += f"- Último valor registrado: {latest_metric.value:.4f} el {latest_metric.timestamp.strftime('%Y-%m-%d')}.\n"
        
        if len(metrics) > 1:
            initial_metric = metrics[0]
            change = latest_metric.value - initial_metric.value
            percentage_change = (change / initial_metric.value) * 100 if initial_metric.value != 0 else 0
            
            trend = "mejora" if change > 0 else "declive"
            if abs(percentage_change) < 1: trend = "estable"

            summary += f"- Evolución total: Ha habido un {trend} con un cambio de {change:.4f} ({percentage_change:.2f}%) desde el primer registro."
        
        return summary
    finally:
        db.close()      
        
# Herramienta rag
retriever = get_retriever()
knowledge_base_tool = create_retriever_tool(
        retriever,
        "knowledge_base_search",
        "Útil para buscar información específica y detallada sobre prácticas de manejo de cultivos, fertilizantes, control de plagas y optimización de la producción en la base de conocimiento agrícola."
    )

# Herramientas api
@tool
def get_weather_forecast(location:str)->str:
    """
    Útil para obtener el pronóstico del tiempo para una ubicación específica.
    La ubicación debe ser en formato 'ciudad,código_país' (ej. 'Bogota,CO').
    Devuelve un resumen del clima actual y el pronóstico para las próximas horas.
    """
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric", # Para obtener la temperatura en Celsius
        "lang": "es"      # Para obtener las descripciones en español
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status() 
        data = response.json()
        
        summary = (
            f"Pronóstico del tiempo para {data['name']}:\n"
            f"- Condición actual: {data['weather'][0]['description']}\n"
            f"- Temperatura: {data['main']['temp']}°C (Sensación real: {data['main']['feels_like']}°C)\n"
            f"- Humedad: {data['main']['humidity']}%\n"
            f"- Viento: {data['wind']['speed']} m/s\n"
        )
        
        return summary
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return f"Error: No se pudo encontrar la ubicación '{location}'. Por favor, verifica el formato (ej. 'Bogota,CO')."
        return f"Error HTTP al obtener el pronóstico: {http_err}"
    except Exception as e:
        return f"Ocurrió un error inesperado al obtener el pronóstico: {e}"
    
@tool
def get_market_price(product_name: str) -> str:
    """
    Útil para obtener el precio de mercado actual y la tendencia para un producto agrícola específico.
    El producto debe ser un nombre simple como 'tomate', 'maíz', etc.
    """
    print(f"---USANDO HERRAMIENTA: get_market_price para {product_name}---")
    try:
        response = requests.get(f"http://127.0.0.1:8000/mock/market-prices?product_name={product_name}")
        response.raise_for_status()
        data = response.json()
        return f"El precio de mercado para '{product_name}' es de ${data['price_usd_kg']} USD por kg, con una tendencia '{data['trend']}'."
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            return f"No se encontraron datos de precios para '{product_name}'."
        return f"Error al obtener los precios: {http_err}"
    except Exception as e:
        return f"Ocurrió un error inesperado: {e}"
    
@tool
def get_historical_weather_summary(latitude: float, longitude: float) -> str:
    """
    Útil para obtener un resumen de datos meteorológicos históricos de los últimos 30 días para una latitud y longitud específicas.
    Analiza los datos para identificar riesgos clave como heladas o estrés por calor.
    """
    print(f"---USANDO HERRAMIENTA: get_historical_weather_summary para Lat: {latitude}, Lon: {longitude}---")
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Se analiza los datos para generar un resumen de riesgos
        min_temps = data['daily']['temperature_2m_min']
        max_temps = data['daily']['temperature_2m_max']
        
        frost_risk_days = sum(1 for temp in min_temps if temp is not None and temp <= 2)
        heat_stress_days = sum(1 for temp in max_temps if temp is not None and temp >= 35)

        summary = (
            f"Análisis de riesgo climático para los últimos 30 días en la ubicación ({latitude}, {longitude}):\n"
            f"- Días con riesgo de helada (temp <= 2°C): {frost_risk_days} días.\n"
            f"- Días con riesgo de estrés por calor (temp >= 35°C): {heat_stress_days} días.\n"
        )
        return summary
    except Exception as e:
        return f"Ocurrió un error al analizar los datos históricos del clima: {e}"
   
@tool
def get_data_agromy(departamento: str, producto: str, limite: int = 100)-> list[dict[str, any]]:
    """
    Útil para recupera datos de conocimiento agrícola (valores, áreas, rendimientos) 
    para un departamento y un producto específico usando la API SODA.
    """
    
    where_clause = f"departamento='{departamento}' AND producto='{producto}'"
    
    params = {
        "$where": where_clause,
        "$limit": limite,
        "$select": "municipio,fecha,valor,unidad_de_medida,rendimiento" # Seleccionamos columnas clave
    }
    
    headers = {
        "X-App-Token": DATOS_GOV_API_KEY,
        "Accept": "application/json"
    }
    
    try:
        response = requests.get("https://www.datos.gov.co/resource/vgsd-2dyp.json", params=params, headers=headers)
        response.raise_for_status() # Lanza HTTPError si el status es 4xx o 5xx
        return response.json()
        
    except requests.exceptions.RequestException as e:
        # Aquí puedes manejar errores específicos o notificar al agente
        return {"error": f"Error de API: No se pudieron obtener los datos. {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Error de procesamiento: La respuesta no es un JSON válido."}
    
@tool
def get_parcel_health_indices(parcel_id: int, start_date: str, end_date: str) -> str:
    """
    Utiliza esta herramienta para obtener los índices de salud vegetal de una parcela 
    específica (ej. 101) y un rango de fechas (ej. '2023-09-01', '2023-09-30').
    El resultado te dará el Índice de Vegetación de Diferencia Normalizada (NDVI).
    """
    
    # Conversión de fechas (el agente las pasará como strings)
    try:
        date_from = date.fromisoformat(start_date)
        date_to = date.fromisoformat(end_date)
    except ValueError:
        return "Error: Las fechas deben estar en formato ISO (YYYY-MM-DD)."

    # 1. Recuperar la Geometría desde la DB (SQLAlchemy)
    geojson_data = get_parcel_geojson(parcel_id)
    if not geojson_data:
        return f"Error: No se encontró ninguna parcela con el ID {parcel_id}."

    # 2. Calcular el NDVI usando el motor geoespacial
    avg_ndvi = calculate_average_ndvi(geojson_data, date_from, date_to)

    # 3. Interpretación y Devolución del resultado (se mantiene igual)
    if avg_ndvi == -999.0:
        return "ERROR: Falló la comunicación con el servicio de datos satelitales."
    elif avg_ndvi == 0.0:
        return "ADVERTENCIA: No se encontraron datos válidos para la vegetación en el rango de fechas. ¿Hay nubes, o estaba la parcela vacía?"
    
    health_status = ""
    if avg_ndvi < 0.2:
        health_status = "Muy pobre (Probablemente suelo desnudo o vegetación muy escasa)."
    elif avg_ndvi < 0.4:
        health_status = "Baja (Vegetación bajo estrés o en crecimiento temprano)."
    elif avg_ndvi < 0.6:
        health_status = "Moderada (Buen crecimiento, pero con potencial de mejora)."
    else:
        health_status = "Excelente (Vegetación densa y saludable)."

    return json.dumps({
        "parcel_id": parcel_id,
        "date_range": f"{start_date} a {end_date}",
        "index": "NDVI",
        "average_value": f"{avg_ndvi:.4f}",
        "interpretation": health_status
    })