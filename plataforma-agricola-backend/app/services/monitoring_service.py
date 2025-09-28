import requests

from sqlalchemy.orm import Session
from app.db import db_models
from app.core.config import OPENWEATHER_API_KEY

def check_frost_risk_for_parcel(db: Session, parcel: db_models.Parcel):
    """
    Verifica el pronóstico de heladas para una única parcela y crea una alerta si es necesario.
    """
    print(f"-- [MONITOREO] Verificando riesgo de helada para parcela ID {parcel.id}: {parcel.name} --")
    try:
        lat, lon = parcel.location.split(',')
        lat = float(lat.strip())
        lon = float(lon.strip())
    except (ValueError, AttributeError):
        print(f'-- [MONITOREO] Parcela ID {parcel.id}, no tiene formato valido "lat,lon" --')
        return
    
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "es"
    }
    
    try:
        response = requests.get(url=base_url, params=params)
        response.raise_for_status()
        forecast_data = response.json()
        
        for forecast in forecast_data['list'][:8]:
            temp_min = forecast['main']['temp_min']
            if temp_min <= 2.0:
                alert_message = f"¡Alerta de Helada! Se pronostica una temperatura mínima de {temp_min}°C para tu parcela '{parcel.name}' en las próximas 24 horas. Considera activar tu plan de contingencia."
                existing_alert = db.query(db_models.Alert).filter(
                    db_models.Alert.parcel_id == parcel.id,
                    db_models.Alert.risk_type == "HELADA"
                ).first()
                
                if not existing_alert:
                    new_alert = db_models.Alert(
                        user_id=parcel.owner_id,
                        parcel_id=parcel.id,
                        risk_type="HELADA",
                        message=alert_message
                    )
                    db.add(new_alert)
                    db.commit()
                    print('Alerta de helada creada')
                else:
                    print('Alerta de helada ya existe')
                    
                return
    except Exception as e:
        print(f"-- [MONITOREO] Error al procesar parcela ID {parcel.id}: {e} --")
        
def run_proactive_monitoring(db: Session):
    """
    Función principal que se ejecuta en segundo plano.
    Obtiene todas las parcelas y verifica el riesgo para cada una.
    """
    print("-- [MONITOREO] Iniciando ciclo de monitoreo proactivo... --")
    all_parcels = db.query(db_models.Parcel).all()
    for parcel in all_parcels:
        check_frost_risk_for_parcel(db, parcel)
    print("-- [MONITOREO] Ciclo de monitoreo proactivo finalizado. --")