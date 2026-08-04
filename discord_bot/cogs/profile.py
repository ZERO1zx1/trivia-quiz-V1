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
        bank = user_data.get('bank_balance', 0)

        embed.add_field(name="Level", value=f"{level} ⭐", inline=True)
        embed.add_field(name="Bank", value=f"🏦 {bank}", inline=True)
        embed.add_field(name="XP", value=f"{xp}", inline=True)
        embed.add_field(name="Coins", value=f"🪙 {coins}", inline=True)
        embed.add_field(name="Wins", value=str(wins), inline=True)
        embed.add_field(name="Games Played", value=str(games), inline=True)
        embed.add_field(name="Accuracy", value=f"{accuracy:.1f}%", inline=True)
        embed.add_field(name="Elo Rating", value=f"📈 {user_data.get('elo_rating', 1200)}", inline=True)
        embed.add_field(name="Reputation", value=f"✨ {user_data.get('reputation', 0)}", inline=True)
        
        spouse = user_data.get('spouse')
        if spouse:
            embed.add_field(name="Spouse", value=f"💍 {spouse}", inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rep", description="Give a reputation point to another user")
    @app_commands.describe(user="User to give reputation to")
    async def rep(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        if user.id == interaction.user.id:
            await interaction.followup.send("You cannot give reputation to yourself!", ephemeral=True)
            return
            
        async with self.bot.session.post(f"{self.bot.api_base}/user/rep/give", json={
            "discord_id": str(interaction.user.id), "target_id": str(user.id)
        }) as resp:
            data = await resp.json()
            if resp.status == 200:
                await interaction.followup.send(f"✨ You gave a reputation point to {user.mention}!")
            else:
                await interaction.followup.send(f"❌ {data.get('error')}", ephemeral=True)

    @app_commands.command(name="marry", description="Marry another user")
    @app_commands.describe(user="User to propose to")
    async def marry(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        if user.id == interaction.user.id:
            await interaction.followup.send("You cannot marry yourself!", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="💍 Marriage Proposal!",
            description=f"{interaction.user.mention} has proposed to {user.mention}! Do you accept?",
            color=0xFF69B4
        )
        
        view = discord.ui.View(timeout=60)
        accept_btn = discord.ui.Button(label="I Do", style=discord.ButtonStyle.success)
        
        async def accept_callback(inter):
            if inter.user.id != user.id:
                await inter.response.send_message("This proposal isn't for you!", ephemeral=True)
                return
            
            async with self.bot.session.post(f"{self.bot.api_base}/user/marry", json={
                "discord_id": str(interaction.user.id), "target_id": str(user.id)
            }) as resp:
                if resp.status == 200:
                    await inter.response.send_message(f"💍 {interaction.user.mention} and {user.mention} are now married! 🎉")
                else:
                    data = await resp.json()
                    await inter.response.send_message(f"❌ {data.get('error')}", ephemeral=True)
                    
        accept_btn.callback = accept_callback
        view.add_item(accept_btn)
        await interaction.followup.send(embed=embed, view=view)

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