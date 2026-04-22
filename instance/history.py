import discord
import datetime
import hashlib
import shutil

from pathlib import Path
import os

from utils.path import (
    BUFF_HISTORY_CHANNEL_NAME,
    CRAFT_HISTORY_CHANNEL_NAME,
    INVENTORY_HISTORY_CHANNEL_NAME,
    COMBAT_HISTORY_CHANNEL_NAME,
    LOOTBOX_HISTORY_CHANNEL_NAME,
    POWER_HISTORY_CHANNEL_NAME,
    STATUS_HISTORY_CHANNEL_NAME,
    TRANSACTION_HISTORY_CHANNEL_NAME,
    RPG_BOT_CATEGORY_NAME,
    DB_FILE,
)
from utils.builder_embed import (
    _generate_power_use_history_embed,
    _generate_buff_application_history_embed,
    _generate_buff_expiration_history_embed,
    _generate_item_update_history_embed,
    _generate_transaction_history_embed,
    _generate_craft_execution_history_embed,
    _generate_lootbox_open_history_embed,
    _generate_npc_trade_history_embed,
    _generate_npc_offer_history_embed,
    _generate_damage_history_embed,
    _generate_spawn_history_embed
)


class History:
    BASE_DIR = Path("history/backups")

    def __init__(self):
        today = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        self._dir = self.BASE_DIR / f"{today}"
        self._dir.mkdir(parents=True, exist_ok=True)
        self.create_backup()

    async def get_or_create_channel(self, guild: discord.Guild, channel_name: str) -> discord.TextChannel:
        """Récupère ou crée un salon pour l'historique."""
        category = discord.utils.get(guild.categories, name=RPG_BOT_CATEGORY_NAME)

        if category is None:
            category = await guild.create_category(RPG_BOT_CATEGORY_NAME)

        channel = discord.utils.get(category.channels, name=channel_name)

        if channel is None:
            channel = await guild.create_text_channel(channel_name, category=category)

        return channel

    @staticmethod
    def _file_hash(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def create_backup(self):
        """Copie rpg.db dans le dossier de backup, sauf si identique au dernier backup."""
        source = Path(DB_FILE)
        if not source.exists():
            return

        current_hash = self._file_hash(source)

        existing_backups = sorted(self.BASE_DIR.glob("*/rpg.db.bak"), key=lambda p: p.stat().st_mtime)
        if existing_backups:
            last_hash = self._file_hash(existing_backups[-1])
            if last_hash == current_hash:
                return

        shutil.copy2(source, self._dir / "rpg.db.bak")

    async def log_power_use(self, guild: discord.Guild, character_name: str, power_name: str, power_effects: dict, roll: dict):
        """Enregistre l'utilisation d'un pouvoir dans l'historique."""
        channel = await self.get_or_create_channel(guild, POWER_HISTORY_CHANNEL_NAME)
        embed = _generate_power_use_history_embed(character_name, power_name, power_effects, roll, datetime.datetime.now())
        await channel.send(embed=embed)

    async def log_buff_application(self, guild: discord.Guild, character_name: str, buff_name: str, buff_source: str, buff_duration: int, buff_effects: dict, buff_auto_decrement: bool):
        """Enregistre l'application d'un buff dans l'historique."""
        channel = await self.get_or_create_channel(guild, BUFF_HISTORY_CHANNEL_NAME)
        embed = _generate_buff_application_history_embed(character_name, buff_name, buff_source, buff_duration, buff_effects, buff_auto_decrement, datetime.datetime.now())
        await channel.send(embed=embed)

    async def log_buff_expiration(self, guild: discord.Guild, character_name: str, buff_name: str, buff_source: str, buff_effects: dict):
        """Enregistre l'expiration d'un buff dans l'historique."""
        channel = await self.get_or_create_channel(guild, BUFF_HISTORY_CHANNEL_NAME)
        embed = _generate_buff_expiration_history_embed(character_name, buff_name, buff_source, buff_effects, datetime.datetime.now())
        await channel.send(embed=embed)

    async def log_inventory_update(self, guild: discord.Guild, character_name: str, item_name: str, quantity_change: int, new_quantity: int):
        """Enregistre une mise à jour d'inventaire dans l'historique."""
        channel = await self.get_or_create_channel(guild, INVENTORY_HISTORY_CHANNEL_NAME)
        embed = _generate_item_update_history_embed(character_name, item_name, quantity_change, new_quantity, datetime.datetime.now())
        await channel.send(embed=embed)

    async def log_transaction(self, guild: discord.Guild, giver_name: str, receiver_name: str, item_name: str, quantity: int, is_gift: bool = False):
        """Enregistre une transaction d'item entre deux personnages dans l'historique."""
        channel = await self.get_or_create_channel(guild, TRANSACTION_HISTORY_CHANNEL_NAME)
        embed = _generate_transaction_history_embed(giver_name, receiver_name, item_name, quantity, datetime.datetime.now(), is_gift=is_gift)
        await channel.send(embed=embed)

    async def log_npc_trade(self, guild: discord.Guild, character_name: str, npc_name: str, received_items: list, given_items: list, currency: int):
        """Enregistre un échange entre un personnage et un NPC marchand."""
        channel = await self.get_or_create_channel(guild, TRANSACTION_HISTORY_CHANNEL_NAME)
        embed = _generate_npc_trade_history_embed(character_name, npc_name, received_items, given_items, currency, datetime.datetime.now())
        await channel.send(embed=embed)

    async def log_npc_offer(self, guild: discord.Guild, character_name: str, npc_name: str, item_name: str, quantity: int, price_per_unit: int):
        """Enregistre une vente d'item à un NPC."""
        channel = await self.get_or_create_channel(guild, TRANSACTION_HISTORY_CHANNEL_NAME)
        embed = _generate_npc_offer_history_embed(character_name, npc_name, item_name, quantity, price_per_unit, datetime.datetime.now())
        await channel.send(embed=embed)
    
    async def log_item_use(self, guild: discord.Guild, character_name: str, item_name: str, new_quantity: int):
        """Enregistre l'utilisation d'un objet dans l'historique."""
        channel = await self.get_or_create_channel(guild, INVENTORY_HISTORY_CHANNEL_NAME)
        embed = _generate_item_update_history_embed(character_name, item_name, -1, new_quantity, datetime.datetime.now(), is_use=True)
        await channel.send(embed=embed)

    async def log_craft(self, guild: discord.Guild, character_name: str, craft: "Craft", quantity: int, craft_status: str, products: list[dict], roll: dict):
        """Enregistre l'exécution d'un craft dans l'historique."""
        channel = await self.get_or_create_channel(guild, CRAFT_HISTORY_CHANNEL_NAME)
        embed = _generate_craft_execution_history_embed(character_name, craft, quantity, datetime.datetime.now(), craft_status, products, roll)
        await channel.send(embed=embed)

    async def log_lootbox(self, guild: discord.Guild, character_name: str, lootbox_name: str, quantity: int, rewards: list[tuple[str, int]]):
        """Enregistre l'ouverture d'une lootbox dans l'historique."""
        channel = await self.get_or_create_channel(guild, LOOTBOX_HISTORY_CHANNEL_NAME)
        embed = _generate_lootbox_open_history_embed(character_name, lootbox_name, quantity, rewards, datetime.datetime.now())
        await channel.send(embed=embed)
    
    async def log_damage(self, guild: discord.Guild, enemy, character, result, enemy_attack=False):
        """Enregistre une action de combat dans l'historique."""
        channel = await self.get_or_create_channel(guild, COMBAT_HISTORY_CHANNEL_NAME)
        embed = _generate_damage_history_embed(result, enemy, character, enemy_attack, datetime.datetime.now())
        await channel.send(embed=embed)

    async def log_spawn(self, guild: discord.Guild, instances: list):
        """Enregistre le spawn d'un ennemi dans l'historique."""
        channel = await self.get_or_create_channel(guild, COMBAT_HISTORY_CHANNEL_NAME)
        for instance in instances:
            embed = _generate_spawn_history_embed(instance, instance.instance_id, datetime.datetime.now())
            await channel.send(embed=embed) 