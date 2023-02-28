"""Create StatusLog

Revision ID: 0d656256c608
Revises: 
Create Date: 2023-02-28 17:47:37.918439

"""
from alembic import op
import sqlalchemy as sa
import enum

# revision identifiers, used by Alembic.
revision = "0d656256c608"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    class Status(enum.Enum):
        online = 1
        offline = 2
        idle = 3
        dnd = 4

    op.create_table(
        "StatusLog",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "guild_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "before",
            sa.Enum(Status),
            nullable=True,
        ),
        sa.Column(
            "after",
            sa.Enum(Status),
            nullable=False,
        ),
        sa.Column(
            "time",
            sa.DateTime(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("StatusLog")
