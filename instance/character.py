from typing import Optional, Dict, List, Tuple
import logging
import locale

logger = logging.getLogger(__name__)


from instance.inventory import Inventory

from utils.utils import _normalize, XP_TABLE, _get_resource_max_bonus
from utils.path import GSHEET_CHARACTER
from utils.load import load_characters
from utils.db import get_connection

class Character:
    """
    Représente un personnage du jeu avec ses attributs, ressources, et autres propriétés.
    """    
    def __init__(
        self, 
        name: str, 
        description: str,
        inventory_size: int,
        role: str,
        role_visible: bool,
        class_name: str,
        resources: Dict[str, int],
        resources_max: Dict[str, int],
        player_channel_id: int,
        level_upgrades: dict[int, list[list]],
        level: int, 
        experience: int,
        stat_points: Dict[str, int],
        craft_points: Dict[str, int],
        user_id: int,
        kills: int,
        bosses_defeated: List[str],
        memory_fragments: List[str],
        discovered_sets: List[str],
        currency: int,
        history: "History",
    ):
        self.name = name
        self.description = description
        self.inventory = Inventory(max_size=inventory_size, history=history)
        self.role = role
        self.role_visible = role_visible
        self.class_name = class_name
        self.resources = resources
        self.resources_max = resources_max
        self.currency = currency
        self.powers = []
        self.buffs = []
        self.player_channel_id = player_channel_id
        self.level_upgrades = level_upgrades
        self.level = level
        self.experience = experience
        self.stat_points = stat_points
        self.craft_points = craft_points
        self.user_id = user_id
        self.kills = kills
        self.bosses_defeated = bosses_defeated
        self.bosses_defeated_names = []
        self.memory_fragments = memory_fragments
        self.discovered_sets = discovered_sets

    def gain_experience(self, amount: int):
        self.experience += amount
        if amount > 0:
            while self.level + 1 in XP_TABLE and self.experience >= XP_TABLE[self.level+1]:
                self.level += 1
        elif amount < 0:
            while self.level > 1 and self.experience < XP_TABLE[self.level]:
                self.level -= 1
        else:
            return

    def gain_kills(self, amount: int = 1):
        self.kills += amount

    def defeat_boss(self, boss_id: str):
        self.bosses_defeated.append(boss_id)

class CharacterRepository:
    """
    Représente un dépôt de personnages avec des méthodes pour les charger et les rechercher.
    """    
    def __init__(self, item_repo: "ItemRepository", power_repo: "PowerRepository", buffs_repo: "BuffRepository", enemy_repo: "EnemyRepository", history: "History"):
        self.characters = {}
        self.players: list[str] = []
        self.item_repo = item_repo
        self.power_repo = power_repo
        self.buffs_repo = buffs_repo
        self.enemy_repo = enemy_repo
        self.history = history
        self.runes_rarity_discovered = set({'rare', 'epic'})
        self.reload()

    def reload(self) -> int:
        self.characters.clear()
        characters_as_dicts, inventories_raw, powers_raw = load_characters(GSHEET_CHARACTER)
        for d in characters_as_dicts:
            d["history"] = self.history  

        self.characters = {
            d["name"]: Character(**d) for d in characters_as_dicts
        }
        # Peuplement des inventaires après construction
        for char_name, entries in inventories_raw.items():
            char = self.characters.get(char_name)
            if not char:
                continue
            for entry_id, item_name, quantity, equipped_quantity, rune_names in entries:
                item = self.item_repo.get_item_by_name(item_name)
                if not item:
                    continue
                rune_items = [r for rn in rune_names if (r := self.item_repo.get_item_by_name(rn))]
                if char.name != "Rémy":
                    self.runes_rarity_discovered.update(rune.rarity for rune in rune_items)
                char.inventory.init_add(item, quantity, entry_id=entry_id, runes=rune_items)
                for i in range(equipped_quantity):
                    char.inventory.equip(item_name, char)

            

        # Peuplement des pouvoirs après construction
        for char_name, power_names in powers_raw.items():
            char = self.characters.get(char_name)
            if not char:
                continue
            for power_name in power_names:
                power = self.power_repo.get_power_by_name(power_name)
                if not power:
                    continue
                char.powers.append(power)
            

        self.reload_buffs()  
        for name, c in self.characters.items():
            if c.bosses_defeated is None:
                c.bosses_defeated = []
            c.bosses_defeated_names = [self._get_enemy_name_from_boss_id(bid) for bid in c.bosses_defeated]
            self.characters[name] = c

        return len(self.characters)

    def _get_enemy_name_from_boss_id(self, boss_id: str) -> Optional[str]:
        if boss_id.startswith("b"):
            boss = self.enemy_repo._catalog.get(boss_id)
            return boss["name"] if boss else None


    def reload_buffs(self):
        for char in self.characters.values():
            char.buffs = self.buffs_repo.get_buffs_by_character(char.name)  

    def get_character_by_name(self, name: str) -> Character:
        return self.characters.get(name)
    
    def get_character_by_user_id(self, user_id: int) -> Optional[Character]:
        for char in self.characters.values():
            if char.user_id == user_id:
                return char
        return None


    def get_all_characters(self) -> List[Character]:
        return sorted(list(self.characters.values()), key=lambda c: locale.strxfrm(c.name))

    def get_all_character_names(self) -> List[str]:
        return sorted([char.name for char in self.characters.values()], key=locale.strxfrm)

    def search_characters(self, query: str, limit: int = 25) -> list[Character]:
        needle = _normalize(query)

        if not needle:
            return list(self.characters.values())

        matches: list[Character] = []
        for char in self.characters.values():
            haystack = _normalize(char.name)
            if haystack.startswith(needle) or f" {needle}" in haystack or f"'{needle}" in haystack:
                matches.append(char)
            if len(matches) >= limit:
                break

        return matches

    def save_local_files(self):
        with get_connection() as conn:
            for char in self.characters.values():
                conn.execute(
                    "INSERT OR REPLACE INTO character_assignments (character_name, user_id) VALUES (?, ?)",
                    (char.name, char.user_id),
                )
                conn.execute(
                    """INSERT OR REPLACE INTO character_status
                       (character_name, hp, mana, stamina, experience, kills, bosses_defeated, memory_fragments, currency, discovered_sets)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        char.name,
                        char.resources.get("hp"),
                        char.resources.get("mana"),
                        char.resources.get("stamina"),
                        char.experience,
                        char.kills,
                        ";".join(char.bosses_defeated),
                        ";".join(char.memory_fragments),
                        char.currency,
                        ";".join(char.discovered_sets),
                    ),
                )
                conn.execute(
                    "DELETE FROM inventories WHERE character_name = ?", (char.name,)
                )
                conn.executemany(
                    "INSERT INTO inventories (entry_id, character_name, item_name, quantity, equipped_quantity, runes) VALUES (?, ?, ?, ?, ?, ?)",
                    [
                        (
                            entry.entry_id,
                            char.name,
                            entry.item.name,
                            entry.quantity,
                            entry.equipped_quantity,
                            ",".join(rune.name for rune in entry.runes),
                        )
                        for entry in char.inventory.entries
                    ],
                )

    def update_character(self, character: Character):
        character.bosses_defeated_names = [self._get_enemy_name_from_boss_id(bid) for bid in character.bosses_defeated]
        self.characters[character.name] = character
        self.reload_buffs()
        try:
            self.save_local_files()
        except Exception:
            logger.exception("Échec de la sauvegarde pour %s", character.name)


    def update_resources(self, character: Character, resources_max: dict[str, int], variations: dict[str, int] | None = None):
        if variations is None:
            variations = {}

        for key in ("hp", "mana", "stamina"):
            current = character.resources.get(key, 0)
            ref_max = resources_max.get(key, 0)
            variation = variations.get(key, 0)
            new_max = ref_max + variation

            # Si le perso était à (ou au-dessus du) max de référence, on applique la variation
            new_value = current + variation if current >= ref_max else current
            character.resources[key] = max(0, min(new_value, new_max))

        self.update_character(character)

    def change_resources(self, character:Character, hp_change: int = 0, mana_change: int = 0, stamina_change: int = 0):
        hp_base, hp_level, hp_item        = _get_resource_max_bonus("hp", character)
        mana_base, mana_level, mana_item  = _get_resource_max_bonus("mana", character)
        stam_base, stam_level, stam_item  = _get_resource_max_bonus("stamina", character)


        current_hp = character.resources.get("hp", 0)
        current_mana = character.resources.get("mana", 0)
        current_stamina = character.resources.get("stamina", 0)


        max_hp = hp_base + hp_level + hp_item
        max_mana = mana_base + mana_level + mana_item
        max_stam = stam_base + stam_level + stam_item


        new_hp = max(0, min(current_hp + hp_change, max_hp)) 
        new_mana = max(0, min(current_mana + mana_change, max_mana))
        new_stamina = max(0, min(current_stamina + stamina_change, max_stam))


        character.resources['hp'] = new_hp
        character.resources['mana'] = new_mana
        character.resources['stamina'] = new_stamina
        self.update_character(character)