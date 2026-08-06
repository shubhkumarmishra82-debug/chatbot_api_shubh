from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None  # omit to start a new conversation


class SourceOut(BaseModel):
    title: str
    link: str


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    answer_type: str  # "custom" | "search" | "fallback"
    sources: list[SourceOut] = []


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]


class CustomReplyIn(BaseModel):
    trigger: str   # comma-separated keywords, e.g. "hi,hello,hey"
    response: str


class CustomReplyOut(BaseModel):
    id: str
    trigger: str
    response: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyOut(BaseModel):
    api_key: str
    status: str


class MemoryNoteIn(BaseModel):
    note: str


class MemoryNoteOut(BaseModel):
    id: str
    note: str
    created_at: datetime

    class Config:
        from_attributes = True
