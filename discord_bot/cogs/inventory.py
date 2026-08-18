"""Inventory Cog - Disabled to avoid duplicate command conflict with Economy cog.

The /inventory command is already defined in cogs/economy.py with full API
integration. This cog is kept as a placeholder for future inventory-specific
features (e.g., item filtering, sorting, equipping UI).
"""
import discord
from discord.ext import commands
from discord import app_commands


class InventoryCog(commands.Cog):
    """Inventory management commands (extends Economy cog functionality)."""

    def __init__(self, bot):
        self.bot = bot

    # NOTE: /inventory command is defined in cogs/economy.py
    # Add inventory-specific commands here that don't conflict


async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
