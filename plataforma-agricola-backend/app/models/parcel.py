from pydantic import BaseModel

class ParcelBase(BaseModel):
    name: str
    location: str | None=None
    are: float
    
class ParcelCreate(ParcelBase):
    pass

class Parcel(ParcelBase):
    id: int
    owner_id: int
    
    class Config:
        from_attribute = True