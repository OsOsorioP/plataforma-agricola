from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.parcel import Parcel
from app.db.models.kpi import KPIMetric

from app.api.deps import get_current_user

from app.schemas.kpi import KPIMetricCreate, KPIMetricResponse

router = APIRouter()

@router.post("/parcels/{parcel_id}/metrics", status_code=201)
def log_kpi_metric(
    parcel_id: int,
    metric: KPIMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registra una nueva medición de KPI para una parcela específica.
    Esto simula la recolección de datos en el campo.
    """
    db_parcel = db.query(Parcel).filter(
        Parcel.id == parcel_id,
        Parcel.owner_id == current_user.id
    ).first()

    if not db_parcel:
        raise HTTPException(status_code=404, detail="Parcela no encontrada o no pertenece al usuario.")

    db_metric = KPIMetric(
        parcel_id=parcel_id,
        **metric.model_dump()
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return {"message": "Métrica de KPI registrada con éxito", "metric_id": db_metric.id}

@router.get("/parcels/{parcel_id}/history", response_model=List[KPIMetricResponse])
def get_kpi_history(
    parcel_id: int,
    kpi_name: Optional[str] = None, # Opcional: filtrar por un KPI específico
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el historial de métricas para una parcela.
    Útil para gráficas de dashboard.
    """
    query = db.query(KPIMetric).filter(
        KPIMetric.parcel_id == parcel_id
    )
    
    if kpi_name:
        query = query.filter(KPIMetric.kpi_name == kpi_name)
        
    # Ordenamos por fecha ascendente para la gráfica
    metrics = query.order_by(KPIMetric.timestamp.asc()).all()
    return metrics