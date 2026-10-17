"""create users and refresh tokens

Revision ID: 85240783390d
Revises: d8c06002eaa1
Create Date: 2026-10-10 19:31:40.213892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85240783390d'
down_revision: Union[str, Sequence[str], None] = 'd8c06002eaa1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE TABLE users (
            id             BIGINT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            email          TEXT         NOT NULL,
            password_hash  TEXT         NOT NULL,
            created_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE UNIQUE INDEX users_email_lower_key ON users (lower(email))")

    op.execute("""
        CREATE TABLE refresh_tokens (
            id          BIGINT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            user_id     BIGINT       NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            token_hash  TEXT         NOT NULL UNIQUE,
            family_id   UUID         NOT NULL,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
            expires_at  TIMESTAMPTZ  NOT NULL,
            revoked_at  TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX refresh_tokens_family_idx ON refresh_tokens (family_id)")
    op.execute("CREATE INDEX refresh_tokens_user_idx ON refresh_tokens (user_id)")

    op.execute("""
        ALTER TABLE urls
            ADD CONSTRAINT urls_user_id_fkey FOREIGN KEY (user_id) REFERENCES users (id)
    """)
    op.execute("CREATE INDEX urls_user_id_idx ON urls (user_id)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX urls_user_id_idx")
    op.execute("ALTER TABLE urls DROP CONSTRAINT urls_user_id_fkey")
    op.execute("DROP TABLE refresh_tokens")
    op.execute("DROP TABLE users")
