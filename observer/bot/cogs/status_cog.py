import discord
from discord.ext import commands
import datetime
from typing import Optional

from ...data import repository


class Status(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        repo: repository.StatusLogRepository,
        guild_ids: list[int],
    ) -> None:
        super().__init__()
        self.bot = bot
        self.guild_ids = guild_ids
        self._repo = repo
        self._is_ready = False

    @commands.Cog.listener()
    async def on_ready(self):
        for guild_id in self.guild_ids:
            guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)
            await self._repo.log_initial_statuses(
                guild.members, guild_id, datetime.datetime.now()
            )

        self._is_ready = True

    async def cog_unload(self):
        for guild_id in self.guild_ids:
            guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)
            await self._repo.log_statuses_before_shutdown(
                guild.members, guild_id, datetime.datetime.now()
            )

    @commands.command()
    async def stats(
        self, ctx: commands.Context, target: Optional[discord.Member] = None
    ):
        """
        Draws a pie chat of amount of time you have spent with different
        statuses (online, idle, DnD, offline)

        don't ask me why.
        """
        if target is None:
            target = ctx.author

        # Record an early log so that the most up-to date data gets shown by
        # Subsequent `get_user_graph` call.
        if target.status is not None:
            await self._repo.log_status_change(
                user_id=target.id,
                guild_id=ctx.guild.id,
                before=target.status.name,
                after=target.status.name,
                timestamp=datetime.datetime.now(),
            )

        image = await self._repo.get_user_graph(target.id, ctx.guild.id)

        if image is None:
            await ctx.send(content="No data to show.")
            return

        await ctx.send(file=discord.File(image, filename="graph.png"))

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if not self._is_ready:
            return False

        if after.guild.id not in self.guild_ids:
            return

        if before.status != after.status:
            await self._repo.log_status_change(
                user_id=after.id,
                guild_id=after.guild.id,
                before=before.status.name,
                after=after.status.name,
                timestamp=datetime.datetime.now(),
            )
