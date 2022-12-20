import discord
from discord.ext import commands


class ObserverBot(commands.Bot):

    def __init__(
        self,
        guild_ids: set[int],
        cogs: list[commands.Cog],
    ):
        # IDs of the guilds to operate in
        self.guild_ids = guild_ids
        self._cogs = cogs

        intents = discord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.messages = True
        intents.message_content = True

        super().__init__(
            command_prefix="~",
            intents=intents,
        )

    @commands.Cog.listener()
    async def on_ready(self):
        for cog in self._cogs:
            await self.add_cog(cog)

    async def on_message(self, message: discord.Message, /) -> None:
        if not self.is_ready:
            return

        # Process commands only for guilds we operate in
        if message.guild is not None and \
            message.guild.id in self.guild_ids:
            return await self.process_commands(message)
