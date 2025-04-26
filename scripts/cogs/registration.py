import discord
from discord.ext import commands
import asyncpg
import logging


logger = logging.getLogger("discord_bot")

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
            # Insert player
            await conn.execute(
                "INSERT INTO players_table (player_id, balance) VALUES ($1, $2)",
                player_id, 50  # Default balance set to 50
            )
            logger.info(f"Player {player_id} created in the database.")
        else:
            logger.info(f"Player {player_id} already exists in the database.")

async def setup(bot):
    db_pool = bot.db_pool  # Use the db_pool from the bot instance
    await bot.add_cog(Registration(bot, db_pool))
    
# When calling this in another cog, use the below line
# bot.load_extension('registration')

