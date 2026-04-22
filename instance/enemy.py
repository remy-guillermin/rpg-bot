import math 
import discord

from utils.utils import VOWELS
from utils.load import load_enemies
from utils.path import GSHEET_ENEMIES

class Enemy:
    def __init__(self, data: dict, instance_id: str):
        self.instance_id = instance_id
        self.enemy_id    = data["id"]
        self.name        = data["name"]
        self.biome       = data["biome"]
        self.description = data["description"]
        self.genre       = data["genre"]       # "M" | "F"
        self.boss        = data["boss"]
        self.loot_body   = data["loot_body"]
        self.loot_boss   = data.get("loot_boss", "")
        self.experience  = data["exp"]
        self.notes       = data.get("notes", "")

        stats            = data["stats"]
        self.max_hp      = stats["hp"]
        self.atk         = stats["Attaque"]
        self.defense     = stats["Défense"]
        self.current_hp  = self.max_hp

        self.damage_log: dict[str, int] = {}
        self.position: tuple[int, int] | None = None

    # ── Combat ──────────────────────────────────────────────

    def take_damage(self, raw: int) -> dict:
        actual = max(1, raw - self.defense)
        old_hp = self.current_hp
        self.current_hp = max(0, self.current_hp - actual)
        return {
            "raw":      raw,
            "actual":   actual,
            "absorbed": raw - actual,
            "hp_before": old_hp,
            "hp_after":  self.current_hp,
            "alive":    self.is_alive(),
        }
    
    def heal(self, amount: int) -> dict:
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return {
            "amount":    self.current_hp - old_hp,
            "hp_before": old_hp,
            "hp_after":  self.current_hp,
        }

    def is_alive(self) -> bool:
        return self.current_hp > 0

    def hp_ratio(self) -> float:
        return self.current_hp / self.max_hp

    def xp_reward(self, damage_log: dict[str, int]) -> dict[str, int]:
        base_exp = self.experience * 0.05
        exp_distribution = {
            name: math.ceil(base_exp + (dmg / self.max_hp) * (self.experience - base_exp * len(damage_log)))
            for name, dmg in damage_log.items()
        }
        return exp_distribution

    # ── Helpers ─────────────────────────────────────────────
    def article(self, capitalize=False) -> str:
        """Le / La / L' selon genre et initiale du nom."""
        if self.name[0] in VOWELS:
            return "L'" if capitalize else "l'"
        art = "La" if self.genre == "F" else "Le"
        return art if capitalize else art.lower()

    def label(self) -> str:
        """ex: 'Goule [goule_2]' pour les menus/autocomplete."""
        return f"{self.name} [{self.instance_id}]"

    def __repr__(self):
        return f"<Enemy {self.instance_id!r} {self.current_hp}/{self.max_hp}hp>"

    
class EnemyRepository:
    def __init__(self):
        self._catalog:  dict[str, dict]  = {}  # enemy_id  → données brutes
        self._active:   dict[str, Enemy] = {}  # instance_id → Enemy vivant
        self._counters: dict[str, int]   = {}  # enemy_id  → nb total spawnés
        self.tracker_message: discord.Message | None = None
        self.reload()


    def reload(self) -> int:
        self._catalog.clear()
        self._active.clear()
        self._counters.clear()
        enemies_as_dicts = load_enemies(GSHEET_ENEMIES)
        self.load_catalog(enemies_as_dicts) 
        return len(self._catalog)

    # ── Catalogue ────────────────────────────────────────────

    def load_catalog(self, enemy_list: list[dict]):
        """Appelé après load_enemy() depuis Google Sheets."""
        self._catalog = {e["id"]: e for e in enemy_list}


    def catalog_ids(self) -> list[str]:
        return list(self._catalog.keys())

    def catalog_items(self) -> list[tuple[str, dict]]:
        """Retourne les paires (id, données) du catalogue."""
        return list(self._catalog.items())

    

    # ── Spawn / Kill ─────────────────────────────────────────
    #              POS1   POS2    POS3    POS4    POS5   POS6   POS7    POS8    POS9    POS10   POS11    POS12    POS13    POS14
    ENEMY_SLOTS = [(0,0), (-1,0), (0,-1), (1,-1), (1,0), (2,0), (2,-1), (2,-2), (1,-2), (0,-2), (-1,-2), (-2,-2), (-2,-1), (-2,0)]

    def spawn(self, enemy_id: str, count: int = 1, players: list[str] = None) -> list[Enemy]:
        if enemy_id not in self._catalog:
            raise ValueError(f"Ennemi '{enemy_id}' introuvable dans le catalogue.")
        occupied = {e.position for e in self._active.values() if e.position is not None}
        free_slots = [s for s in self.ENEMY_SLOTS if s not in occupied]
        spawned = []
        for i in range(count):
            self._counters[enemy_id] = self._counters.get(enemy_id, 0) + 1
            iid = f"{enemy_id}_{self._counters[enemy_id]}"
            enemy = Enemy(self._catalog[enemy_id], iid)
            enemy.damage_log = {player: 0 for player in (players or [])}
            enemy.position = free_slots[i] if i < len(free_slots) else (0, -4)
            occupied.add(enemy.position)
            self._active[iid] = enemy
            spawned.append(enemy)

        return spawned

    def kill(self, instance_id: str) -> Enemy | None:
        """Retire l'ennemi des actifs. Retourne l'instance (pour loot/exp)."""
        return self._active.pop(instance_id, None)

    def clear_active(self):
        self._active.clear()

    # ── Recherche ────────────────────────────────────────────

    def get(self, instance_id: str) -> Enemy | None:
        return self._active.get(instance_id)

    def search_active(self, query: str) -> list[Enemy]:
        """Recherche partielle sur nom ou instance_id."""
        q = query.lower()
        return [
            e for e in self._active.values()
            if q in e.name.lower() or q in e.instance_id.lower()
        ]

    def list_active(self) -> list[Enemy]:
        return list(self._active.values())