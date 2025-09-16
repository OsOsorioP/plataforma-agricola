from fastapi import APIRouter, HTTPException
from app.models.parcel import Parcel, ParcelCreate
from app.db_mock import parcel_id_counter, db_parcels, db_users

router = APIRouter()

@router.post("/", response_model=Parcel, status_code=201)
def create_parcel_for_user(owner_id: int, parcel: ParcelCreate):
    """
    Crea una nueva parcela para un usuario específico.
    """
    # Verificar que el usuario exista
    if owner_id not in db_users:
        raise HTTPException(status_code=404, detail="Owner user not found")
    
    global parcel_id_counter
    parcel_id_counter+=1
    
    new_parcel = Parcel(
        id=parcel_id_counter,
        name=parcel.name,
        location=parcel.location,
        area=parcel.area,
        owner_id=owner_id
    )
    db_parcels[new_parcel.id] = new_parcel
    
    return new_parcel

@router.get("/{parcel_id}", response_model=Parcel)
def read_parcel(parcel_id: int):
    """
    Obtiene una parcela por su ID.
    """
    parcel = db_parcels.get(parcel_id)
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel