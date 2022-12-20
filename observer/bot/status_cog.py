import discord
from discord.ext import commands
import datetime

from ..data import repository, models


class Status(commands.Cog):
    def __init__(
        self,
        repo: repository.StatusLogRepository,
        guild_ids: list[int],
    ) -> None:
        super().__init__()
        self.guild_ids = guild_ids
        self._repo = repo

    @commands.Cog.listener()
    async def on_ready(self):
        for guild_id in self.guild_ids:
            guild = self.get_guild(guild_id) or self.fetch_guild(guild_id)
            await self._repo.log_initial_statuses(guild.members, guild_id)

    @commands.command()
    async def stats(
        self,
        ctx: commands.Context,
    ):
        """
        Draws a pie chat of amount of time you have spent with different
        statuses (online, idle, DnD, offline)

        don't ask me why.
        """

        image = await self._repo.get_user_graph(ctx.author.id, ctx.guild.id)

        await ctx.send(
            file=discord.File(
                image,
                filename="graph.png"
            )
        )

    @commands.Cog.listener()
    async def on_presence_update(
        self,
        before: discord.Member,
        after: discord.Member):

        if after.guild.id not in self.guild_ids:
            return

        if before.status != after.status:
            obj = models.StatusUpdateEntry(
                before=before.status.name,
                after=after.status.name,
                timestamp=datetime.datetime.now(),
                user_id=after.id,
                guild_id=after.guild.id,
            )

            await self._repo.log_status_change(obj)
