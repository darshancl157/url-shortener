"""Request/response bodies for /api/auth."""

from datetime import datetime

from pydantic import BaseModel


class Credentials(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime