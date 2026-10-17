"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.auth_repo import AuthRepository
from app.db.urls_repo import UrlRepository
from app.services.auth_service import AuthService
from app.services.url_service import UrlService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_url_service(request: Request, settings: SettingsDep) -> UrlService:
    return UrlService(UrlRepository(request.app.state.engine), settings)


def get_auth_service(request: Request, settings: SettingsDep) -> AuthService:
    return AuthService(AuthRepository(request.app.state.engine), settings)


UrlServiceDep = Annotated[UrlService, Depends(get_url_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

_bearer = HTTPBearer(auto_error=False)  # also adds the "Authorize" button to /docs


def get_current_user_id(
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> int:
    if credentials is None:
        raise UnauthorizedError("Not authenticated.")
    return decode_access_token(credentials.credentials, settings.jwt_secret)


CurrentUserDep = Annotated[int, Depends(get_current_user_id)]