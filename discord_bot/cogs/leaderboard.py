import discord
from discord.ext import commands
from discord import app_commands

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _fetch_leaderboard(self, period: str = "alltime", limit: int = 10):
        try:
            async with self.bot.session.get(
                f"{self.bot.api_base}/leaderboard",
                params={"period": period, "limit": limit}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception:
            return []

    @app_commands.command(name="leaderboard", description="View global leaderboard")
    @app_commands.describe(period="Time period", limit="Number of players (max 25)")
    @app_commands.choices(period=[
        app_commands.Choice(name="Daily", value="daily"),
        app_commands.Choice(name="Weekly", value="weekly"),
        app_commands.Choice(name="Monthly", value="monthly"),
        app_commands.Choice(name="All Time", value="alltime")
    ])
    async def leaderboard(self, interaction: discord.Interaction, period: str = "alltime", limit: int = 10):
        limit = min(max(limit, 3), 25)
        await interaction.response.defer()

        data = await self._fetch_leaderboard(period=period, limit=limit)
        if not data:
            embed = discord.Embed(
                title="🏆 Leaderboard",
                description="No data available yet.",
                color=0xFFD700
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"🏆 {period.title()} Leaderboard",
            color=0xFFD700
        )

        medals = ["🥇", "🥈", "🥉"]
        for i, entry in enumerate(data[:limit]):
            rank = i + 1
            medal = medals[i] if i < 3 else f"#{rank}"
            username = entry.get('username', 'Unknown')
            score = entry.get('score', 0)
            embed.add_field(
                name=f"{medal} {username}",
                value=f"Score: {score} | Wins: {entry.get('wins', 0)}",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="stats", description="View server statistics")
    async def stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            async with self.bot.session.get(f"{self.bot.api_base}/stats") as resp:
                if resp.status == 200:
                    data = await resp.json()
                else:
                    data = None
        except Exception:
            data = None
        
        embed = discord.Embed(
            title="📊 TriviaVerse Statistics",
            color=0x5865F2
        )
        
        if data:
            embed.add_field(name="👥 Total Players", value=f"{data.get('total_players', 'N/A'):,}", inline=True)
            embed.add_field(name="❓ Total Questions", value=f"{data.get('total_questions', 'N/A'):,}", inline=True)
            embed.add_field(name="📁 Categories", value=f"{data.get('total_categories', 'N/A')}", inline=True)
            embed.add_field(name="🚪 Active Rooms", value=f"{data.get('active_rooms', 'N/A')}", inline=True)
        else:
            embed.description = "⚠️ Could not fetch statistics from the server."
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))