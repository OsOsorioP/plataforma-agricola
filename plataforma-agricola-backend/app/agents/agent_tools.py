from langchain.tools import tool
from langchain.tools.retriever import create_retriever_tool

from app.services.rag_service import get_retriever
from app.database import SessionLocal
from app import db_models
from app.core.config import OPENWEATHER_API_KEY

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