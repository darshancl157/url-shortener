"""Auth endpoints. The access token goes in the response body; the refresh token only
ever travels in an HttpOnly cookie scoped to /api/auth."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Response
from fastapi.responses import JSONResponse

from app.api.deps import AuthServiceDep, CurrentUserDep, SettingsDep
from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.schemas.auth import Credentials, TokenResponse, UserResponse
from app.schemas.url import ErrorResponse
from app.services.auth_service import TokenPair

router = APIRouter(prefix="/api/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"
COOKIE_PATH = "/api/auth"
_COOKIE_FLAGS = {"path": COOKIE_PATH, "httponly": True, "secure": True, "samesite": "strict"}

UNAUTHORIZED = {401: {"model": ErrorResponse, "description": "Not authenticated"}}
RefreshCookie = Annotated[str | None, Cookie(alias=REFRESH_COOKIE)]


def _issue(pair: TokenPair, response: Response, settings: Settings) -> TokenResponse:
    response.set_cookie(
        REFRESH_COOKIE,
        pair.refresh_token,
        max_age=settings.refresh_token_ttl_days * 24 * 3600,
        **_COOKIE_FLAGS,
    )
    return TokenResponse(
        access_token=pair.access_token, expires_in=settings.access_token_ttl_minutes * 60
    )


def _clear_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, **_COOKIE_FLAGS)


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: Credentials, service: AuthServiceDep) -> UserResponse:
    user_id = service.register(body.email, body.password)
    return UserResponse(**service.get_user(user_id))


@router.post("/login", response_model=TokenResponse, responses=UNAUTHORIZED)
def login(
    body: Credentials, response: Response, service: AuthServiceDep, settings: SettingsDep
) -> TokenResponse:
    return _issue(service.login(body.email, body.password), response, settings)


@router.post("/refresh", response_model=TokenResponse, responses=UNAUTHORIZED)
def refresh(
    response: Response,
    service: AuthServiceDep,
    settings: SettingsDep,
    refresh_token: RefreshCookie = None,
):
    try:
        pair = service.refresh(refresh_token)
    except UnauthorizedError as exc:
        failed = JSONResponse(status_code=401, content={"detail": exc.message})
        _clear_cookie(failed)  # a dead cookie is useless; stop the browser sending it
        return failed
    return _issue(pair, response, settings)


@router.post("/logout", status_code=204)
def logout(service: AuthServiceDep, refresh_token: RefreshCookie = None) -> Response:
    service.logout(refresh_token)
    done = Response(status_code=204)
    _clear_cookie(done)
    return done


@router.get("/me", response_model=UserResponse, responses=UNAUTHORIZED)
def me(user_id: CurrentUserDep, service: AuthServiceDep) -> UserResponse:
    return UserResponse(**service.get_user(user_id))