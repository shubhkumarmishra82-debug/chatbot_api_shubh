"""
Schemas matching OpenAI's /v1/chat/completions shape, plus a couple of
optional extension fields (web_search, use_documents) that OpenAI's real
API doesn't have -- clients that don't send them get sensible defaults,
so this stays a drop-in-compatible client target.
"""
from typing import List, Optional
from pydantic import BaseModel


class OAIMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "gms-default"
    messages: List[OAIMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    # Extensions beyond standard OpenAI fields:
    web_search: Optional[bool] = None       # None = auto-decide, True/False = force
    use_documents: Optional[bool] = True    # search your own document knowledge base


class OAIChoice(BaseModel):
    index: int
    message: OAIMessage
    finish_reason: str


class OAIUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[OAIChoice]
    usage: OAIUsage
    gms_answer_type: str  # extension: "calculator" | "custom" | "ai" | "search" | "fallback"
