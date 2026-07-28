"""Moderation Discord Bot Cog"""
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
ALLOWED_ROLE = os.getenv('DISCORD_MOD_ROLE_ID')


class ModerationCog(commands.Cog):
    """Moderation commands"""

    def __init__(self, bot):
        self.bot = bot

    async def check_permissions(self, interaction: discord.Interaction):
        """Check if user has moderation permissions"""
        if ALLOWED_ROLE:
            role = discord.utils.get(interaction.user.roles, id=int(ALLOWED_ROLE))
            if not role and not interaction.user.guild_permissions.administrator:
                return False
        elif not interaction.user.guild_permissions.administrator:
            return False
        return True

    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.describe(user="The user to ban", reason="Ban reason")
    async def ban(self, interaction: discord.Interaction, user: discord.User, reason: str = "No reason provided"):
        """Ban a user"""
        if not await self.check_permissions(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            try:
                # Find user in database
                url = f"{API_BASE_URL}/api/v1/discord/{user.id}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("User not found in database.")
                        return

                    user_data = await resp.json()
                    user_id = user_data.get('id')

                    # Ban the user
                    ban_url = f"{API_BASE_URL}/admin/users/{user_id}/ban"
                    async with session.post(ban_url, json={'reason': reason}) as ban_resp:
                        if ban_resp.status == 200:
                            embed = discord.Embed(
                                title="🔨 User Banned",
                                description=f"**{user}** has been banned.\nReason: {reason}",
                                color=0xEF4444
                            )
                            embed.set_footer(text=f"Banned by {interaction.user}")
                            await interaction.followup.send(embed=embed)
                        else:
                            await interaction.followup.send("Failed to ban user.")

            except Exception as e:
                await interaction.followup.send(f"Error: {e}")

    @app_commands.command(name="kick", description="Kick a user")
    @app_commands.describe(user="The user to kick", reason="Kick reason")
    async def kick(self, interaction: discord.Interaction, user: discord.User, reason: str = "No reason provided"):
        """Kick a user"""
        if not await self.check_permissions(interaction):
            await interaction.response.send_message("You don't have permission.", ephemeral=True)
            return

        embed = discord.Embed(
            title="👢 User Kicked",
            description=f"**{user}** has been kicked.\nReason: {reason}",
            color=0xF59E0B
        )
        embed.set_footer(text=f"Kicked by {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(user="The user to warn", reason="Warning reason")
    async def warn(self, interaction: discord.Interaction, user: discord.User, reason: str = "No reason provided"):
        """Warn a user"""
        if not await self.check_permissions(interaction):
            await interaction.response.send_message("You don't have permission.", ephemeral=True)
            return

        embed = discord.Embed(
            title="⚠️ Warning Issued",
            description=f"**{user}** has been warned.\nReason: {reason}",
            color=0xF59E0B
        )
        embed.set_footer(text=f"Warned by {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unban", description="Unban a user")
    @app_commands.describe(user="The user to unban")
    async def unban(self, interaction: discord.Interaction, user: discord.User):
        """Unban a user"""
        if not await self.check_permissions(interaction):
            await interaction.response.send_message("You don't have permission.", ephemeral=True)
            return

        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            try:
                url = f"{API_BASE_URL}/api/v1/discord/{user.id}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("User not found.")
                        return

                    user_data = await resp.json()
                    user_id = user_data.get('id')

                    unban_url = f"{API_BASE_URL}/admin/users/{user_id}/unban"
                    async with session.post(unban_url) as unban_resp:
                        if unban_resp.status == 200:
                            embed = discord.Embed(
                                title="✅ User Unbanned",
                                description=f"**{user}** has been unbanned.",
                                color=0x10B981
                            )
                            await interaction.followup.send(embed=embed)
                        else:
                            await interaction.followup.send("Failed to unban.")

            except Exception as e:
                await interaction.followup.send(f"Error: {e}")

    @app_commands.command(name="black-list", description="Add/remove item from blacklist")
    async def black_list(self, interaction: discord.Interaction, action: str, item_name: str = None):
        """Manage blacklist"""
        if not await self.check_permissions(interaction):
            await interaction.response.send_message("You don't have permission.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🚫 Blacklist Management",
            description=f"Action: **{action}**\nItem: **{item_name}**",
            color=0xEF4444
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add-item", description="Add an item to the shop")
    async def add_item(self, interaction: discord.Interaction, name: str, price: int, item_type: str):
        """Add item to shop"""
        if not await self.check_permissions(interaction):
            await interaction.response.send_message("You don't have permission.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🛒 Add Shop Item",
            description=f"Name: **{name}**\nPrice: **{price}** coins\nType: **{item_type}**",
            color=0x10B981
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
