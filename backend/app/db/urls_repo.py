"""SQL for the urls table. No business rules here, only queries."""

from datetime import datetime
from typing import Any

from sqlalchemy import Engine, text


class UrlRepository:
    def __init__(self, engine: Engine):
        self._engine = engine

    def insert(
        self, short_id: str, long_url: str, expires_at: datetime | None, user_id: int
    ) -> bool:
        """Insert a row. Returns False if short_id already exists."""
        with self._engine.begin() as conn:
            row = conn.execute(
                text(
                    "INSERT INTO urls (short_id, long_url, expires_at, user_id) "
                    "VALUES (:short_id, :long_url, :expires_at, :user_id) "
                    "ON CONFLICT (short_id) DO NOTHING "
                    "RETURNING short_id"
                ),
                {"short_id": short_id, "long_url": long_url,
                 "expires_at": expires_at, "user_id": user_id},
            ).first()
        return row is not None

    def hit(self, short_id: str) -> str | None:
        """Count a click and return the long URL, or None if missing/expired/disabled."""
        with self._engine.begin() as conn:
            row = conn.execute(
                text(
                    "UPDATE urls SET click_count = click_count + 1 "
                    "WHERE short_id = :short_id AND NOT is_disabled "
                    "AND (expires_at IS NULL OR expires_at > now()) "
                    "RETURNING long_url"
                ),
                {"short_id": short_id},
            ).first()
        return row[0] if row else None

    def stats(self, short_id: str) -> dict[str, Any] | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT short_id, long_url, created_at, expires_at, click_count, is_disabled, user_id "
                    "FROM urls WHERE short_id = :short_id"
                ),
                {"short_id": short_id},
            ).mappings().first()
        return dict(row) if row else None

    def list_by_user(self, user_id: int, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        """One page of a user's links, newest first, plus the user's total link count."""
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT short_id, long_url, created_at, expires_at, click_count, is_disabled "
                    "FROM urls WHERE user_id = :user_id "
                    "ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
                ),
                {"user_id": user_id, "limit": limit, "offset": offset},
            ).mappings().all()
            total = conn.execute(
                text("SELECT count(*) FROM urls WHERE user_id = :user_id"), {"user_id": user_id}
            ).scalar_one()
        return [dict(r) for r in rows], total