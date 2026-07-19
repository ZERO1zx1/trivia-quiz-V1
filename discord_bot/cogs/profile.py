import discord
from discord.ext import commands
from discord import app_commands

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _fetch_user_data(self, discord_id: str):
        """Discord ID-аар хэрэглэгчийн мэдээллийг API-с авах"""
        try:
            async with self.bot.session.get(
                f"{self.bot.api_base}/user/{discord_id}"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
            return None

    async def _fetch_leaderboard(self, period: str = "alltime", limit: int = 10):
        """API-с leaderboard өгөгдөл авах"""
        try:
            async with self.bot.session.get(
                f"{self.bot.api_base}/leaderboard",
                params={"period": period, "limit": limit}
            ) as resp:import discord
from discord.ext import commands
from discord import app_commands

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _fetch_user_data(self, discord_id: str):
        try:
            async with self.bot.session.get(
                f"{self.bot.api_base}/user/{discord_id}"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
            return None

    @app_commands.command(name="profile", description="View your TriviaVerse profile")
    @app_commands.describe(user="User to view (optional)")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        target = user or interaction.user
        user_data = await self._fetch_user_data(str(target.id))

        if not user_data:
            embed = discord.Embed(
                title="❌ Profile Not Found",
                description=f"{target.mention} hasn't linked their TriviaVerse account yet.",
                color=0xED4245
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"🎮 {user_data.get('display_name', target.display_name)}'s Profile",
            color=0x5865F2
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        level = user_data.get('level', 1)
        xp = user_data.get('xp', 0)
        coins = user_data.get('coins', 0)
        wins = user_data.get('wins', 0)
        games = user_data.get('games_played', 0)
        accuracy = user_data.get('accuracy', 0.0)

        embed.add_field(name="Level", value=f"{level} ⭐", inline=True)
        embed.add_field(name="XP", value=f"{xp}", inline=True)
        embed.add_field(name="Coins", value=f"🪙 {coins}", inline=True)
        embed.add_field(name="Wins", value=str(wins), inline=True)
        embed.add_field(name="Games Played", value=str(games), inline=True)
        embed.add_field(name="Accuracy", value=f"{accuracy:.1f}%", inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="my-rank", description="Check your leaderboard rank")
    async def my_rank(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_data = await self._fetch_user_data(str(interaction.user.id))

        if not user_data:
            embed = discord.Embed(
                title="❌ Not Linked",
                description="Link your account to see your rank.",
                color=0xED4245
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title="🏆 Your Ranking",
            description=f"Level: {user_data.get('level',1)} | Score: {user_data.get('score',0)}",
            color=0xFFD700
        )
        embed.add_field(name="Wins", value=str(user_data.get('wins', 0)))
        embed.add_field(name="Games", value=str(user_data.get('games_played', 0)))
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception:
            return []

    # ---------------------------
    #  /profile [user]
    # ---------------------------
    @app_commands.command(name="profile", description="View your TriviaVerse profile")
    @app_commands.describe(user="User to view (optional)")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        target = user or interaction.user
        user_data = await self._fetch_user_data(str(target.id))

        if not user_data:
            embed = discord.Embed(
                title="❌ Profile Not Found",
                description=f"{target.mention} hasn't linked their TriviaVerse account yet.",
                color=0xED4245
            )
            await interaction.followup.send(embed=embed)
            return

        # API-с ирсэн өгөгдлөөр embed бөглөх
        embed = discord.Embed(
            title=f"🎮 {user_data.get('display_name', target.display_name)}'s Profile",
            color=0x5865F2
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        level = user_data.get('level', 1)
        xp = user_data.get('xp', 0)
        coins = user_data.get('coins', 0)
        wins = user_data.get('wins', 0)
        games = user_data.get('games_played', 0)
        accuracy = user_data.get('accuracy', 0.0)

        embed.add_field(name="Level", value=f"{level} ⭐", inline=True)
        embed.add_field(name="XP", value=f"{xp}", inline=True)
        embed.add_field(name="Coins", value=f"🪙 {coins}", inline=True)
        embed.add_field(name="Wins", value=str(wins), inline=True)
        embed.add_field(name="Games Played", value=str(games), inline=True)
        embed.add_field(name="Accuracy", value=f"{accuracy:.1f}%", inline=True)

        await interaction.followup.send(embed=embed)

    # ---------------------------
    #  /rank
    # ---------------------------
    @app_commands.command(name="rank", description="Check your leaderboard rank")
    async def rank(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_data = await self._fetch_user_data(str(interaction.user.id))

        if not user_data:
            embed = discord.Embed(
                title="❌ Not Linked",
                description="Link your account to see your rank.",
                color=0xED4245
            )
            await interaction.followup.send(embed=embed)
            return

        # API-с тусгайлан rank endpoint байхгүй бол ерөнхий leaderboard-с хайх
        # Энд бид /leaderboard?period=alltime&limit=100 гэх мэтээр татаад хэрэглэгчийг олох боломжтой
        # Хялбарчлахын тулд түр орхиё: хэрэглэгчийн score-г харуулна
        embed = discord.Embed(
            title="🏆 Your Ranking",
            description=f"Level: {user_data.get('level',1)} | Score: {user_data.get('score',0)}",
            color=0xFFD700
        )
        embed.add_field(name="Wins", value=str(user_data.get('wins', 0)))
        embed.add_field(name="Games", value=str(user_data.get('games_played', 0)))
        await interaction.followup.send(embed=embed)

    # ---------------------------
    #  /leaderboard
    # ---------------------------
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

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))