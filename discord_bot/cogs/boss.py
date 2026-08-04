import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import random

class BossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_boss = None
        self.player_cooldowns = {}
        self.player_damage = {}
        self.bot.loop.create_task(self.spawn_boss())

    async def spawn_boss(self):
        await self.bot.wait_until_ready()
        while True:
            # Өдөр бүр 12:00 цагт (UTC) эсвэл өөр тохиргоогоор
            now = datetime.utcnow()
            target = now.replace(hour=12, minute=0, second=0, microsecond=0)
            if target < now:
                target += timedelta(days=1)
            await asyncio.sleep((target - now).total_seconds())

            # API-р босс үүсгэх
            async with self.bot.session.post(f"{self.bot.api_base}/boss/spawn", json={"name":"🐉 Асуултын Дракон", "hp":100000}) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    self.active_boss = data
                    self.player_cooldowns = {}
                    self.player_damage = {}
                    channel = self.bot.get_channel(YOUR_CHANNEL_ID)  # сувгийн ID
                    if channel:
                        await channel.send(f"🐉 **{data['name']}** сэрлээ! (HP: {data['max_hp']:,})\n`/attack` ашиглан тулалдацгаа!")
            await asyncio.sleep(86400)  # дахин хүлээх

    @app_commands.command(name="attack", description="Босс руу дайрах")
    async def attack(self, interaction: discord.Interaction):
        if not self.active_boss or self.active_boss['status'] != 'active':
            await interaction.response.send_message("Одоо идэвхтэй босс байхгүй.", ephemeral=True)
            return

        # Cooldown (stun) шалгах
        if interaction.user.id in self.player_cooldowns:
            if datetime.utcnow() < self.player_cooldowns[interaction.user.id]:
                await interaction.response.send_message("Та 10 минутын өмнө буруу хариулсан тул хүлээх хэрэгтэй.", ephemeral=True)
                return

        # Асуулт авах (API)
        async with self.bot.session.get(f"{self.bot.api_base}/questions/random") as resp:
            if resp.status != 200:
                await interaction.response.send_message("Асуулт авахад алдаа гарлаа.", ephemeral=True)
                return
            question = await resp.json()

        embed = discord.Embed(title="⚔️ Boss Attack", description=question['question_text'], color=0xff0000)
        view = discord.ui.View()
        for i, ans in enumerate(question['answers']):
            btn = discord.ui.Button(label=ans['answer_text'], style=discord.ButtonStyle.primary, custom_id=f"boss_{i}_{question['correct_index']}")
            btn.callback = self.boss_answer_callback
            view.add_item(btn)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def boss_answer_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data['custom_id']
        _, selected, correct = custom_id.split('_')
        selected = int(selected)
        correct = int(correct)
        is_correct = (selected == correct)

        # Cooldown / Damage тооцоолол
        if is_correct:
            # Хурдан хариултыг шалгах (энгийнээр)
            damage = 1000
            # (илүү нарийвчлалтай цаг хэмжихийн тулд interaction-н created_at-г ашиглаж болно)
            if interaction.created_at and (datetime.utcnow() - interaction.created_at).total_seconds() < 3:
                damage = 2500
            self.player_damage[interaction.user.id] = self.player_damage.get(interaction.user.id, 0) + damage

            # API-р damage илгээх
            async with self.bot.session.post(f"{self.bot.api_base}/boss/damage", json={"boss_id": self.active_boss['id'], "discord_id": str(interaction.user.id), "damage": damage}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('defeated'):
                        await interaction.channel.send(f"🎉 Босс ялагдлаа! Шилдэг 3 тоглогчид шагнал олгогдлоо.")
                        self.active_boss = None
                    else:
                        await interaction.response.send_message(f"Та {damage} хохирол учрууллаа! Боссын үлдэгдэл HP: {data['current_hp']:,}", ephemeral=True)
        else:
            # 10 минутын cooldown
            self.player_cooldowns[interaction.user.id] = datetime.utcnow() + timedelta(minutes=10)
            await interaction.response.send_message("❌ Буруу хариулт! Та 10 минутын турш дахин дайрч чадахгүй.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BossCog(bot))