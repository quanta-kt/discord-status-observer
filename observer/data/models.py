import enum
import sqlalchemy as sa


metadata = sa.MetaData()


class Status(enum.Enum):
    online = 1
    offline = 2
    idle = 3
    dnd = 4


StatusLog = sa.Table(
    "StatusLog",
    metadata,
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
        nullable=True,
    ),
    sa.Column(
        "time",
        sa.DateTime(),
        nullable=False,
    ),
)
