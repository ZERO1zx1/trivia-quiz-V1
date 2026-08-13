import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

class QuizCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        # message_id -> {answers, correct_index}
        self._solo_cache = {}

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

    @app_commands.command(name="quiz-duel", description="Challenge another player to a 1v1 duel")
    @app_commands.describe(opponent="User to challenge", bet="Coin bet amount")
    async def quiz_duel(self, interaction: discord.Interaction, opponent: discord.User, bet: int = 100):
        await interaction.response.defer()
        
        if opponent.id == interaction.user.id:
            await interaction.followup.send("You cannot duel yourself!", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="⚔️ Quiz Duel Challenge!",
            description=f"{interaction.user.mention} has challenged {opponent.mention} to a quiz duel for **🪙 {bet} coins**!",
            color=0xFFA500
        )
        
        view = discord.ui.View(timeout=60)
        accept_btn = discord.ui.Button(label="Accept", style=discord.ButtonStyle.success)
        
        async def accept_callback(inter):
            if inter.user.id != opponent.id:
                await inter.response.send_message("Only the challenged player can accept!", ephemeral=True)
                return
            
            # Call backend to create a duel room
            payload = {
                "name": f"Duel: {interaction.user.name} vs {opponent.name}",
                "host_discord_id": str(interaction.user.id),
                "private": True,
                "game_mode": "duel",
                "bet": bet,
                "opponent_discord_id": str(opponent.id)
            }
            async with self.bot.session.post(f"{self.bot.api_base}/rooms/create", json=payload) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    room_code = data.get('code')
                    await inter.response.send_message(f"Duel accepted! Join here: http://localhost:5000/rooms/{room_code}")
                else:
                    await inter.response.send_message("Failed to create duel room.", ephemeral=True)
        
        accept_btn.callback = accept_callback
        view.add_item(accept_btn)
        
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="survival", description="Start a survival mode game (one wrong answer and you're out!)")
    async def survival(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Similar to create-room but forced survival mode
        payload = {
            "name": f"{interaction.user.name}'s Survival",
            "host_discord_id": str(interaction.user.id),
            "game_mode": "survival",
            "survival_lives": 1
        }
        async with self.bot.session.post(f"{self.bot.api_base}/rooms/create", json=payload) as resp:
            if resp.status in (200, 201):
                data = await resp.json()
                await interaction.followup.send(f"Survival room created! Code: `{data.get('code')}`\nJoin: http://localhost:5000/rooms/{data.get('code')}")
            else:
                await interaction.followup.send("Failed to create survival room.", ephemeral=True)

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

            msg = await interaction.followup.send(embed=embed, view=view)
            # Cache answers so callback can show correct answer if wrong
            self._solo_cache[msg.id] = {
                'answers': answers,
                'correct_index': correct_index
            }

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
            # Show correct answer if cached
            cache = self._solo_cache.get(interaction.message.id, {})
            answers = cache.get('answers', [])
            if answers and 0 <= correct < len(answers):
                embed.description += f"\n\nЗөв хариулт: **{answers[correct]}**"
            embed.description += f"\n{interaction.user.mention}, дараа дахин оролдоорой!"

        # Clean cache
        self._solo_cache.pop(interaction.message.id, None)
        await interaction.response.edit_message(embed=embed, view=None)

    @commands.command(name='play')
    async def play_trivia(self, ctx):
        """Discord суваг дотор trivia асуулт асуух"""
        # API-с асуулт татах
        async with self.bot.session.get(f"{self.bot.api_base}/questions/random") as resp:
            if resp.status != 200:
                await ctx.send("❌ Could not load question.")
                return
            question = await resp.json()

        embed = discord.Embed(
            title=f"❓ {question.get('category', 'Trivia')}",
            description=question['question_text'],
            color=0x00D4FF
        )
        emojis = ['🇦', '🇧', '🇨', '🇩']
        for i, ans in enumerate(question['answers']):
            embed.add_field(name=f"{emojis[i]} {ans['answer_text']}", value='', inline=False)

        msg = await ctx.send(embed=embed)
        for emoji in emojis[:len(question['answers'])]:
            await msg.add_reaction(emoji)

        # Хариултыг хадгалах
        self.active_games[msg.id] = {
            'question': question,
            'answers': {},
            'expires': datetime.utcnow() + timedelta(seconds=30)
        }

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        if reaction.message.id not in self.active_games:
            return

        game = self.active_games[reaction.message.id]
        if datetime.utcnow() > game['expires']:
            return

        emoji_map = {'🇦': 0, '🇧': 1, '🇨': 2, '🇩': 3}
        if str(reaction.emoji) not in emoji_map:
            return

        answer_idx = emoji_map[str(reaction.emoji)]
        is_correct = (answer_idx == game['question']['correct_index'])

        # Хариултыг бүртгэх
        game['answers'][user.id] = {'correct': is_correct}

        # XP, coins нэмэх API дуудах
        if is_correct:
            async with self.bot.session.post(
                f"{self.bot.api_base}/users/xp/add",
                json={"discord_id": str(user.id), "amount": 10, "reason": "Discord trivia"}
            ) as resp:
                pass

    @app_commands.command(name="black-list", description="[Admin] Ban a user from using the bot")
    @app_commands.describe(user="User to blacklist")
    @app_commands.checks.has_permissions(administrator=True)
    async def black_list(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        async with self.bot.session.post(f"{self.bot.api_base}/admin/users/{user.id}/toggle-ban") as resp:
            if resp.status == 200:
                await interaction.followup.send(f"✅ Blacklist status updated for {user.mention}!", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to update blacklist status.", ephemeral=True)

    @app_commands.command(name="add-item", description="[Admin] Give an item to a user")
    @app_commands.describe(user="User to give item to", item_id="ID of the item")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_item(self, interaction: discord.Interaction, user: discord.Member, item_id: int):
        await interaction.response.defer(ephemeral=True)
        # Assuming we can use the buy logic or a new admin endpoint
        async with self.bot.session.post(f"{self.bot.api_base}/admin/give-item", json={
            "discord_id": str(user.id), "item_id": item_id
        }) as resp:
            if resp.status == 200:
                await interaction.followup.send(f"✅ Item granted to {user.mention}!", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to grant item.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(QuizCog(bot))
