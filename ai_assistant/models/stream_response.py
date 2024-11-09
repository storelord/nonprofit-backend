from typing import Literal, Union

from pydantic import BaseModel, Field


class AIResponseContent(BaseModel):
    type: Literal["content"] = "content"
    data: str = Field(..., description="The content chunk of the AI response")


class AIResponseSummary(BaseModel):
    type: Literal["summary"] = "summary"
    data: str = Field(..., description="The entire message from the chatbot")


class AIResponseError(BaseModel):
    type: Literal["error"] = "error"
    data: str = Field(..., description="Error message if something went wrong")


AIResponse = Union[AIResponseContent, AIResponseSummary, AIResponseError]


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's input message")
