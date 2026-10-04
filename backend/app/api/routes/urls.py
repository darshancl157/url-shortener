"""URL endpoints.

`redirect_router` holds the catch-all `GET /{short_id}` and must be registered last,
so it doesn't swallow `/stats/...`, `/health`, `/docs`, etc.
"""
from fastapi import APIRouter

# from app.api.deps import UrlServiceDep
from app.schemas.url import ErrorResponse

router = APIRouter(tags=["urls"])
redirect_router = APIRouter(tags=["redirect"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Short code not found"}}