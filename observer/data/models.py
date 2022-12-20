import dataclasses
import datetime


@dataclasses.dataclass
class StatusUpdateEntry:
    before: str
    after: str
    timestamp: datetime.datetime
    user_id: int
    guild_id: int

    @staticmethod
    def from_document(doc: dict) -> 'StatusUpdateEntry':
        return StatusUpdateEntry(**doc)

    def to_document(self) -> dict:
        return dataclasses.asdict(self)
