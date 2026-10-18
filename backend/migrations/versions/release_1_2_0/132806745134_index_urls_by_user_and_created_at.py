"""index urls by user and created_at

Revision ID: 132806745134
Revises: 85240783390d
Create Date: 2026-10-18 23:51:57.449074

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '132806745134'
down_revision: Union[str, Sequence[str], None] = '85240783390d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE INDEX urls_user_created_idx ON urls (user_id, created_at DESC)")
    op.execute("DROP INDEX urls_user_id_idx")

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("CREATE INDEX urls_user_id_idx ON urls (user_id)")
    op.execute("DROP INDEX urls_user_created_idx")
