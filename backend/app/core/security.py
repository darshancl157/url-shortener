"""Password hashing and token helpers. Pure functions: no database, no HTTP."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.exceptions import UnauthorizedError

_hasher = PasswordHasher()  # Argon2id with the library's recommended parameters
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def create_access_token(
    user_id: int, secret: str, ttl: timedelta, now: datetime | None = None
) -> str:
    now = now or datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "type": "access", "iat": now, "exp": now + ttl}
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret: str) -> int:
    """Returns the user id, or raises UnauthorizedError."""
    try:
        payload = jwt.decode(
            token, secret, algorithms=[_ALGORITHM], options={"require": ["exp", "iat", "sub"]}
        )
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid or expired token.")
    return int(payload["sub"])


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()