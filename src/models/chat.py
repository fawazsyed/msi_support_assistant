"""
Chat-related Pydantic models for API requests/responses.
"""

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Request body for chat endpoints."""
    messages: list[ChatMessage]