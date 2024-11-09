from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    message: str
    id: str
    date: datetime
    role: Literal["assistant", "user"]


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] | None = None
    model: str | None = Field(
        default="gpt-3.5-turbo", description="The AI model to use for the response"
    )
    temperature: float | None = Field(
        default=0.7, ge=0, le=1, description="Controls randomness in the response"
    )
    max_tokens: int | None = Field(
        default=None, ge=1, description="Maximum number of tokens in the response"
    )
