from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from instance.character import Character
    from instance.item import Item, ItemRepository

import discord

from utils.utils import SLOT_CONFLICTS, MAX_WEAPONS, FORCE_DUAL_TWO_HAND

@dataclass
class InventoryEntry:
    entry_id: str
    item: "Item"
    quantity: int = 1
    equipped_quantity: int = 0
    runes: List["Item"] = field(default_factory=list)  # resolved Item objects


class Inventory:
    def __init__(self, max_size: int, history: "History"):
        self.max_size = max_size
        self._entries: dict[str, InventoryEntry] = {}  # keyed by entry_id
        self.history = history

    # ── Lecture ──────────────────────────────────────────────

    @property
    def entries(self) -> List[InventoryEntry]:
        return list(self._entries.values())

    @property
    def equipped(self) -> Dict[str, "Item"]:
        return {
            e.item.equippable_slot: e.item
            for e in self._entries.values() if e.equipped_quantity > 0
        }

    def get_quantity(self, item_name: str) -> int:
        return sum(e.quantity for e in self._entries.values() if e.item.name.lower() == item_name.lower())

    def slots_used(self) -> int:
        return sum(e.quantity - e.equipped_quantity for e in self._entries.values())

    def slots_available(self) -> int:
        return self.max_size - self.slots_used()

    def get_entry(self, item_name: str) -> Optional[InventoryEntry]:
        """Returns the first entry matching item_name (case-insensitive)."""
        needle = item_name.lower()
        for e in self._entries.values():
            if e.item.name.lower() == needle:
                return e
        return None

    def get_entries_by_name(self, item_name: str) -> List[InventoryEntry]:
        """Returns all entries matching item_name (case-insensitive)."""
        needle = item_name.lower()
        return [e for e in self._entries.values() if e.item.name.lower() == needle]

    def get_entry_by_id(self, entry_id: str) -> Optional[InventoryEntry]:
        return self._entries.get(entry_id)

    def is_full(self) -> bool:
        return self.slots_used() >= self.max_size

    def get_equipped_items(self) -> List[InventoryEntry]:
        return [e for e in self._entries.values() if e.equipped_quantity > 0]

    def has_item(self, item_name: str) -> bool:
        entry = self.get_entry(item_name)
        return entry is not None and entry.quantity > 0

    # ── Modification ─────────────────────────────────────────

    def init_add(self, item: "Item", quantity: int = 1, entry_id: str = None, runes: List["Item"] = None) -> bool:
        """Add item during initialization (from DB load). No history logging."""
        if item.unique and self.get_entry(item.name):
            return False
        if self.is_full():
            return False

        if item.equippable:
            # Each equippable instance gets its own entry (quantity always 1)
            eid = entry_id if entry_id else str(uuid.uuid4())
            self._entries[eid] = InventoryEntry(
                entry_id=eid,
                item=item,
                quantity=1,
                runes=list(runes) if runes else [],
            )
        else:
            # Non-equippable: group by item name
            existing = self.get_entry(item.name)
            if existing:
                existing.quantity += quantity
            else:
                eid = entry_id if entry_id else str(uuid.uuid4())
                self._entries[eid] = InventoryEntry(
                    entry_id=eid,
                    item=item,
                    quantity=quantity,
                    runes=[],
                )
        return True

    async def add(self, guild: discord.Guild, character: "Character", item: "Item", quantity: int = 1, trade: bool = False, craft: bool = False, loot: bool = False, quest: bool = False) -> bool:
        if self.is_full():
            return False

        if item.equippable:
            # Each equippable instance is a distinct entry
            for _ in range(quantity):
                eid = str(uuid.uuid4())
                self._entries[eid] = InventoryEntry(entry_id=eid, item=item, quantity=1)
            new_quantity = len(self.get_entries_by_name(item.name))
        else:
            entry = self.get_entry(item.name)
            if entry:
                entry.quantity += quantity
                new_quantity = entry.quantity
            else:
                eid = str(uuid.uuid4())
                self._entries[eid] = InventoryEntry(entry_id=eid, item=item, quantity=quantity)
                new_quantity = quantity

        if not trade and not craft and not loot and not quest:
            await self.history.log_inventory_update(
                guild=guild,
                character_name=character.name,
                item_name=item.name,
                quantity_change=quantity,
                new_quantity=new_quantity,
            )

        return True

    async def remove(self, guild: discord.Guild, character: "Character", item_name: str, quantity: int = 1, trade: bool = False, craft: bool = False) -> bool:
        if trade and craft:
            return False

        item_name_lower = item_name.lower()
        entries = self.get_entries_by_name(item_name)

        if not entries:
            return False

        first_entry = entries[0]

        if first_entry.item.equippable:
            # Remove unequipped instances first, then equipped ones
            unequipped = [e for e in entries if e.equipped_quantity == 0]
            if len(unequipped) < quantity:
                return False
            for e in unequipped[:quantity]:
                del self._entries[e.entry_id]
            new_quantity = len(self.get_entries_by_name(item_name))
        else:
            entry = first_entry
            if entry.quantity < quantity:
                return False
            entry.quantity -= quantity
            new_quantity = entry.quantity
            if entry.quantity == 0:
                del self._entries[entry.entry_id]

        if not trade and not craft:
            await self.history.log_inventory_update(
                guild=guild,
                character_name=character.name,
                item_name=item_name,
                quantity_change=-quantity,
                new_quantity=new_quantity,
            )
        return True

    async def use(self, guild: discord.Guild, item_name: str, character: "Character") -> (bool, list[dict]):
        entry = self.get_entry(item_name)
        buff_dict = [{}]
        if not entry or entry.quantity == 0:
            return False, buff_dict
        if not entry.item.useable:
            return False, buff_dict
        if entry.item.tags == ["relique"]:
            return True, {
                "name": entry.item.use_title,
                "description": entry.item.use_description,
                "source": f"Relique: {entry.item.name}"
            }
        entry.quantity -= 1
        if entry.quantity == 0:
            del self._entries[entry.entry_id]

        for effect, (value, duration) in entry.item.use_effects.items():
            buff_dict.append({
                "name": entry.item.use_title,
                "description": entry.item.use_description,
                "effects": {effect: value},
                "duration": duration,
                "source": f"Objet: {entry.item.name}"
            })

        await self.history.log_item_use(
            guild=guild,
            character_name=character.name,
            item_name=item_name,
            new_quantity=entry.quantity if entry.entry_id in self._entries else 0,
        )
        return True, buff_dict

    def equip(self, item_name: str, character: "Character") -> bool:
        # Find the first unequipped entry for this item
        candidates = [e for e in self.get_entries_by_name(item_name) if e.equipped_quantity == 0]
        if not candidates:
            return False
        entry = candidates[0]
        if not entry.item.equippable:
            return False

        slot = entry.item.equippable_slot

        if slot in ("arme_une_main", "arme_deux_mains"):
            can_dual_two_hand = character.stat_points.get("Force", 0) >= FORCE_DUAL_TWO_HAND
            equipped_weapons = [
                e for e in self._entries.values()
                if e.equipped_quantity > 0 and e.item.equippable_slot in ("arme_une_main", "arme_deux_mains")
            ]
            total_equipped = sum(e.equipped_quantity for e in equipped_weapons)

            if not can_dual_two_hand:
                if slot == "arme_deux_mains" and total_equipped >= 1:
                    for e in equipped_weapons:
                        e.equipped_quantity = 0
                elif any(e.item.equippable_slot == "arme_deux_mains" for e in equipped_weapons):
                    for e in equipped_weapons:
                        e.equipped_quantity = 0

            if total_equipped >= MAX_WEAPONS:
                for e in equipped_weapons:
                    if e.equipped_quantity > 0:
                        e.equipped_quantity -= 1
                        break
        else:
            for e in self._entries.values():
                if e.equipped_quantity > 0 and e.item.equippable_slot == slot:
                    e.equipped_quantity = 0
                    break

        entry.equipped_quantity += 1
        return True

    def unequip(self, item_name: str) -> bool:
        # Find the first equipped entry for this item
        candidates = [e for e in self.get_entries_by_name(item_name) if e.equipped_quantity > 0]
        if not candidates:
            return False
        entry = candidates[0]
        if not entry.item.equippable:
            return False
        entry.equipped_quantity -= 1
        return True

    def apply_rune(self, entry_id: str, rune_item: "Item") -> bool:
        """Apply a rune to an equippable item entry. Returns False if no slot available."""
        entry = self.get_entry_by_id(entry_id)
        if not entry or not entry.item.equippable:
            return False
        if len(entry.runes) >= entry.item.rune_slots:
            return False
        entry.runes.append(rune_item)
        return True

    RUNES_RECOVERED = {"legendary", "mythic"}

    def remove_rune(self, entry_id: str, rune_name: str) -> tuple[bool, Optional["Item"]]:
        """
        Remove the first rune matching rune_name from the entry.
        Returns (success, recovered_item).
        recovered_item is the Item if the rune should be returned to inventory
        (legendary/mythic), or None if it is destroyed (common/uncommon/rare/epic).
        """
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            return False, None
        needle = rune_name.lower()
        for i, rune in enumerate(entry.runes):
            if rune.name.lower() == needle:
                entry.runes.pop(i)
                recovered = rune if rune.rarity in self.RUNES_RECOVERED else None
                return True, recovered
        return False, None

