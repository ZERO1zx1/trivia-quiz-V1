"""Marketplace Discord Bot Cog"""
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')


class MarketplaceCog(commands.Cog):
    """Marketplace commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="trade", description="Trade items with another user")
    async def trade(self, interaction: discord.Interaction, user: discord.User, item: str):
        """Trade items"""
        embed = discord.Embed(
            title="🔄 Trade Request",
            description=f"{interaction.user.mention} wants to trade **{item}** with {user.mention}\n\n"
                        f"To complete this trade, please visit:\n{API_BASE_URL}/marketplace",
            color=0xF59E0B
        )

        view = TradeView(user, item)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="marketplace", description="View marketplace listings")
    async def marketplace(self, interaction: discord.Interaction, item_type: str = "all", sort: str = "newest"):
        """View marketplace"""
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            try:
                url = f"{API_BASE_URL}/marketplace/api/listings?type={item_type}"
                async with session.get(url) as resp:
                    data = await resp.json()
                    listings = data.get('listings', [])

                    if not listings:
                        await interaction.followup.send("No items for sale.")
                        return

                    embed = discord.Embed(
                        title="🛒 Marketplace",
                        color=0x10B981
                    )

                    for listing in listings[:10]:
                        rarity_emoji = {
                            'mythic': '🌟', 'legendary': '⭐', 'epic': '💎',
                            'rare': '🔵', 'common': '⚪'
                        }.get(listing.get('rarity', 'common'), '⚪')

                        embed.add_field(
                            name=f"{rarity_emoji} {listing.get('item_name', 'Unknown')}",
                            value=f"Price: **{listing.get('price', 0)}** coins\n"
                                  f"Seller: {listing.get('seller', {}).get('username', 'Unknown')}",
                            inline=True
                        )

                    embed.set_footer(text=f"Total: {data.get('total', 0)} listings")
                    await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"Error: {e}")

    @app_commands.command(name="auction", description="View active auctions")
    async def auction(self, interaction: discord.Interaction):
        """View active auctions"""
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            try:
                url = f"{API_BASE_URL}/marketplace/api/auctions"
                async with session.get(url) as resp:
                    data = await resp.json()
                    auctions = data.get('auctions', [])

                    if not auctions:
                        await interaction.followup.send("No active auctions.")
                        return

                    embed = discord.Embed(
                        title="🔨 Active Auctions",
                        color=0xF59E0B
                    )

                    for a in auctions[:10]:
                        embed.add_field(
                            name=f"🔨 {a.get('item_name', 'Unknown')}",
                            value=f"Current Bid: **{a.get('current_bid', a.get('starting_price', 0))}** coins\n"
                                  f"Bids: {a.get('bid_count', 0)} | "
                                  f"Buy Now: {a.get('buy_now_price', 'N/A')} coins\n"
                                  f"Ends: {a.get('ends_at', 'Unknown')}",
                            inline=False
                        )

                    await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"Error: {e}")


class TradeView(discord.ui.View):
    def __init__(self, target_user, item):
        super().__init__(timeout=300)
        self.target_user = target_user
        self.item = item

    @discord.ui.button(label="Accept Trade", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id:
            await interaction.response.send_message("Only the target user can accept.", ephemeral=True)
            return

        embed = discord.Embed(
            title="✅ Trade Accepted",
            description=f"{self.target_user.mention} accepted the trade for **{self.item}**!\n\n"
                        f"Visit {API_BASE_URL}/marketplace to complete the transaction.",
            color=0x10B981
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Decline Trade", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id:
            await interaction.response.send_message("Only the target user can decline.", ephemeral=True)
            return

        embed = discord.Embed(
            title="❌ Trade Declined",
            description=f"{self.target_user.mention} declined the trade.",
            color=0xEF4444
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(MarketplaceCog(bot))
