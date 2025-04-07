import discord
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
import os

# Path to the .env file
ENV_PATH = os.path.join(os.path.dirname(__file__), '../config/.env')

# Load the .env file
load_dotenv(ENV_PATH)

# Now use the keys
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# Ensure that the TOKEN is set. There are no recovery or fallback if the TOKEN is missing
if not TOKEN:
    raise EnvironmentError(
        "Missing required environment variable: TOKEN\n"
        "Please set the TOKEN in ./config/.env before running the bot.\n"
        "Or delete the .env and fill in the required value in the newly generated file."
    )
if TOKEN == "null":
    raise EnvironmentError("Required environment variable is set to null: TOKEN")
if not Path("./config/.env").exists():
    raise FileNotFoundError("Missing .env file at ./config/.env — cannot continue.")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="wd!", intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    # Check if tree is initialized
    if client.tree is None:
        print("client.tree is not initialized.")
        return

    # Clear all commands
    print(f"Attempting to clear commands for guild {GUILD_ID}")
    try:
        guild = discord.Object(id=GUILD_ID)
        await client.tree.clear_commands(guild=guild)
        print(f"Successfully wiped commands for guild {GUILD_ID}")
    except Exception as e:
        print(f"Error wiping commands: {e}")
        return

    # Sync commands
    try:
        print(f"Syncing commands to guild {GUILD_ID}...")
        await client.tree.sync(guild=guild)
        print(f"Successfully synced commands to guild {GUILD_ID}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# Loading the cogs
async def load_cogs():
    for filename in os.listdir("./scripts/cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await client.load_extension(f"cogs.{filename[:-3]}")

@client.event
async def on_ready():
    print(f"Bot is ready.")
    await load_cogs()  # Load all cogs after bot is ready
    # Then sync commands after cogs are loaded
    await client.tree.sync()
    print("Commands synced.")

# Start the bot
client.run(TOKEN)
