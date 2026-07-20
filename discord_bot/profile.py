import discord
from discord.ext import commands
from discord import app_commands

class Profile(commands.Cog):
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
    await bot.add_cog(Profile(bot))