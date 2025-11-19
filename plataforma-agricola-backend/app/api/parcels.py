from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from typing import List

from app.models.parcel import Parcel, ParcelCreate
from app.db import db_models
from app.db.database import get_db
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=Parcel, status_code=201)
def create_parcel_for_current_user(
    parcel: ParcelCreate,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    """
    Crea una nueva parcela para el usuario actualmente autenticado.
    El owner_id se obtiene automáticamente del token.
    """
    db_parcel = db_models.Parcel(**parcel.model_dump(), owner_id=current_user.id)
    db.add(db_parcel)
    db.commit()
    db.refresh(db_parcel)
    return db_parcel

@router.get("/", response_model=List[Parcel])
def read_parcels_for_current_user(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    """
    Obtiene la lista de parcelas del usuario actualmente autenticado.
    """
    return current_user.parcels