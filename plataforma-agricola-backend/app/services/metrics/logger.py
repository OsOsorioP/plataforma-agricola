import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.db.session import SessionLocal
from app.db.models import (
    KPILog, 
    InterventionEvent, 
    WaterCalculation, 
    VisionDiagnostic, 
    OrchestrationEvent, 
    LatencyLog, 
    RiskAlert
)
from app.db.models.parcel import Parcel

class KPILogger:
    """Logger especializado para capturar métricas de KPIs.
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
            'risk_alerts': logging.FileHandler('logs/risk_alerts.jsonl'),
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

    # =========================================================================
    # KS1 Y KS2: INTERVENCIONES ECOLÓGICAS
    # =========================================================================

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
        """Registra evento de intercepción del Sustainability Agent (KS1, KS2)

        Args:
            user_id (int): _description_
            agent_source (str): _description_
            chemical_name (str): _description_
            chemical_category (str): _description_
            was_vetoed (bool): _description_
            veto_reason (Optional[str]): _description_
            eiq_base (float): _description_
            eiq_alternative (Optional[float]): _description_
            alternative_proposed (Optional[str]): _description_
            parcel_id (Optional[int], optional): _description_. Defaults to None.
        """
        db = SessionLocal()
        try:
            # Calcular delta EIQ
            if eiq_alternative and eiq_base > 0:
                delta_eiq = ((eiq_base - eiq_alternative) / eiq_base) * 100
            else:
                delta_eiq = 0.0

            # Guardar en tabla específica
            intervention = InterventionEvent.InterventionEvent(
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
            kpi_log = KPILog.KPILog(
                kpi_type="KS1" if was_vetoed else "KS2",
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
                "kpi": "KS1" if was_vetoed else "KS2",
                "user_id": user_id,
                "parcel_id": parcel_id,
                "chemical": chemical_name,
                "category": chemical_category,
                "alternative": alternative_proposed,
                "vetoed": was_vetoed,
                "eiq_base": eiq_base,
                "eiq_alt": eiq_alternative,
                "delta_eiq": round(delta_eiq, 2)
            })

            print(
                f"[KPI-KS1] Intervención registrada: {chemical_name} ({'VETOED' if was_vetoed else 'APPROVED'})")

        except Exception as e:
            db.rollback()
            print(f"[KPI-ERROR] Error logging intervention: {e}")
        finally:
            db.close()

    # =========================================================================
    # KS3: PRECISIÓN HÍDRICA
    # =========================================================================

    def log_water_calculation(
        self,
        user_id: int,
        parcel_id: int,
        crop_type: str,
        development_stage: str,
        etc_theoretical: float,  # mm/día
        v_agent: float,  # litros/día
        p_eff: float,  # mm/día
        soil_type: Optional[str] = None,
        irrigation_type: Optional[str] = None,
        ndwi_value: Optional[float] = None,
        days_since_planting: Optional[int] = None,
    ):
        """Registra cálculo de prescripción hídrica (KS3)

        Args:
            user_id (int): _description_
            parcel_id (int): _description_
            crop_type (str): _description_
            development_stage (str): _description_
            etc_theoretical (float): _description_
            irrigation_type (Optional[str], optional): _description_. Defaults to None.
            ndwi_value (Optional[float], optional): _description_. Defaults to None.
            days_since_planting (Optional[int], optional): _description_. Defaults to None.
        """
        db = SessionLocal()
        try:
            # Obtener área de la parcela
            parcel = db.query(Parcel.Parcel).filter(
                Parcel.Parcel.id == parcel_id
            ).first()

            if not parcel:
                print(f"[KPI-ERROR] Parcela {parcel_id} no encontrada")
                return

            area_m2 = parcel.area * 10000  # hectáreas a m²
            # Necesidad neta en mm/día (ETc - P_eff)
            need_net_mm_day = max(0, etc_theoretical - p_eff)
            
            # Convertir necesidad neta a litros/día
            # 1 mm sobre 1 m² = 1 litro
            need_theoretical_liters = need_net_mm_day * area_m2
            
            # --- CÁLCULO DE WPA (Water Prescription Accuracy) ---
            if need_theoretical_liters == 0:
                # Caso: No se necesita riego (lluvia suficiente)
                if v_agent == 0:
                    # Perfecto: No se necesita y no se recomienda
                    wpa_score = 1.0
                    deviation_percent = 0.0
                else:
                    # Error: No se necesita pero se recomienda regar
                    # Penalización proporcional al exceso
                    wpa_score = 0.0
                    deviation_percent = 100.0
                    
            else:
                # Caso: Se necesita riego
                # Fórmula: WPA = 1 - |V_agente - Need_theoretical| / ETc_total
                
                # ETc total en litros (sin restar precipitación)
                etc_total_liters = etc_theoretical * area_m2
                
                # Desviación absoluta
                deviation_absolute = abs(v_agent - need_theoretical_liters)
                
                # Desviación relativa respecto a ETc (denominador estable)
                deviation_relative = deviation_absolute / etc_total_liters
                
                # WPA score
                wpa_score = max(0.0, 1.0 - deviation_relative)
                deviation_percent = deviation_relative * 100

            # --- VALIDACIONES DE CALIDAD ---
            # Detectar sobre-riego crítico (>50% de exceso)
            if need_theoretical_liters > 0:
                over_irrigation_ratio = v_agent / need_theoretical_liters
                if over_irrigation_ratio > 1.5:
                    print(f"[KPI-WARNING] Sobre-riego detectado: {over_irrigation_ratio:.1f}x necesidad")
            
            # Detectar sub-riego crítico (<50% de necesidad)
            if need_theoretical_liters > 0:
                under_irrigation_ratio = v_agent / need_theoretical_liters
                if under_irrigation_ratio < 0.5:
                    print(f"[KPI-WARNING] Sub-riego detectado: {under_irrigation_ratio:.1%} de necesidad")

            # --- GUARDAR EN BASE DE DATOS ---
            water_calc = WaterCalculation.WaterCalculation(
                user_id=user_id,
                parcel_id=parcel_id,
                crop_type=crop_type,
                development_stage=development_stage,
                days_since_planting=days_since_planting,
                etc_theoretical=etc_theoretical,
                p_eff=p_eff,
                v_agent=v_agent,
                need_theoretical_liters=need_theoretical_liters,  # Agregar este campo
                wpa_score=wpa_score,
                deviation_percent=deviation_percent,
                soil_type=soil_type,
                irrigation_type=irrigation_type,
                ndwi_value=ndwi_value
            )
            db.add(water_calc)

            # Log general
            kpi_log = KPILog.KPILog(
                kpi_type="KS3",
                event_type="calculo_hidrico",
                user_id=user_id,
                parcel_id=parcel_id,
                agent_source="water",
                metric_value=wpa_score,
                metric_metadata={
                    "etc_mm_day": etc_theoretical,
                    "p_eff_mm_day": p_eff,
                    "need_net_mm_day": need_net_mm_day,
                    "need_theoretical_liters": round(need_theoretical_liters, 2),
                    "v_agent_liters": v_agent,
                    "area_m2": area_m2,
                    "deviation_percent": round(deviation_percent, 2),
                    "wpa_score": round(wpa_score, 4)
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
                "etc_mm_day": etc_theoretical,
                "p_eff_mm_day": p_eff,
                "need_theoretical_liters": round(need_theoretical_liters, 2),
                "v_agent_liters": v_agent,
                "wpa_score": round(wpa_score, 4),
                "deviation_percent": round(deviation_percent, 2),
                "meets_target": deviation_percent < 10.0
            })

            # Log en consola con colores
            status = "✓ PASS" if deviation_percent < 10.0 else "✗ FAIL"
            print(f"[KPI-KS3] {status} | WPA={wpa_score:.3f} | Desv={deviation_percent:.1f}%")
            print(f"         Need={need_theoretical_liters:.0f}L | Agent={v_agent:.0f}L")

        except Exception as e:
            db.rollback()
            print(f"[KPI-ERROR] Error logging water calculation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

    # =========================================================================
    # KT2: DIAGNÓSTICO DEL VISION AGENT
    # =========================================================================

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
        """Registra diagnóstico del Vision Agent (KT2)

        Args:
            user_id (int): _description_
            diagnosis (str): _description_
            confidence (float): _description_
            processing_time (float): _description_
            image_size_kb (int): _description_
            image_conditions (Dict[str, Any]): _description_
            parcel_id (Optional[int], optional): _description_. Defaults to None.
            ground_truth (Optional[str], optional): _description_. Defaults to None.
        """
        db = SessionLocal()
        try:
            is_correct = None
            if ground_truth:
                is_correct = diagnosis.lower() == ground_truth.lower()

            diagnostic = VisionDiagnostic.VisionDiagnostic(
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

            kpi_log = KPILog.KPILog(
                kpi_type="KT2",
                event_type="diagnostico_vision",
                user_id=user_id,
                parcel_id=parcel_id,
                agent_source="vision",
                metric_value=confidence,
                metric_metadata={
                    "processing_time":processing_time,
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
                "processing_time":processing_time,
                "confidence": confidence,
                "correct": is_correct
            })

            print(
                f"[KPI-KT2] Diagnóstico registrado: {diagnosis} ({confidence:.2f})")

        except Exception as e:
            db.rollback()
            print(f"[KPI-ERROR] Error logging diagnosis: {e}")
        finally:
            db.close()

    # =========================================================================
    # KT1: EFICIENCIA DE ORQUESTACIÓN
    # =========================================================================

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
        """Registra eficiencia de orquestación (KT1)

        Args:
            user_id (int): _description_
            conversation_id (str): _description_
            query_text (str): _description_
            nodes_visited (List[str]): _description_
            nodes_minimum (int): _description_
            query_type (str): _description_
            has_image (bool, optional): _description_. Defaults to False.
        """
        db = SessionLocal()
        try:
            nodes_count = len(nodes_visited)
            g_eff = nodes_minimum / nodes_count if nodes_count > 0 else 0

            orchestration = OrchestrationEvent.OrchestrationEvent(
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

            kpi_log = KPILog.KPILog(
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

    # =========================================================================
    # KA3: LATENCIA DE INFERENCIA
    # =========================================================================

    def log_latency(
        self,
        user_id: int,
        conversation_id: str,
        total_time: float,
        time_breakdown: Dict[str, float],
        has_image: bool
    ):
        """Registra latencia de inferencia (KA3)

        Args:
            user_id (int): _description_
            conversation_id (str): _description_
            total_time (float): _description_
            time_breakdown (Dict[str, float]): _description_
            has_image (bool): _description_
        """
        db = SessionLocal()
        try:
            threshold = 60.0 if has_image else 65.0
            meets_threshold = total_time <= threshold

            latency = LatencyLog.LatencyLog(
                user_id=user_id,
                conversation_id=conversation_id,
                total_time=total_time,
                has_image=has_image,
                time_breakdown=time_breakdown,
                threshold=threshold,
                meets_threshold=meets_threshold
            )
            db.add(latency)

            kpi_log = KPILog.KPILog(
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

            print(
                f"[KPI-KA3] Latencia registrada: {total_time:.2f}s ({'✓' if meets_threshold else '✗'})")

        except Exception as e:
            db.rollback()
            print(f"[KPI-ERROR] Error logging latency: {e}")
        finally:
            db.close()

    # =========================================================================
    # KE1: ALERTAS DE RIESGO
    # =========================================================================

    def log_risk_alert(
        self,
        user_id: int,
        parcel_id: int,
        risk_type: str,
        probability: float,
        projected_loss: float,
        hours_before_event: int
    ):
        """
        Registra alerta de riesgo (KE1)
        """
        db = SessionLocal()
        try:
            alert = RiskAlert.RiskAlert(
                user_id=user_id,
                parcel_id=parcel_id,
                risk_type=risk_type,
                probability=probability,
                projected_loss=projected_loss,
                alert_sent_at=datetime.now(),
                hours_before_event=hours_before_event
            )
            db.add(alert)

            kpi_log = KPILog.KPILog(
                kpi_type="KE1",
                event_type="alerta_riesgo",
                user_id=user_id,
                parcel_id=parcel_id,
                agent_source="risk",
                metric_value=projected_loss,
                metric_metadata={
                    "risk_type": risk_type,
                    "probability": probability,
                    "hours_before": hours_before_event
                },
                success=True
            )
            db.add(kpi_log)
            db.commit()

            self._log_to_file('risk_alerts', {
                "timestamp": datetime.now().isoformat(),
                "kpi": "KE1",
                "user_id": user_id,
                "parcel_id": parcel_id,
                "risk_type": risk_type,
                "probability": probability,
                "projected_loss": projected_loss
            })

            print(
                f"[KPI-KE1] Alerta registrada: {risk_type} (${projected_loss:.2f})")

        except Exception as e:
            db.rollback()
            print(f"[KPI-ERROR] Error logging risk alert: {e}")
        finally:
            db.close()

kpi_logger = KPILogger()
