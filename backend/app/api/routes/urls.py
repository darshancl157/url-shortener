"""URL endpoints.

`redirect_router` holds the catch-all `GET /{short_id}` and must be registered last,
so it doesn't swallow `/api/...`, `/health`, `/docs`, etc.
"""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUserDep, SettingsDep, UrlServiceDep
from app.core.config import Settings
from app.schemas.url import (
    ErrorResponse,
    ShortenRequest,
    ShortenResponse,
    StatsResponse,
    UrlListItem,
    UrlListResponse,
)

router = APIRouter(tags=["urls"])
redirect_router = APIRouter(tags=["redirect"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Short code not found"}}
UNAUTHORIZED = {401: {"model": ErrorResponse, "description": "Not authenticated"}}
BAD_INPUT = {
    400: {"model": ErrorResponse, "description": "Invalid input"},
    409: {"model": ErrorResponse, "description": "Alias already taken"},
}


def _short_url(settings: Settings, short_id: str) -> str:
    return f"{settings.base_url}/{short_id}"


@router.post(
    "/api/shortenurl",
    response_model=ShortenResponse,
    status_code=201,
    responses={**BAD_INPUT, **UNAUTHORIZED},
)
def shorten(
    body: ShortenRequest, user_id: CurrentUserDep, service: UrlServiceDep, settings: SettingsDep
) -> ShortenResponse:
    short_id, long_url = service.shorten(body.long_url, body.custom_alias, body.expires_at, user_id)
    return ShortenResponse(
        short_id=short_id,
        short_url=_short_url(settings, short_id),
        long_url=long_url,
        expires_at=body.expires_at,
    )


@router.get(
    "/api/urls",
    response_model=UrlListResponse,
    responses={400: BAD_INPUT[400], **UNAUTHORIZED},
)
def list_urls(
    user_id: CurrentUserDep,
    service: UrlServiceDep,
    settings: SettingsDep,
    limit: int = 50,
    offset: int = 0,
) -> UrlListResponse:
    rows, total = service.list_urls(user_id, limit, offset)
    items = [UrlListItem(**row, short_url=_short_url(settings, row["short_id"])) for row in rows]
    return UrlListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/api/stats/{short_id}", response_model=StatsResponse, responses={**NOT_FOUND, **UNAUTHORIZED}
)
def stats(short_id: str, user_id: CurrentUserDep, service: UrlServiceDep) -> StatsResponse:
    return StatsResponse(**service.stats(short_id, user_id))


@redirect_router.get("/{short_id}", status_code=302, responses=NOT_FOUND, response_class=RedirectResponse)
def redirect(short_id: str, service: UrlServiceDep) -> RedirectResponse:
    return RedirectResponse(service.resolve(short_id), status_code=302)