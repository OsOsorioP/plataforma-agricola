from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.parcel import Parcel, ParcelCreate
from app import db_models
from app.database import get_db

router = APIRouter()

@router.post("/", response_model=Parcel, status_code=201)
def create_parcel_for_user(owner_id: int, parcel: ParcelCreate, db: Session = Depends(get_db)):
    # Verificamos que el usuario exista
    owner = db.query(db_models.User).filter(db_models.User.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner user not found")
        
    db_parcel = db_models.Parcel(**parcel.model_dump(), owner_id=owner_id)
    db.add(db_parcel)
    db.commit()
    db.refresh(db_parcel)
    return db_parcel

@router.get("/{parcel_id}", response_model=Parcel)
def read_parcel(parcel_id: int, db: Session = Depends(get_db)):
    db_parcel = db.query(db_models.Parcel).filter(db_models.Parcel.id == parcel_id).first()
    if db_parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return db_parcel