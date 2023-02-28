import discord
from discord.ext import commands


class ObserverBot(commands.Bot):
    def __init__(
        self,
        guild_ids: set[int],
    ):
        # IDs of the guilds to operate in
        self.guild_ids = guild_ids

        intents = discord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.messages = True
        intents.message_content = True

        super().__init__(
            command_prefix="~",
            intents=intents,
        )

    async def on_message(self, message: discord.Message, /) -> None:
        if not self.is_ready:
            return

        # Process commands only for guilds we operate in
        if message.guild is not None and message.guild.id in self.guild_ids:
            return await self.process_commands(message)

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        await super().on_error(event_method, *args, **kwargs)
