import discord
import datetime

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from instance.lootbox import LootBox

from utils.utils import COLOR_BY_RARITY_LOOTBOX


def _generate_lootbox_list_embed(lootboxes: list["LootBox"]) -> discord.Embed:
    """
    _generate_lootbox_list_embed génère un embed Discord listant les lootboxes disponibles.

    Parameters
    ----------
    lootboxes : list["LootBox"]
        La liste des lootboxes à afficher.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant la liste des lootboxes disponibles.
    """
    embed = discord.Embed(title="📦 Lootboxes disponibles", color=discord.Color.gold())

    grouped: dict[str, list[str]] = {}
    for lb in lootboxes:
        grouped.setdefault(lb.type, []).append(lb.name)

    for loot_type, names in sorted(grouped.items()):
        embed.add_field(
            name=loot_type.capitalize(),
            value="\n".join(f"• {name}" for name in names),
            inline=True
        )

    return embed


def _generate_lootbox_info_embed(lootbox: "LootBox") -> discord.Embed:
    """
    _generate_lootbox_info_embed génère un embed Discord contenant les informations détaillées d'une lootbox.

    Parameters
    ----------
    lootbox : "LootBox"
        La lootbox dont les informations doivent être affichées.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations détaillées de la lootbox.
    """
    embed = discord.Embed(
        title=f"📦 {lootbox.name}",
        color=COLOR_BY_RARITY_LOOTBOX.get(lootbox.rarity, discord.Color.light_gray())
    )
    embed.add_field(name="ID", value=lootbox.id, inline=True)
    embed.add_field(name="Type", value=lootbox.type.capitalize(), inline=True)
    embed.add_field(name="Rareté", value=str(lootbox.rarity), inline=True)

    total_weight = sum(weight for _, (_, weight) in lootbox.items)
    items_lines = [
        f"• **{name}** x{qty} — ({weight / total_weight * 100:.1f}%)"
        for name, (qty, weight) in lootbox.items
    ]
    embed.add_field(
        name=f"Contenu ({len(lootbox.items)} item{'s' if len(lootbox.items) > 1 else ''})",
        value="\n".join(items_lines) if items_lines else "Aucun item.",
        inline=False
    )

    return embed


def _generate_lootbox_open_history_embed(character_name: str, lootbox_name: str, quantity: int, rewards: list[tuple[str, int]], timestamp: datetime.datetime) -> discord.Embed:
    """
    Génère un embed Discord pour afficher une entrée d'historique d'ouverture de lootbox.

    Parameters
    ----------
    character_name : str
        Le nom du personnage qui a ouvert la lootbox.
    lootbox_name : str
        Le nom de la lootbox ouverte.
    quantity : int
        La quantité de lootboxes ouvertes.
    rewards : list[tuple[str, int]]
        La liste des récompenses obtenues, chaque récompense étant un tuple avec les clés "item" (nom de l'objet) et "quantity" (quantité obtenue).
    timestamp : datetime.datetime
        L'horodatage de l'ouverture de la lootbox.

    Returns
    -------
    discord.Embed
        L'embed Discord affichant l'entrée d'historique.
    """
    title = f"📦 {character_name} — {quantity}x {lootbox_name}"

    reward_lines = "\n".join(f"- {item} x{qty}" for item, qty in rewards)
    description = f"**Récompenses obtenues :**\n{reward_lines}"

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.gold(),
        timestamp=timestamp
    )

    return embed
