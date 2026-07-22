import requests
from flask import current_app

def send_discord_error_log(message, stack_trace=''):
    """Discord-ын #server-errors суваг руу алдаа илгээх"""
    webhook_url = current_app.config.get('DISCORD_ERROR_WEBHOOK')
    if not webhook_url:
        return

    content = f"**🚨 Server Error**\n```\n{message[:1900]}\n```"
    if stack_trace:
        content += f"\n**Stack Trace:**\n```\n{stack_trace[:1800]}\n```"

    try:
        requests.post(webhook_url, json={"content": content, "username": "TriviaVerse Logger"}, timeout=5)
    except Exception:
        pass