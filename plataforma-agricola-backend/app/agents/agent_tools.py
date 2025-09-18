from langchain.tools import tool

from app.database import SessionLocal
from app import db_models

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