import discord
from discord.ext import commands
from discord import app_commands

class FortuneCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="spin", description="🎰 Spin the daily fortune wheel")
    async def spin(self, interaction: discord.Interaction):
        async with self.bot.session.post(
            f"{self.bot.api_base}/fortune/spin",
            json={"discord_id": str(interaction.user.id)}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get('success'):
                    prize = data['prize']
                    embed = discord.Embed(title="🎡 Fortune Wheel", description=f"You won **{prize['name']}**! {prize['icon']}", color=0xFFD700)
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message(data.get('message', 'Error'), ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to spin.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(FortuneCog(bot))