import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class SyncCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="sync", description="Manually sync slash commands to the guild.")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        """
        Syncs the bot's commands to the guild and provides feedback.
        Only accessible by administrators.
        """
        try:
            # Log the start of the sync process
            logger.debug("Started syncing commands for guild: %s", interaction.guild.name)

            # Send an initial response acknowledging the command
            await interaction.response.send_message("Syncing commands, please wait...", ephemeral=True)

            # Fetch the guild ID from the interaction and create a guild object
            guild_id = interaction.guild.id
            guild = discord.Object(id=guild_id)

            # Log that the sync process has started
            logger.debug("Syncing commands for guild ID: %d", guild_id)

            # Perform the sync operation
            synced = await self.client.tree.sync(guild=guild)

            # If commands were successfully synced, log and list each command
            if synced:
                synced_commands = [command.name for command in synced]
                logger.debug("Successfully synced the following commands for guild %s: %s", interaction.guild.name, ', '.join(synced_commands))
                await interaction.followup.send(f"Commands synced for this guild! Synced {len(synced)} command(s): {', '.join(synced_commands)}.", ephemeral=True)
            else:
                # If no commands were synced, send a notification
                logger.debug("No commands synced for guild %s.", interaction.guild.name)
                await interaction.followup.send("No commands were synced.", ephemeral=True)
        
        except Exception as e:
            # Log the error
            logger.error("Error syncing commands for guild %s: %s", interaction.guild.name, str(e))

            # Send an error message to the user using followup to avoid interaction responded issue
            await interaction.followup.send(f"Error syncing commands: {e}", ephemeral=True)

            # Log the exception traceback for debugging
            logger.exception("Exception occurred during sync command.")

async def setup(client: commands.Bot):
    await client.add_cog(SyncCommands(client))
