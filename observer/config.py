import dotenv
import os


dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")    
GUILD_IDS = { int(x) for x in os.getenv("GUILD_IDS").split(";") }
