from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

from datetime import datetime
import enum


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String(50), nullable=False)
    hashed_password = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now())

    parcels = relationship("Parcel", back_populates="owner",
                           cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user")
    alerts = relationship("Alert", back_populates="user")


class CropType(str, enum.Enum):
    MAIZ = "maiz"
    TRIGO = "trigo"
    SOJA = "soja"
    CAFE = "cafe"
    ARROZ = "arroz"
    PAPA = "papa"
    TOMATE = "tomate"
    HORTALIZAS = "hortalizas"
    PLATANO = "platano"
    OTROS = "otros"


class DevelopmentStage(str, enum.Enum):
    PREPARACION = "preparacion"
    SIEMBRA = "siembra"
    GERMINACION = "germinacion"
    CRECIMIENTO = "crecimiento"
    FLORACION = "floracion"
    MADURACION = "maduracion"
    COSECHA = "cosecha"


class Parcel(Base):
    __tablename__ = 'parcels'

    # Identificación básica
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    area = Column(Float, nullable=False)  # en hectáreas
    geometry = Column(String)  # Coordenadas

    # Información del cultivo
    crop_type = Column(Enum(CropType), index=True)
    development_stage = Column(Enum(DevelopmentStage), index=True)
    planting_date = Column(DateTime)

    # Características clave del suelo
    soil_type = Column(String)  # arcilloso, arenoso, franco
    soil_ph = Column(Float)

    # Sistema de riego
    irrigation_type = Column(String)  # goteo, aspersión, secano

    # Estado actual del cultivo
    health_status = Column(String)  # bueno, regular, malo
    current_issues = Column(Text)  # Plagas o problemas actuales

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="parcels")
    recommendations = relationship(
        "Recommendation", back_populates="parcel", cascade="all, delete-orphan")
    kpi_metrics = relationship(
        "KPIMetric", back_populates="parcel", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = 'chat_message'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # El session_id nos va a permitir agrupar conversaciones, se implementará a futuro.
    # session_id = Column(String, index=True)
    sender_type = Column(String, nullable=False)  # 'user' o 'ai'
    content = Column(String, nullable=False)
    attachement = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parcel_id = Column(Integer, ForeignKey("parcels.id"), nullable=False)
    risk_type = Column(String, index=True)  # "HELADA", "OLA_DE_CALOR", "PLAGA"
    message = Column(String)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="alerts")


class Recommendation(Base):
    __tablename__ = 'recommendations'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parcel_id = Column(Integer, ForeignKey('parcels.id'), nullable=False)
    # ej. "water_agent", "production_agent"
    agent_source = Column(String, nullable=False)
    recommendation_text = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, applied, discarded
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recommendations")
    parcel = relationship("Parcel", back_populates="recommendations")


class KPIMetric(Base):
    __tablename__ = 'kpi_metrics'

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey('parcels.id'), nullable=False)
    # ej. "SOIL_HEALTH_NDVI", "WATER_EFFICIENCY_LITERS"
    kpi_name = Column(String, index=True, nullable=False)
    value = Column(Float, nullable=False)
    # Opcional: para vincular una métrica a una recomendación que la generó
    recommendation_id = Column(Integer, ForeignKey(
        "recommendations.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    parcel = relationship("Parcel", back_populates="kpi_metrics")


class KPILog(Base):
    """
    Tabla general para logs de eventos de KPIs.
    Almacena todos los eventos del sistema para análisis posterior.
    """
    __tablename__ = 'kpi_logs'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # Clasificación del evento
    # KS1, KS2, KS3, KT1, KT2, KE1, KA2, KA3
    kpi_type = Column(String, index=True)
    # intercepcion, calculo_agua, diagnostico, etc.
    event_type = Column(String, index=True)

    # Contexto del evento
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parcel_id = Column(Integer, ForeignKey('parcels.id'), nullable=True)
    # Para trackear conversación completa
    conversation_id = Column(String, nullable=True)
    # production, water, risk, sustainability, vision, supervisor
    agent_source = Column(String)

    # Métricas
    metric_value = Column(Float)  # Valor principal del KPI
    metric_metadata = Column(JSON)  # Datos adicionales en formato JSON

    # Estado del evento
    success = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)

    # Relaciones
    user = relationship("User")
    parcel = relationship("Parcel")


class InterventionEvent(Base):
    """
    Tabla específica para KS1 y KS2: Intervenciones del Sustainability Agent
    """
    __tablename__ = 'intervention_events'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # Contexto
    user_id = Column(Integer, ForeignKey('users.id'))
    parcel_id = Column(Integer, ForeignKey('parcels.id'), nullable=True)
    # Quién propuso el químico (production, vision)
    agent_source = Column(String)

    # Información del químico propuesto
    chemical_proposed = Column(String, nullable=False)
    chemical_category = Column(String)  # Ia, Ib, II, III, IV

    # Resultado de la intervención
    was_vetoed = Column(Boolean, nullable=False)
    veto_reason = Column(Text)
    alternative_proposed = Column(Text)

    # Métricas EIQ
    eiq_base = Column(Float)
    eiq_alternative = Column(Float, nullable=True)
    delta_eiq_percent = Column(Float)

    # Seguimiento
    # Si usuario aceptó la alternativa
    user_accepted = Column(Boolean, nullable=True)

    # Relaciones
    user = relationship("User")
    parcel = relationship("Parcel")


class WaterCalculation(Base):
    """
    Tabla específica para KS3: Cálculos de prescripción hídrica
    """
    __tablename__ = 'water_calculations'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # Contexto
    user_id = Column(Integer, ForeignKey('users.id'))
    parcel_id = Column(Integer, ForeignKey('parcels.id'))

    # Información del cultivo
    crop_type = Column(String)
    development_stage = Column(String)
    days_since_planting = Column(Integer)

    # Cálculos
    etc_theoretical = Column(Float)  # mm/día (Penman-Monteith)
    p_eff = Column(Float)  # mm/día (precipitación efectiva)
    v_agent = Column(Float)  # litros/día (recomendado por agente)

    # Métricas
    wpa_score = Column(Float)  # Precisión de prescripción hídrica
    deviation_percent = Column(Float)

    # Contexto adicional
    soil_type = Column(String)
    irrigation_type = Column(String)
    ndwi_value = Column(Float)  # Valor NDWI usado para ajuste

    # Relaciones
    user = relationship("User")
    parcel = relationship("Parcel")


class VisionDiagnostic(Base):
    """
    Tabla específica para KT2: Diagnósticos del Vision Agent
    """
    __tablename__ = 'vision_diagnostics'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # Contexto
    user_id = Column(Integer, ForeignKey('users.id'))
    parcel_id = Column(Integer, ForeignKey('parcels.id'), nullable=True)

    # Diagnóstico
    diagnosis = Column(String, nullable=False)
    confidence = Column(Float)  # 0-1

    # Validación (llenado posteriormente por experto o usuario)
    ground_truth = Column(String, nullable=True)
    is_correct = Column(Boolean, nullable=True)

    # Condiciones de la imagen
    image_conditions = Column(JSON)  # {lighting, distance, focus, etc.}
    image_size_kb = Column(Integer)

    # Tiempos
    processing_time = Column(Float)  # segundos

    # Relaciones
    user = relationship("User")
    parcel = relationship("Parcel")


class OrchestrationEvent(Base):
    """
    Tabla específica para KT1: Eficiencia de orquestación
    """
    __tablename__ = 'orchestration_events'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # Contexto
    user_id = Column(Integer, ForeignKey('users.id'))
    conversation_id = Column(String, unique=True, index=True)

    # Query del usuario
    query_text = Column(Text)
    query_type = Column(String)  # riego, diagnostico, precio, multi-dominio
    has_image = Column(Boolean, default=False)

    # Métricas de orquestación
    nodes_visited = Column(JSON)  # Lista de agentes visitados en orden
    nodes_count = Column(Integer)
    nodes_minimum = Column(Integer)  # Cantidad mínima necesaria
    g_eff = Column(Float)  # Eficiencia de orquestación

    # Relaciones
    user = relationship("User")


class LatencyLog(Base):
    """
    Tabla específica para KA3: Latencia de inferencia
    """
    __tablename__ = 'latency_logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # Contexto
    user_id = Column(Integer, ForeignKey('users.id'))
    conversation_id = Column(String, index=True)

    # Métricas de tiempo
    total_time = Column(Float)  # segundos
    has_image = Column(Boolean)

    # Desglose de tiempos
    time_breakdown = Column(JSON)  # {supervisor: 0.3, agent: 2.1, db: 0.4}

    # Evaluación
    threshold = Column(Float)  # 5s para texto, 10s para imagen
    meets_threshold = Column(Boolean)

    # Relaciones
    user = relationship("User")


class RiskAlert(Base):
    """
    Tabla específica para KE1: Alertas de riesgo y valor mitigado
    """
    __tablename__ = 'risk_alerts'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # Contexto
    user_id = Column(Integer, ForeignKey('users.id'))
    parcel_id = Column(Integer, ForeignKey('parcels.id'))

    # Información del riesgo
    risk_type = Column(String)  # helada, granizo, sequia, ola_calor
    probability = Column(Float)  # 0-1
    projected_loss = Column(Float)  # USD

    # Alerta
    alert_sent_at = Column(DateTime)
    hours_before_event = Column(Integer)

    # Seguimiento
    user_action_taken = Column(Boolean, nullable=True)
    action_description = Column(Text, nullable=True)

    # Resultado real
    actual_event_occurred = Column(Boolean, nullable=True)
    actual_loss = Column(Float, nullable=True)
    value_saved = Column(Float, nullable=True)  # Calculado post-evento

    # Relaciones
    user = relationship("User")
    parcel = relationship("Parcel")


class FeedbackLog(Base):
    """
    Tabla para capturar feedback de usuarios sobre respuestas del sistema
    """
    __tablename__ = 'feedback_logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)

    # Contexto
    user_id = Column(Integer, ForeignKey('users.id'))
    conversation_id = Column(String)

    # Feedback
    was_helpful = Column(Boolean)
    accuracy_rating = Column(Integer)  # 1-5
    recommendation_followed = Column(Boolean)

    # Texto libre
    actual_result = Column(Text, nullable=True)
    ground_truth_diagnosis = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)

    # Relaciones
    user = relationship("User")
