import requests
import csv
import json
import io
from pathlib import Path

from utils.utils import (
    _clean,
    _parse_bool,
    _parse_int,
    _extract_stat_bonuses,
    _extract_craft_bonuses,
    _extract_upgrades,
    _extract_tags,
    _extract_power_use_effect,
    _extract_target_effect,
    _extract_item_use_effect,
    _extract_equipped_bonus,
    _extract_ingredients,
    _extract_lootbox_items,
    XP_TABLE,
    STATS_CLEAN,
)
from utils.db import get_connection


def load_characters(sheet_csv_url: str) -> list[dict]:
    """
    Charge les personnages depuis Google Sheets (données statiques) et SQLite (état local).

    Returns
    -------
    tuple[list[dict], dict, dict]
        (characters, inventories_raw, powers_raw)
    """
    response = requests.get(sheet_csv_url)
    response.raise_for_status()
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    characters = {}
    for row in reader:
        if row is None:
            continue
        name = row.get("name")
        if not name:
            continue
        character = {
            "name": name,
            "inventory_size": _parse_int(row.get("inventory_size")),
            "role": _clean(row.get("role")),
            "role_visible": _parse_bool(row.get("role_visible")),
            "class_name": _clean(row.get("class")),
            "resources_max": {
                "hp": _parse_int(row.get("hp_max")),
                "mana": _parse_int(row.get("mana_max")),
                "stamina": _parse_int(row.get("stamina_max")),
            },
            "resources": {
                "hp": _parse_int(row.get("hp_max")),
                "mana": _parse_int(row.get("mana_max")),
                "stamina": _parse_int(row.get("stamina_max")),
            },
            "player_channel_id": _parse_int(row.get("player_channel_id")),
            "description": _clean(row.get("description")),
            "level_upgrades": _extract_upgrades(row.get("lvl_upgrades")),
            "stat_points": _extract_stat_bonuses(row.get("stat_points") or ""),
            "craft_points": _extract_craft_bonuses(row.get("craft_points") or ""),
            "user_id": None,
            "level": 1,
            "experience": 0,
            "kills": 0,
            "bosses_defeated": [],
            "memory_fragments": [],
            "discovered_sets": [],
            "currency": 0,
        }
        characters[character["name"]] = character

    with get_connection() as conn:
        for row in conn.execute("SELECT character_name, user_id FROM character_assignments"):
            name = row["character_name"]
            if name in characters:
                characters[name]["user_id"] = row["user_id"]

        for row in conn.execute(
            "SELECT character_name, hp, mana, stamina, experience, kills, bosses_defeated, memory_fragments, currency, discovered_sets FROM character_status"
        ):
            name = row["character_name"]
            if name not in characters:
                continue
            experience = row["experience"]
            characters[name]["experience"] = experience
            if experience is not None:
                level = 0
                for xp_threshold in list(XP_TABLE.values()):
                    if experience >= xp_threshold:
                        level += 1
                    else:
                        break
                characters[name]["level"] = level

            hp, mana, stamina = row["hp"], row["mana"], row["stamina"]
            if hp is not None and mana is not None and stamina is not None:
                characters[name]["resources"]["hp"] = hp
                characters[name]["resources"]["mana"] = mana
                characters[name]["resources"]["stamina"] = stamina

            characters[name]["kills"] = row["kills"] or 0
            bosses_str = row["bosses_defeated"] or ""
            characters[name]["bosses_defeated"] = [b for b in bosses_str.split(";") if b]
            memories_str = row["memory_fragments"] or ""
            characters[name]["memory_fragments"] = [m for m in memories_str.split(";") if m]
            discovered_str = row["discovered_sets"] or ""
            characters[name]["discovered_sets"] = [s for s in discovered_str.split(";") if s]
            characters[name]["currency"] = row["currency"] or 0

        inventories_raw: dict[str, list[tuple[str, str, int, int, list[str]]]] = {}
        for row in conn.execute(
            "SELECT character_name, entry_id, item_name, quantity, equipped_quantity, runes FROM inventories"
        ):
            name = row["character_name"]
            if name not in characters:
                continue
            rune_list = [r for r in (row["runes"] or "").split(",") if r]
            inventories_raw.setdefault(name, []).append(
                (row["entry_id"], row["item_name"], row["quantity"], row["equipped_quantity"], rune_list)
            )

        powers_raw: dict[str, list[str]] = {}
        for row in conn.execute(
            "SELECT character_name, power_name FROM power_assignments"
        ):
            name = row["character_name"]
            if name not in characters:
                continue
            powers_raw.setdefault(name, []).append(row["power_name"])

    return list(characters.values()), inventories_raw, powers_raw


def load_items(sheet_csv_url: str) -> list[dict]:
    """
    load_items permet de charger les objets à partir d'une feuille Google Sheets.

    Parameters
    ----------
    sheet_csv_url : str
        L'URL du CSV exporté de la feuille Google Sheets contenant les données des objets.

    Returns
    -------
    list[dict] 
    Une liste de dictionnaires représentant les objets chargés.
        
    """    
    response = requests.get(sheet_csv_url)
    response.raise_for_status()
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    items = []
    for row in reader:
        if row is None:
            continue
        item = {
            "name": _clean(row.get("name")),
            "description": _clean(row.get("description")),
            "tags": _extract_tags(row.get("tags")) if row.get("tags") else [],
            "image_path": _clean(row.get("img_path")),
            "value": _parse_int(row.get("value")),
            "unique": _parse_bool(row.get("unique")),
            "tradeable": _parse_bool(row.get("tradeable")),
            "useable": _parse_bool(row.get("useable")),
            "use_title": _clean(row.get("use_title")),
            "use_effects": _extract_item_use_effect(row.get("use_effect")) if row.get("use_effect") else {},
            "use_description": _clean(row.get("use_description")),
            "equippable": _parse_bool(row.get("equippable")),
            "equippable_slot": _clean(row.get("equippable_slot")),
            "equipped_bonus": _extract_equipped_bonus(row.get("equipped_bonus")) if row.get("equipped_bonus") else {},
            "rarity": _clean(row.get("rarity")),
            "rune_slots": _parse_int(row.get("rune_slots")) or 0,
            "forbidden": _parse_bool(row.get("forbidden")),
            "set_name": _clean(row.get("set")),
        }
        items.append(item)

    return items


def load_powers(sheet_csv_url: str) -> list[dict]:
    """
    load_powers permet de charger les pouvoirs à partir d'une feuille Google Sheets.

    Parameters
    ----------
    sheet_csv_url : str
        L'URL du CSV exporté de la feuille Google Sheets contenant les données des pouvoirs.


    Returns
    -------
    list[dict]
        Une liste de dictionnaires représentant les pouvoirs chargés.
    """    
    response = requests.get(sheet_csv_url)
    response.raise_for_status()
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    powers = []
    for idx, row in enumerate(reader):
        if row is None:
            continue
        power = {
            "id": idx,
            "name": _clean(row.get("name")),
            "description": _clean(row.get("description")),
            "category": _clean(row.get("category")),
            "cost": {
                "hp": _parse_int(row.get("hp_cost")),
                "mana": _parse_int(row.get("mana_cost")),
                "stamina": _parse_int(row.get("stamina_cost"))
            },
            "dice": _clean(row.get("dice")),
            "bonus": _extract_power_use_effect(row.get("bonus")) if row.get("bonus") else {},
            "duration": _parse_int(row.get("duration")),
            "image_path": _clean(row.get("img_path")),
            "target": _parse_bool(row.get("target")),
            "target_effect": _extract_target_effect(row.get("target_effect")) if row.get("target_effect") else None,
        }
        powers.append(power)

    return powers


def load_buffs(buffs_csv_file: str) -> list[dict]:
    """
    load_buffs permet de charger les buffs à partir d'un fichier CSV local.

    Returns
    -------
    dict[str, dict]
        Un dictionnaire de buffs chargés.
    """
    buffs = []
    with open(buffs_csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            buffs.append({
                "name": row["name"],
                "description": row["description"],
                "duration": int(row["duration"]),
                "effects": json.loads(row["effects"]),
                "character_name": row["character_name"],
                "source": row["source"],
            })
    return buffs
            

def load_crafts(sheet_csv_url: str) -> list[dict]:
    """
    load_crafts permet de charger les crafts à partir d'une feuille Google Sheets.

    Parameters
    ----------
    sheet_csv_url : str
        L'URL du CSV exporté de la feuille Google Sheets contenant les données des crafts.

    Returns
    -------
    list[dict]
        Une liste de dictionnaires représentant les crafts chargés.
    """       
    response = requests.get(sheet_csv_url)
    response.raise_for_status()
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))

    crafts = [] 
    for row in reader:
        craft = {
            "name": row.get("name"),
            "description": row.get("description"),
            "method": row.get("method"),
            "ingredients": _extract_ingredients(row.get("ingredients") or ""),
            "base_products": _extract_ingredients(row.get("base_products") or ""),
            "success_products": _extract_ingredients(row.get("success_products") or ""),
            "failure_products": _extract_ingredients(row.get("failure_products") or ""),
            "difficulty": int(row.get("difficulty") or 1),
            "success_bonus": _parse_int(row.get("success_bonus")) or 0,
            "experience_gain": _parse_int(row.get("experience_gain")),
            "visible": _parse_bool(row.get("visible")),
        }
        crafts.append(craft)

    return crafts


def load_lootboxes(sheet_csv_url: str) -> list[dict]:
    """
    load_lootboxes permet de charger les lootboxes à partir d'une feuille Google Sheets.

    Parameters
    ----------
    sheet_csv_url : str
        L'URL du CSV exporté de la feuille Google Sheets contenant les données des lootboxes.

    Returns
    -------
    list[dict]
        Une liste de dictionnaires représentant les lootboxes chargées.
    """       
    response = requests.get(sheet_csv_url)
    response.raise_for_status()
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))

    lootboxes = [] 
    for row in reader:
        lootbox = {
            "id": row.get("id"),
            "name": row.get("name"),
            "type": row.get("type"),
            "items": _extract_lootbox_items(row.get("items") or ""),
            "rarity": int(row.get("rarity") or 1),
        }
        lootboxes.append(lootbox)

    return lootboxes


def load_enemies(sheet_csv_url: str) -> list[dict]:
    """
    load_enemies permet de charger les ennemis à partir d'une feuille Google Sheets.

    Parameters
    ----------
    sheet_csv_url : str
        L'URL du CSV exporté de la feuille Google Sheets contenant les données des ennemis.

    Returns
    -------
    list[dict]
        Une liste de dictionnaires représentant les ennemis chargés.
    """       
    response = requests.get(sheet_csv_url)
    response.raise_for_status()
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))

    enemies = [] 
    for row in reader:
        enemy = {
            "id": row.get("id"),
            "name": row.get("name"),
            "biome": row.get("biome"),
            "description": row.get("description"),
            "genre": row.get("genre"),
            "boss": _parse_bool(row.get("boss")),
            "loot_body": row.get("loot_body"),
            "loot_boss": row.get("loot_boss").split(";") if row.get("loot_boss") else [],
            "exp": _parse_int(row.get("exp")),
            "notes": row.get("notes"),
            "stats": {
                "hp": _parse_int(row.get("hp")),
                "Attaque": _parse_int(row.get("attack")),
                "Défense": _parse_int(row.get("defense"))
            }
        }
        enemies.append(enemy)

    return enemies


def load_memories(sheet_csv_url: str) -> list[dict]:
    """
    load_memories permet de charger les mémoires à partir d'une feuille Google Sheets.

    Parameters
    ----------
    sheet_csv_url : str
        L'URL du CSV exporté de la feuille Google Sheets contenant les données des mémoires.

    Returns
    -------
    list[dict]
        Une liste de dictionnaires représentant les mémoires chargées.
    """       
    response = requests.get(sheet_csv_url)
    response.raise_for_status()
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))

    memories = [] 
    for row in reader:
        memory = {
            "player": row.get("player"),
            "id": row.get("id"),
            "name": row.get("name"),
            "content": row.get("content"),
        }
        memories.append(memory)

    return memories


def load_quests(sheet_csv_url: str) -> list[dict]:
    """
    load_quests permet de charger les quêtes à partir d'une feuille Google Sheets.

    Parameters
    ----------
    sheet_csv_url : _type_
        L'URL du CSV exporté de la feuille Google Sheets contenant les données des quêtes.

    Returns
    -------
    list[dict]
        Une liste de dictionnaires représentant les quêtes chargées.
    """
    response = requests.get(sheet_csv_url)
    response.raise_for_status()
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))

    quests = []
    for row in reader:
        quest = {
            "quest_id": row.get("quest_id"),
            "npc_name": row.get("npc_name"),
            "title": row.get("title"),
            "description": row.get("description"),
            "condition_quest": row.get("condition_quest"),
            "condition_items": _extract_ingredients(row.get("condition_items")),
            "reward_xp": _parse_int(row.get("reward_xp")),
            "reward_items": _extract_ingredients(row.get("reward_items") or ""),
        } 
        quests.append(quest)
    
    return quests


def load_npcs(sheet_csv_url: str) -> list[dict]:
    """
    load_npcs permet de charger les NPCs à partir d'une feuille Google Sheets.

    Parameters
    ----------
    sheet_csv_url : str
        L'URL du CSV exporté de la feuille Google Sheets contenant les données des NPCs.

    Returns
    -------
    list[dict]
        Une liste de dictionnaires représentant les NPCs chargés.
    """       
    response = requests.get(sheet_csv_url)
    response.raise_for_status()
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))

    npcs = [] 
    for row in reader:
        npc = {
            "name": row.get("name"),
            "description": row.get("description"),
            "location": row.get("location"),
            "city": row.get("city"),
            "realm": row.get("realm"),
            "roles": _extract_tags(row.get("roles")) if row.get("roles") else [],
            "specialty": row.get("specialty"),
            "image_name": row.get("img_name"),
            "quest_ids": row.get("quest_ids").split(";") if row.get("quest_ids") else [],
            "trade_ids": row.get("trade_ids").split(";") if row.get("trade_ids") else [],
        }
        npcs.append(npc)

    return npcs


def load_trades(sheet_csv_url: str) -> list[dict]:
    """
    Charge les trades depuis Google Sheets (catalogue) et SQLite (historique).
    """
    response = requests.get(sheet_csv_url)
    response.raise_for_status()
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))

    trades = []
    for row in reader:
        trade = {
            "trade_id": row.get("trade_id"),
            "offered_items": _extract_ingredients(row.get("offered_items") or ""),
            "requested_items": _extract_ingredients(row.get("requested_items") or ""),
            "quantity": _parse_int(row.get("qty_available")) or 1,
        }
        trades.append(trade)

    past_trades = []
    with get_connection() as conn:
        for row in conn.execute(
            "SELECT trade_id, item_received_by_player, item_received_by_merchant, currency, player, timestamp FROM past_trades"
        ):
            past_trades.append({
                "trade_id": row["trade_id"],
                "item_received_by_player": json.loads(row["item_received_by_player"] or "[]"),
                "item_received_by_merchant": json.loads(row["item_received_by_merchant"] or "[]"),
                "currency": row["currency"],
                "player": row["player"],
                "timestamp": row["timestamp"],
            })

    return trades, past_trades