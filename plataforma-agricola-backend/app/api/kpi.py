from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.database import get_db
from app.db import db_models
from app.auth import get_current_user
from app.models.kpi import KPIMetricCreate, KPIMetricResponse

router = APIRouter()

@router.post("/parcels/{parcel_id}/metrics", status_code=201)
def log_kpi_metric(
    parcel_id: int,
    metric: KPIMetricCreate,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    """
    Registra una nueva medición de KPI para una parcela específica.
    Esto simula la recolección de datos en el campo.
    """
    db_parcel = db.query(db_models.Parcel).filter(
        db_models.Parcel.id == parcel_id,
        db_models.Parcel.owner_id == current_user.id
    ).first()

    if not db_parcel:
        raise HTTPException(status_code=404, detail="Parcela no encontrada o no pertenece al usuario.")

    db_metric = db_models.KPIMetric(
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
    current_user: db_models.User = Depends(get_current_user)
):
    """
    Obtiene el historial de métricas para una parcela.
    Útil para gráficas de dashboard.
    """
    query = db.query(db_models.KPIMetric).filter(
        db_models.KPIMetric.parcel_id == parcel_id
    )
    
    if kpi_name:
        query = query.filter(db_models.KPIMetric.kpi_name == kpi_name)
        
    # Ordenamos por fecha ascendente para la gráfica
    metrics = query.order_by(db_models.KPIMetric.timestamp.asc()).all()
    return metrics