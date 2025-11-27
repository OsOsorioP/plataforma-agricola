from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas.parcel import Parcel as ParcelShema, ParcelCreate, ParcelUpdate

from app.db.models.parcel import Parcel
from app.db.models.user import User
from app.db.session import get_db

from app.api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=ParcelShema, status_code=201)
def create_parcel_for_current_user(
    parcel: ParcelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea una nueva parcela con información básica y opcionalmente información del cultivo.
    Los campos de cultivo, suelo y riego son opcionales.
    """
    db_parcel = Parcel(**parcel.model_dump(), owner_id=current_user.id)
    db.add(db_parcel)
    db.commit()
    db.refresh(db_parcel)
    return db_parcel

@router.get("/", response_model=List[ParcelShema])
def read_parcels_for_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene todas las parcelas del usuario actual con información completa.
    """
    return current_user.parcels

@router.get("/{parcel_id}", response_model=ParcelShema)
def read_parcel(
    parcel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene detalles completos de una parcela específica incluyendo
    información de cultivo, suelo, riego y estado de salud.
    """
    parcel = db.query(Parcel).filter(
        Parcel.id == parcel_id,
        Parcel.owner_id == current_user.id
    ).first()
    
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcela no encontrada o no pertenece al usuario")
    
    return parcel

@router.put("/{parcel_id}", response_model=ParcelShema)
def update_parcel(
    parcel_id: int,
    parcel_update: ParcelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza información de una parcela existente.
    Solo actualiza los campos proporcionados en el request.
    Útil para que el usuario actualice información del cultivo conforme avanza la temporada.
    """
    db_parcel = db.query(Parcel).filter(
        Parcel.id == parcel_id,
        Parcel.owner_id == current_user.id
    ).first()
    
    if not db_parcel:
        raise HTTPException(status_code=404, detail="Parcela no encontrada o no pertenece al usuario")
    
    # Actualizar solo los campos proporcionados (exclude_unset=True)
    update_data = parcel_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_parcel, field, value)
    
    db.commit()
    db.refresh(db_parcel)
    return db_parcel

@router.delete("/{parcel_id}", status_code=204)
def delete_parcel(
    parcel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina una parcela y todas sus recomendaciones y métricas asociadas.
    """
    db_parcel = db.query(Parcel).filter(
        Parcel.id == parcel_id,
        Parcel.owner_id == current_user.id
    ).first()
    
    if not db_parcel:
        raise HTTPException(status_code=404, detail="Parcela no encontrada o no pertenece al usuario")
    
    db.delete(db_parcel)
    db.commit()
    return None