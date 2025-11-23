import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import db_models
import os

class KPILogger:
    """
    Logger especializado para capturar métricas de KPIs.
    Registra eventos tanto en base de datos como en archivos JSONL.
    """
    
    def __init__(self):
        # Crear directorio de logs si no existe
        os.makedirs('logs', exist_ok=True)
        
        # Configurar logger de Python para archivos JSONL
        self.logger = logging.getLogger('kpi_logger')
        self.logger.setLevel(logging.INFO)
        
        # Handler para archivo general
        general_handler = logging.FileHandler('logs/kpi_events.jsonl')
        general_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(general_handler)
        
        # Handlers específicos por tipo de KPI
        self.handlers = {
            'interventions': logging.FileHandler('logs/interventions.jsonl'),
            'water': logging.FileHandler('logs/water_calculations.jsonl'),
            'diagnostics': logging.FileHandler('logs/diagnostics.jsonl'),
            'orchestration': logging.FileHandler('logs/orchestration.jsonl'),
            'latency': logging.FileHandler('logs/latency.jsonl'),
        }
        
        for handler in self.handlers.values():
            handler.setFormatter(logging.Formatter('%(message)s'))
    
    def _log_to_file(self, filename: str, data: dict):
        """Escribe evento en archivo JSONL específico"""
        handler = self.handlers.get(filename)
        if handler:
            logger = logging.getLogger(f'kpi_{filename}')
            if not logger.handlers:
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)
            logger.info(json.dumps(data, ensure_ascii=False))
    
    def log_intervention(
        self,
        user_id: int,
        agent_source: str,
        chemical_name: str,
        chemical_category: str,
        was_vetoed: bool,
        veto_reason: Optional[str],
        eiq_base: float,
        eiq_alternative: Optional[float],
        alternative_proposed: Optional[str],
        parcel_id: Optional[int] = None
    ):
        """
        Registra evento de intercepción del Sustainability Agent (KS1, KS2)
        
        Args:
            user_id: ID del usuario
            agent_source: Agente que propuso el químico (production/vision)
            chemical_name: Nombre del químico propuesto
            chemical_category: Categoría toxicológica (Ia, Ib, II, III, IV)
            was_vetoed: Si fue bloqueado por Sustainability
            veto_reason: Razón del veto
            eiq_base: EIQ del químico original
            eiq_alternative: EIQ de la alternativa (None si no fue vetado)
            alternative_proposed: Texto de la alternativa propuesta
            parcel_id: ID de la parcela (opcional)
        """
        db = SessionLocal()
        try:
            # Calcular delta EIQ
            if eiq_alternative and eiq_base > 0:
                delta_eiq = ((eiq_base - eiq_alternative) / eiq_base) * 100
            else:
                delta_eiq = 0.0
            
            # Guardar en tabla específica
            intervention = db_models.InterventionEvent(
                user_id=user_id,
                parcel_id=parcel_id,
                agent_source=agent_source,
                chemical_proposed=chemical_name,
                chemical_category=chemical_category,
                was_vetoed=was_vetoed,
                veto_reason=veto_reason,
                alternative_proposed=alternative_proposed,
                eiq_base=eiq_base,
                eiq_alternative=eiq_alternative,
                delta_eiq_percent=delta_eiq
            )
            db.add(intervention)
            
            # Guardar en log general
            kpi_log = db_models.KPILog(
                kpi_type="KS1",
                event_type="intercepcion_ecologica",
                user_id=user_id,
                parcel_id=parcel_id,
                agent_source=agent_source,
                metric_value=1.0 if was_vetoed else 0.0,
                metric_metadata={
                    "chemical": chemical_name,
                    "category": chemical_category,
                    "eiq_base": eiq_base,
                    "eiq_alt": eiq_alternative,
                    "delta_eiq": delta_eiq
                },
                success=True
            )
            db.add(kpi_log)
            db.commit()
            
            # Log en archivo JSONL
            self._log_to_file('interventions', {
                "timestamp": datetime.now().isoformat(),
                "kpi": "KS1",
                "user_id": user_id,
                "parcel_id": parcel_id,
                "chemical": chemical_name,
                "category": chemical_category,
                "vetoed": was_vetoed,
                "eiq_base": eiq_base,
                "eiq_alt": eiq_alternative,
                "delta_eiq": round(delta_eiq, 2)
            })
            
            print(f"[KPI-KS1] Intervención registrada: {chemical_name} ({'VETOED' if was_vetoed else 'APPROVED'})")
            
        except Exception as e:
            db.rollback()
            print(f"[KPI-ERROR] Error logging intervention: {e}")
        finally:
            db.close()
    
    def log_water_calculation(
        self,
        user_id: int,
        parcel_id: int,
        crop_type: str,
        development_stage: str,
        etc_theoretical: float,
        v_agent: float,
        p_eff: float,
        soil_type: Optional[str] = None,
        irrigation_type: Optional[str] = None,
        ndwi_value: Optional[float] = None,
        days_since_planting: Optional[int] = None
    ):
        """
        Registra cálculo de prescripción hídrica (KS3)
        
        Args:
            user_id: ID del usuario
            parcel_id: ID de la parcela
            crop_type: Tipo de cultivo
            development_stage: Etapa fenológica
            etc_theoretical: ETc teórico (mm/día)
            v_agent: Volumen recomendado por agente (litros/día)
            p_eff: Precipitación efectiva (mm/día)
            soil_type: Tipo de suelo
            irrigation_type: Tipo de riego
            ndwi_value: Valor NDWI usado
            days_since_planting: Días desde siembra
        """
        db = SessionLocal()
        try:
            # Obtener área de la parcela para cálculo
            parcel = db.query(db_models.Parcel).filter(db_models.Parcel.id == parcel_id).first()
            if not parcel:
                print(f"[KPI-ERROR] Parcela {parcel_id} no encontrada")
                return
            
            area_m2 = parcel.area * 10000  # hectáreas a m²
            
            # Cálculo de WPA (Water Prescription Accuracy)
            need_theoretical = (etc_theoretical - p_eff) * area_m2  # litros/día
            if need_theoretical < 0:
                need_theoretical = 0  # No puede ser negativo
            
            if etc_theoretical > 0:
                deviation = abs(v_agent - need_theoretical) / (etc_theoretical * area_m2)
                wpa_score = 1 - deviation
                deviation_percent = deviation * 100
            else:
                wpa_score = 0
                deviation_percent = 100
            
            # Guardar en tabla específica
            water_calc = db_models.WaterCalculation(
                user_id=user_id,
                parcel_id=parcel_id,
                crop_type=crop_type,
                development_stage=development_stage,
                days_since_planting=days_since_planting,
                etc_theoretical=etc_theoretical,
                p_eff=p_eff,
                v_agent=v_agent,
                wpa_score=wpa_score,
                deviation_percent=deviation_percent,
                soil_type=soil_type,
                irrigation_type=irrigation_type,
                ndwi_value=ndwi_value
            )
            db.add(water_calc)
            
            # Log general
            kpi_log = db_models.KPILog(
                kpi_type="KS3",
                event_type="calculo_hidrico",
                user_id=user_id,
                parcel_id=parcel_id,
                agent_source="water",
                metric_value=wpa_score,
                metric_metadata={
                    "etc": etc_theoretical,
                    "v_agent": v_agent,
                    "deviation": round(deviation_percent, 2)
                },
                success=True
            )
            db.add(kpi_log)
            db.commit()
            
            # Log en archivo
            self._log_to_file('water', {
                "timestamp": datetime.now().isoformat(),
                "kpi": "KS3",
                "user_id": user_id,
                "parcel_id": parcel_id,
                "crop": crop_type,
                "stage": development_stage,
                "etc": etc_theoretical,
                "v_agent": v_agent,
                "wpa": round(wpa_score, 4),
                "deviation": round(deviation_percent, 2)
            })
            
            print(f"[KPI-KS3] Cálculo hídrico registrado: WPA={wpa_score:.2f}")
            
        except Exception as e:
            db.rollback()
            print(f"[KPI-ERROR] Error logging water calculation: {e}")
        finally:
            db.close()
    
    def log_diagnosis(
        self,
        user_id: int,
        diagnosis: str,
        confidence: float,
        processing_time: float,
        image_size_kb: int,
        image_conditions: Dict[str, Any],
        parcel_id: Optional[int] = None,
        ground_truth: Optional[str] = None
    ):
        """
        Registra diagnóstico del Vision Agent (KT2)
        """
        db = SessionLocal()
        try:
            is_correct = None
            if ground_truth:
                is_correct = diagnosis.lower() == ground_truth.lower()
            
            diagnostic = db_models.VisionDiagnostic(
                user_id=user_id,
                parcel_id=parcel_id,
                diagnosis=diagnosis,
                confidence=confidence,
                ground_truth=ground_truth,
                is_correct=is_correct,
                image_conditions=image_conditions,
                image_size_kb=image_size_kb,
                processing_time=processing_time
            )
            db.add(diagnostic)
            
            kpi_log = db_models.KPILog(
                kpi_type="KT2",
                event_type="diagnostico_vision",
                user_id=user_id,
                parcel_id=parcel_id,
                agent_source="vision",
                metric_value=confidence,
                metric_metadata={
                    "diagnosis": diagnosis,
                    "ground_truth": ground_truth,
                    "is_correct": is_correct
                },
                success=True
            )
            db.add(kpi_log)
            db.commit()
            
            self._log_to_file('diagnostics', {
                "timestamp": datetime.now().isoformat(),
                "kpi": "KT2",
                "user_id": user_id,
                "diagnosis": diagnosis,
                "confidence": confidence,
                "correct": is_correct
            })
            
            print(f"[KPI-KT2] Diagnóstico registrado: {diagnosis} ({confidence:.2f})")
            
        except Exception as e:
            db.rollback()
            print(f"[KPI-ERROR] Error logging diagnosis: {e}")
        finally:
            db.close()
    
    def log_orchestration(
        self,
        user_id: int,
        conversation_id: str,
        query_text: str,
        nodes_visited: List[str],
        nodes_minimum: int,
        query_type: str,
        has_image: bool = False
    ):
        """
        Registra eficiencia de orquestación (KT1)
        """
        db = SessionLocal()
        try:
            nodes_count = len(nodes_visited)
            g_eff = nodes_minimum / nodes_count if nodes_count > 0 else 0
            
            orchestration = db_models.OrchestrationEvent(
                user_id=user_id,
                conversation_id=conversation_id,
                query_text=query_text,
                query_type=query_type,
                has_image=has_image,
                nodes_visited=nodes_visited,
                nodes_count=nodes_count,
                nodes_minimum=nodes_minimum,
                g_eff=g_eff
            )
            db.add(orchestration)
            
            kpi_log = db_models.KPILog(
                kpi_type="KT1",
                event_type="orquestacion",
                user_id=user_id,
                conversation_id=conversation_id,
                agent_source="supervisor",
                metric_value=g_eff,
                metric_metadata={
                    "nodes": nodes_visited,
                    "count": nodes_count,
                    "minimum": nodes_minimum
                },
                success=g_eff >= 0.85
            )
            db.add(kpi_log)
            db.commit()
            
            self._log_to_file('orchestration', {
                "timestamp": datetime.now().isoformat(),
                "kpi": "KT1",
                "user_id": user_id,
                "conversation_id": conversation_id,
                "nodes": nodes_visited,
                "g_eff": round(g_eff, 3)
            })
            
            print(f"[KPI-KT1] Orquestación registrada: G_eff={g_eff:.2f}")
            
        except Exception as e:
            db.rollback()
            print(f"[KPI-ERROR] Error logging orchestration: {e}")
        finally:
            db.close()
    
    def log_latency(
        self,
        user_id: int,
        conversation_id: str,
        total_time: float,
        time_breakdown: Dict[str, float],
        has_image: bool
    ):
        """
        Registra latencia de inferencia (KA3)
        """
        db = SessionLocal()
        try:
            threshold = 10.0 if has_image else 5.0
            meets_threshold = total_time <= threshold
            
            latency = db_models.LatencyLog(
                user_id=user_id,
                conversation_id=conversation_id,
                total_time=total_time,
                has_image=has_image,
                time_breakdown=time_breakdown,
                threshold=threshold,
                meets_threshold=meets_threshold
            )
            db.add(latency)
            
            kpi_log = db_models.KPILog(
                kpi_type="KA3",
                event_type="latencia_inferencia",
                user_id=user_id,
                conversation_id=conversation_id,
                agent_source="system",
                metric_value=total_time,
                metric_metadata=time_breakdown,
                success=meets_threshold
            )
            db.add(kpi_log)
            db.commit()
            
            self._log_to_file('latency', {
                "timestamp": datetime.now().isoformat(),
                "kpi": "KA3",
                "user_id": user_id,
                "total_time": round(total_time, 2),
                "has_image": has_image,
                "meets_threshold": meets_threshold
            })
            
            print(f"[KPI-KA3] Latencia registrada: {total_time:.2f}s ({'✓' if meets_threshold else '✗'})")
            
        except Exception as e:
            db.rollback()
            print(f"[KPI-ERROR] Error logging latency: {e}")
        finally:
            db.close()

# Instancia global del logger
kpi_logger = KPILogger()