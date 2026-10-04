"""Pydantic models for request/response bodies and internal records."""

from pydantic import BaseModel

class ErrorResponse(BaseModel):
    detail: str
