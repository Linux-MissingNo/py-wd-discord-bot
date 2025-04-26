import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class InventoryCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_player(self, player_id: str):
        registration_cog = self.bot.get_cog('Registration')
        if registration_cog:
            await registration_cog.create_player_if_not_exists(self.bot.db_pool, player_id)
        else:
            logger.error("Registration cog is not loaded. Unable to create player.")
            raise Exception("Registration cog not found.")

    def has_admin_permission(self, member: discord.Member) -> bool:
        return member.guild_permissions.manage_guild

    @app_commands.command(name="inventory", description="Check a player's inventory (balance, guns, vests, medkits).")
    @app_commands.describe(user="(Optional) The user whose inventory you want to check.")
    async def check_inventory(self, interaction: discord.Interaction, user: discord.Member = None):
        """
        Displays the inventory of the caller or another player (requires 'Manage Server' permission for others).
        """
        caller = interaction.user
        target = user or caller

        if user and user.id != caller.id and not self.has_admin_permission(caller):
            await interaction.response.send_message(
                "You must have the **Manage Server** permission to check another player's inventory.",
                ephemeral=True
            )
            logger.warning(f"{caller} attempted to view {user}'s inventory without permission.")
            return

        player_id = str(target.id)

        await self.create_player(player_id)

        async with self.bot.db_pool.acquire() as conn:
            try:
                query = """
                    SELECT balance, guns, vest, medkit
                    FROM players_table
                    WHERE player_id = $1
                """
                data = await conn.fetchrow(query, player_id)

                if data is None:
                    await interaction.response.send_message("Player data not found.", ephemeral=True)
                    logger.warning(f"No data found for player {player_id}.")
                    return

                embed = discord.Embed(
                    title=f"{target.display_name}'s Inventory",
                    color=discord.Color.gold() if user else discord.Color.blurple()
                )
                embed.add_field(name="Balance", value=f"${data['balance']}", inline=False)
                embed.add_field(name="Guns", value=f"{data['guns']}", inline=True)
                embed.add_field(name="Vests", value=f"{data['vest']}", inline=True)
                embed.add_field(name="Medkits", value=f"{data['medkit']}", inline=True)

                await interaction.response.send_message(embed=embed)

            except Exception as e:
                logger.exception(f"Error fetching inventory for {player_id}: {e}")
                await interaction.response.send_message("An error occurred while fetching the inventory.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(InventoryCommand(bot))