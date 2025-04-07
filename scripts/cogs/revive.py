import discord
from discord import app_commands
from discord.ext import commands
import os


class ReviveCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Slash command
    @app_commands.command(name="revive", description="revive a player")
    @app_commands.describe(user="The user you want to revive")
    async def removeRole(self, interaction: discord.Interaction, user: discord.Member):
        print(f"{interaction.user.mention} want to revive {user.mention}")

        role_id = int(os.getenv("SHOT_ROLE"))
        role = interaction.guild.get_role(role_id)

        # Check if the user already have the role
        has_role = any(r.name == role.name for r in user.roles)
        has_medkit = True # TBD: Implement a logic that check for if the user have a medkit

        # Check if the role exists
        if not role:
            await interaction.response.send_message("Shot Role not found.", ephemeral=True)
            return
        if not has_role:
            await interaction.response.send_message(f"{user.mention} is not dead", ephemeral=True)
            return
        # Check if the user has a medkit that can be used
        if not has_medkit:
            await interaction.response.send_message(f"You don't have any medkit, lel", ephemeral=True)
            return
        else:
            try:
                await user.remove_roles(role)
                await interaction.response.send_message(f"{user.mention} has been revived!")
            except discord.Forbidden:
                await interaction.response.send_message(f"I do not have permission to remove that role. Please enable manage roles and/or move my role above the shot role")
            except Exception as e:
                await interaction.response.send_message(f"An error occured: {e}")


# Export to main.py or something similar
async def setup(bot: commands.Bot):
    await bot.add_cog(ReviveCommand(bot))
