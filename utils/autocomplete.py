from discord import Interaction
from discord import app_commands

import unicodedata

from utils.utils import STATS_CLEAN, UPGRADE_EQUIPMENT
from utils.locations import LOCATIONS


# --- Helpers ---

def _word_startswith(name: str, current: str) -> bool:
    """Returns True if any word in `name` starts with `current`.
    Apostrophes (straight and curly) are treated as word separators."""
    if not current:
        return True
    normalized = name.lower().replace("'", " ").replace("\u2019", " ")
    current_lower = current.lower()
    return any(word.startswith(current_lower) for word in normalized.split())


def _accent_sort_key(name: str) -> str:
    """Sort key that groups accented chars with their base letter (é,è → e, à → a)."""
    return unicodedata.normalize('NFD', name.lower())


# --- Character Autocomplete ---
def make_active_player_autocomplete(character_repository):
    """Autocomplete limité aux joueurs actifs en session (character_repository.players)."""
    async def active_player_autocomplete(interaction, current: str):
        return sorted([
            app_commands.Choice(name=name, value=name)
            for name in character_repository.players
            if _word_startswith(name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return active_player_autocomplete

def make_character_autocomplete(character_repository):
    async def character_name_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        suggestions = character_repository.search_characters(current)
        return sorted(
            [app_commands.Choice(name=char.name, value=char.name) for char in suggestions],
            key=lambda c: _accent_sort_key(c.name)
        )
    return character_name_autocomplete

def make_character_autocomplete_by_user_id(character_repository):
    async def character_name_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character = character_repository.get_character_by_user_id(interaction.user.id)
        suggestions = character_repository.search_characters(current)
        return sorted(
            [
                app_commands.Choice(name=char.name, value=char.name)
                for char in suggestions
                if character is not None and char.name != character.name
            ],
            key=lambda c: _accent_sort_key(c.name)
        )
    return character_name_autocomplete


# --- Item Autocomplete ---
def make_item_info_autocomplete(character_repository):
    """Autocomplete for /item info: entry_id for equippable items (with rune label), item_name for others."""
    async def item_info_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character = character_repository.get_character_by_user_id(interaction.user.id)
        if not character or not character.inventory:
            return []

        seen_names = set()
        choices = []
        for entry in sorted(character.inventory.entries, key=lambda x: _accent_sort_key(x.item.name)):
            name = entry.item.name
            if not _word_startswith(name, current):
                continue
            if entry.item.equippable:
                if entry.runes:
                    rune_label = ", ".join(r.name for r in entry.runes)
                    label = f"{name} [{rune_label}]"
                else:
                    label = f"{name} [0/{entry.item.rune_slots} runes]" if entry.item.rune_slots > 0 else name
                choices.append(app_commands.Choice(name=label[:100], value=entry.entry_id))
            else:
                if name not in seen_names:
                    seen_names.add(name)
                    choices.append(app_commands.Choice(name=name, value=name))
        return choices[:25]
    return item_info_autocomplete

def make_item_autocomplete(character_repository):
    async def item_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character = character_repository.get_character_by_user_id(interaction.user.id)

        if not character or not character.inventory:
            return []

        seen = set()
        choices = []
        for entry in sorted(character.inventory.entries, key=lambda x: _accent_sort_key(x.item.name)):
            name = entry.item.name
            if name in seen:
                continue
            if _word_startswith(name, current):
                seen.add(name)
                choices.append(app_commands.Choice(name=name, value=name))
        return choices[:25]
    return item_autocomplete

def make_items_autocomplete(item_repository):
    async def items_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        items = item_repository.items.values()
        return sorted([
            app_commands.Choice(name=item.name, value=item.name)
            for item in items
            if _word_startswith(item.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]

    return items_autocomplete

def make_equippable_item_autocomplete(character_repository):
    async def item_equippable_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character = character_repository.get_character_by_user_id(interaction.user.id)

        if not character or not character.inventory:
            return []

        seen = set()
        choices = []
        for entry in sorted(character.inventory.entries, key=lambda x: _accent_sort_key(x.item.name)):
            if not entry.item.equippable or entry.equipped_quantity >= entry.quantity:
                continue
            name = entry.item.name
            if name in seen:
                continue
            if _word_startswith(name, current):
                seen.add(name)
                choices.append(app_commands.Choice(name=name, value=name))
        return choices[:25]
    return item_equippable_autocomplete

def make_unequippable_item_autocomplete(character_repository):
    async def item_unequippable_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character = character_repository.get_character_by_user_id(interaction.user.id)

        if not character or not character.inventory:
            return []

        seen = set()
        choices = []
        for entry in sorted(character.inventory.entries, key=lambda x: _accent_sort_key(x.item.name)):
            if not entry.item.equippable or entry.equipped_quantity == 0:
                continue
            name = entry.item.name
            if name in seen:
                continue
            if _word_startswith(name, current):
                seen.add(name)
                choices.append(app_commands.Choice(name=name, value=name))
        return choices[:25]
    return item_unequippable_autocomplete

def make_useable_item_autocomplete(character_repository):
    async def item_useable_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character = character_repository.get_character_by_user_id(interaction.user.id)

        if not character or not character.inventory:
            return []

        useable_items = [entry for entry in character.inventory.entries if entry.item.useable]

        return sorted([
            app_commands.Choice(name=entry.item.name, value=entry.item.name)
            for entry in useable_items
            if _word_startswith(entry.item.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return item_useable_autocomplete

def make_rune_on_entry_autocomplete(character_repository):
    """Autocomplete for runes currently on a specific entry (reads entry_id from namespace)."""
    async def rune_on_entry_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character = character_repository.get_character_by_user_id(interaction.user.id)
        if not character or not character.inventory:
            return []
        entry_id = getattr(interaction.namespace, "entry_id", None)
        if entry_id:
            entry = character.inventory.get_entry_by_id(entry_id)
            if entry:
                return sorted([
                    app_commands.Choice(name=rune.name, value=rune.name)
                    for rune in entry.runes
                    if _word_startswith(rune.name, current)
                ], key=lambda c: _accent_sort_key(c.name))[:25]
        # Fallback: show all runes on any entry
        seen = set()
        choices = []
        for entry in character.inventory.entries:
            for rune in entry.runes:
                if rune.name not in seen and _word_startswith(rune.name, current):
                    seen.add(rune.name)
                    choices.append(app_commands.Choice(name=rune.name, value=rune.name))
        return sorted(choices, key=lambda c: _accent_sort_key(c.name))[:25]
    return rune_on_entry_autocomplete

def make_enchanted_entry_autocomplete(character_repository):
    """Autocomplete for equippable item entries that have at least one rune. Value = entry_id."""
    async def enchanted_entry_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character = character_repository.get_character_by_user_id(interaction.user.id)
        if not character or not character.inventory:
            return []

        choices = []
        for entry in character.inventory.entries:
            if not entry.item.equippable or not entry.runes:
                continue
            rune_names = ", ".join(r.name for r in entry.runes)
            label = f"{entry.item.name} [{rune_names}]"
            if _word_startswith(entry.item.name, current):
                choices.append(app_commands.Choice(name=label[:100], value=entry.entry_id))
        return sorted(choices, key=lambda c: _accent_sort_key(c.name))[:25]
    return enchanted_entry_autocomplete

def make_enchantable_entry_autocomplete_for_character(character_repository):
    """Autocomplete for enchantable entries based on character_name in namespace (admin use)."""
    async def enchantable_entry_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character_name = getattr(interaction.namespace, "character_name", None)
        character = (
            character_repository.get_character_by_name(character_name)
            if character_name
            else character_repository.get_character_by_user_id(interaction.user.id)
        )
        if not character or not character.inventory:
            return []

        choices = []
        for entry in character.inventory.entries:
            if not entry.item.equippable or entry.item.rune_slots == 0:
                continue
            if len(entry.runes) >= entry.item.rune_slots:
                continue
            slots_used = len(entry.runes)
            slots_total = entry.item.rune_slots
            label = f"{entry.item.name} [{slots_used}/{slots_total} runes]"
            if _word_startswith(entry.item.name, current):
                choices.append(app_commands.Choice(name=label[:100], value=entry.entry_id))
        return sorted(choices, key=lambda c: _accent_sort_key(c.name))[:25]
    return enchantable_entry_autocomplete

def make_enchantable_entry_autocomplete(character_repository):
    """Autocomplete for equippable item entries that have free rune slots. Value = entry_id."""
    async def enchantable_entry_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character = character_repository.get_character_by_user_id(interaction.user.id)
        if not character or not character.inventory:
            return []

        choices = []
        for entry in character.inventory.entries:
            if not entry.item.equippable or entry.item.rune_slots == 0:
                continue
            if len(entry.runes) >= entry.item.rune_slots:
                continue
            slots_used = len(entry.runes)
            slots_total = entry.item.rune_slots
            label = f"{entry.item.name} [{slots_used}/{slots_total} runes]"
            if _word_startswith(entry.item.name, current):
                choices.append(app_commands.Choice(name=label, value=entry.entry_id))
        return sorted(choices, key=lambda c: _accent_sort_key(c.name))[:25]
    return enchantable_entry_autocomplete

def make_rune_autocomplete(character_repository):
    """Autocomplete for rune items in the player's inventory (only rare/epic — others require a master blacksmith)."""
    async def rune_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character = character_repository.get_character_by_user_id(interaction.user.id)
        if not character or not character.inventory:
            return []

        return sorted([
            app_commands.Choice(name=entry.item.name, value=entry.item.name)
            for entry in character.inventory.entries
            if "rune" in entry.item.tags
            and entry.item.rarity in ("rare", "epic")
            and _word_startswith(entry.item.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return rune_autocomplete

# --- Power Autocomplete ---

def make_all_powers_autocomplete(power_repository):
    """Autocomplete for all powers in the repository (admin use)."""
    async def all_powers_autocomplete(
        interaction: Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        return sorted([
            app_commands.Choice(name=power.name, value=power.name)
            for power in power_repository.powers.values()
            if _word_startswith(power.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return all_powers_autocomplete

def make_power_autocomplete(character_repository):
    async def power_autocomplete(
        interaction: Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Retourne les pouvoirs du personnage de l'utilisateur."""
        character = character_repository.get_character_by_user_id(interaction.user.id)
        if not character or not character.powers:
            return []

        return sorted([
            app_commands.Choice(name=power.name, value=power.name)
            for power in character.powers
            if _word_startswith(power.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return power_autocomplete


# --- Blacksmith Autocomplete ---

def make_blacksmith_npc_autocomplete(npc_repository, bot):
    """Autocomplete for NPCs with the 'blacksmith' role."""
    async def blacksmith_npc_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        if bot.location.city is not None and bot.location.realm != "":
            npcs = [n for n in npc_repository.by_city(bot.location.city) if n.has_role("blacksmith")]
        elif bot.location.realm != "":
            npcs = [n for n in npc_repository.by_realm_outside_city(bot.location.realm) if n.has_role("blacksmith")]
        else:
            npcs = [n for n in npc_repository.npcs() if n.has_role("blacksmith")]
        return sorted([
            app_commands.Choice(name=f"[{npc.location}] - {npc.name}", value=npc.name)
            for npc in npcs
            if _word_startswith(npc.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return blacksmith_npc_autocomplete

def make_blacksmith_rune_autocomplete(character_repository):
    """Autocomplete for runes (all rarities) in the selected character's inventory."""
    async def blacksmith_rune_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character_name = getattr(interaction.namespace, "character_name", None)
        character = (
            character_repository.get_character_by_name(character_name)
            if character_name
            else character_repository.get_character_by_user_id(interaction.user.id)
        )
        if not character or not character.inventory:
            return []
        return sorted([
            app_commands.Choice(name=entry.item.name, value=entry.item.name)
            for entry in character.inventory.entries
            if "rune" in entry.item.tags
            and _word_startswith(entry.item.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return blacksmith_rune_autocomplete

def make_upgradeable_item_autocomplete(character_repository, item_repository):
    """Autocomplete for items in the selected character's inventory that can be upgraded, unequipped only."""
    import math
    async def upgradeable_item_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character_name = getattr(interaction.namespace, "character_name", None)
        character = (
            character_repository.get_character_by_name(character_name)
            if character_name
            else character_repository.get_character_by_user_id(interaction.user.id)
        )
        if not character or not character.inventory:
            return []
        seen = set()
        choices = []
        for entry in character.inventory.entries:
            name = entry.item.name
            upgrade_entry = next((u for u in UPGRADE_EQUIPMENT if u["source"] == name), None)
            if not upgrade_entry or name in seen or entry.equipped_quantity > 0:
                continue
            if not _word_startswith(name, current):
                continue
            dest_name = upgrade_entry["dest"]
            dest_item = item_repository.get_item_by_name(dest_name)
            if dest_item and entry.item.value is not None and dest_item.value is not None:
                cost = math.ceil((dest_item.value - entry.item.value) * 0.8)
                label = f"{name} → {dest_name} ({cost}🪙)"
            else:
                label = f"{name} → {dest_name}"
            seen.add(name)
            choices.append(app_commands.Choice(name=label[:100], value=name))
        return sorted(choices, key=lambda c: _accent_sort_key(c.name))[:25]
    return upgradeable_item_autocomplete

# --- Craft Autocomplete ---
def make_craft_filter_autocomplete(craft_repository):
    async def craft_filter_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice]:
        """ Retourne les méthodes de craft, difficultés et l'option 'craftable' pour filtrer la liste des crafts. """
        options = (
            ["craftable"]
            + sorted(craft_repository.methods)
            + [str(d) for d in sorted(craft_repository.difficulties)]
        )
        return [
            app_commands.Choice(name=opt, value=opt)
            for opt in options if _word_startswith(opt, current)
        ]
    return craft_filter_autocomplete

def make_craft_autocomplete(craft_repository):
    async def craft_name_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice]:
        visible = craft_repository.get_visible_crafts()
        return sorted([
            app_commands.Choice(name=craft.name, value=craft.name)
            for craft in visible
            if _word_startswith(craft.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return craft_name_autocomplete



def make_craftable_craft_autocomplete(craft_repository, character_repository):
    async def craftable_craft_name_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice]:
        character = character_repository.get_character_by_user_id(interaction.user.id)
        if not character or not character.powers:
            return []
        visible = craft_repository.find_craftable_crafts(character)

        return sorted([
            app_commands.Choice(name=craft.name, value=craft.name)
            for craft in visible
            if _word_startswith(craft.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return craftable_craft_name_autocomplete

# --- Enemy Autocomplete ---
def make_active_enemy_autocomplete(enemy_repository):
    async def active_enemy_autocomplete(interaction, current: str):
        return sorted([
            app_commands.Choice(name=e.label(), value=e.instance_id)
            for e in enemy_repository.list_active()
            if _word_startswith(e.label(), current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return active_enemy_autocomplete

def make_catalog_enemy_autocomplete(enemy_repository):
    async def catalog_autocomplete(interaction, current: str):
        return sorted([
            app_commands.Choice(name=data["name"], value=eid)
            for eid, data in enemy_repository.catalog_items()
            if _word_startswith(data["name"], current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return catalog_autocomplete

# --- Dice Autocomplete ---
def make_stat_dice_autocomplete():
    async def stat_dice_autocomplete(
        interaction: Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Retourne les stats du personnage de l'utilisateur."""
        excluded = {"HP max", "Mana max", "Stamina max"}
        return sorted([
            app_commands.Choice(name=stat, value=stat)
            for stat in STATS_CLEAN.values()
            if stat not in excluded
            and _word_startswith(stat, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return stat_dice_autocomplete

def make_realm_autocomplete():
    """Autocomplete for realm names from LOCATIONS."""
    async def realm_autocomplete(
        interaction: Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        return sorted([
            app_commands.Choice(name=r, value=r)
            for r in LOCATIONS
            if _word_startswith(r, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return realm_autocomplete

def make_city_autocomplete(location):
    """Autocomplete for city names within the current realm from LOCATIONS."""
    async def city_autocomplete(
        interaction: Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        cities = LOCATIONS.get(location.realm, [])
        return sorted([
            app_commands.Choice(name=c, value=c)
            for c in cities
            if _word_startswith(c, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return city_autocomplete

def make_lootbox_autocomplete(lootbox_repository):
    async def lootbox_name_autocomplete(
        interaction: Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Retourne les noms des lootboxes disponibles."""
        lootboxes = lootbox_repository.list_lootboxes()
        return sorted([
            app_commands.Choice(name=lootbox.name, value=lootbox.name)
            for lootbox in lootboxes
            if _word_startswith(lootbox.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return lootbox_name_autocomplete

def make_combat_target_autocomplete(enemy_repository, combat):
    """Retourne les ennemis actifs ET les joueurs en combat pour la commande /enemy move."""
    async def combat_target_autocomplete(interaction, current: str):
        choices = []
        for e in enemy_repository.list_active():
            if _word_startswith(e.label(), current):
                choices.append(app_commands.Choice(name=e.label(), value=e.instance_id))
        for player_name in combat.player_positions:
            if _word_startswith(player_name, current):
                choices.append(app_commands.Choice(name=player_name, value=player_name))
        return sorted(choices, key=lambda c: _accent_sort_key(c.name))[:25]
    return combat_target_autocomplete


# --- NPC Autocomplete ---

def make_npc_autocomplete(npc_repository, bot):
    """Autocomplete for all NPCs (location-aware)."""
    async def npc_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        if bot.location.city is not None and bot.location.realm != "":
            npcs = list(npc_repository.by_city(bot.location.city))
        elif bot.location.realm != "":
            npcs = list(npc_repository.by_realm_outside_city(bot.location.realm))
        else:
            npcs = list(npc_repository.npcs())
        return sorted([
            app_commands.Choice(name=f"[{npc.location}] - {npc.name} ({', '.join(npc.roles)})", value=npc.name)
            for npc in npcs
            if _word_startswith(npc.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return npc_autocomplete

def make_merchant_npc_autocomplete(npc_repository, bot):
    """Autocomplete for NPCs with the 'merchant' role (location-aware)."""
    async def merchant_npc_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        if bot.location.city is not None and bot.location.realm != "":
            npcs = [n for n in npc_repository.by_city(bot.location.city) if n.has_role("merchant")]
        elif bot.location.realm != "":
            npcs = [n for n in npc_repository.by_realm_outside_city(bot.location.realm) if n.has_role("merchant")]
        else:
            npcs = [n for n in npc_repository.npcs() if n.has_role("merchant")]
        return sorted([
            app_commands.Choice(name=f"[{npc.location}] - {npc.name}", value=npc.name)
            for npc in npcs
            if _word_startswith(npc.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return merchant_npc_autocomplete

def make_sale_npc_autocomplete(npc_repository, bot):
    """Autocomplete for NPCs with 'merchant' or 'blacksmith' role (location-aware)."""
    async def sale_npc_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        def is_seller(npc):
            return npc.has_role("merchant") or npc.has_role("blacksmith")
        if bot.location.city is not None and bot.location.realm != "":
            npcs = [n for n in npc_repository.by_city(bot.location.city) if is_seller(n)]
        elif bot.location.realm != "":
            npcs = [n for n in npc_repository.by_realm_outside_city(bot.location.realm) if is_seller(n)]
        else:
            npcs = [n for n in npc_repository.npcs() if is_seller(n)]
        return sorted([
            app_commands.Choice(name=f"[{npc.location}] - {npc.name} ({', '.join(npc.roles)})", value=npc.name)
            for npc in npcs
            if _word_startswith(npc.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return sale_npc_autocomplete

def make_offer_item_autocomplete(character_repository):
    """Autocomplete for items from the character named in namespace.character_name."""
    async def offer_item_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character_name = interaction.namespace.character_name
        character = character_repository.get_character_by_name(character_name)
        if not character:
            return []
        return sorted([
            app_commands.Choice(name=f"{e.item.name} (x{e.quantity})", value=e.item.name)
            for e in character.inventory.entries
            if _word_startswith(e.item.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return offer_item_autocomplete

def make_trade_id_autocomplete(npc_repository, trade_repository):
    """Autocomplete for trade IDs available from the NPC named in namespace.npc_name."""
    async def trade_id_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        npc_name = interaction.namespace.npc_name
        npc = npc_repository.get(npc_name)
        if not npc:
            return []
        return sorted([
            app_commands.Choice(
                name=f"{t.offered_items[0].item.name if t.offered_items else trade_id} ({trade_id})",
                value=trade_id,
            )
            for trade_id, t in trade_repository.trades.items()
            if t in npc.trades and _word_startswith(trade_id, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return trade_id_autocomplete

def make_sale_id_autocomplete(npc_repository, trade_repository):
    """Autocomplete for sale trade IDs (type='sale') from the NPC named in namespace.npc_name."""
    async def sale_id_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        npc_name = interaction.namespace.npc_name
        npc = npc_repository.get(npc_name)
        if not npc:
            return []
        return sorted([
            app_commands.Choice(
                name=f"{t.offered_items[0].item.name if t.offered_items else trade_id} ({trade_id})",
                value=trade_id,
            )
            for trade_id, t in trade_repository.trades.items()
            if t in npc.trades and t.type == "sale" and _word_startswith(trade_id, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return sale_id_autocomplete

def make_accept_quest_autocomplete(npc_repository, quest_progress, bot):
    """Autocomplete for quests available to start in the current city."""
    async def accept_quest_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        completed = quest_progress.get_completed()
        choices = []
        for npc in npc_repository.by_city(bot.location.city):
            for quest in npc.visible_quests(completed):
                status = quest_progress.get_status(quest.quest_id)
                if status is None:
                    if _word_startswith(quest.title, current) or _word_startswith(quest.quest_id, current):
                        choices.append(app_commands.Choice(
                            name=f"{quest.title} ({quest.quest_id})",
                            value=quest.quest_id,
                        ))
        return sorted(choices, key=lambda c: _accent_sort_key(c.name))[:25]
    return accept_quest_autocomplete

def make_active_quest_autocomplete(npc_repository, quest_progress):
    """Autocomplete for currently active quests."""
    async def active_quest_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        active = quest_progress.get_active()
        choices = []
        for quest_id in active:
            quest = npc_repository.get_quest(quest_id)
            if quest and (_word_startswith(quest.title, current) or _word_startswith(quest_id, current)):
                choices.append(app_commands.Choice(
                    name=f"{quest.title} ({quest_id})",
                    value=quest_id,
                ))
        return sorted(choices, key=lambda c: _accent_sort_key(c.name))[:25]
    return active_quest_autocomplete


# --- Tag Autocomplete ---

def make_tag_autocomplete(item_repository):
    """Autocomplete for item tags."""
    async def tag_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        return sorted([
            app_commands.Choice(name=tag, value=tag)
            for tag in item_repository.tags
            if _word_startswith(tag, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return tag_autocomplete


# --- Buff Autocomplete ---

def make_buff_autocomplete(buff_repository):
    """Autocomplete for active buffs for the character named in namespace.character_name."""
    async def buff_autocomplete(
        interaction: Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        character_name = interaction.namespace.character_name
        if not character_name:
            return []
        buffs = buff_repository.get_buffs_by_character(character_name)
        return sorted([
            app_commands.Choice(name=buff.name, value=buff.name)
            for buff in buffs
            if _word_startswith(buff.name, current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return buff_autocomplete


# --- Memory Fragment Autocomplete ---

def make_fragment_id_autocomplete(memory_repository):
    """Autocomplete for memory fragments for the character named in namespace.character_name."""
    async def fragment_id_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        character_name = interaction.namespace.character_name
        if not character_name:
            return []
        fragments = memory_repository.get_all_fragments_for_player(character_name)
        return sorted([
            app_commands.Choice(name=f"{f.id} — {f.name}", value=f.id)
            for f in fragments
            if _word_startswith(f.name, current) or str(f.id).startswith(current)
        ], key=lambda c: _accent_sort_key(c.name))[:25]
    return fragment_id_autocomplete
