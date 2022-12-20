import asyncio
import discord
import motor.motor_asyncio
import datetime
from io import BytesIO

from .models import StatusUpdateEntry
from ..imggen import graph


class StatusLogRepository:

    def __init__(
        self,
        motor_client: motor.motor_asyncio.AsyncIOMotorClient
    ) -> None:

        self._motor_client = motor_client
        self._db = motor_client.observer
        self._status_log_collection = self._db.status_log

    async def log_status_change(self, obj: StatusUpdateEntry) -> None:
        await self._status_log_collection.insert_one(obj.to_document())

    async def log_initial_statuses(self, members: list[discord.Member], guild_id: int) -> None:
        timestamp = datetime.datetime.now()

        docs = [
            StatusUpdateEntry(
                before=None,
                after=member.status.name,
                timestamp=timestamp,
                user_id=member.id,
                guild_id=guild_id
            ).to_document()

            for member in members
        ]
            
        await self._status_log_collection.insert_many(docs)

    async def log_bot_shutdown(self) -> None:
        pass

    async def normalize(self) -> None:
        pass

    async def get_user_stats(self, user_id, guild_id) -> list[StatusUpdateEntry]:
        cursor = self._status_log_collection.find({
            'user_id': { '$eq': user_id },
            'guild_id': { '$eq': guild_id },
        }).sort('timestamp')

        return [
            StatusUpdateEntry.from_document(x)
            for x in await cursor.to_list()
        ]

    async def get_user_graph(
        self,
        user_id: int,
        guild_id: int
    ) -> BytesIO:
        
        # TODO: Fetch time periods instead of using random values

        import random
        values = [random.random() * 0.4 for _ in range(3)]
        values.append(1 - sum(values))

        image = await asyncio.to_thread(
            graph.generate_status_pie_graph,
            *values
        )

        fp = BytesIO()
        fp.name = "graph.png"
        image.save(fp)
        fp.seek(0)

        return fp
