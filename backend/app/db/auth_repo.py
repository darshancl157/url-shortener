"""SQL for users and refresh_tokens. No business rules here, only queries."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, text


class AuthRepository:
    def __init__(self, engine: Engine):
        self._engine = engine

    # ---- users ----

    def create_user(self, email: str, password_hash: str) -> int | None:
        """Returns the new user id, or None if the email is already registered."""
        with self._engine.begin() as conn:
            row = conn.execute(
                text(
                    "INSERT INTO users (email, password_hash) VALUES (:email, :password_hash) "
                    "ON CONFLICT DO NOTHING RETURNING id"
                ),
                {"email": email, "password_hash": password_hash},
            ).first()
        return row[0] if row else None

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, email, password_hash FROM users WHERE lower(email) = lower(:email)"),
                {"email": email},
            ).mappings().first()
        return dict(row) if row else None

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, email, created_at FROM users WHERE id = :id"), {"id": user_id}
            ).mappings().first()
        return dict(row) if row else None

    def update_password_hash(self, user_id: int, password_hash: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text("UPDATE users SET password_hash = :h WHERE id = :id"),
                {"h": password_hash, "id": user_id},
            )

    # ---- refresh tokens ----

    def insert_refresh_token(
        self, user_id: int, token_hash: str, family_id: UUID, expires_at: datetime
    ) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO refresh_tokens (user_id, token_hash, family_id, expires_at) "
                    "VALUES (:user_id, :token_hash, :family_id, :expires_at)"
                ),
                {"user_id": user_id, "token_hash": token_hash,
                 "family_id": family_id, "expires_at": expires_at},
            )

    def rotate_refresh_token(
        self, old_hash: str, new_hash: str, new_expires_at: datetime
    ) -> int | None:
        """Atomically revoke a valid token and issue its successor in the same family.

        Returns the user id, or None if the old token is unknown, revoked or expired.
        The `revoked_at IS NULL` condition means two concurrent calls can't both succeed.
        """
        with self._engine.begin() as conn:
            row = conn.execute(
                text(
                    "UPDATE refresh_tokens SET revoked_at = now() "
                    "WHERE token_hash = :old AND revoked_at IS NULL AND expires_at > now() "
                    "RETURNING user_id, family_id"
                ),
                {"old": old_hash},
            ).first()
            if row is None:
                return None
            conn.execute(
                text(
                    "INSERT INTO refresh_tokens (user_id, token_hash, family_id, expires_at) "
                    "VALUES (:user_id, :token_hash, :family_id, :expires_at)"
                ),
                {"user_id": row.user_id, "token_hash": new_hash,
                 "family_id": row.family_id, "expires_at": new_expires_at},
            )
        return row.user_id

    def find_refresh_token(self, token_hash: str) -> dict[str, Any] | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT user_id, family_id, revoked_at, expires_at "
                    "FROM refresh_tokens WHERE token_hash = :h"
                ),
                {"h": token_hash},
            ).mappings().first()
        return dict(row) if row else None

    def revoke_family(self, family_id: UUID) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE refresh_tokens SET revoked_at = now() "
                    "WHERE family_id = :f AND revoked_at IS NULL"
                ),
                {"f": family_id},
            )