import discord
import datetime
import os
import random

from typing import TYPE_CHECKING, List, Optional
if TYPE_CHECKING:
    from instance.character import Character
    from instance.item import Item
    from instance.inventory import InventoryEntry
    from instance.lootbox import LootBox
    from instance.craft import Craft

from utils.path import ASSETS_FOLDER
from utils.utils import (
    STATS_CLEAN,
    SLOTS_CLEAN,
    COLOR_BY_RARITY_ITEM,
    RARITY_CLEAN_ITEM,
    SET_RESOURCE_MAX_MAP,
    SETS,
    de_du_nom,
)
from utils.variations_item import ITEM_NOTIFICATION_VARIATIONS


def _generate_item_embed(item: "Item", entry: "Optional[InventoryEntry]" = None, ingredient_for: list["Craft"] = None, product_of: list["Craft"] = None, character: "Optional[Character]" = None) -> (discord.Embed, discord.File):
    """
        Génère un embed Discord contenant les informations d'un objet.

    Parameters
    ----------
    item : Item
        L'objet dont les informations doivent être affichées.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations de l'objet.
    """
    description = item.description if item.description else "Aucune description disponible."
    slot_clean = item.equippable_slot if item.equippable_slot else "Aucun"

    color = discord.Color.dark_red() if item.forbidden else COLOR_BY_RARITY_ITEM.get(item.rarity, discord.Color.light_gray())

    embed = discord.Embed(
        title=f"{item.name}",
        description=description,
        color=color,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="🏷️ Rareté", value=RARITY_CLEAN_ITEM.get(item.rarity, item.rarity), inline=True)
    if item.forbidden:
        tradeable_value = "⚠️ Marché noir uniquement"
    else:
        tradeable_value = "Oui" if item.tradeable else "Non"
    embed.add_field(name="🤝 Échangeable", value=tradeable_value, inline=True)

    if item.forbidden:
        value_display = f"~~{item.value}~~ *(non coté)*" if item.value > 0 else "Non coté"
    else:
        value_display = f"{item.value}" if item.value > 0 else "Aucune valeur marchande"
    embed.add_field(name="💰 Valeur marchande", value=value_display, inline=True)

    if item.useable:
        embed.add_field(name="🔨 Utilisable", value="Oui" if item.useable else "Non", inline=True)
        numeric_effects = {k: v for k, v in item.use_effects.items() if not isinstance(v, bool)}
        use_effect_display = "".join(f"- {stat}: {'+' if bonus[0] >= 0 else ''}{bonus[0]} {f'| {bonus[1]} tours' if bonus[1] > 0 else ''}\n" for stat, bonus in numeric_effects.items()) if numeric_effects else "Effet spécial"
        embed.add_field(name="✨ Effet à l'utilisation", value=use_effect_display, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

    if item.equippable:
        embed.add_field(name="🛡️ Équipable", value=f"{SLOTS_CLEAN.get(slot_clean, slot_clean)}" if item.equippable else "Non", inline=True)
        bonus_display = "\n".join(f"- {STATS_CLEAN.get(stat, stat)}: +{bonus}" for stat, bonus in item.equipped_bonus.items()) if item.equipped_bonus else "Aucun"
        embed.add_field(name=f"⚔️ Bonus équipé{'s' if len(item.equipped_bonus) > 1 else ''}", value=bonus_display, inline=True)
        if item.rune_slots > 0:
            if entry is not None:
                slots_used = len(entry.runes)
                if entry.runes:
                    rune_lines = "\n".join(
                        f"• **{rune.name}** — " + (
                            "\n".join(f"{STATS_CLEAN.get(s, s)}: +{b}" for s, b in rune.equipped_bonus.items()) or "aucun bonus"
                        )
                        for rune in entry.runes
                    )
                    embed.add_field(
                        name=f"💎 Runes ({slots_used}/{item.rune_slots})",
                        value=rune_lines,
                        inline=False,
                    )
                else:
                    embed.add_field(name=f"💎 Runes (0/{item.rune_slots})", value="Aucune rune enchâssée", inline=False)
            else:
                embed.add_field(name=f"💎 Slots de rune", value=str(item.rune_slots), inline=False)

    if item.is_rune:
        embed.add_field(name="💎 Bonus", value="\n".join(f"- {STATS_CLEAN.get(stat, stat)}: +{bonus}" for stat, bonus in item.equipped_bonus.items()), inline=False)
    

    if ingredient_for and len(ingredient_for) > 0:
        ingredient_lines = "\n".join(f"• {craft.name}" for craft in ingredient_for)
        embed.add_field(name="🔧 Ingrédient pour", value=ingredient_lines, inline=True)

    if product_of and len(product_of) > 0:
        product_lines = "\n".join(f"• {craft.name}" for craft in product_of)
        embed.add_field(name="🔨 Produit par", value=product_lines, inline=True)

    if item.forbidden:
        embed.add_field(
            name="🌑 Objet banni",
            value="*Aucun sceau officiel ne couvre cet objet. Ce qui arrive ensuite ne regarde que vous, et votre conscience...*",
            inline=False
        )

    if item.set_name and character is not None:
        set_info = SETS.get(item.set_name)
        if set_info:
            is_discovered = item.set_name in character.discovered_sets
            inventory_names = {e.item.name.lower() for e in character.inventory.entries if e.quantity > 0}
            has_all_in_inventory = all(s.lower() in inventory_names for s in set_info["items"])
            if is_discovered or has_all_in_inventory:
                bonus_line = f"[{', '.join(f' {stat}: +{bonus}' for stat, bonus in set_info['bonuses'].items())}]"
                other_item = [i for i in set_info["items"] if i.lower() != item.name.lower()]
                embed.add_field(
                    name=f"✨ {set_info['name']} avec {', '.join(other_item)} - {bonus_line}",
                    value=f"{set_info['lore']}",
                    inline=False,
                )

    if item.tags:
        embed.set_footer(text=f"Tag{'s' if len(item.tags) > 1 else ''}: {', '.join(item.tags)}")


    file = None
    if item.image_path:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if "map" in item.tags:
            img_path = os.path.join(project_root, ASSETS_FOLDER, "maps", f"{item.image_path}.png")
            attach_name = "map.png"
            set_fn = embed.set_image
        else:
            img_path = os.path.join(project_root, ASSETS_FOLDER, "items", f"{item.image_path}.png")
            attach_name = "thumbnail.png"
            set_fn = embed.set_thumbnail

        if os.path.isfile(img_path):
            file = discord.File(img_path, filename=attach_name)
            set_fn(url=f"attachment://{attach_name}")

    return embed, file


def _generate_set_potential_embed(set_info: dict) -> discord.Embed:
    """Embed narratif envoyé quand le joueur possède tous les items d'un set sans l'avoir encore découvert."""
    bonus_line = ", ".join(f"{stat} +{bonus}" for stat, bonus in set_info["bonuses"].items())
    items_list = "\n".join(f"• {item}" for item in set_info["items"])
    embed = discord.Embed(
        title=f"🔍 Un set se dessine...",
        description=set_info["lore"],
        color=discord.Color.from_rgb(180, 140, 60),
        timestamp=datetime.datetime.now(),
    )
    embed.add_field(name="Objets du set", value=items_list, inline=True)
    embed.add_field(name="Bonus potentiels", value=bonus_line, inline=True)
    embed.set_footer(text=f"Équipe tous les objets pour découvrir le set « {set_info['name']} »")
    return embed


def _generate_set_discovery_embed(set_info: dict) -> discord.Embed:
    """Embed narratif envoyé quand le joueur découvre un set en équipant tous ses items."""
    bonus_lines = "\n".join(f"• {stat} : +{bonus}" for stat, bonus in set_info["bonuses"].items())
    embed = discord.Embed(
        title=f"✨ Set découvert : {set_info['name']}",
        description=set_info["lore"],
        color=discord.Color.gold(),
        timestamp=datetime.datetime.now(),
    )
    embed.add_field(name="Bonus actifs", value=bonus_lines, inline=False)
    return embed


def _generate_item_equip_embed(item: "Item", character: "Character", unequipped: bool) -> (discord.Embed, discord.File):
    """
        Génère un embed Discord contenant les informations sur un objet équippé.

    Parameters
    ----------
    item : Item
        L'objet équippé.
    character : Character
        Le personnage qui a équipé l'objet.
    unequipped : bool
        Indique si l'objet est déséquippé.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations de l'objet équippé.
    """
    # Couleur et titre selon l'action
    if unequipped:
        color = discord.Color.dark_gray()
        title = f"🗃️ {item.name} déséquipé"
        action_label = "Retiré de"
    else:
        color = discord.Color.gold()
        title = f"⚔️ {item.name} équipé !"
        action_label = "Placé dans"

    embed = discord.Embed(title=title, description=item.description, color=color)

    # Emplacement
    embed.add_field(
        name="Emplacement",
        value=f"{action_label} : **{item.equippable_slot}**",
        inline=False
    )

    # Bonus d'équipement
    if item.equipped_bonus:
        sign = -1 if unequipped else 1
        bonus_lines = [
            f"`{STATS_CLEAN.get(stat, stat).upper()}` {sign * value:+d}"
            for stat, value in item.equipped_bonus.items()
        ]
        embed.add_field(
            name="Bonus" if not unequipped else "Bonus perdus",
            value="\n".join(bonus_lines),
            inline=True
        )

    # Tags
    if item.tags:
        embed.add_field(
            name="Tags",
            value=" · ".join(f"*{tag}*" for tag in item.tags),
            inline=True
        )


    embed.set_footer(text=f"Inventaire de {character.name}")


    file = None
    if item.image_path:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        thumbnail_path = os.path.join(project_root, ASSETS_FOLDER, "items", f"{item.image_path}.png")

        if os.path.isfile(thumbnail_path):
            file = discord.File(thumbnail_path, filename="thumbnail.png")
            embed.set_thumbnail(url="attachment://thumbnail.png")

    return embed, file


def _generate_item_discard_embed(item: "Item", character: "Character", quantity: int) -> (discord.Embed, discord.File):
    """
        Génère un embed Discord contenant les informations sur un objet jeté.

    Parameters
    ----------
    item : Item
        L'objet jeté.
    character : Character
        Le personnage qui a jeté l'objet.
    quantity : int
        La quantité de l'objet jetée.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations de l'objet jeté.
    """
    embed = discord.Embed(
        title=f"🗑️ {item.name} jeté !",
        description=item.description,
        color=discord.Color.red()
    )

    embed.add_field(
        name="Quantité",
        value=f"{quantity} x {item.name}",
        inline=False
    )

    embed.set_footer(text=f"Inventaire de {character.name}")

    file = None
    if item.image_path:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        thumbnail_path = os.path.join(project_root, ASSETS_FOLDER, "items", f"{item.image_path}.png")

        if os.path.isfile(thumbnail_path):
            file = discord.File(thumbnail_path, filename="thumbnail.png")
            embed.set_thumbnail(url="attachment://thumbnail.png")

    return embed, file


def _generate_item_trade_embed(giver: "Character", receiver: "Character", item: "Item", quantity: int) -> (discord.Embed, discord.File):
    """
        Génère un embed Discord contenant les informations sur un objet échangé entre deux personnages.

    Parameters
    ----------
    giver : Character
        Le personnage qui donne l'objet.
    receiver : Character
        Le personnage qui reçoit l'objet.
    item : Item
        L'objet échangé.
    quantity : int
        La quantité de l'objet échangée.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations de l'objet échangé.
    """
    embed = discord.Embed(
        title="🤝 Échange d'objet",
        description=f"**{giver.name}** a donné **{quantity}x {item.name}** à **{receiver.name}**.",
        color=discord.Color.gold(),
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="📦 Objet", value=item.name, inline=True)
    embed.add_field(name="🔢 Quantité", value=str(quantity), inline=True)
    embed.add_field(name="💰 Valeur totale", value=f"{item.value * quantity}", inline=True)
    embed.add_field(name="📜 Description", value=item.description or "Aucune description.", inline=False)
    embed.set_footer(text=f"{giver.name} → {receiver.name}")


    file = None
    if item.image_path:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        thumbnail_path = os.path.join(project_root, ASSETS_FOLDER, "items", f"{item.image_path}.png")

        if os.path.isfile(thumbnail_path):
            file = discord.File(thumbnail_path, filename="thumbnail.png")
            embed.set_thumbnail(url="attachment://thumbnail.png")

    return embed, file


def _generate_item_use_embed(item: "Item", character: "Character", buff_dicts: list, auto_decrement: bool) -> (discord.Embed, discord.File):
    """
        Génère un embed Discord narratif lors de l'utilisation d'un objet.

    Parameters
    ----------
    item : Item
        L'objet utilisé.
    character : Character
        Le personnage qui utilise l'objet.
    buff_dicts : list
        La liste des dictionnaires de buffs à appliquer.

    Returns
    -------
    discord.Embed, discord.File
        L'embed Discord narratif décrivant l'utilisation de l'objet.
    """
    embed = discord.Embed(
        title=f"🧪 {item.name} utilisé !",
        description=item.use_description or item.description,
        color=COLOR_BY_RARITY_ITEM.get(item.rarity, discord.Color.light_gray())
    )

    instant_lines = []
    buffs = []

    for d in buff_dicts:
        effects = d.get("effects", {})
        if not effects:
            continue

        duration = d.get("duration", 0)

        if duration > 0:
            # Buff temporaire
            for effect, value in effects.items():
                sign = "+" if value >= 0 else "-"
                buffs.append({
                    "name": f"`{effect.upper()}` {sign}{value}",
                    "value": f"Durée : {duration} tour{'s' if duration > 1 else ''}",
                    "inline": True
                })
        else:
            # Effet instantané
            for effect, value in effects.items():
                sign = "+" if value >= 0 else "-"
                if effect.lower() in ["hp", "mana", "stamina"]:
                    current = character.resources.get(effect.lower(), 0)
                    maximum = character.resources_max.get(effect.lower(), "?")
                    # La valeur affichée est le résultat après application
                    after = min(current, maximum) if isinstance(maximum, int) else current
                    instant_lines.append(
                        f"`{effect.upper()}` {sign}{value}  →  **{after}/{maximum}**"
                    )
                else:
                    instant_lines.append(f"`{effect.upper()}` {sign}{value}")

    if instant_lines:
        embed.add_field(
            name="⚡ Effets instantanés",
            value="\n".join(instant_lines),
            inline=False
        )

    if buffs:
        embed.add_field(
            name="🕐 Buffs appliqués",
            value="",
            inline=False
        )
        for buff in buffs:
            embed.add_field(**buff)

    if item.tags:
        embed.add_field(
            name="Tags",
            value=" · ".join(f"*{tag}*" for tag in item.tags),
            inline=False
        )

    embed.set_footer(text=f"Utilisé par {character.name}")

    file = None
    if item.image_path:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        thumbnail_path = os.path.join(project_root, ASSETS_FOLDER, "items", f"{item.image_path}.png")

        if os.path.isfile(thumbnail_path):
            file = discord.File(thumbnail_path, filename="thumbnail.png")
            embed.set_thumbnail(url="attachment://thumbnail.png")

    return embed, file


def _generate_new_item_notification_embed(
    item: "Item",
    quantity: int,
    sender: "Character" = None,
    origin: str = "admin_give",
    npc_name: str = None,
) -> (discord.Embed, discord.File):
    """
        Génère un embed Discord pour notifier un personnage de la réception d'un nouvel objet.

    Parameters
    ----------
    item : Item
        L'objet reçu.
    quantity : int
        La quantité de l'objet reçue.
    sender : Character, optional
        Le personnage qui a envoyé l'objet. Par défaut à None.
    origin : str, optional
        L'origine de l'objet : "npc_purchase", "player_gift" ou "admin_give". Par défaut à "admin_give".
    npc_name : str, optional
        Le nom du NPC vendeur (requis si origin == "npc_purchase"). Par défaut à None.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations de l'objet reçu.
    """
    qty_str = f"{quantity}x " if quantity > 1 else ""

    if origin == "npc_purchase" and npc_name:
        template = random.choice(ITEM_NOTIFICATION_VARIATIONS["npc_purchase"])
        description = template.format(
            npc=npc_name,
            de_npc=de_du_nom(npc_name),
            item=item.name,
            qty=qty_str,
        )
    elif origin == "player_gift" and sender:
        template = random.choice(ITEM_NOTIFICATION_VARIATIONS["player_gift"])
        description = template.format(
            sender=sender.name,
            de_sender=de_du_nom(sender.name),
            item=item.name,
            qty=qty_str,
        )
    else:
        template = random.choice(ITEM_NOTIFICATION_VARIATIONS["admin_give"])
        description = template.format(item=item.name, qty=qty_str)

    embed = discord.Embed(
        title="📦 Nouvel objet reçu !",
        description=description,
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )

    embed.set_footer(text=f"Nouvel objet ajouté à ton inventaire")


    file = None
    if item.image_path:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        thumbnail_path = os.path.join(project_root, ASSETS_FOLDER, "items", f"{item.image_path}.png")

        if os.path.isfile(thumbnail_path):
            file = discord.File(thumbnail_path, filename="thumbnail.png")
            embed.set_thumbnail(url="attachment://thumbnail.png")

    return embed, file


def _generate_new_item_from_lootbox_notification_embed(items: list[("Item", int)], lootbox: "LootBox") -> discord.Embed:
    """
        Génère un embed Discord pour notifier un personnage de la réception d'un nouvel objet provenant d'une lootbox.

    Parameters
    ----------
    item : [Item]
        Les objets reçus.
    quantity : [int]
        Les quantités des objets reçus.
    lootbox : LootBox
        La lootbox dont proviennent les objets.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations de l'objet reçu.
    """
    if lootbox is not None:
        lootbox_type = lootbox.type
        key = f"lootbox_{lootbox_type}" if lootbox_type in ("cadavre", "caisse", "coffre") else "admin_give"
        template = random.choice(ITEM_NOTIFICATION_VARIATIONS[key])

        if len(items) == 1:
            itm, qty = items[0]
            qty_str = f"{qty}x " if qty > 1 else ""
            items_desc = f"{qty_str}**{itm.name}**"
        else:
            items_desc = "les objets suivants :\n" + "\n".join(
                f"- **{qty}x {itm.name}**" for itm, qty in items
            )

        description = template.format(
            lootbox=lootbox.name,
            de_lootbox=de_du_nom(lootbox.name),
            le_lootbox=lootbox.name,
            items_desc=items_desc,
            item=items[0][0].name if len(items) == 1 else "",
            qty=f"{items[0][1]}x " if len(items) == 1 and items[0][1] > 1 else "",
        )
    else:
        itm, qty = items[0]
        qty_str = f"{qty}x " if qty > 1 else ""
        template = random.choice(ITEM_NOTIFICATION_VARIATIONS["admin_give"])
        description = template.format(item=itm.name, qty=qty_str)

    embed = discord.Embed(
        title="📦 Nouvel objet reçu !" if len(items) == 1 else "📦 Nouveaux objets reçus !",
        description=description,
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )

    return embed


def _generate_relic_used_embed(relic: ["Item"]) -> discord.Embed:
    """
    Génère un embed Discord pour notifier un personnage de l'utilisation d'une relique.

    Parameters
    ----------
    relic : Item
        La relique utilisée.
    character : Character
        Le personnage qui a utilisé la relique.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations sur l'utilisation de la relique.
    """
    embed = discord.Embed(
        title=relic.use_title,
        description=relic.use_description,
        color=discord.Color.gold(),
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text=relic.name)
    return embed


def _generate_item_update_history_embed(character_name: str, item_name: str, quantity: int, new_quantity: int, timestamp: datetime.datetime, is_use: bool = False) -> discord.Embed:
    """
    Génère un embed Discord pour afficher une entrée d'historique d'addition/suppression d'objet.

    Parameters
    ----------
    character_name : str
        Le nom du personnage qui a perdu l'objet.
    item_name : str
        Le nom de l'objet supprimé.
    quantity : int
        La quantité d'objet supprimée.
    new_quantity : int
        La nouvelle quantité de l'objet dans l'inventaire après suppression.
    timestamp : datetime.datetime
        L'horodatage de la suppression de l'objet.

    Returns
    -------
    discord.Embed
        L'embed Discord affichant l'entrée d'historique.
    """
    if is_use:
        title = f"✨ {character_name} a utilisé {item_name}"
        description = f"**{character_name}** a utilisé **{-quantity} x {item_name}**."
        color = discord.Color.fuchsia()
    else:
        title = f"🗑️ {item_name} supprimé de {character_name}" if quantity < 0 else f"📦 {item_name} ajouté à {character_name}"
        description = f"""
        **{abs(quantity)} x {item_name}** a été {"supprimé" if quantity < 0 else "ajouté"} de l'inventaire de **{character_name}**.
        Nouvelle quantité : {new_quantity}.
        """
        color = discord.Color.red() if quantity < 0 else discord.Color.green()

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=timestamp
    )

    return embed


def _generate_transaction_history_embed(giver_name: str, receiver_name: str, item_name: str, quantity: int, timestamp: datetime.datetime, is_gift: bool = False) -> discord.Embed:
    """
    Génère un embed Discord pour afficher une entrée d'historique de transaction d'objet entre deux personnages.

    Parameters
    ----------
    giver_name : str
        Le nom du personnage qui a donné l'objet.
    receiver_name : str
        Le nom du personnage qui a reçu l'objet.
    item_name : str
        Le nom de l'objet échangé.
    quantity : int
        La quantité d'objet échangée.
    timestamp : datetime.datetime
        L'horodatage de la transaction.

    Returns
    -------
    discord.Embed
        L'embed Discord affichant l'entrée d'historique.
    """
    title = f"🤝 {giver_name} a donné {quantity} x {item_name} à {receiver_name}"
    description = f"""
    **{giver_name}** a donné **{quantity} x {item_name}** à **{receiver_name}**.
    """

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.gold() if is_gift else discord.Color.blue(),
        timestamp=timestamp
    )

    return embed


def _notify_admin_relic_used_embed(relic: ["Item"], character: "Character") -> discord.Embed:
    """
    Génère un embed Discord pour notifier les administrateurs de l'utilisation d'une relique par un personnage.

    Parameters
    ----------
    relic : Item
        La relique utilisée.
    character : Character
        Le personnage qui a utilisé la relique.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations sur l'utilisation de la relique.
    """
    embed = discord.Embed(
        title="⚠️ Relique utilisée !",
        description=f"Le personnage **{character.name}** a utilisé la relique **{relic.name}**. \n Il attend ta décision.",
        color=discord.Color.orange(),
        timestamp=datetime.datetime.now()
    )
    return embed


def _generate_item_forbidden_embed(item: "Item") -> discord.Embed:
    """
    Génère un embed Discord pour notifier qu'un objet est interdit.

    Parameters
    ----------
    item : Item
        L'objet interdit.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations sur l'objet interdit.
    """
    embed = discord.Embed(
        title="🚫 Objet banni",
        description=f"L'objet **{item.name}** est banni et ne peut pas être échangé, du moins pas par les voies normales.",
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.now()
    )
    return embed
