import discord
from discord.ext import commands
from discord import app_commands

class QuizCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @app_commands.command(name="create-room", description="Create a trivia room on the website")
    @app_commands.describe(name="Room name", private="Make room private", password="Password for private room")
    async def create_room(self, interaction: discord.Interaction, name: str = "Trivia Room",
                          private: bool = False, password: str = None):
        await interaction.response.defer()

        payload = {
            "name": name,
            "host_discord_id": str(interaction.user.id),
            "private": private,
        }
        if private and password:
            payload["password"] = password

        try:
            async with self.bot.session.post(f"{self.bot.api_base}/rooms/create", json=payload) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    room_code = data.get('code', '??????')
                    embed = discord.Embed(
                        title="🚪 Room Created!",
                        description=f"**{name}**\nCode: `{room_code}`",
                        color=0x5865F2
                    )
                    embed.add_field(name="Players", value="1/8", inline=True)
                    embed.add_field(name="Status", value="⏳ Waiting", inline=True)
                    if not private:
                        embed.add_field(name="Join", value="Anyone with the code can join!", inline=False)
                    else:
                        embed.add_field(name="Join", value="Password protected", inline=False)

                    await interaction.followup.send(embed=embed)
                else:
                    error_msg = await resp.text()
                    raise Exception(f"API error: {resp.status} - {error_msg}")
        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=f"Could not create room: {str(e)}", color=0xED4245)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="join-room", description="Join a trivia room (gives you the link)")
    @app_commands.describe(code="Room code")
    async def join_room(self, interaction: discord.Interaction, code: str):
        await interaction.response.defer()
        code = code.strip().upper()

        try:
            async with self.bot.session.get(f"{self.bot.api_base}/rooms/{code}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('exists'):
                        embed = discord.Embed(
                            title="✅ Room Found!",
                            description=f"**{data.get('name', 'Unknown')}** ({code})",
                            color=0x57F287
                        )
                        embed.add_field(name="Players", value=f"{data.get('player_count',1)}/{data.get('max_players',8)}", inline=True)
                        embed.add_field(name="Status", value=data.get('status', 'waiting').title(), inline=True)
                        embed.add_field(name="Join", value=f"[Click to join the room](http://localhost:5000/rooms/{code})", inline=False)
                        await interaction.followup.send(embed=embed)
                    else:
                        raise Exception("Room not found.")
                elif resp.status == 404:
                    embed = discord.Embed(title="❌ Room Not Found", description=f"No room with code `{code}` exists.", color=0xED4245)
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    raise Exception(f"Unexpected API response: {resp.status}")
        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=str(e), color=0xED4245)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="trivia", description="Quick solo trivia question")
    @app_commands.describe(category="Category (leave empty for random)")
    async def trivia(self, interaction: discord.Interaction, category: str = None):
        await interaction.response.defer()

        try:
            url = f"{self.bot.api_base}/questions/random"
            params = {}
            if category:
                params['category'] = category
            async with self.bot.session.get(url, params=params) as resp:
                if resp.status == 200:
                    q = await resp.json()
                else:
                    raise Exception("Could not fetch question from the server.")

            question_text = q['question']
            answers = q['answers']
            correct_index = q['correct_index']
            category_name = q.get('category', 'General')

            embed = discord.Embed(
                title=f"❓ {category_name} Trivia",
                description=question_text,
                color=0x00D4FF
            )

            view = discord.ui.View(timeout=30)
            for i, ans in enumerate(answers):
                btn = discord.ui.Button(
                    label=ans,
                    style=discord.ButtonStyle.primary,
                    custom_id=f"answer_{i}_{correct_index}_{interaction.user.id}"
                )
                btn.callback = self.solo_answer_callback
                view.add_item(btn)

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=str(e), color=0xED4245)
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def solo_answer_callback(self, interaction: discord.Interaction):
        parts = interaction.data['custom_id'].split('_')
        selected = int(parts[1])
        correct = int(parts[2])
        original_user_id = int(parts[3])

        if interaction.user.id != original_user_id:
            await interaction.response.send_message("This question isn't for you!", ephemeral=True)
            return

        correct_bool = (selected == correct)
        embed = interaction.message.embeds[0]
        embed.colour = 0x57F287 if correct_bool else 0xED4245
        
        if correct_bool:
            embed.title = "✅ Correct!"
            try:
                async with self.bot.session.post(f"{self.bot.api_base}/users/coins/add", json={
                    "discord_id": str(interaction.user.id),
                    "amount": 10,
                    "reason": "Solo trivia correct answer"
                }) as resp:
                    pass
            except:
                pass
            embed.description += f"\n\n+10 coins, {interaction.user.mention}!"
            
            try:
                async with self.bot.session.post(
                    f"{self.bot.api_base}/users/xp/add",
                    json={
                        "discord_id": str(interaction.user.id),
                        "amount": 10,
                        "reason": "Solo trivia correct answer"
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('level_up'):
                            level_up_embed = discord.Embed(
                                title="🎉 Level Up!",
                                description=f"You are now level {data['new_level']}!",
                                color=0x57F287
                            )
                            await interaction.followup.send(embed=level_up_embed, ephemeral=True)
            except:
                pass
        else:
            embed.title = "❌ Wrong!"
            embed.description += f"\n\n{interaction.user.mention}, better luck next time!"

        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(QuizCog(bot))