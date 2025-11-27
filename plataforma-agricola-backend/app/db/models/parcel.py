from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

import enum

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