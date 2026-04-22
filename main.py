import os
import locale
import logging
import discord

locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
from discord import app_commands, Interaction
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import datetime
import traceback

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

from utils.path import COGS
from utils.db import init_db
from instance.buff import BuffRepository
from instance.character import CharacterRepository
from instance.craft import CraftRepository
from instance.enemy import EnemyRepository
from instance.item import ItemRepository
from instance.lootbox import LootBoxRepository
from instance.memory import Memory
from instance.power import PowerRepository
from instance.npc import NPCRepository
from instance.quest_progress import QuestProgress
from instance.trade import TradeRepository
from instance.dice import DiceSession
from instance.history import History
from instance.location import Location

from utils.path import PLAYER_VOICE_CHANNELS, GM_NAMES
from utils.utils import update_bot_status

init_db()

intents = discord.Intents.default()
intents.message_content = True

class RPGBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history = History()
        self.dice_session = DiceSession()
        self.item_repository = ItemRepository(history=self.history)
        self.buff_repository = BuffRepository(history=self.history)
        self.craft_repository = CraftRepository(history=self.history, dice_session=self.dice_session, item_repository=self.item_repository)
        self.enemy_repository = EnemyRepository()
        self.lootbox_repository = LootBoxRepository(history=self.history)
        self.memory = Memory()
        self.power_repository = PowerRepository(history=self.history, dice_session=self.dice_session)
        self.character_repository = CharacterRepository(
            item_repo=self.item_repository,
            power_repo=self.power_repository,
            buffs_repo=self.buff_repository,
            enemy_repo=self.enemy_repository,
            history=self.history
        )
        self.trade_repository = TradeRepository(item_repository=self.item_repository, history=self.history, dice_session=self.dice_session)
        self.npc_repository = NPCRepository(trade_repository=self.trade_repository, item_repository=self.item_repository)
        self.quest_progress = QuestProgress()
        self.location = Location()

bot = RPGBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Commandes slash synchronisées: {len(synced)}")
        logger.info("Pensez à activer l'autodecrement des buffs avec /buff autodec")
    except Exception as e:
        logger.error(f"Erreur de synchronisation: {e}")

    for guild in bot.guilds:
        for channel in guild.voice_channels:
            if channel.name not in PLAYER_VOICE_CHANNELS:
                continue
            for member in channel.members:
                char = bot.character_repository.get_character_by_user_id(member.id)
                if char and char.name not in bot.character_repository.players and char.name not in GM_NAMES:
                    bot.character_repository.players.append(char.name)
                    logger.info(f"Joueur ajouté à la session: {char.name} (salon: {channel.name})")

    logger.info(f"Joueurs en session: {bot.character_repository.players}")
    await update_bot_status(bot)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    embed = discord.Embed(color=discord.Color.red())

    if isinstance(error, app_commands.CommandOnCooldown):
        embed.description = f"Commande en cooldown. Réessaie dans {error.retry_after:.1f}s."
    elif isinstance(error, app_commands.MissingPermissions):
        embed.description = "Tu n'as pas les permissions nécessaires."
    elif isinstance(error, app_commands.CommandInvokeError):
        original = error.original
        # Interaction expirée : rien à faire, on log et on sort
        if isinstance(original, discord.NotFound) and original.code == 10062:
            logger.warning(f"Interaction expirée, impossible de répondre : {error}")
            return
        embed.description = f"Une erreur est survenue : `{original}`"
    else:
        embed.description = f"Erreur inattendue : `{error}`"

    # Utiliser followup si déjà acknowledged, response sinon
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.HTTPException:
        logger.warning(f"Impossible d'envoyer le message d'erreur : {error}")

async def main():
    await bot.load_extension("cogs.reload")
    error_count = 0
    for cog in COGS:
        try:
            await bot.load_extension(f"cogs.{cog}")
            logger.info(f"Cog chargé: {cog}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cog {cog}: {e}")
            error_count += 1
    if error_count > 0:
        logger.warning(f"Nombre d'erreurs lors du chargement des cogs: {error_count}")
    await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())