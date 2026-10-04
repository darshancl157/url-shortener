"""Application settings, read once from environment variables (and .env if present)."""

import logging

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

def _load_dotenv(path: Path) -> None:
    """Minimal .env loader so we don't need python-dotenv. Real env vars take precedence."""
    if not path.is_file():
        logger.warning("No .env file found.")
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

def _split_csv(value: str) -> list[str]:
    return [v.strip().rstrip("/") for v in value.split(",") if v.strip()]

@dataclass(frozen=True)
class Settings:
    app_name: str = "URL Shortener"
    database_url: str = ""
    base_url: str = "http://127.0.0.1:8000"
    cors_origins: list[str] = field(default_factory=list)
    # localhost / 127.0.0.1 on any port, for local development.
    cors_origin_regex: str | None = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
    short_id_length: int = 6
    max_url_length: int = 2048
    max_id_attempts: int = 10


@lru_cache
def get_settings() -> Settings:
    _load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set."
        )
    allow_localhost = os.getenv("CORS_ALLOW_LOCALHOST", "true").lower() in {"1", "true", "yes"}
    return Settings(
        database_url=database_url,
        base_url=os.getenv("BASE_URL", Settings.base_url).rstrip("/"),
        cors_origins=_split_csv(os.getenv("CORS_ORIGINS", "")),
        cors_origin_regex=Settings.cors_origin_regex if allow_localhost else None,
    )