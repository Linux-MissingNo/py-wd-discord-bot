import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncpg
import logging

logger = logging.getLogger("discord_bot")
DEBUG = os.getenv("DEBUG") == "True"  # Set DEBUG to True if the environment variable is "True"

class Registration(commands.Cog):
    def __init__(self, bot, db_pool):
        self.bot = bot
        self.db_pool = db_pool  # Use the database connection pool

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Registration cog has been loaded.")

    @commands.command(name='register')
    async def register_player(self, ctx, player_id: str = None):
        """Registers a player if they don't exist in the database.
        If no player_id is provided, defaults to the author's ID."""
        player_id = player_id or str(ctx.author.id)  # Use the author's Discord ID if no player_id is given
        
        try:
            # Use the database connection pool to get a connection
            async with self.db_pool.acquire() as conn:
                await self.create_player_if_not_exists(conn, player_id)
                await ctx.send(f"Player {player_id} has been registered.")
        except Exception as e:
            logger.error(f"Error registering player {player_id}: {e}")
            await ctx.send(f"Failed to register player {player_id}.")

    async def create_player_if_not_exists(self, conn, player_id):
        # Check if player exists
        result = await conn.fetchrow("SELECT player_id FROM players_table WHERE player_id = $1", player_id)

        if result is None:  # Player doesn't exist
            # Set default values based on the DEBUG variable
            if DEBUG:
                guns = 127
                vest = 127
                medkit = 127
                balance = 101010
                logger.info(f"Setting default values for player {player_id} in DEBUG mode.")
            else:
                guns = 0
                vest = 0
                medkit = 0
                balance = 50
                logger.info(f"Setting default values for player {player_id} in normal mode.")

            # Insert player with default values
            await conn.execute(
                "INSERT INTO players_table (player_id, guns, medkit, vest, balance) VALUES ($1, $2, $3, $4, $5)",
                player_id, guns, medkit, vest, balance
            )
            logger.info(f"Player {player_id} created in the database with default values.")
        else:
            logger.info(f"Player {player_id} already exists in the database.")

async def setup(bot):
    db_pool = bot.db_pool  # Use the db_pool from the bot instance
    await bot.add_cog(Registration(bot, db_pool))

# When calling this in another cog, use the below line
# bot.load_extension('registration')
