
"""rename verified_at to retrieved_at

Revision ID: 4ecdb94226e1
Revises: 15332a17c75e
Create Date: 2026-10-20 03:37:29.414232
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4ecdb94226e1"
down_revision: Union[str, Sequence[str], None] = "15332a17c75e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename the column without losing existing data."""
    op.alter_column(
        "medicine_ingredients",
        "verified_at",
        new_column_name="retrieved_at",
        existing_type=None,
        existing_nullable=True,
    )


def downgrade() -> None:
    """Restore the original column name."""
    op.alter_column(
        "medicine_ingredients",
        "retrieved_at",
        new_column_name="verified_at",
        existing_type=None,
        existing_nullable=True,
    )
