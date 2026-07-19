import asyncio
import os
import logging
import signal
import sys

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('triviaverse')


class TriviaVerseBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )

        self.api_base = os.getenv('API_BASE_URL', 'http://localhost:5000/api')
        self.session = None

    async def setup_hook(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": "TriviaVerseBot/1.0"}
        )

        cogs = [
            'discord_bot.cogs.profile',
            'discord_bot.cogs.economy',
            'discord_bot.cogs.quiz',
            'discord_bot.cogs.level',
            'discord_bot.cogs.leaderboard',
            'discord_bot.cogs.help',
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

        guild_id = os.getenv('DISCORD_GUILD_ID')
        try:
            if guild_id:
                guild = discord.Object(id=int(guild_id))
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} commands to guild {guild_id}")
            else:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} global commands")
        except discord.HTTPException as e:
            logger.error(f"Command sync failed: {e}")

    async def on_ready(self):
        logger.info(f'{self.user} ({self.user.id}) has connected to Discord!')
        logger.info(f'API Base: {self.api_base}')
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name='TriviaVerse | /help'
            )
        )

    async def on_error(self, event_method: str, /, *args, **kwargs):
        logger.exception(f"Error in {event_method}")

    async def close(self):
        logger.info("Shutting down bot...")
        if self.session and not self.session.closed:
            await self.session.close()
        await super().close()


async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏰ Дахин оролдох: `{error.retry_after:.1f}` секунд", ephemeral=True
        )
    elif isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message(
            "🚫 Энэ команд ашиглах эрхгүй байна.", ephemeral=True
        )
    else:
        logger.exception(f"Command error: {error}")
        msg = "❌ Алдаа гарлаа. Дахин оролдоно уу."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)


def run_bot():
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN environment variable not set")

    bot = TriviaVerseBot()
    bot.tree.on_error = on_app_command_error

    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(bot.close())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    bot.run(token, log_handler=None)


if __name__ == '__main__':
    run_bot()