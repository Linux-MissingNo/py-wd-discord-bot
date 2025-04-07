import discord
from discord import app_commands
from discord.ext import commands

class SyncCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="sync", description="Manually sync slash commands to the guild.")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        
        print(f"{interaction.user} has called a guild sync")

        try:
            synced = await self.client.tree.sync(guild=interaction.guild)
            await interaction.response.send_message(f"Commands synced for this guild! Synced {len(synced)} command(s).", ephemeral=True)
            print(f"Synced commands for guild: {interaction.guild.name}")
        except Exception as e:
            await interaction.response.send_message(f"Error syncing commands: {e}", ephemeral=True)
            print(f"Error syncing commands: {e}")

async def setup(client: commands.Bot):
    await client.add_cog(SyncCommands(client))
