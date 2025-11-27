# app/models/parcel.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ParcelBase(BaseModel):
    name: str = Field(..., description="Nombre de la parcela")
    location: Optional[str] = Field(None, description="Coordenadas lat,lon")
    area: float = Field(..., description="Área en hectáreas")
    geometry: Optional[str] = Field(None, description="GeoJSON del polígono")
    
    # Nuevos campos opcionales - Información del cultivo
    crop_type: Optional[str] = Field(None, description="Tipo de cultivo: maiz, cafe, tomate, etc.")
    development_stage: Optional[str] = Field(None, description="Etapa: preparacion, siembra, crecimiento, floracion, cosecha")
    planting_date: Optional[datetime] = Field(None, description="Fecha de siembra del cultivo actual")
    
    # Nuevos campos opcionales - Características del suelo
    soil_type: Optional[str] = Field(None, description="Tipo de suelo: arcilloso, arenoso, franco, limoso")
    soil_ph: Optional[float] = Field(None, ge=0, le=14, description="pH del suelo (0-14)")
    
    # Nuevos campos opcionales - Sistema de riego
    irrigation_type: Optional[str] = Field(None, description="Sistema de riego: goteo, aspersion, inundacion, secano")
    
    # Nuevos campos opcionales - Estado actual del cultivo
    health_status: Optional[str] = Field(None, description="Estado de salud: excelente, bueno, regular, malo")
    current_issues: Optional[str] = Field(None, description="Problemas actuales detectados o reportados")

class ParcelCreate(ParcelBase):
    """Modelo para crear una nueva parcela"""
    pass

class ParcelUpdate(BaseModel):
    """Modelo para actualizar información de una parcela existente"""
    name: Optional[str] = None
    crop_type: Optional[str] = None
    development_stage: Optional[str] = None
    planting_date: Optional[datetime] = None
    soil_type: Optional[str] = None
    soil_ph: Optional[float] = Field(None, ge=0, le=14)
    irrigation_type: Optional[str] = None
    health_status: Optional[str] = None
    current_issues: Optional[str] = None

class Parcel(ParcelBase):
    """Modelo completo de parcela con datos del sistema"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True