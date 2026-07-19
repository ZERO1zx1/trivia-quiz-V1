"""Helper Utilities"""
import random
import string
from datetime import datetime, timedelta

def generate_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def format_time_ago(dt):
    if not dt:
        return 'Never'
    now = datetime.utcnow()
    diff = now - dt
    if diff < timedelta(minutes=1):
        return 'Just now'
    elif diff < timedelta(hours=1):
        return f'{int(diff.seconds / 60)}m ago'
    elif diff < timedelta(days=1):
        return f'{int(diff.seconds / 3600)}h ago'
    elif diff < timedelta(days=7):
        return f'{diff.days}d ago'
    else:
        return dt.strftime('%b %d, %Y')

def format_number(num):
    if num >= 1_000_000:
        return f'{num / 1_000_000:.1f}M'
    elif num >= 1_000:
        return f'{num / 1_000:.1f}K'
    return str(num)

def get_level_color(level):
    if level >= 100:
        return '#FFD700'
    elif level >= 50:
        return '#C0C0C0'
    elif level >= 25:
        return '#CD7F32'
    elif level >= 10:
        return '#8B5CF6'
    else:
        return '#5865F2'
