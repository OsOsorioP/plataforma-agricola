from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db 
from app.db.models.alert import Alert
from app.db.models.user import User

from app.schemas.alert import Alert as AlertSchema

from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[AlertSchema])
def get_my_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene todas las alertas no leídas para el usuario actual.
    """
    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False
    ).order_by(Alert.timestamp.desc()).all()
    return alerts