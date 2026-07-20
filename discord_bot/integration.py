import discord
from discord.ext import commands
from discord import app_commands

class IntegrationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def sync_role_for_user(self, discord_id: str, level: int):
        """Хэрэглэгчийн level-д тохирох Discord role олгох"""
        guild_id = int(self.bot.config.get('DISCORD_GUILD_ID', 0))
        if not guild_id:
            return

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        member = guild.get_member(int(discord_id))
        if not member:
            return

        # Level-д тохирох role-уудыг тодорхойлох (серверт урьдчилан үүсгэсэн байх ёстой)
        role_names = {
            5: 'Trivia Novice',
            10: 'Trivia Master',
            25: 'Trivia God',
            50: 'Trivia Legend'
        }

        # Хэрэглэгчид оноох ёстой role-г тодорхойлох
        target_role_name = None
        for lvl, role_name in sorted(role_names.items(), reverse=True):
            if level >= lvl:
                target_role_name = role_name
                break

        if not target_role_name:
            return

        # Сервер дээрх role объектыг авах
        role = discord.utils.get(guild.roles, name=target_role_name)
        if not role:
            print(f"Role '{target_role_name}' not found in guild.")
            return

        # Хэрэглэгчид role оноох
        if role not in member.roles:
            try:
                await member.add_roles(role)
                print(f"Added role {role.name} to {member.display_name}")

                # Хэрэглэгчид DM илгээх
                try:
                    await member.send(f"🎉 Congratulations! You've reached level {level} and earned the **{role.name}** role!")
                except discord.Forbidden:
                    pass
            except discord.Forbidden:
                print(f"Cannot add role to {member.display_name}")

    @app_commands.command(name="sync-roles", description="[Admin] Manually sync all user roles")
    @app_commands.default_permissions(administrator=True)
    async def sync_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        # Энэ командаар бүх хэрэглэгчдийн level-г шалгаж role оноож болно
        # API-с бүх хэрэглэгчдийг татаж, sync_role_for_user дуудах
        await interaction.followup.send("Role sync started.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(IntegrationCog(bot))