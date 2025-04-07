import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
import os


class ShootCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.cooldown(1, 5, commands.BucketType.user) 
    @app_commands.command(name="shoot", description="Kill a user")
    @app_commands.describe(user="The user you want dead")
    async def assignRole(self, interaction: discord.Interaction, user: discord.Member):
        print(f"{interaction.user.mention} wants to shoot {user.mention}")

        role_id = int(os.getenv("SHOT_ROLE"))
        timeout_dur = int(os.getenv("SHOT_TIMEOUT_IN_HOURS"))
        role = interaction.guild.get_role(role_id)

        print(f"Role ID: {role_id}, Role fetched: {role}")

        if not role:
            await interaction.response.send_message("Shot Role not found.", ephemeral=True)
            return
        
        has_role = any(r.id == role.id for r in user.roles)
        print(f"User has role {role.name}: {has_role}")
        
        if has_role:
            await interaction.response.send_message(f"{user.mention} is already dead.", ephemeral=True)
            return

        try:
            print(f"Checking timeout status for {user.mention}")
            if user.timed_out:
                await interaction.response.send_message(f"{user.mention} is timed out, they will not be shot.", ephemeral=True)
                return
        except AttributeError:
            print(f"Cannot check timeout for {user.mention}, skipping this check.")

        print(f"User has gun: {True}")  # Replace this with your actual logic
        if not True:  # Replace with actual gun check
            await interaction.response.send_message(f"You don't have any gun, lel", ephemeral=True)
            return

        print(f"User has vest: {False}")  # Replace this with actual vest logic
        if False:  # Replace with actual vest check
            await interaction.response.send_message(f"{user.mention} was shot but their vest saved them!")
            return
        
        try:
            print(f"Assigning shot role and timeout to {user.mention}")
            await user.add_roles(role)
            await user.timeout(timedelta(seconds=timeout_dur))
            await interaction.response.send_message(f"{user.mention} has been shot!")
        except discord.Forbidden as e:
            print(f"Permission error: {e}")
            await interaction.response.send_message("Permission denied.", ephemeral=True)
        except Exception as e:
            print(f"Unexpected error: {e}")
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @assignRole.error
    async def shoot_command_error(self, interaction: discord.Interaction, error: Exception):
        if isinstance(error, commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"You're on cooldown! Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True
            )


# Export to main.py or something similar
async def setup(bot: commands.Bot):
    await bot.add_cog(ShootCommands(bot))