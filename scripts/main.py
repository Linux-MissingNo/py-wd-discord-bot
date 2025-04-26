import discord
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import asyncpg

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ---------- Environment Setup ----------
ENV_PATH = os.path.join(os.path.dirname(__file__), '../config/.env')
load_dotenv(dotenv_path=ENV_PATH)

if not Path(ENV_PATH).exists():
    logging.critical(f"Missing .env file at {ENV_PATH}")
    raise FileNotFoundError("Missing .env file — cannot continue.")

# ---------- Load Environment Variables ----------
TOKEN = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST", "localhost")  # Default to localhost
DB_PORT = os.getenv("DB_PORT", "5432")        # Default to 5432

# ---------- Validation ----------
missing_keys = {
    "TOKEN": TOKEN,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_NAME": DB_NAME,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT
}

for key, value in missing_keys.items():
    if not value or value.lower() == "null":
        logging.critical(f"{key} is missing or set to 'null'. Cannot continue.")
        raise EnvironmentError(f"Required environment variable not set or invalid: {key}")

# Optional GUILD_ID validation
if not GUILD_ID or GUILD_ID.lower() == "null":
    logging.warning("GUILD_ID is missing or set to 'null'. This may affect command syncs.")
else:
    GUILD_ID = int(GUILD_ID)

# ---------- Discord Bot Setup ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="wd!", intents=intents)

# ---------- Database Setup ----------
async def create_db_pool():
    return await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=int(DB_PORT)
    )

@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user}")

    if client.tree is None:
        logging.warning("client.tree is not initialized.")
        return

    # Clear and sync commands
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        try:
            logging.info(f"Clearing commands for guild {GUILD_ID}")
            client.tree.clear_commands(guild=guild)
            await client.tree.sync(guild=guild)
            logging.info(f"Commands synced to guild {GUILD_ID}")
        except Exception as e:
            logging.error(f"Failed to sync commands to guild: {e}")
    else:
        logging.warning("Skipping command sync due to missing GUILD_ID")

    logging.info("Starting the database pool")
    client.db_pool = await create_db_pool()

    logging.info("Loading cogs...")
    await load_cogs()
    await client.tree.sync()
    logging.info("Bot is ready and commands are synced.")

# ---------- Load Cogs ----------
async def load_cogs():
    for filename in os.listdir("./scripts/cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await client.load_extension(f"cogs.{filename[:-3]}")

# ---------- Run Bot ----------
client.run(TOKEN)
