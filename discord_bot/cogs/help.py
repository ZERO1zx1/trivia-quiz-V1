import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
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
                ("`/quiz-duel`", "Challenge a player to 1v1 PvP Duel"),
                ("`/survival`", "Start an elimination mode game"),
                ("`/create-room`", "Create a trivia room on the website"),
                ("`/join-room`", "Join a trivia room by code"),
            ],
            "👤 Social & Profile": [
                ("`/profile`", "View your or another user's profile"),
                ("`/rep`", "Give reputation point to a user"),
                ("`/marry`", "Propose to another user"),
                ("`/my-rank`", "Check your leaderboard rank"),
            ],
            "💰 Economy & Gamble": [
                ("`/daily`", "Claim your daily reward"),
                ("`/deposit`", "Put coins in bank (safe from robbery)"),
                ("`/withdraw`", "Take coins from bank"),
                ("`/coinflip`", "Gamble coins on a coin flip"),
                ("`/rob`", "Attempt to steal from another user"),
                ("`/balance`", "Check your coin balance"),
                ("`/shop`", "Browse the shop (dynamic pricing!)"),
                ("`/buy`", "Buy an item from the shop"),
                ("`/inventory`", "View your purchased items"),
                ("`/equip`", "Equip an item from your inventory"),
            ],
            "🏆 Stats": [
                ("`/leaderboard`", "View global leaderboard"),
                ("`/server-stats`", "View global server statistics"),
            ],
        }
        
        for category, cmds in commands_info.items():
            value = "\n".join([f"{name} — {desc}" for name, desc in cmds])
            embed.add_field(name=category, value=value, inline=False)
        
        embed.set_footer(text="Use /command_name to run a command!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))