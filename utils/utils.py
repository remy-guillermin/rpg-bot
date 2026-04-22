import discord
import logging
import math
import re
import random
import numpy as np

logger = logging.getLogger(__name__)

# ------------------- CONSTANTS  ------------------
XP_TABLE = {
    1: 0,
    2: 100,
    3: 300,
    4: 600,
    5: 1000,
    6: 1500,
    7: 2100,
    8: 2800,
    9: 3600,
    10: 4500,
}

STATS_CLEAN = {
    "force": "Force",
    "defense": "Défense",
    "resistance": "Résistance",
    "agilite": "Agilité",
    "perception": "Perception",
    "discretion": "Discrétion", 
    "attaque": "Attaque",
    "infiltration": "Infiltration",
    "charisme": "Charisme",
    "hp_max": "HP max",
    "mana_max": "Mana max",
    "stamina_max": "Stamina max",
}

BUFF_CLEAN = {
    "force": "Force",
    "defense": "Défense",
    "resistance": "Résistance",
    "agilite": "Agilité",
    "perception": "Perception",
    "discretion": "Discrétion",
    "attaque": "Attaque",
    "infiltration": "Infiltration",
    "charisme": "Charisme",
    "hp": "HP",
    "mana": "Mana",
    "stamina": "Stamina",
    "all": "Toutes les stats",
    "hp max": "HP max",
    "mana max": "Mana max",
    "stamina max": "Stamina max",
}

STAT_MAP = {
    "hp": "hp_change",
    "mana": "mana_change",
    "stamina": "stamina_change"
}

SLOTS_CLEAN = {
    "tete": "Tête",
    "armure": "Armure",
    "arme_une_main": "Arme à une main",
    "arme_deux_mains": "Arme à deux mains",
    "artefact": "Artéfact"
}

EMOJI_BY_SLOT = {
    "Tête": "🎩",
    "Armure": "🛡️",
    "Arme à une main": "🗡️",
    "Arme à deux mains": "⚔️",
    "Artéfact": "🗿"
}

EMOJI_BY_BUFF = {
    "hp": "❤️",
    "hp max": "❤️‍🔥",
    "mana": "💧",
    "mana max": "💎",
    "stamina": "💨",
    "stamina max": "🌪️",
    "attaque": "⚔️",
    "défense": "🛡️",
    "force": "💪",
    "résistance": "🩸",
    "perception": "👁️",
    "discrétion": "🌑",
    "infiltration": "🐍",
    "agilité": "💨",
    "charisme": "🎭",
}

SLOT_CONFLICTS = {
    "arme_deux_mains": {"arme_une_main"},
    "arme_une_main":   {"arme_deux_mains"},
}

MAX_WEAPONS = 2
FORCE_DUAL_TWO_HAND = 4


TAGS_CLEAN = {
    "consommable": "Consommable",
    "armurerie": "Armurerie",
    "relique": "Relique",
    "ressource": "Ressource",
    "sans_tag": "Sans tag",
    "artéfact": "Artéfact",
    "document": "Document",
    "outil": "Outil",
    "rune": "Rune",
    "map": "Carte",
}

EMOJI_BY_TAG = {
    "Consommable": "🍖",
    "Armurerie": "⚔️",
    "Relique": "🔮",
    "Ressource": "⛏️",
    "Sans tag": "❓",
    "Artéfact": "🗿",
    "Document": "📜",
    "Outil": "🧰",
    "Rune": "߷",
}

ENCHANT_THRESHOLDS = {"rare": 35, "epic": 65}
ENCHANT_COOLDOWN_MINUTES = 10

UPGRADE_EQUIPMENT: list[dict[str, str]] = [
    {"source": "Bouclier en bois", "dest": "Bouclier en acier", "cost": 10},
    {"source": "Armure", "dest": "Cotte de mailles", "cost": 30},
]

METHOD_CLEAN = {
    "forging": "Forge",
    "brewing": "Alchimie",
    "crafting": "Artisanat",
}

EMOJI_BY_METHOD = {
    "Forge": "⚒️",
    "Alchimie": "⚗️",
    "Artisanat": "🛠️",
}

COLOR_BY_RARITY_LOOTBOX = {
    1: discord.Color.light_grey(),
    2: discord.Color.green(), 
    3: discord.Color.blue(),
    4: discord.Color.purple(),  
    5: discord.Color.orange(),  
    6: discord.Color.gold(),  
}

RARITY_CLEAN_ITEM = {
    "common": "Commun",
    "uncommon": "Peu commun",
    "rare": "Rare",
    "epic": "Épique",
    "legendary": "Légendaire",
    "mythic": "Mythique",
    "unknown": "???",
}

COLOR_BY_RARITY_ITEM = {
    "common": discord.Color.light_grey(),
    "uncommon": discord.Color.green(),
    "rare": discord.Color.blue(),
    "epic": discord.Color.purple(),
    "legendary": discord.Color.orange(),
    "mythic": discord.Color.gold(),
    "unique": discord.Color.yellow(),
    "unknown": discord.Color.red(),
}


BG_COLOR  = '#1a1a2e'
TEAL      = '#5DCAA5'
TEAL_DIM  = '#2a6e5a'

VOWELS = "aeiouyàâäéèêëîïôùûüæœhAEIOUYÀÂÄÉÈÊËÎÏÔÙÛÜÆŒH"

ITEMS_PER_PAGE = 25

COLOR_NPC = 0x8B6914
COLOR_QUEST = 0xD4A017
COLOR_SUCCESS = 0x4CAF50
COLOR_ERROR = 0xE53935

ROLE_ICONS = {
    "quest_giver": "📜",
    "merchant": "🛒",
    "blacksmith": "⚒️",
    "black_market_dealer": "🌘",
}

ROLE_CLEAN = {
    "quest_giver": "Donneur de quête",
    "merchant": "Marchand",
    "blacksmith": "Forgeron",
    "black_market_dealer": "Marchand du marché noir"
}

SPECIALTY_TAGS_BONUS = {
    "armorer": {"armurerie": 15, "document":-10, "artefact": 8, "outil": 5, "consommable": -5},
    "alchemist": {"consommable": 15, "ressource":8, "armurerie": -5},
    "potion": {"consommable": 15, "ressource": 3},
    "materials": {"ressource": 15, "consommable": -5, "armurerie": -5, "artefact": -5},
    "trapper": {"ressource": 10, "consommable": 5, "armurerie": -5},
    "cartographer": {"document": 15, "consommable": -5, "armurerie": -5, "artefact": -5},
}

PLAYER_COLORS = {
    'Achille'   :  '#6ABF4B',  # vert poison
    'Altaïr'    :  '#D8D8D8',  # blanc grisé
    'Jules'     :  '#4A4A4A',  # gris foncé
    'Justin'    :  '#D4A017',  # doré
    'Léa'       :  '#1A1A1A',  # noir
    'Louanne'   :  '#4A0072',  # violet foncé
    'Louise'    :  '#2E7D32',  # vert nature
    'Marine'    :  '#F06292',  # rose
}

PLAYER_INITIALS = {
    'Achille'   : 'AC',
    'Altaïr'    : 'AI',
    'Jules'     : 'JL',
    'Justin'    : 'JS',
    'Léa'       : 'LÉ',
    'Louanne'   : 'LN',
    'Louise'    : 'LI',
    'Marine'    : 'MA',
}

RUNES_COST = {
    "rare": 25,
    "epic": 55,
    "legendary": 100,
    "mythic": 150,
}

SET_RESOURCE_MAX_MAP = {
    "HP max": "hp",
    "Mana max": "mana",
    "Stamina max": "stamina",
}

SETS = {
    "ghost": {
        "name": "Set du Fantôme",
        "lore": "Deux lames taillées dans le même cristal de portail, par la même main, lors d'une seule nuit dont personne ne connaît la date. Elles ne font pas de bruit. Elles ne reflètent pas la lumière. Ceux qui les ont portées ensemble n'ont généralement pas été revus.",
        "items": ["Éclat fantôme", "Lame fantôme"],
        "bonuses": {
            "Attaque": 1,
            "Infiltration": 1,
        }
    },
    "king": {
        "name": "Set du Roi",
        "lore": "La couronne et le sceptre d'un souverain dont le nom a été effacé de chaque registre, chaque chronique, chaque pierre gravée. Portés ensemble, ils ne font pas que décorer : ils rappellent à ceux qui les voient qu'il y a quelqu'un ici qui décide, et que ce n'est pas eux.",
        "items": ["Sceptre du Souverain Oublié", "Couronne de fer blanc"],
        "bonuses": {
            "Charisme": 1,
            "Mana max": 20,
        }
    },
    "frost_ash": {
        "name": "Set Cendre et Givre",
        "lore": "La faux détruit par la chaleur et le mouvement. L'orbe détruit par le froid et l'immobilité. Deux objets qui n'ont aucune raison d'aller ensemble, sauf que le résultat est toujours le même : il ne reste rien.",
        "items": ["Faux de cendre", "Cœur de givre"],
        "bonuses": {
            "Résistance": 1,
            "Attaque": 1,
            "HP max": 10,
        }
    },
    "fallen_knight": {
        "name": "Set du Chevalier Déchu",
        "lore": "Un ordre entier réduit à deux lames. La grande pour ceux qui ne doutaient plus de rien. La courte pour ceux qui n'avaient plus rien à perdre. Portées ensemble, elles portent le poids de tout ce que cet ordre a commis avant de tomber.",
        "items": ["Épée courte de Chevalier", "Épée enflammée du Chevalier"],
        "bonuses": {
            "Attaque": 2,
        }
    },
    "hunter": {
        "name": "Set du Chasseur",
        "lore": "L'arc pour frapper de loin. La veste pour ne pas être touché en retour. Conçus ensemble par quelqu'un qui avait compris que la meilleure façon de survivre à une chasse était de ne jamais laisser la proie devenir le chasseur.",
        "items": ["Arc du Chasseur", "Veste du Chasseur"],
        "bonuses": {
            "Perception": 2,
        }
    }
}

# --------------------------------------------
# ----------------  UTILS  -------------------
# --------------------------------------------

def _clean(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def _normalize(value: str) -> str:
    return value.strip().casefold()


def _parse_bool(value: str | None) -> bool:
    raw = _clean(value).casefold()
    return raw in {"1", "true", "yes", "y", "oui", "vrai"}


def _parse_int(value: str | None) -> int | None:
    raw = _clean(value)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _extract_stat_bonuses(value: str) -> dict[str, int]:
    """Extract dynamic stat bonuses from CSV column."""
    stat_bonuses: dict[str, int] = {}

    for stat in value.split(","):
        parts = stat.split(":")
        if len(parts) == 2:
            stat_name = parts[0].strip().casefold()
            bonus = _parse_int(parts[1])
            if stat_name in STATS_CLEAN and bonus is not None:
                stat_bonuses[STATS_CLEAN[stat_name]] = bonus
            else:
                logger.warning(f"Invalid stat bonus format '{stat}' or unknown stat '{stat_name}'")

    force = stat_bonuses.get("Force")
    agilite = stat_bonuses.get("Agilité")
    discretion = stat_bonuses.get("Discrétion")
    
    # attaque = ceil((2*(force+1)+agilite)/3)
    if isinstance(force, int) and isinstance(agilite, int):
        stat_bonuses["Attaque"] = math.ceil((2 * (force + 1) + agilite) / 3)

    # infiltration = floor((((discretion+2)*2)+((agilite-1)*2))/4)
    if isinstance(discretion, int) and isinstance(agilite, int):
        stat_bonuses["Infiltration"] = math.floor((((discretion + 2) * 2) + ((agilite - 1) * 2)) / 4)

    return stat_bonuses


def _extract_craft_bonuses(value: str) -> dict[str, int]:
    """Extract dynamic craft bonuses from CSV column."""
    craft_bonuses: dict[str, int] = {}

    for bonus in value.split(","):
        parts = bonus.split(":")
        if len(parts) == 2:
            method_name = parts[0].strip().casefold()
            bonus_value = _parse_int(parts[1])
            if method_name in METHOD_CLEAN and bonus_value is not None:
                craft_bonuses[METHOD_CLEAN[method_name]] = bonus_value
            else:
                logger.warning(f"Invalid craft bonus format '{bonus}' or unknown method '{method_name}'")
    
    return craft_bonuses


def _extract_upgrades(value: str) -> dict[int, list[list]]:
    """Extract dynamic upgrade levels from CSV column."""
    upgrades: dict[int, list[list]] = {}
    for lvl_upgrade in value.split(","):
        upgrade = lvl_upgrade.split(":")
        try:
            lvl = int(upgrade[0])
        except (ValueError, IndexError):
            logger.warning(f"Invalid level in upgrades: '{lvl_upgrade}'")
            continue
        changes = []
        for change in upgrade[1].split("|"):
            parts = change.split("+")
            key = parts[0]
            try:
                val = int(parts[1])
            except (ValueError, IndexError):
                logger.warning(f"Invalid stat change value in upgrades: '{change}'")
                continue
            if key.endswith("_max"):
                # bonus de ressource max, pas de validation STATS_CLEAN
                changes.append([key, val])
            elif key in STATS_CLEAN:
                changes.append([STATS_CLEAN[key], val])
            else:
                logger.warning(f"Unknown stat '{key}' in upgrades")
        if changes:
            upgrades[lvl] = changes
    return upgrades


def _extract_tags(value: str) -> list[str]:
    """Extract dynamic tags from CSV column."""
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def _extract_power_use_effect(value: str) -> dict[str, int]:
    """Extract dynamic power use effects from CSV column."""
    effects: dict[str, int] = {}

    for effect in value.split(","):
        stat_change = effect.split(":")
        if _normalize(stat_change[0]) not in BUFF_CLEAN:
            logger.warning(f"Unknown stat '{stat_change[0]}' in use_effect")
            continue
        try:
            stat_change[1] = int(stat_change[1])
        except (ValueError, IndexError):
            logger.warning(f"Invalid value in power use_effect: '{effect}'")
            continue
        effects[BUFF_CLEAN.get(_normalize(stat_change[0]))] = stat_change[1]

    return effects


def _extract_item_use_effect(value: str) -> dict[str, int, int]:
    """Extract dynamic item use effects from CSV column."""
    effects: dict[str, int, int] = {}

    if value == "relic_use":
        effects["relic_use"] = True
        return effects

    for effect in value.split(","):
        stat_change = effect.split(":")
        if _normalize(stat_change[0]) not in BUFF_CLEAN:
            logger.warning(f"Unknown stat '{stat_change[0]}' in use_effect")
            continue
        try:
            stat_change[1] = int(stat_change[1])
            stat_change[2] = int(stat_change[2])
        except (ValueError, IndexError):
            logger.warning(f"Invalid value in item use_effect: '{effect}'")
            continue
        effects[BUFF_CLEAN.get(_normalize(stat_change[0]))] = (stat_change[1], stat_change[2])

    return effects


def _extract_equipped_bonus(value: str) -> dict[str, int]:
    """Extract dynamic equipped bonuses from CSV column."""
    bonuses: dict[str, int] = {}
    for bonus in value.split(","):
        stat_change = bonus.split(":")
        normalized = _normalize(stat_change[0])
        try:
            bonuses[normalized] = int(stat_change[1])
        except (ValueError, IndexError):
            logger.warning(f"Invalid equipped bonus format: '{bonus}'")
    return bonuses


def _extract_buff_effects(value: str) -> dict[str, int, int]:

    effects: dict[str, [int, int]] = {}


    for effect in value.split(","):
        parts = effect.split(":")
        if len(parts) == 3 and _normalize(parts[0]) in BUFF_CLEAN:
            stat = BUFF_CLEAN[_normalize(parts[0])]
            try:
                bonus = int(parts[1])
                duration = int(parts[2])
            except ValueError:
                logger.warning(f"Invalid buff effect values: '{effect}'")
                continue
            effects[stat] = (bonus, duration)
        if len(parts) == 2 and _normalize(parts[0]) in ["hp", "mana", "stamina"]:
            stat = BUFF_CLEAN[_normalize(parts[0])]
            try:
                bonus = int(parts[1])
            except ValueError:
                logger.warning(f"Invalid buff effect value: '{effect}'")
                continue
            duration = -1
            effects[stat] = (bonus, duration)

    return effects


def _extract_target_effect(value: str) -> dict[str, tuple[int, int, int]]:
    """Extract target effects from CSV column.

    Format: ``stat:bonus:duration:count`` where duration=-1 means instant
    (resource change) and count=-1 means all active players, count=1 means
    a single chosen ally.
    """
    effects: dict[str, tuple[int, int, int]] = {}
    for effect in value.split(","):
        parts = effect.strip().split(":")
        if len(parts) != 4:
            logger.warning(f"Invalid target_effect format (expected 4 parts): '{effect}'")
            continue
        stat_raw, bonus_raw, duration_raw, count_raw = parts
        stat = BUFF_CLEAN.get(_normalize(stat_raw))
        if not stat:
            logger.warning(f"Unknown stat '{stat_raw}' in target_effect")
            continue
        try:
            bonus = int(bonus_raw)
            duration = int(duration_raw)
            count = int(count_raw)
        except ValueError:
            logger.warning(f"Invalid values in target_effect: '{effect}'")
            continue
        effects[stat] = (bonus, duration, count)
    return effects


def _extract_ingredients(value: str) -> list[dict]:
    """Extract dynamic crafting ingredients from CSV column."""
    ingredients: list[dict] = []

    if value:
        for ingredient in value.split(","):
            parts = ingredient.split(":")
            if len(parts) == 2:
                item_name = parts[0].strip()
                try:
                    quantity = int(parts[1].strip())
                except ValueError:
                    logger.warning(f"Invalid ingredient quantity in '{ingredient}'")
                    continue
                ingredients.append({"item": item_name, "quantity": quantity})
            else:
                logger.warning(f"Invalid ingredient format '{ingredient}'")

    return ingredients


def _extract_lootbox_items(value: str) -> list[tuple[str, tuple[int, int]]]:
    """Extract dynamic lootbox items from CSV column."""
    items: list[tuple[str, tuple[int, int]]] = []

    if value:
        for item in value.split(","):
            parts = item.split(":")
            if len(parts) == 3:
                item_name = parts[0].strip()
                try:
                    quantity = int(parts[1])
                    rarity = int(parts[2])
                except ValueError:
                    logger.warning(f"Invalid lootbox item format: '{item}'")
                    continue
                items.append((item_name, (quantity, rarity)))

    return items


def _get_active_sets(character: "Character") -> list[dict]:
    """Returns the list of SETS that the character has fully equipped."""
    equipped_names = {entry.item.name.lower() for entry in character.inventory.get_equipped_items()}
    return [
        set_info for set_info in SETS.values()
        if all(item.lower() in equipped_names for item in set_info["items"])
    ]


def _get_stat_bonus(called_stat: str, character: "Character") -> (int, int, int):
    """
    Calculate the total bonus for a given stat based on character's base stats, level upgrades and equipped items. 

    Parameters
    ----------
    called_stat : str
        The stat for which to calculate the bonus.
    character : Character
        The character for whom to calculate the bonus.

    Returns
    -------
    int
        The total bonus for the given stat.
    """    
    stat_bonus = character.stat_points.get(called_stat, 0)

    level_bonus = {}

    for lvl in range(1, character.level + 1):
        if lvl in character.level_upgrades:
            for stat_change in character.level_upgrades[lvl]:  # itère sur la liste
                if stat_change[0] in level_bonus:
                    level_bonus[stat_change[0]] += stat_change[1]
                else:
                    level_bonus[stat_change[0]] = stat_change[1]
    
    stat_level_bonus = level_bonus.get(called_stat, 0)

    item_bonus = {}
    equipped_entries = character.inventory.get_equipped_items()
    for entry in equipped_entries:
        item, qty = entry.item, entry.equipped_quantity
        for stat, bonus in item.equipped_bonus.items():
            clean = STATS_CLEAN.get(stat, stat)
            item_bonus[clean] = item_bonus.get(clean, 0) + bonus * qty
        for rune in entry.runes:
            for stat, bonus in rune.equipped_bonus.items():
                clean = STATS_CLEAN.get(stat, stat)
                item_bonus[clean] = item_bonus.get(clean, 0) + bonus

    stat_item_bonus = item_bonus.get(called_stat, 0)

    for set_info in _get_active_sets(character):
        for stat, bonus in set_info["bonuses"].items():
            if stat not in SET_RESOURCE_MAX_MAP and stat == called_stat:
                stat_item_bonus += bonus

    buff_bonus = sum(
        buff.effects.get(called_stat, 0)
        for buff in character.buffs
    )

    return stat_bonus, stat_level_bonus, stat_item_bonus, buff_bonus


def _get_resource_max_bonus(resource: str, character: "Character") -> tuple[int, int, int]:
    """
    Calculate the resource max bonuses from all sources.
    Parameters
    ----------
    resource : str
        The resource for which to calculate the bonus (ex: "hp", "mana", "stamina").
    character : Character
        The character for whom to calculate the bonus.
    Returns
    -------
    tuple[int, int, int]
        (base, level_bonus, item_bonus)
    """
    base = character.resources_max.get(resource, 0)

    key = f"{resource}_max"
    level_bonus = 0
    for lvl in range(1, character.level + 1):
        if lvl in character.level_upgrades:
            for stat_change in character.level_upgrades[lvl]:
                if stat_change[0] == key:
                    level_bonus += stat_change[1]

    item_bonus = 0
    for entry in character.inventory.get_equipped_items():
        item_bonus += entry.item.equipped_bonus.get(key, 0) * entry.equipped_quantity
        for rune in entry.runes:
            item_bonus += rune.equipped_bonus.get(key, 0)

    for set_info in _get_active_sets(character):
        for stat, bonus in set_info["bonuses"].items():
            if SET_RESOURCE_MAX_MAP.get(stat) == resource:
                item_bonus += bonus

    

    return base, level_bonus, item_bonus


def de_du_nom(name: str) -> str:
    return f"d'{name}" if name[0] in VOWELS else f"de {name}"


# --------------------------------------------
# ------------  DISCORD UTILS  ---------------
# --------------------------------------------


def _send_embed(interaction: discord.Interaction, embed: discord.Embed):
    """
    Envoie un embed en réponse à une interaction.

    Parameters
    ----------
    interaction : discord.Interaction
        L'interaction à laquelle répondre.
    embed : discord.Embed
        L'embed à envoyer.

    """ 
    return interaction.response.send_message(embed=embed)


# --------------------------------------------
# --------------  DICE UTILS  ----------------
# --------------------------------------------


def parse_dice(expression: str) -> dict:
    expression = expression.strip().lower()
    pattern = r"(\d+d\d+)|([+-]\d+)"
    matches = re.findall(pattern, expression)
    if not matches:
        raise ValueError("Format invalide. Utilise: 1d20+2 ou 2d6-1")
    dice, modifier = [], 0
    for dice_match, mod_match in matches:
        if dice_match:
            num, faces = map(int, dice_match.split("d"))
            if num <= 0 or faces <= 0:
                raise ValueError("Le nombre de dés et de faces doit être > 0")
            dice.append((num, faces))
        elif mod_match:
            modifier += int(mod_match)
    return {"dice": dice, "modifier": modifier}


def roll_dice(expression: str) -> dict:
    parsed = parse_dice(expression)
    results, total = [], 0
    for num, faces in parsed["dice"]:
        rolls = [random.randint(1, faces) for _ in range(num)]
        subtotal = sum(rolls)
        results.append({"expression": f"{num}d{faces}", "rolls": rolls, "subtotal": subtotal})
        total += subtotal
    base_total = total
    total += parsed["modifier"]
    return {"results": results, "modifier": parsed["modifier"], "base_total": base_total, "total": total}


def get_outcome(roll_result: dict) -> str:
    natural_roll = roll_result["results"][0]["rolls"][0]
    faces = int(roll_result["results"][0]["expression"].split("d")[1])
    modifier = roll_result["modifier"]

    if natural_roll == 1 and modifier > 0:
        return "saved_fail"
    elif natural_roll == 1:
        return "critical_fail"
    elif natural_roll == faces and modifier < 0:
        return "cancelled_success"
    elif natural_roll == faces:
        return "critical_success"
    else:
        return "normal"


def get_base_outcome(roll_result: dict) -> str:
    natural_roll = roll_result["results"][0]["rolls"][0]
    faces = int(roll_result["results"][0]["expression"].split("d")[1])

    if natural_roll == 1:
        return "critical_fail"
    elif natural_roll == faces:
        return "critical_success"
    else:
        return "normal"


def get_craft_outcome(roll_result: dict, has_failure: bool = False, has_success: bool = False) -> str:
    natural_roll = roll_result["results"][0]["rolls"][0]
    faces = int(roll_result["results"][0]["expression"].split("d")[1])
    modifier = roll_result["modifier"]
    total = roll_result["total"]


    if natural_roll == 1 and has_failure:
        return "natural_failure"
    elif natural_roll == faces and has_success:
        return "natural_success"
    elif total <= 1 and has_failure:
        return "critical_failure"
    elif total < faces * 0.75:
        return "normal"
    elif total < faces:
        return "success"
    elif total >= faces and has_success:
        return "critical_success"
    else:
        return "normal" if total < faces * 0.75 else "success"


def clean_dice_summary(summary: dict[str, dict]) -> dict[str, tuple]:
    """Clean the summary by replacing keys with their cleaned versions."""
    summary_cleaned = {}
     # Filter to only active rollers
    active = {name: data for name, data in summary.items() if data['total_rolls'] > 0}

    # Best/worst base roller (by average_base_total)
    best_roller  = max(active, key=lambda n: active[n]['average_base_total'])
    worst_roller = min(active, key=lambda n: active[n]['average_base_total'])

    summary_cleaned['best_roller'] = (best_roller, np.round(active[best_roller]['average_base_total'], 2))
    summary_cleaned['worst_roller'] = (worst_roller, np.round(active[worst_roller]['average_base_total'], 2))

    # Most dice rolled
    most_rolls = max(active, key=lambda n: active[n]['total_rolls'])

    summary_cleaned['most_rolls'] = (most_rolls, active[most_rolls]['total_rolls'])

    # Most of each outcome
    for outcome in ('natural_success', 'critical_success', 'critical_fail', 'natural_fail'):
        candidates = {name: data['outcomes'].get(outcome, 0) for name, data in active.items()}
        top_count = max(candidates.values())
        if top_count == 0:
            summary_cleaned[f"most_{outcome}"] = (None, 0)
        else:
            top = [name for name, count in candidates.items() if count == top_count]
            summary_cleaned[f"most_{outcome}"] = (top[0], top_count)
        
    return summary_cleaned



# --------------------------------------------
# --------------  NPC UTILS  ----------------
# --------------------------------------------


def roles_display(roles: list[str]) -> str:
    return "  ".join(f"{ROLE_ICONS.get(r, r)} {ROLE_CLEAN.get(r, r)}" for r in roles)


def make_score_curve():
    # Résolution de k : 99 * (50/99)^k + 1 = 75
    # → (50/99)^k = 74/99
    # → k = ln(74/99) / ln(50/99)
    k = math.log(74 / 99) / math.log(50 / 99)
    return k


K = make_score_curve()  # ≈ 0.4258

def price_offer(x: float) -> float:
    """
    Transforme une valeur en entrée [1, 100] en une valeur [1, 100].
    Décroissante et non-linéaire : f(1)=100, f(50)=75, f(100)=1.
    """
    if not (1 <= x <= 100):
        raise ValueError("x doit être entre 1 et 100")
    return int(99 * ((100 - x) / 99) ** K + 1)


# ── Bot bio ──────────────────────────────────────────────────────────────────

async def update_bot_status(bot) -> None:
    """Met à jour le statut du bot avec les joueurs par salon vocal."""
    from utils.path import PLAYER_VOICE_CHANNELS
    from utils.locations import LOCATIONS

    realm, city = bot.location.get_location()

    if realm and city:
        location_str = f"{city}"
    elif realm:
        location_str = realm
    else:
        location_str = "Localisation inconnue"

    parts = []
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            if channel.name not in PLAYER_VOICE_CHANNELS:
                continue
            chars = []
            for member in channel.members:
                char = bot.character_repository.get_character_by_user_id(member.id)
                if char and char.name != "Rémy":
                    chars.append(char.name)
            if chars:
                parts.append(f"{channel.name} : {', '.join(chars)}")

    status = f"{location_str} | " + " | ".join(parts) if parts else f"{location_str} | Aucun joueur connecté."
    await bot.change_presence(activity=discord.Game(name=status))

