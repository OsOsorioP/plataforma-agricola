from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    image_base64: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    content: str
    sender: str
    isMe: bool
    attachement: Optional[str] = None