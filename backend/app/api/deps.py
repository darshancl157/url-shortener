"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.db.urls_repo import UrlRepository
from app.services.url_service import UrlService


def get_url_service(request: Request) -> UrlService:
    return UrlService(UrlRepository(request.app.state.engine), get_settings())


UrlServiceDep = Annotated[UrlService, Depends(get_url_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]