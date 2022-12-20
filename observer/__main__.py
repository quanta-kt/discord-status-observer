import motor.motor_asyncio

from .bot import ObserverBot
from .data.repository import StatusLogRepository
from . import config
from .bot import status_cog


if __name__ == "__main__":
    motor_client = motor.motor_asyncio.AsyncIOMotorClient(
        config.MONGO_CONNECTION_STRING,
        serverSelectionTimeoutMS=5000,
    )

    repo = StatusLogRepository(motor_client)

    bot = ObserverBot(
        guild_ids=config.GUILD_IDS,
        cogs = [
            status_cog.Status(
                repo=repo,
                guild_ids=config.GUILD_IDS,
            ),
        ]
    )

    bot.run(config.BOT_TOKEN)
