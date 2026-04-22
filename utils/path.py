import os

# Google Sheet CSV URLs — defined in .env
GSHEET_CHARACTER = os.getenv("GSHEET_CHARACTER")
GSHEET_CRAFT = os.getenv("GSHEET_CRAFT")
GSHEET_ITEMS = os.getenv("GSHEET_ITEMS")
GSHEET_LOOTBOXES = os.getenv("GSHEET_LOOTBOXES")
GSHEET_POWER = os.getenv("GSHEET_POWER")
GSHEET_ENEMIES = os.getenv("GSHEET_ENEMIES")
GSHEET_MEMORIES = os.getenv("GSHEET_MEMORIES")
GSHEET_NPCS = os.getenv("GSHEET_NPCS")
GSHEET_QUESTS = os.getenv("GSHEET_QUESTS")
GSHEET_TRADES = os.getenv("GSHEET_TRADES")

# Database
DB_FILE = os.path.join("data", "rpg.db")

# Local CSV file paths
ROLL_DIR = "history/dice"
INVENTORIES_CSV_FILE = os.path.join("data", "inventories.csv")
BUFFS_CSV_FILE = os.path.join("data", "buffs.csv")
ASSETS_FOLDER = os.path.join("data", "assets")
MAP_FILE = os.path.join(ASSETS_FOLDER, "map.png")

# Discord channels names
BUFF_HISTORY_CHANNEL_NAME = "buff-history"
CRAFT_HISTORY_CHANNEL_NAME = "craft-history"
INVENTORY_HISTORY_CHANNEL_NAME = "inventory-history"
COMBAT_HISTORY_CHANNEL_NAME = "combat-history"
LOOTBOX_HISTORY_CHANNEL_NAME = "lootbox-history"
POWER_HISTORY_CHANNEL_NAME = "power-history"
STATUS_HISTORY_CHANNEL_NAME = "status-history"
TRANSACTION_HISTORY_CHANNEL_NAME = "transaction-history"
# GENERAL_CHANNEL_NAME = "📜-général" 
GENERAL_CHANNEL_NAME = "📘-lore"
COMBAT_CHANNEL_NAME = "⚔️-combat"
ADMIN_CHANNEL_NAME = "🔧-admin"
RPG_BOT_CATEGORY_NAME = "RPG-BOT"
PLAYER_VOICE_CHANNELS = ["📖 Histoire", "🎭 Groupe 1", "🎭 Groupe 2", "🎭 Groupe 3"]

# Paths
COGS_DIR = "cogs"

# List of cogs to load
# Noms des personnages MJ exclus de la liste des joueurs
GM_NAMES = ["Rémy", "Rémy2"]

COGS = [
    "admin",
    "buffs",
    "characters",
    "combat",
    "crafts",
    "dices",
    "help",
    "histories",
    "inventories",
    "items",
    "lootboxes",
    "map",
    "memories",
    "npcs",
    "my",
    "powers",
    # "reload",
    "settings",
    "status",
]
