"""Guild System Discord Bot Cog"""
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os

GUILD_ID = os.getenv('DISCORD_GUILD_ID')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')


class GuildCog(commands.Cog):
    """Guild system commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="guild", description="View guild information")
    async def guild_info(self, interaction: discord.Interaction, guild_name: str = None):
        """View guild information"""
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            try:
                if guild_name:
                    url = f"{API_BASE_URL}/guild/api/list?search={guild_name}"
                    async with session.get(url) as resp:
                        data = await resp.json()
                        guilds = data.get('guilds', [])
                        if not guilds:
                            await interaction.followup.send(f"No guild found with name '{guild_name}'.")
                            return

                        g = guilds[0]
                        embed = discord.Embed(
                            title=f"🏰 {g['name']} [{g['tag']}]",
                            description=g.get('description', 'No description'),
                            color=0x7C3AED
                        )
                        embed.add_field(name="Level", value=str(g.get('level', 1)), inline=True)
                        embed.add_field(name="Members", value=str(g.get('member_count', 0)), inline=True)
                        embed.add_field(name="Coins", value=str(g.get('coins', 0)), inline=True)
                        embed.add_field(name="Region", value=g.get('region', 'global'), inline=True)
                        embed.add_field(name="Created", value=g.get('created_at', 'Unknown'), inline=True)

                        await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("Usage: /guild <guild_name>")

            except Exception as e:
                await interaction.followup.send(f"Error fetching guild info: {e}")

    @app_commands.command(name="guild-create", description="Create a new guild")
    async def guild_create(self, interaction: discord.Interaction, name: str, tag: str):
        """Create a new guild"""
        await interaction.response.defer()

        embed = discord.Embed(
            title="🏰 Create Guild",
            description=f"To create a guild, please visit the website:\n{API_BASE_URL}/guild/create\n\n"
                        f"Guild Name: **{name}**\nTag: **[{tag}]**",
            color=0x10B981
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="guild-top", description="View top guilds")
    async def guild_top(self, interaction: discord.Interaction, region: str = "global"):
        """View top guilds"""
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            try:
                url = f"{API_BASE_URL}/guild/api/list?region={region}&page=1"
                async with session.get(url) as resp:
                    data = await resp.json()
                    guilds = data.get('guilds', [])

                    if not guilds:
                        await interaction.followup.send("No guilds found.")
                        return

                    embed = discord.Embed(
                        title=f"🏆 Top Guilds - {region.upper()}",
                        color=0x7C3AED
                    )

                    for i, g in enumerate(guilds[:10], 1):
                        medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f"**{i}**"
                        embed.add_field(
                            name=f"{medal} {g['name']} [{g['tag']}]",
                            value=f"Level {g.get('level', 1)} | {g.get('member_count', 0)} members",
                            inline=False
                        )

                    await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"Error: {e}")


async def setup(bot):
    await bot.add_cog(GuildCog(bot))
