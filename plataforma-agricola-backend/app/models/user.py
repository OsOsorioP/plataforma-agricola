from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    password: str
    
class UserCreate(UserBase):
    avatar: Optional[str] = None
    full_name: str
    
class User(UserBase):
    id: int
    is_active: bool = True
    
    class Config:
        from_attributes = True