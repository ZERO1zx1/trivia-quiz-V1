ROLE_COLORS = {
    'owner': '#FFD700',      # Алтан шар
    'developer': '#FF4500',  # Улбар шар
    'admin': '#FF3333',      # Улаан
    'moderator': '#33FF33',  # Ногоон
    'helper': '#3399FF',     # Цэнхэр
    'user': '#CCCCCC'        # Саарал
}

ROLE_NAMES = {
    'owner': 'Owner',
    'developer': 'Developer',
    'admin': 'Admin',
    'moderator': 'Moderator',
    'helper': 'Helper',
    'user': 'Player'
}

def get_role_color(role):
    return ROLE_COLORS.get(role, '#CCCCCC')

def get_role_name(role):
    return ROLE_NAMES.get(role, 'Player')