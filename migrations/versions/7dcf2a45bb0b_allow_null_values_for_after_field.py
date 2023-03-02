"""Allow null values for 'after' field

Revision ID: 7dcf2a45bb0b
Revises: 0d656256c608
Create Date: 2023-03-02 20:03:17.344783

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7dcf2a45bb0b"
down_revision = "0d656256c608"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("StatusLog", "after", nullable=True)


def downgrade() -> None:
    op.alter_column("StatusLog", "after", nullable=False)
