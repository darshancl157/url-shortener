"""PostgreSQL connection handling."""
from sqlalchemy import Engine, create_engine, text


def make_engine(database_url: str) -> Engine:
    """Create a pooled engine. Connections are opened lazily on first use."""
    return create_engine(database_url, pool_pre_ping=True)


def check_connection(engine: Engine) -> None:
    """Fail fast at startup if the database is unreachable."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))