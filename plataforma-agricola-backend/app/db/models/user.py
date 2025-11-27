from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base

from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String(50), nullable=False)
    hashed_password = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now())

    parcels = relationship("Parcel", back_populates="owner",
                           cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user")
    alerts = relationship("Alert", back_populates="user")