from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

from datetime import datetime
import enum

class Recommendation(Base):
    __tablename__ = 'recommendations'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parcel_id = Column(Integer, ForeignKey('parcels.id'), nullable=False)
    # ej. "water_agent", "production_agent"
    agent_source = Column(String, nullable=False)
    recommendation_text = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, applied, discarded
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recommendations")
    parcel = relationship("Parcel", back_populates="recommendations")