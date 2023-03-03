import asyncio
import discord
import datetime
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine
from io import BytesIO
from typing import Optional

from .models import StatusLog
from .imggen import graph


class StatusLogRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def log_status_change(
        self, user_id, guild_id, before, after, timestamp
    ) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(
                StatusLog.insert(),
                {
                    "user_id": user_id,
                    "guild_id": guild_id,
                    "before": before,
                    "after": after,
                    "time": timestamp,
                },
            )

    async def log_initial_statuses(
        self,
        members: list[discord.Member],
        guild_id: int,
        startup_time: datetime.datetime,
    ) -> None:
        entires = [
            {
                "user_id": member.id,
                "guild_id": guild_id,
                "before": None,
                "after": member.status.name,
                "time": startup_time,
            }
            for member in members
        ]

        async with self._engine.begin() as conn:
            await conn.execute(StatusLog.insert(), entires)

    async def log_statuses_before_shutdown(
        self,
        members: list[discord.Member],
        guild_id: int,
        shutdown_time: datetime.datetime,
    ) -> None:
        entires = [
            {
                "user_id": member.id,
                "guild_id": guild_id,
                "before": member.status.name,
                "after": None,
                "time": shutdown_time,
            }
            for member in members
        ]

        async with self._engine.begin() as conn:
            await conn.execute(StatusLog.insert(), entires)

    async def get_user_stats(self, user_id, guild_id):
        subquery = (
            sa.select(
                StatusLog.c.before.label("status"),
                StatusLog.c.time.label("end_time"),
                sa.func.lag(StatusLog.c.time)
                .over(order_by=StatusLog.c.time)
                .label("start_time"),
                (
                    sa.func.lag(StatusLog.c.after).over(order_by=StatusLog.c.time)
                    == StatusLog.c.before
                ).label("is_valid"),
            )
            .select_from(StatusLog)
            .where(StatusLog.c.user_id == user_id)
            .where(StatusLog.c.guild_id == guild_id)
            .subquery()
        )

        query = (
            sa.select(
                subquery.c.status.label("status"),
                sa.func.sum(subquery.c.end_time - subquery.c.start_time).label("time"),
            )
            .where(subquery.c.is_valid)
            .group_by(subquery.c.status)
        )

        async with self._engine.connect() as conn:
            result = await conn.execute(query)
            return result.fetchall()

    async def get_user_graph(self, user_id: int, guild_id: int) -> Optional[BytesIO]:
        stats = await self.get_user_stats(user_id=user_id, guild_id=guild_id)

        if not stats:
            return None

        total_time = sum(stat.time.total_seconds() for stat in stats)

        values = {
            stat.status.name: stat.time.total_seconds() / total_time for stat in stats
        }

        image = await asyncio.to_thread(graph.generate_status_pie_graph, **values)

        fp = BytesIO()
        fp.name = "graph.png"
        image.save(fp)
        fp.seek(0)

        return fp
