"""Business rules: validation, ID generation, lookups."""

import re
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Protocol
from urllib.parse import urlsplit

from app.core.config import Settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    IdGenerationError,
    NotFoundError,
)

ALPHABET = string.ascii_letters + string.digits
ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{3,10}$")  # urls.short_id is VARCHAR(10)
RESERVED = {"api", "docs", "redoc", "openapi.json", "health", "stats"}


class UrlRepo(Protocol):
    def insert(self, short_id: str, long_url: str, expires_at: datetime | None) -> bool: ...
    def hit(self, short_id: str) -> str | None: ...
    def stats(self, short_id: str) -> dict[str, Any] | None: ...


class UrlService:
    def __init__(self, repo: UrlRepo, settings: Settings):
        self._repo = repo
        self._s = settings

    def shorten(
        self, long_url: str, custom_alias: str | None, expires_at: datetime | None
    ) -> tuple[str, str]:
        """Returns (short_id, normalized long_url)."""
        long_url = self._validate_url(long_url)
        if expires_at is not None:
            if expires_at.tzinfo is None:
                raise BadRequestError("expires_at must include a timezone.")
            if expires_at <= datetime.now(timezone.utc):
                raise BadRequestError("expires_at must be in the future.")

        if custom_alias:
            if not ALIAS_RE.match(custom_alias) or custom_alias.lower() in RESERVED:
                raise BadRequestError(
                    "Alias must be 3-10 characters (letters, digits, - or _) and not reserved."
                )
            if not self._repo.insert(custom_alias, long_url, expires_at):
                raise ConflictError("That alias is already taken.")
            return custom_alias, long_url

        for _ in range(self._s.max_id_attempts):
            short_id = "".join(secrets.choice(ALPHABET) for _ in range(self._s.short_id_length))
            if short_id.lower() in RESERVED:
                continue
            if self._repo.insert(short_id, long_url, expires_at):
                return short_id, long_url
        raise IdGenerationError()

    def resolve(self, short_id: str) -> str:
        long_url = self._repo.hit(short_id)
        if long_url is None:
            raise NotFoundError()
        return long_url

    def stats(self, short_id: str) -> dict[str, Any]:
        row = self._repo.stats(short_id)
        if row is None:
            raise NotFoundError()
        return row

    def _validate_url(self, value: str) -> str:
        value = value.strip()
        if not value or len(value) > self._s.max_url_length:
            raise BadRequestError(f"URL must be 1-{self._s.max_url_length} characters.")
        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise BadRequestError("URL must start with http:// or https:// and include a host.")
        return value