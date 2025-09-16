from pydantic import BaseModel

class ParcelBase(BaseModel):
    name: str
    location: str | None=None
    area: float
    
class ParcelCreate(ParcelBase):
    pass

class Parcel(ParcelBase):
    id: int
    owner_id: int
    
    class Config:
        from_attribute = True