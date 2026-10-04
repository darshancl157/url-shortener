"""create urls table

Revision ID: d8c06002eaa1
Revises: 
Create Date: 2026-10-04 14:19:57.543374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8c06002eaa1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE TABLE urls (
            short_id     VARCHAR(10)  PRIMARY KEY,
            long_url     TEXT         NOT NULL,
            created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
            expires_at   TIMESTAMPTZ,
            user_id      BIGINT,
            click_count  BIGINT       NOT NULL DEFAULT 0,
            is_disabled  BOOLEAN      NOT NULL DEFAULT FALSE
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE urls")
