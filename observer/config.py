import dotenv
import os


dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

DATABASE_URI = os.getenv("DATABASE_URI")
# The database used for running tests
TEST_DATABASE_URI = os.getenv("TEST_DATABASE_URI")

GUILD_IDS = {int(x) for x in os.getenv("GUILD_IDS").split(";")}
