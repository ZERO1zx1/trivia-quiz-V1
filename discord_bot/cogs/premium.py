import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class PremiumCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_premium_info(self, discord_id: str):
        """Вэб API-с хэрэглэгчийн premium мэдээллийг авах"""
        async with self.bot.session.get(
            f"{self.bot.api_base}/user/{discord_id}"
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data
            return None

    @app_commands.command(name="premium", description="View your premium status")
    async def premium(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_data = await self._get_premium_info(str(interaction.user.id))
        if not user_data:
            await interaction.followup.send("❌ Not linked to website.", ephemeral=True)
            return

        is_prem = user_data.get('is_premium', False)
        if not is_prem:
            await interaction.followup.send("❌ You are not premium.", ephemeral=True)
            return

        embed = discord.Embed(title="👑 Premium Status", color=0xFFD700)
        embed.add_field(name="Expires", value=user_data.get('premium_expiry', 'N/A'))
        embed.add_field(name="Coin Multiplier", value="3x")
        embed.add_field(name="Daily Bonus", value="3,000 Coins")

        view = discord.ui.View()
        # Claim Daily Button
        view.add_item(discord.ui.Button(label="💳 Claim 3,000 Coins", style=discord.ButtonStyle.primary, custom_id="claim_premium_daily"))
        # Open Boxes Button
        view.add_item(discord.ui.Button(label="🧰 Open Boxes", style=discord.ButtonStyle.secondary, custom_id="open_boxes"))
        # Premium Perks Button
        view.add_item(discord.ui.Button(label="👑 Premium Perks", style=discord.ButtonStyle.success, custom_id="premium_perks"))

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # Button callback
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get('custom_id')

        if custom_id == "claim_premium_daily":
            # API-р дамжуулан өдрийн шагнал авах
            async with self.bot.session.post(
                f"{self.bot.api_base}/premium/daily-premium-reward",
                json={"discord_id": str(interaction.user.id)}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('success'):
                        await interaction.response.send_message(f"✅ Claimed {data['reward']} coins!", ephemeral=True)
                    else:
                        await interaction.response.send_message(data.get('message', 'Error'), ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Failed to claim.", ephemeral=True)

        elif custom_id == "open_boxes":
            # Хэрэглэгчийн авдруудыг харуулах (энгийн жишээ)
            await interaction.response.send_message("📦 Opening boxes... (future feature)", ephemeral=True)

        elif custom_id == "premium_perks":
            embed = discord.Embed(title="👑 Premium Perks", color=0xFFD700)
            embed.add_field(name="💰 3,000 Daily Coins", value="Claim every 24 hours")
            embed.add_field(name="📈 3x Coin Multiplier", value="In all games")
            embed.add_field(name="📦 500+ Box Storage", value="Keep all your loot")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def open_boxes_callback(self, interaction: discord.Interaction):
        # Товчлуурыг шууд идэвхгүй болгох
        for child in interaction.message.components[0].children:
            child.disabled = True
        await interaction.response.edit_message(view=interaction.message.components[0])

        # API дуудах
        async with self.bot.session.post(
            f"{self.bot.api_base}/box/open-box/{box_id}",
            json={"discord_id": str(interaction.user.id)}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                await interaction.followup.send(f"Opened! Got: {data['loot']}", ephemeral=True)
            else:
                await interaction.followup.send("Failed to open box.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PremiumCog(bot))