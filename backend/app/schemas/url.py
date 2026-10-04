"""Pydantic models for request/response bodies."""

from datetime import datetime
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    detail: str

class ShortenRequest(BaseModel):
    long_url: str
    custom_alias: str | None = None
    expires_at: datetime | None = None

class ShortenResponse(BaseModel):
    short_id: str
    short_url: str
    long_url: str
    expires_at: datetime | None = None

class StatsResponse(BaseModel):
    short_id: str
    long_url: str
    created_at: datetime
    expires_at: datetime | None = None
    click_count: int
    is_disabled: bool