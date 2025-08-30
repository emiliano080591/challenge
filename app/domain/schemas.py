from typing import Optional, List, Literal
from pydantic import BaseModel, Field

Role = Literal["user", "bot"]


class MessageOut(BaseModel):
    role: Role
    message: str = Field(alias="content")

    class Config:
        populate_by_name = True


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    message: List[MessageOut]
