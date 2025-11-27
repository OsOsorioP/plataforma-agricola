from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.monitoring_service import run_proactive_monitoring

router = APIRouter()

@router.post("/trigger-monitoring", status_code=202)
def trigger_monitoring_endpoint(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Dispara el proceso de monitoreo proactivo en segundo plano.
    La API responde inmediatamente mientras la tarea se ejecuta.
    """
    print("-- [API] Recibida solicitud para iniciar monitoreo en segundo plano. --")
    background_tasks.add_task(run_proactive_monitoring, db)
    return {"message": "El monitoreo proactivo ha sido iniciado en segundo plano."}