"""SQL for the urls table. No business rules here, only queries."""

from datetime import datetime
from typing import Any

from sqlalchemy import Engine, text


class UrlRepository:
    def __init__(self, engine: Engine):
        self._engine = engine

    def insert(self, short_id: str, long_url: str, expires_at: datetime | None) -> bool:
        """Insert a row. Returns False if short_id already exists."""
        with self._engine.begin() as conn:
            row = conn.execute(
                text(
                    "INSERT INTO urls (short_id, long_url, expires_at) "
                    "VALUES (:short_id, :long_url, :expires_at) "
                    "ON CONFLICT (short_id) DO NOTHING "
                    "RETURNING short_id"
                ),
                {"short_id": short_id, "long_url": long_url, "expires_at": expires_at},
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
                    "SELECT short_id, long_url, created_at, expires_at, click_count, is_disabled "
                    "FROM urls WHERE short_id = :short_id"
                ),
                {"short_id": short_id},
            ).mappings().first()
        return dict(row) if row else None