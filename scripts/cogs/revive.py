import discord
from discord import app_commands
from discord.ext import commands
import os
import logging

logger = logging.getLogger("discord_bot")

class ReviveCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="revive", description="Revive a player")
    @app_commands.describe(user="The user you want to revive")
    async def revive_player(self, interaction: discord.Interaction, user: discord.Member):
        """
        Allows a user (medic) to revive another user (patient) if they have a medkit.
        """
        medic: discord.Member = interaction.user
        patient: discord.Member = user

        async def create_player(player_id: str):
            """
            Ensures the player exists in the database by calling the registration cog.
            """
            registration_cog = self.bot.get_cog('Registration')
            if registration_cog:
                await registration_cog.create_player_if_not_exists(self.bot.db_pool, player_id)
            else:
                logger.error("Registration cog is not loaded. Unable to create player.")
                raise Exception("Registration cog not found.")

        # Ensure both players are registered
        await create_player(str(medic.id))
        await create_player(str(patient.id))

        logger.info(f"{medic.mention} wants to revive {patient.mention}")

        shot_role_id = int(os.getenv("SHOT_ROLE"))
        shot_role = interaction.guild.get_role(shot_role_id)

        if not shot_role:
            await interaction.response.send_message("Shot Role not found.", ephemeral=True)
            logger.error("Shot role not found. Check SHOT_ROLE environment variable.")
            return

        # Check if the patient has the shot role
        has_shot_role = any(role.id == shot_role.id for role in patient.roles)
        if not has_shot_role:
            await interaction.response.send_message(f"{patient.mention} is not dead.", ephemeral=True)
            return

        async with self.bot.db_pool.acquire() as conn:
            try:
                # Check medic's medkit count
                result = await conn.fetchrow("""
                    SELECT medkit FROM players_table WHERE player_id = $1;
                """, str(medic.id))

                if not result:
                    await interaction.response.send_message("You are not registered in the game.", ephemeral=True)
                    logger.warning(f"Medic {medic.id} is not registered in the DB.")
                    return

                medkit_count = result["medkit"]
                logger.info(f"{medic.mention} has {medkit_count} medkits.")

                if medkit_count <= 0:
                    await interaction.response.send_message(f"{medic.mention}, you don't have any medkits!", ephemeral=True)
                    return

                # Subtract medkit and update patient's status
                await conn.execute("""
                    UPDATE players_table
                    SET medkit = GREATEST(medkit - 1, 0)
                    WHERE player_id = $1;
                """, str(medic.id))

                # Remove shot role and timeout
                await patient.remove_roles(shot_role)
                await patient.edit(timed_out_until=None)

                await interaction.response.send_message(
                    f"{patient.mention} has been revived by {medic.mention}!"
                )
                logger.info(f"{medic.mention} successfully revived {patient.mention}.")

            except discord.Forbidden:
                await interaction.response.send_message(
                    "Missing permissions to modify roles or timeouts. Please check role hierarchy and permissions.",
                    ephemeral=True
                )
                logger.error(f"Permission error while reviving {patient.mention}.")
            except Exception as e:
                await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)
                logger.exception(f"Unexpected error while reviving {patient.mention}: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ReviveCommand(bot))
