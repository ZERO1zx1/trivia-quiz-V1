import discord
from discord.ext import commands
from discord import app_commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Show all available commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📚 TriviaVerse Bot Commands",
            description="Here are all available commands:",
            color=0x5865F2
        )
        
        commands_info = {
            "🎮 Quiz": [
                ("`/trivia`", "Quick solo trivia question"),
                ("`/create-room`", "Create a trivia room on the website"),
                ("`/join-room`", "Join a trivia room by code"),
            ],
            "👤 Profile": [
                ("`/profile`", "View your or another user's profile"),
                ("`/my-rank`", "Check your leaderboard rank"),
            ],
            "⭐ Level & XP": [
                ("`/level`", "Check your or another user's level and XP"),
                ("`/top`", "View top players by level"),
                ("`/add-xp`", "[Admin] Add XP to a user"),
            ],
            "🏆 Leaderboard": [
                ("`/leaderboard`", "View global leaderboard (daily/weekly/monthly/alltime)"),
                ("`/stats`", "View server statistics"),
            ],
            "💰 Economy": [
                ("`/daily`", "Claim your daily reward"),
                ("`/balance`", "Check your coin balance"),
                ("`/shop`", "Browse the TriviaVerse shop"),
                ("`/buy`", "Buy an item from the shop"),
                ("`/inventory`", "View your purchased items"),
                ("`/equip`", "Equip an item from your inventory"),
            ],
        }
        
        for category, cmds in commands_info.items():
            value = "\n".join([f"{name} — {desc}" for name, desc in cmds])
            embed.add_field(name=category, value=value, inline=False)
        
        embed.set_footer(text="Use /command_name to run a command!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))