import discord
from discord.ext import commands
from discord import app_commands

class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_user_xp(self, discord_id: str):
        try:
            async with self.bot.session.get(
                f"{self.bot.api_base}/user/{discord_id}"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
            return None

    async def _add_xp(self, discord_id: str, amount: int, reason: str = "Discord activity"):
        try:
            async with self.bot.session.post(
                f"{self.bot.api_base}/users/xp/add",
                json={
                    "discord_id": discord_id,
                    "amount": amount,
                    "reason": reason
                }
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
            return None

    @app_commands.command(name="level", description="Check your or another user's level and XP")
    @app_commands.describe(user="User to check (optional)")
    async def level(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        target = user or interaction.user
        data = await self._get_user_xp(str(target.id))

        if not data:
            embed = discord.Embed(
                title="❌ Not Found",
                description="This user hasn't linked their TriviaVerse account yet.",
                color=0xED4245
            )
            await interaction.followup.send(embed=embed)
            return

        level = data.get('level', 1)
        xp = data.get('xp', 0)
        xp_for_next = (level) ** 2 * 100
        progress = min(int((xp / xp_for_next) * 100), 100) if xp_for_next > 0 else 100

        embed = discord.Embed(
            title=f"⭐ {target.display_name}'s Level",
            color=0x5865F2
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp}** / {xp_for_next}", inline=True)
        embed.add_field(name="Progress", value=f"{progress}%", inline=True)
        embed.add_field(name="Coins", value=f"🪙 {data.get('coins', 0)}", inline=True)
        embed.add_field(name="Wins", value=data.get('wins', 0), inline=True)
        embed.add_field(name="Accuracy", value=f"{data.get('accuracy', 0):.1f}%", inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="top", description="View top players by level")
    async def top(self, interaction: discord.Interaction, limit: int = 10):
        await interaction.response.defer()
        limit = min(max(limit, 3), 10)

        try:
            async with self.bot.session.get(
                f"{self.bot.api_base}/leaderboard/top-level",
                params={"limit": limit}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                else:
                    raise Exception("API error")
        except Exception:
            embed = discord.Embed(
                title="❌ Error",
                description="Could not fetch leaderboard.",
                color=0xED4245
            )
            await interaction.followup.send(embed=embed)
            return

        if not data:
            embed = discord.Embed(
                title="🏆 Top Players",
                description="No players yet.",
                color=0xFFD700
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title="🏆 Top Players by Level",
            color=0xFFD700
        )
        medals = ["🥇", "🥈", "🥉"]
        for i, player in enumerate(data):
            rank = i + 1
            medal = medals[i] if i < 3 else f"#{rank}"
            embed.add_field(
                name=f"{medal} {player['username']}",
                value=f"Level: **{player['level']}** | XP: **{player['xp']}** | Coins: 🪙 {player['coins']}",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="add-xp", description="[Admin] Add XP to a user")
    @app_commands.describe(user="Target user", amount="Amount of XP to add", reason="Reason")
    @app_commands.default_permissions(administrator=True)
    async def add_xp(self, interaction: discord.Interaction, user: discord.Member, amount: int, reason: str = "Manual addition"):
        await interaction.response.defer(ephemeral=True)
        result = await self._add_xp(str(user.id), amount, reason)

        if result and 'error' not in result:
            embed = discord.Embed(
                title="✅ XP Added",
                description=f"Added **{amount}** XP to {user.mention}.\nNew Level: {result.get('level')}, XP: {result.get('xp')}",
                color=0x57F287
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="❌ Failed",
                description="Could not add XP. Is the user registered?",
                color=0xED4245
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(LevelCog(bot))