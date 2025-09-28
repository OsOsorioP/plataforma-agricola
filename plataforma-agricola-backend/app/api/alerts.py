from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.auth import get_current_user
from app.db import db_models
from app.models.alert import Alert

router = APIRouter()

@router.get("/", response_model=List[Alert])
def get_my_alerts(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    """
    Obtiene todas las alertas no leídas para el usuario actual.
    """
    alerts = db.query(db_models.Alert).filter(
        db_models.Alert.user_id == current_user.id,
        db_models.Alert.is_read == False
    ).order_by(db_models.Alert.timestamp.desc()).all()
    return alerts