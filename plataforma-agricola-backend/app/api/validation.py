# app/api/validation.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import db_models
from pydantic import BaseModel

router = APIRouter()

class VisionValidation(BaseModel):
    ground_truth: str
    is_correct: bool

class RagValidation(BaseModel):
    hallucination_score: float # 0.0 (Correcto) a 1.0 (Alucinación)

class RiskValidation(BaseModel):
    event_occurred: bool
    user_took_action: bool
    actual_loss: float

@router.post("/vision/{diagnostic_id}")
def validate_vision_diagnosis(diagnostic_id: int, val: VisionValidation, db: Session = Depends(get_db)):
    """Inyecta la verdad terreno para KT2"""
    record = db.query(db_models.VisionDiagnostic).filter_by(id=diagnostic_id).first()
    if not record: raise HTTPException(404, "Registro no encontrado")
    
    record.ground_truth = val.ground_truth
    record.is_correct = val.is_correct
    db.commit()
    return {"status": "updated"}

@router.post("/rag/{log_id}")
def validate_rag_response(log_id: int, val: RagValidation, db: Session = Depends(get_db)):
    """Inyecta puntaje de alucinación para KA2"""
    record = db.query(db_models.RagValidationLog).filter_by(id=log_id).first()
    if not record: raise HTTPException(404, "Registro no encontrado")
    
    record.hallucination_score = val.hallucination_score
    db.commit()
    return {"status": "updated"}

@router.post("/risk/{log_id}")
def validate_risk_event(log_id: int, val: RiskValidation, db: Session = Depends(get_db)):
    """Calcula KE1 post-evento"""
    record = db.query(db_models.RiskEventLog).filter_by(id=log_id).first()
    if not record: raise HTTPException(404, "Registro no encontrado")
    
    record.event_occurred = val.event_occurred
    record.user_took_action = val.user_took_action
    record.actual_loss = val.actual_loss
    
    # Cálculo de KE1: Si hubo evento, alertamos y usuario actuó -> Valor Salvado
    if val.event_occurred and record.alert_sent and val.user_took_action:
        record.value_saved = record.projected_loss - val.actual_loss
    else:
        record.value_saved = 0.0
        
    db.commit()
    return {"status": "updated", "value_saved": record.value_saved}