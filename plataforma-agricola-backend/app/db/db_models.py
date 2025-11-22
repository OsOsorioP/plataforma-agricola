from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
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

    parcels = relationship("Parcel", back_populates="owner", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user")
    alerts = relationship("Alert", back_populates="user")
    
class CropType(str, enum.Enum):
    MAIZ = "maiz"
    TRIGO = "trigo"
    SOJA = "soja"
    CAFE = "cafe"
    HORTALIZAS = "hortalizas"
    OTROS = "otros"

class DevelopmentStage(str, enum.Enum):
    PREPARACION = "preparacion"
    SIEMBRA = "siembra"
    CRECIMIENTO = "crecimiento"
    FLORACION = "floracion"
    COSECHA = "cosecha"

class Parcel(Base):
    __tablename__ = 'parcels'
    
    # Identificación básica
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    area = Column(Float, nullable=False) # en hectáreas
    geometry = Column(String) # Coordenadas
    
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
    recommendations = relationship("Recommendation", back_populates="parcel", cascade="all, delete-orphan")
    kpi_metrics = relationship("KPIMetric", back_populates="parcel", cascade="all, delete-orphan")
    
class ChatMessage(Base):
    __tablename__ = 'chat_message'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # El session_id nos va a permitir agrupar conversaciones, se implementará a futuro.
    # session_id = Column(String, index=True)
    sender_type = Column(String, nullable=False) # 'user' o 'ai'
    content = Column(String, nullable=False)
    attachement = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parcel_id = Column(Integer, ForeignKey("parcels.id"), nullable=False)
    risk_type = Column(String, index=True) # "HELADA", "OLA_DE_CALOR", "PLAGA"
    message = Column(String)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="alerts")
    
class Recommendation(Base):
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parcel_id = Column(Integer, ForeignKey('parcels.id'), nullable=False)
    agent_source = Column(String, nullable=False) # ej. "water_agent", "production_agent"
    recommendation_text = Column(String, nullable=False)
    status = Column(String, default="pending") # pending, applied, discarded
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="recommendations")
    parcel = relationship("Parcel", back_populates="recommendations")
    
class KPIMetric(Base):
    __tablename__ = 'kpi_metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey('parcels.id'), nullable=False)
    kpi_name = Column(String, index=True, nullable=False) # ej. "SOIL_HEALTH_NDVI", "WATER_EFFICIENCY_LITERS"
    value = Column(Float, nullable=False)
    # Opcional: para vincular una métrica a una recomendación que la generó
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=True) 
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    parcel = relationship("Parcel", back_populates="kpi_metrics")