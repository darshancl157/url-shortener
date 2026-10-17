"""Auth rules: registration, login, refresh-token rotation with reuse detection, logout."""

import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import cache
from typing import Any, Protocol
from uuid import UUID

from app.core.config import Settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    password_needs_rehash,
    verify_password,
)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD, MAX_PASSWORD = 8, 128
INVALID_LOGIN = "Invalid email or password."
INVALID_REFRESH = "Session expired. Please log in again."


class AuthRepo(Protocol):
    def create_user(self, email: str, password_hash: str) -> int | None: ...
    def get_user_by_email(self, email: str) -> dict[str, Any] | None: ...
    def get_user(self, user_id: int) -> dict[str, Any] | None: ...
    def update_password_hash(self, user_id: int, password_hash: str) -> None: ...
    def insert_refresh_token(
        self, user_id: int, token_hash: str, family_id: UUID, expires_at: datetime
    ) -> None: ...
    def rotate_refresh_token(
        self, old_hash: str, new_hash: str, new_expires_at: datetime
    ) -> int | None: ...
    def find_refresh_token(self, token_hash: str) -> dict[str, Any] | None: ...
    def revoke_family(self, family_id: UUID) -> None: ...


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    refresh_expires_at: datetime


@cache
def _dummy_hash() -> str:
    # Used when the email doesn't exist, so a failed login takes as long either way.
    return hash_password("timing-equalizer-not-a-real-password")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:
    def __init__(self, repo: AuthRepo, settings: Settings, now: Callable[[], datetime] = _utcnow):
        self._repo = repo
        self._s = settings
        self._now = now

    def register(self, email: str, password: str) -> int:
        email = self._normalize_email(email)
        if not MIN_PASSWORD <= len(password) <= MAX_PASSWORD:
            raise BadRequestError(f"Password must be {MIN_PASSWORD}-{MAX_PASSWORD} characters.")
        user_id = self._repo.create_user(email, hash_password(password))
        if user_id is None:
            raise ConflictError("An account with this email already exists.")
        return user_id

    def login(self, email: str, password: str) -> TokenPair:
        user = self._repo.get_user_by_email(self._normalize_email(email, validate=False))
        if user is None:
            verify_password(_dummy_hash(), password)
            raise UnauthorizedError(INVALID_LOGIN)
        if not verify_password(user["password_hash"], password):
            raise UnauthorizedError(INVALID_LOGIN)
        if password_needs_rehash(user["password_hash"]):
            self._repo.update_password_hash(user["id"], hash_password(password))

        refresh, expires_at = new_refresh_token(), self._refresh_expiry()
        self._repo.insert_refresh_token(
            user["id"], hash_refresh_token(refresh), uuid.uuid4(), expires_at
        )
        return TokenPair(self._access_token(user["id"]), refresh, expires_at)

    def refresh(self, refresh_token: str | None) -> TokenPair:
        if not refresh_token:
            raise UnauthorizedError(INVALID_REFRESH)
        old_hash = hash_refresh_token(refresh_token)
        new, expires_at = new_refresh_token(), self._refresh_expiry()

        user_id = self._repo.rotate_refresh_token(old_hash, hash_refresh_token(new), expires_at)
        if user_id is None:
            row = self._repo.find_refresh_token(old_hash)
            if row is not None and row["revoked_at"] is not None:
                # An already-used token came back: someone else has a copy. Kill the family.
                self._repo.revoke_family(row["family_id"])
            raise UnauthorizedError(INVALID_REFRESH)
        return TokenPair(self._access_token(user_id), new, expires_at)

    def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        row = self._repo.find_refresh_token(hash_refresh_token(refresh_token))
        if row is not None:
            self._repo.revoke_family(row["family_id"])

    def get_user(self, user_id: int) -> dict[str, Any]:
        user = self._repo.get_user(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    def _access_token(self, user_id: int) -> str:
        ttl = timedelta(minutes=self._s.access_token_ttl_minutes)
        return create_access_token(user_id, self._s.jwt_secret, ttl, now=self._now())

    def _refresh_expiry(self) -> datetime:
        return self._now() + timedelta(days=self._s.refresh_token_ttl_days)

    @staticmethod
    def _normalize_email(email: str, validate: bool = True) -> str:
        email = email.strip().lower()
        if validate and (len(email) > 254 or not EMAIL_RE.match(email)):
            raise BadRequestError("Enter a valid email address.")
        return email