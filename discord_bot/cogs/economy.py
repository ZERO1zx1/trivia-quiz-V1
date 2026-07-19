import discord
from discord.ext import commands
from discord import app_commands

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_user(self, discord_id: str):
        async with self.bot.session.get(
            f"{self.bot.api_base}/user/{discord_id}"
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return None

    async def _add_coins(self, discord_id: str, amount: int, reason: str):
        async with self.bot.session.post(
            f"{self.bot.api_base}/users/coins/add",
            json={"discord_id": discord_id, "amount": amount, "reason": reason}
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return None

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with self.bot.session.post(
            f"{self.bot.api_base}/daily",
            json={"discord_id": str(interaction.user.id)}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("success"):
                    embed = discord.Embed(
                        title="🎁 Daily Reward Claimed!",
                        description=f"You received **🪙 {data.get('reward', 100)} coins**!",
                        color=0x57F287
                    )
                    embed.add_field(name="New Balance", value=f"🪙 {data.get('new_coins', '?')} coins")
                    embed.set_footer(text="Come back tomorrow for more!")
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(
                        f"⏰ {data.get('message', 'You already claimed your daily reward.')}",
                        ephemeral=True
                    )
            elif resp.status == 400:
                data = await resp.json()
                await interaction.followup.send(
                    f"⏰ {data.get('message', 'Cooldown not over.')}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ Failed to claim daily reward. Try again later.",
                    ephemeral=True
                )
        
        try:
            async with self.bot.session.post(
                f"{self.bot.api_base}/notify",
                json={
                    "discord_id": str(interaction.user.id),
                    "title": "Daily Reward",
                    "message": "You claimed your daily reward!",
                    "type": "success"
                }
            ):
                pass
        except Exception:
            pass

    @app_commands.command(name="balance", description="Check your coin balance")
    async def balance(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_data = await self._get_user(str(interaction.user.id))
        if user_data:
            coins = user_data.get("coins", 0)
            embed = discord.Embed(
                title="💰 Your Balance",
                description=f"**🪙 {coins}** coins",
                color=0xFFD700
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(
                "❌ Could not retrieve balance. Have you linked your account?",
                ephemeral=True
            )

    @app_commands.command(name="shop", description="Browse the TriviaVerse shop")
    async def shop(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with self.bot.session.get(f"{self.bot.api_base}/shop/items") as resp:
            if resp.status == 200:
                items = await resp.json()
                if not items:
                    await interaction.followup.send("🛒 The shop is empty.", ephemeral=True)
                    return

                embed = discord.Embed(
                    title="🛒 TriviaVerse Shop",
                    description="Use `/buy <item_id>` to purchase an item.",
                    color=0x5865F2
                )
                for item in items[:5]:
                    embed.add_field(
                        name=f"{item['name']} (ID: {item['id']})",
                        value=f"{item['description']}\n🪙 **{item['price']}** coins",
                        inline=False
                    )
                if len(items) > 5:
                    embed.set_footer(text=f"... and {len(items)-5} more items.")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(
                    "❌ Could not load shop items.",
                    ephemeral=True
                )

    @app_commands.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(item_id="ID of the item to buy")
    async def buy(self, interaction: discord.Interaction, item_id: int):
        await interaction.response.defer(ephemeral=True)

        async with self.bot.session.post(
            f"{self.bot.api_base}/buy",
            json={"discord_id": str(interaction.user.id), "item_id": item_id}
        ) as resp:
            data = await resp.json()
            if resp.status == 200 and data.get("success"):
                embed = discord.Embed(
                    title="✅ Purchase Successful",
                    description=f"You bought **{data.get('item_name', 'item')}**!",
                    color=0x57F287
                )
                embed.add_field(name="Coins left", value=f"🪙 {data.get('coins_left', '?')}")
                await interaction.followup.send(embed=embed, ephemeral=True)
            elif resp.status == 402:
                await interaction.followup.send(
                    "❌ Not enough coins!",
                    ephemeral=True
                )
            elif resp.status == 404:
                await interaction.followup.send(
                    "❌ Item not found.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Purchase failed: {data.get('error', 'Unknown error')}",
                    ephemeral=True
                )

    @app_commands.command(name="inventory", description="View your purchased items")
    async def inventory(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with self.bot.session.get(
            f"{self.bot.api_base}/user/{interaction.user.id}/inventory"
        ) as resp:
            if resp.status == 200:
                items = await resp.json()
                if not items:
                    await interaction.followup.send(
                        "🎒 Your inventory is empty. Visit the shop!",
                        ephemeral=True
                    )
                    return

                embed = discord.Embed(
                    title="🎒 Your Inventory",
                    color=0x8B5CF6
                )
                for inv in items[:10]:
                    equipped = "✅ " if inv.get("is_equipped") else ""
                    embed.add_field(
                        name=f"{equipped}{inv['item']['name']} (x{inv['quantity']})",
                        value=f"ID: {inv['item_id']} | Use `/equip {inv['item_id']}` to equip",
                        inline=False
                    )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    "❌ Could not load inventory.",
                    ephemeral=True
                )

    @app_commands.command(name="equip", description="Equip an item from your inventory")
    @app_commands.describe(item_id="ID of the item to equip")
    async def equip(self, interaction: discord.Interaction, item_id: int):
        await interaction.response.defer(ephemeral=True)

        async with self.bot.session.post(
            f"{self.bot.api_base}/equip",
            json={"discord_id": str(interaction.user.id), "item_id": item_id}
        ) as resp:
            data = await resp.json()
            if resp.status == 200 and data.get("success"):
                await interaction.followup.send(
                    f"✅ Equipped **{data.get('item_name', 'item')}**!",
                    ephemeral=True
                )
            elif resp.status == 404:
                await interaction.followup.send(
                    "❌ Item not found in your inventory.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Could not equip: {data.get('error', 'Unknown error')}",
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))