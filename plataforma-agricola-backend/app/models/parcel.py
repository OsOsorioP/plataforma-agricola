from pydantic import BaseModel
from typing import Optional

class ParcelBase(BaseModel):
    name: str
    location: Optional[str] = None
    area: float
    geometry: Optional[str] = None
    
class ParcelCreate(ParcelBase):
    pass

class Parcel(ParcelBase):
    id: int
    owner_id: int
    
    class Config:
        from_attribute = True