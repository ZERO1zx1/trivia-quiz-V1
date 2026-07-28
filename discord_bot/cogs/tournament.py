"""Tournament System Discord Bot Cog"""
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
from datetime import datetime

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')


class TournamentCog(commands.Cog):
    """Tournament system commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tournament", description="View tournament information")
    async def tournament_info(self, interaction: discord.Interaction, tournament_id: int = None):
        """View tournament information"""
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            try:
                if tournament_id:
                    url = f"{API_BASE_URL}/tournament/api/{tournament_id}"
                    async with session.get(url) as resp:
                        if resp.status == 404:
                            await interaction.followup.send("Tournament not found.")
                            return
                        data = await resp.json()

                        embed = discord.Embed(
                            title=f"🏆 {data['name']}",
                            description=data.get('description', 'No description'),
                            color=0xF59E0B
                        )
                        embed.add_field(name="Type", value=data.get('type', 'bracket'), inline=True)
                        embed.add_field(name="Status", value=data.get('status', 'unknown'), inline=True)
                        embed.add_field(name="Category", value=data.get('category', 'general'), inline=True)
                        embed.add_field(name="Difficulty", value=data.get('difficulty', 'mixed'), inline=True)
                        embed.add_field(name="Max Players", value=str(data.get('max_participants', 0)), inline=True)
                        embed.add_field(name="Prize Pool", value=f"{data.get('prize_pool', 0)} coins", inline=True)
                        embed.add_field(name="Region", value=data.get('region', 'global'), inline=True)
                        embed.add_field(name="Participants", value=str(data.get('participants_count', 0)), inline=True)

                        if data.get('start_time'):
                            embed.add_field(name="Start Time", value=data['start_time'], inline=False)

                        await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("Usage: /tournament <tournament_id>")

            except Exception as e:
                await interaction.followup.send(f"Error: {e}")

    @app_commands.command(name="tournament-list", description="List upcoming tournaments")
    async def tournament_list(self, interaction: discord.Interaction, status: str = "upcoming"):
        """List tournaments"""
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            try:
                url = f"{API_BASE_URL}/tournament/api/list?status={status}"
                async with session.get(url) as resp:
                    data = await resp.json()
                    tournaments = data.get('tournaments', [])

                    if not tournaments:
                        await interaction.followup.send(f"No {status} tournaments found.")
                        return

                    embed = discord.Embed(
                        title=f"🏆 {status.capitalize()} Tournaments",
                        color=0xF59E0B
                    )

                    for t in tournaments[:10]:
                        embed.add_field(
                            name=f"#{t['id']} - {t['name']}",
                            value=f"{t.get('type', 'bracket')} | {t.get('prize_pool', 0)} coins prize | "
                                  f"{t.get('participants_count', 0)}/{t.get('max_participants', 0)} players",
                            inline=False
                        )

                    await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"Error: {e}")

    @app_commands.command(name="tournament-register", description="Register for a tournament")
    async def tournament_register(self, interaction: discord.Interaction, tournament_id: int):
        """Register for a tournament"""
        embed = discord.Embed(
            title="🏆 Tournament Registration",
            description=f"To register for tournament #{tournament_id}, please visit:\n"
                        f"{API_BASE_URL}/tournament/{tournament_id}\n\n"
                        f"Or use the button below to register directly.",
            color=0x10B981
        )

        view = TournamentRegisterView(tournament_id)
        await interaction.response.send_message(embed=embed, view=view)


class TournamentRegisterView(discord.ui.View):
    def __init__(self, tournament_id):
        super().__init__(timeout=60)
        self.tournament_id = tournament_id

    @discord.ui.button(label="Register Now", style=discord.ButtonStyle.success)
    async def register(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏆 Registration",
            description=f"To register for tournament #{self.tournament_id}, "
                        f"please visit the website:\n{API_BASE_URL}/tournament/{self.tournament_id}",
            color=0x3B82F6
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(TournamentCog(bot))
