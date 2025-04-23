import discord
from discord import app_commands
from discord.ext import commands
import os
import logging

logger = logging.getLogger("discord_bot")

class ReviveCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="revive", description="revive a player")
    @app_commands.describe(user="The user you want to revive")
    async def removeRole(self, interaction: discord.Interaction, user: discord.Member):
        logger.info(f"{interaction.user.mention} want to revive {user.mention}")

        role_id = int(os.getenv("SHOT_ROLE"))
        role = interaction.guild.get_role(role_id)

        has_role = any(r.name == role.name for r in user.roles)
        has_medkit = True  # TBD: Implement a logic that check for if the user have a medkit

        if not role:
            await interaction.response.send_message("Shot Role not found.", ephemeral=True)
            logger.error(f"Failed to find shot role, ensure that the SHOT role have been enabled and/or ID have been set in the .env")
            logger.debug(f"The ID of the SHOT role was set to {role_id}")
            return
        if not has_role:
            await interaction.response.send_message(f"{user.mention} is not dead", ephemeral=True)
            return
        if not has_medkit:
            await interaction.response.send_message(f"You don't have any medkit, lel", ephemeral=True)
            return
        else:
            try:
                await user.remove_roles(role)
                await interaction.response.send_message(f"{user.mention} has been revived!")
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I do not have permission to remove that role. Please enable manage roles and/or move my role above the shot role"
                )
                logger.error(f"Failed to remove SHOT role from {user.mention}, Ensure that the bot's role have the manage role authority and is above the SHOT role")
            except Exception as e:
                await interaction.response.send_message(f"An error occured: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ReviveCommand(bot))
