from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class KPIMetricCreate(BaseModel):
    kpi_name: str
    value: float
    recommendation_id: Optional[int] = None


class KPIMetricResponse(BaseModel):
    id: int
    kpi_name: str
    value: float
    timestamp: datetime

    class Config:
        from_attributes = True
