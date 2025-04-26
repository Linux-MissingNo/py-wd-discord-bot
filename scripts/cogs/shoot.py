import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
import os
import logging

# Setting up logger for debugging and information tracking
logger = logging.getLogger(__name__)

class ShootCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_player(self, player_id: str):
        """
        Ensures the player exists in the database by calling the registration cog.
        """
        registration_cog = self.bot.get_cog('Registration')
        if registration_cog:
            await registration_cog.create_player_if_not_exists(self.bot.db_pool, player_id)
        else:
            logger.error("Registration cog is not loaded. Unable to create player.")
            raise Exception("Registration cog not found.")

    async def fetch_player_data(self, conn, player_id: str):
        """
        Fetches the player's data (guns, vest, and is_vested) from the database.
        """
        query = "SELECT guns, vest, is_vested FROM players_table WHERE player_id = $1"
        player_data = await conn.fetchrow(query, player_id)
        if player_data is None:
            logger.error(f"Player {player_id} not found in the database.")
        return player_data

    async def update_player_guns(self, conn, player_id: str):
        """
        Updates the player's guns in the database after shooting.
        """
        await conn.execute("""
            UPDATE players_table
            SET guns = GREATEST(guns - 1, 0)
            WHERE player_id = $1
        """, player_id)

    async def update_vest_status(self, conn, player_id: str):
        """
        Updates the victim's vest status in the database (removes vest and sets is_vested to false).
        """
        await conn.execute("""
            UPDATE players_table
            SET is_vested = false, vest = GREATEST(vest - 1, 0)
            WHERE player_id = $1
        """, player_id)

    async def update_last_dead(self, conn, player_id: str):
        """
        Updates the 'last_dead' timestamp for the victim in the database.
        """
        await conn.execute("""
            UPDATE players_table
            SET last_dead = CURRENT_TIMESTAMP
            WHERE player_id = $1
        """, player_id)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.command(name="shoot", description="Kill a user")
    @app_commands.describe(user="The user you want dead")
    async def assign_role(self, interaction: discord.Interaction, user: discord.Member):
        """
        Command that allows a user to 'shoot' another user (assign them the 'shot' role and timeout).
        The shooter is the one issuing the command, and the victim is the user being targeted.
        """
        shooter = interaction.user  # The one issuing the command (the shooter)
        victim = user  # The target user (the victim)

        logger.info(f"{shooter.mention} wants to shoot {victim.mention}")

        # Fetch shot role ID and timeout duration from environment variables
        role_id = int(os.getenv("SHOT_ROLE"))
        timeout_dur = int(os.getenv("SHOT_TIMEOUT_IN_HOURS"))
        role = interaction.guild.get_role(role_id)

        logger.debug(f"Role ID: {role_id}, Role fetched: {role}")

        if not role:
            await interaction.response.send_message("Shot Role not found.", ephemeral=True)
            return
        
        # Check if the victim already has the shot role
        has_role = any(r.id == role.id for r in victim.roles)
        logger.info(f"Victim has role {role.name}: {has_role}")
        
        if has_role:
            await interaction.response.send_message(f"{victim.mention} is already dead.", ephemeral=True)
            return

        # Check if the victim is timed out (cannot be shot if they are)
        try:
            logger.info(f"Checking timeout status for {victim.mention}")
            if victim.timed_out:
                await interaction.response.send_message(f"{victim.mention} is timed out, they will not be shot.", ephemeral=True)
                return
        except AttributeError:
            logger.warning(f"Cannot check timeout for {victim.mention}, assuming this player is not timed out and continuing")

        # Get the shooter and victim's player IDs for database operations
        shooter_id = str(shooter.id)
        victim_id = str(victim.id)
        
        # Ensure both shooter and victim have their player entries in the database
        await self.create_player(shooter_id)
        await self.create_player(victim_id)
        
        # Fetch the shooter and victim's details from the database
        async with self.bot.db_pool.acquire() as conn:
            shooter_data = await self.fetch_player_data(conn, shooter_id)
            victim_data = await self.fetch_player_data(conn, victim_id)

            if shooter_data is None:
                await interaction.response.send_message(f"Player data for {shooter.mention} not found.", ephemeral=True)
                return

            # Extract guns and vest information from database
            guns = shooter_data["guns"]
            vest = victim_data["vest"]
            is_vested = victim_data["is_vested"]

        # Log expected and database values for guns and vest
        logger.info(f"Shooter has {guns} guns. Expected: {guns}, Victim has {vest} vest. Expected: {vest}, is_vested: {is_vested}")

        # Gun check logic: if the shooter has no guns, prevent shooting
        if guns <= 0:
            await interaction.response.send_message(f"{shooter.mention} does not have any guns!", ephemeral=True)
            return

        # Reduce the number of guns the shooter has after shooting
        async with self.bot.db_pool.acquire() as conn:
            await self.update_player_guns(conn, shooter_id)

        # Check if the victim has a vest and prevent the shooting if it saves them
        if is_vested:
            # SQL to set is_vested to false and reduce the vest amount, ensuring it doesn't go below 0
            async with self.bot.db_pool.acquire() as conn:
                await self.update_vest_status(conn, victim_id)
            logger.info(f"{victim.mention}'s vest saved them, vest removed.")
            await interaction.response.send_message(f"{victim.mention} was shot but their vest saved them!", ephemeral=True)
            return

        # If no vest saved the victim, proceed with assigning the shot role and applying timeout
        try:
            logger.info(f"Assigning shot role and timeout to {victim.mention}")
            await victim.add_roles(role)  # Assign 'shot' role to the victim
            await victim.timeout(timedelta(seconds=timeout_dur))  # Apply timeout to the victim
            async with self.bot.db_pool.acquire() as conn:
                await self.update_last_dead(conn, victim_id)

            await interaction.response.send_message(f"{victim.mention} has been shot!")
        except discord.Forbidden as e:
            logger.error(f"Permission error: {e}")
            await interaction.response.send_message("Unable to add timeout.", ephemeral=True)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @assign_role.error
    async def shoot_command_error(self, interaction: discord.Interaction, error: Exception):
        """
        Handles errors related to the shoot command, such as cooldown issues.
        """
        if isinstance(error, commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"You're on cooldown! Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True
            )


# Export the cog to be loaded in the main bot script
async def setup(bot: commands.Bot):
    await bot.add_cog(ShootCommands(bot))
