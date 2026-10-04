"""URL endpoints.

`redirect_router` holds the catch-all `GET /{short_id}` and must be registered last,
so it doesn't swallow `/api/...`, `/health`, `/docs`, etc.
"""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.api.deps import SettingsDep, UrlServiceDep
from app.schemas.url import ErrorResponse, ShortenRequest, ShortenResponse, StatsResponse

router = APIRouter(tags=["urls"])
redirect_router = APIRouter(tags=["redirect"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Short code not found"}}
BAD_INPUT = {
    400: {"model": ErrorResponse, "description": "Invalid input"},
    409: {"model": ErrorResponse, "description": "Alias already taken"},
}


@router.post("/api/shortenurl", response_model=ShortenResponse, status_code=201, responses=BAD_INPUT)
def shorten(body: ShortenRequest, service: UrlServiceDep, settings: SettingsDep) -> ShortenResponse:
    short_id, long_url = service.shorten(body.long_url, body.custom_alias, body.expires_at)
    return ShortenResponse(
        short_id=short_id,
        short_url=f"{settings.base_url}/{short_id}",
        long_url=long_url,
        expires_at=body.expires_at,
    )


@router.get("/api/stats/{short_id}", response_model=StatsResponse, responses=NOT_FOUND)
def stats(short_id: str, service: UrlServiceDep) -> StatsResponse:
    return StatsResponse(**service.stats(short_id))


@redirect_router.get("/{short_id}", status_code=302, responses=NOT_FOUND, response_class=RedirectResponse)
def redirect(short_id: str, service: UrlServiceDep) -> RedirectResponse:
    return RedirectResponse(service.resolve(short_id), status_code=302)