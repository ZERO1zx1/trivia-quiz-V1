import discord
from discord.ext import commands
from discord import app_commands

class SocialCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add-friend", description="Send a friend request")
    @app_commands.describe(username="TriviaVerse username")
    async def add_friend(self, interaction: discord.Interaction, username: str):
        # Discord ID-аар хэрэглэгчийг олох (эхлээд өөрийнхөө)
        async with self.bot.session.post(
            f"{self.bot.api_base}/friends/search",
            json={
                "discord_id": str(interaction.user.id),
                "username": username
            }
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                embed = discord.Embed(
                    title="✅ Friend Request Sent",
                    description=f"Sent to **{username}**!",
                    color=0x57F287
                )
            else:
                embed = discord.Embed(
                    title="❌ Failed",
                    description="User not found or request already pending.",
                    color=0xED4245
                )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SocialCog(bot))