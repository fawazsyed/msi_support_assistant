"""
Authentication-related Pydantic models for OAuth/JWT flows.
"""

from pydantic import BaseModel, Field


class RegistrationRequest(BaseModel):
    """OAuth client registration request."""
    redirect_uris: list[str]
    client_name: str = Field(default="client")  # Reserved for future stateful implementation