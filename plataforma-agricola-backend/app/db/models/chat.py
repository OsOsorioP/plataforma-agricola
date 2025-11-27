from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class ChatMessage(Base):
    __tablename__ = 'chat_message'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # El session_id nos va a permitir agrupar conversaciones, se implementará a futuro.
    # session_id = Column(String, index=True)
    sender_type = Column(String, nullable=False)  # 'user' o 'ai'
    content = Column(String, nullable=False)
    attachement = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())