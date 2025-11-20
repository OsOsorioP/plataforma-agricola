# plataforma-agricola-backend/app/models/user.py

from typing import Optional
from pydantic import BaseModel, EmailStr

# Modelo para recibir los datos del Login (ESTE ES EL NUEVO)
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 1. Base: Campos comunes
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    avatar: Optional[str] = None

# 2. Create: Hereda de Base y añade password
class UserCreate(UserBase):
    password: str

# 3. Response: Hereda de Base y añade ID (sin password)
class User(UserBase):
    id: int
    is_active: bool = True
    
    class Config:
        from_attributes = True