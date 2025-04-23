import discord
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

logging.basicConfig(
    level=logging.INFO,  # Minimum level to show
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Path to the .env file
ENV_PATH = os.path.join(os.path.dirname(__file__), '../config/.env')

# Load the .env file
load_dotenv(ENV_PATH)
# Check if the path exists
if not Path("./config/.env").exists():
    logging.critical("Missing required environment variable: TOKEN. Cannot continue.")
    raise FileNotFoundError("Missing .env file at ./config/.env — cannot continue.")

# Now use the keys
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# Ensure that the TOKEN is set. There are no recovery or fallback if the TOKEN is missing

if not TOKEN:
    logging.critical("TOKEN is missing, cannot continue")
    raise EnvironmentError(
        "Missing required environment variable: TOKEN\n"
        "Please set the TOKEN in ./config/.env before running the bot.\n"
        "Or delete the .env, rerun the program, and then fill in the required value in the newly generated file."
    )
if TOKEN == "null":
    logging.critical("TOKEN is set to 'null' in .env. Cannot continue.")
    raise EnvironmentError("Required environment variable is set to null: TOKEN")

# Check if GUILD_ID exist. Not required but can cause issues with guild sync if it isn't set
if not GUILD_ID:
    logging.warning("GUILD is missing, this will cause problems with command syncs!")
if GUILD_ID == "null":
    logging.warning("GUILD_ID is set to 'null', this will cause problems with command syncs!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="wd!", intents=intents)

@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user}")

    # Check if tree is initialized
    if client.tree is None:
        logging.warning("client.tree is not initialized.")
        return

    # Clear all commands
    logging.info(f"Attempting to clear commands for guild {GUILD_ID}")
    try:
        guild = discord.Object(id=GUILD_ID)
        client.tree.clear_commands(guild=guild)
        logging.info(f"Successfully wiped commands for guild {GUILD_ID}")
    except Exception as e:
        logging.error(f"Error wiping commands: {e}")
        return

    # Sync commands
    try:
        logging.info(f"Syncing commands to guild {GUILD_ID}...")
        await client.tree.sync(guild=guild)
        logging.info(f"Successfully synced commands to guild {GUILD_ID}")
    except Exception as e:
        logging.error(f"Failed to sync commands: {e}")

    # Now run the bot

    logging.info(f"Bot is ready.")
    await load_cogs()  # Load all cogs after bot is ready
    # Then sync commands after cogs are loaded
    
    await client.tree.sync()
    logging.info("Commands synced.")

# Loading the cogs
async def load_cogs():
    for filename in os.listdir("./scripts/cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await client.load_extension(f"cogs.{filename[:-3]}")

# Start the bot
client.run(TOKEN)
