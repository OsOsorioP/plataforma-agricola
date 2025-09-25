from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    image_base64: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str