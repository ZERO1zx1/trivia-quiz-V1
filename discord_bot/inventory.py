import discord
from discord.ext import commands
from discord import app_commands

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="View your inventory")
    async def inventory(self, interaction: discord.Interaction):
        view = discord.ui.View()
        # Dropdown (Select Menu)
        select = discord.ui.Select(
            placeholder="Choose a category...",
            options=[
                discord.SelectOption(label="All Items", value="all", emoji="🎒"),
                discord.SelectOption(label="Frames", value="frames", emoji="🖼️"),
                discord.SelectOption(label="Boxes", value="boxes", emoji="📦"),
                discord.SelectOption(label="Titles", value="titles", emoji="👑"),
            ]
        )
        async def select_callback(interaction: discord.Interaction):
            selected = select.values[0]
            await interaction.response.send_message(f"You selected: {selected}", ephemeral=True)
        select.callback = select_callback
        view.add_item(select)

        await interaction.response.send_message("Select a category:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))