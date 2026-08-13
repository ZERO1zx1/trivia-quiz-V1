from .user import User, DiscordAccount, Friend
from .question import Question, Answer, Category
from .room import GameSnapshot, Room, RoomPlayer, Match, Score
from .economy import Transaction, LeaderboardEntry
from .shop import ShopItem, UserInventory
from .notification import Notification
from .achievement import Achievement, UserAchievement
from .box import Box, UserBox
from .profile import ProfileView, UserRespect, GameChallenge, GiftTransaction
from .quest import DailyQuest
from .boss import Boss
from .user_question import UserQuestion

# New Enterprise Models
from .guild import Guild, GuildMember, GuildRank, GuildSkill, GuildQuest, GuildWar, GuildBoss
from .tournament import Tournament, TournamentParticipant, TournamentMatch, TournamentHistory
from .battle_pass import Season, BattlePass, BattlePassReward, BattlePassProgress
from .pet import PetSpecies, Pet, PetEvolution, PetEquipment
from .craft import CraftRecipe, CraftingMaterial, UserCraftingProgress
from .mail import Mail, MailAttachment
from .marketplace import MarketplaceListing, MarketplaceTransaction, Auction, AuctionBid
from .replay import Replay, ReplayEvent, ReplayLike
from .chat import ChatChannel, ChatMember, ChatMessage, ChatReaction
from .event import GameEvent, EventReward, EventParticipant
from .region import Region, RegionLeaderboard
from .collection import CollectionItem, CollectionProgress, CollectionReward
from .community import ForumCategory, ForumPost, ForumComment, ForumLike, UserBookmark
from .puzzle import Puzzle, PuzzleAttempt, PuzzleLeaderboardEntry
from .learning import Flashcard, StudyNote, ExamAttempt
from .analytics import PlayerAnalytics, CategoryAnalytics, ServerAnalytics
from .companion import Cosmetic, UserCosmetic, ProfileTheme, UserProfileTheme
from .settings import UserSettings, DeviceHistory, TwoFactorAuth, Session, BanAppeal, AuditLog, FeatureToggle

__all__ = [
    # Core models
    'User', 'DiscordAccount', 'Friend',
    'Question', 'Answer', 'Category',
    'Room', 'RoomPlayer', 'Match', 'Score', 'GameSnapshot',
    'Transaction', 'LeaderboardEntry',
    'ShopItem', 'UserInventory',
    'Notification',
    'Achievement', 'UserAchievement',
    'Box', 'UserBox',
    'ProfileView', 'UserRespect', 'GameChallenge', 'GiftTransaction',
    'DailyQuest',
    'Boss',
    'UserQuestion',
    # Guild System
    'Guild', 'GuildMember', 'GuildRank', 'GuildSkill', 'GuildQuest', 'GuildWar', 'GuildBoss',
    # Tournament System
    'Tournament', 'TournamentParticipant', 'TournamentMatch', 'TournamentHistory',
    # Battle Pass
    'Season', 'BattlePass', 'BattlePassReward', 'BattlePassProgress',
    # Pet System
    'PetSpecies', 'Pet', 'PetEvolution', 'PetEquipment',
    # Crafting
    'CraftRecipe', 'CraftingMaterial', 'UserCraftingProgress',
    # Mail
    'Mail', 'MailAttachment',
    # Marketplace
    'MarketplaceListing', 'MarketplaceTransaction', 'Auction', 'AuctionBid',
    # Replay
    'Replay', 'ReplayEvent', 'ReplayLike',
    # Chat
    'ChatChannel', 'ChatMember', 'ChatMessage', 'ChatReaction',
    # Events
    'GameEvent', 'EventReward', 'EventParticipant',
    # Regions
    'Region', 'RegionLeaderboard',
    # Collection
    'CollectionItem', 'CollectionProgress', 'CollectionReward',
    # Community
    'ForumCategory', 'ForumPost', 'ForumComment', 'ForumLike', 'UserBookmark',
    # Puzzle
    'Puzzle', 'PuzzleAttempt', 'PuzzleLeaderboardEntry',
    # Learning
    'Flashcard', 'StudyNote', 'ExamAttempt',
    # Analytics
    'PlayerAnalytics', 'CategoryAnalytics', 'ServerAnalytics',
    # Premium Cosmetics
    'Cosmetic', 'UserCosmetic', 'ProfileTheme', 'UserProfileTheme',
    # Settings
    'UserSettings', 'DeviceHistory', 'TwoFactorAuth', 'Session', 'BanAppeal', 'AuditLog', 'FeatureToggle',
]
