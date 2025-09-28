from pydantic import BaseModel
from datetime import datetime

class Alert(BaseModel):
    id: int
    risk_type: str
    message: str
    timestamp: datetime
    class Config:
        from_attributes = True