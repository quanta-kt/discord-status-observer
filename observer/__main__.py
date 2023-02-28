import discord
from sqlalchemy.ext.asyncio import create_async_engine

from .bot import ObserverBot
from .data.repository import StatusLogRepository
from . import config
from .bot import cogs


async def main():
    discord.utils.setup_logging()

    engine = create_async_engine(config.DATABASE_URI)

    try:
        repo = StatusLogRepository(engine)

        bot = ObserverBot(
            guild_ids=config.GUILD_IDS,
        )

        await bot.add_cog(
            cogs.Status(
                bot=bot,
                repo=repo,
                guild_ids=config.GUILD_IDS,
            )
        ),

        async with bot:
            await bot.start(config.BOT_TOKEN)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
