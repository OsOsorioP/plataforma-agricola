from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    
class UserCreate(BaseModel):
    password: str
    
class User(BaseModel):
    id: int
    is_active: bool = True
    
    class Config:
        from_attributes = True