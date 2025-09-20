from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String(50), nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now())

    parcels = relationship("Parcel", back_populates="owner")

class Parcel(Base):
    __tablename__ = 'parcels'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    area = Column(Float)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="parcels")
    
class ChatMessage(Base):
    __tablename__ = 'chat_message'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # El session_id nos va a permitir agrupar conversaciones, se implementará a futuro.
    # session_id = Column(String, index=True)
    sender_type = Column(String, nullable=False) # 'user' o 'ai'
    message = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())