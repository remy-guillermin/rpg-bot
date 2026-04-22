import discord
import datetime
import locale

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from instance.character import Character

from utils.builder_graphic import _build_status_block, _build_stats_block
from utils.utils import (
    XP_TABLE,
    STATS_CLEAN,
    TAGS_CLEAN,
    SLOTS_CLEAN,
    COLOR_QUEST,
)


def _generate_character_embed(character: "Character", my_command: bool = True) -> (discord.Embed, discord.File):
    """
        Génère un embed Discord contenant les informations d'un personnage.

    Parameters
    ----------
    character : Character
        Le personnage dont les informations doivent être affichées.
    my_command : bool, optional
        Indique si la commande est utilisée pour afficher les informations de son propre personnage (True) ou pour afficher les informations d'un autre personnage (False). Par défaut à True.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations du personnage.
    discord.File
        Le fichier image contenant le bloc de statut du personnage.
    """
    role = character.role if character.role_visible else "Inconnu..."
    description = character.description if character.description else "Aucune description disponible."
    experience_to_next_level = XP_TABLE.get(character.level + 1, "N/A") - character.experience if character.level + 1 in XP_TABLE else "N/A"
    if experience_to_next_level is not None:
        xp_display = (
            f"**Niveau {character.level}** [{character.experience}/{XP_TABLE.get(character.level + 1, '?')}] \n"
            f" {experience_to_next_level} XP avant le niveau {character.level + 1}"
        )
    else:
        xp_display = f"**Niveau {character.level} (MAX)** [{character.experience} XP]"

    bosses_display = ""
    if character.bosses_defeated_names == []:
        bosses_display = "Aucun boss abattu"
    elif len(character.bosses_defeated_names) <= 3:
        for boss in character.bosses_defeated_names[::-1]:
            if boss is not None:
                bosses_display += f"- {boss}\n"
    else:
        for boss in character.bosses_defeated_names[::-1][:2]:
            if boss is not None:
                bosses_display += f"- {boss}\n"

        bosses_display += f"... et {len(character.bosses_defeated_names) - 2} autre{'s' if len(character.bosses_defeated_names) - 2 > 1 else ''}"

    bosses_title = f"🗡️ Boss abattu{'s' if len(character.bosses_defeated_names) > 1 else ''} {f'[{len(character.bosses_defeated_names)}]' if len(character.bosses_defeated_names) > 3 else ''}"
    buf = _build_status_block(character)

    embed = discord.Embed(
        title=f"Mon personnage: {character.name}" if my_command else f"Informations sur {character.name}",
        color=discord.Color.dark_teal(),
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="🎭 Role", value=role, inline=False)
    embed.add_field(name="📜 Description", value=description, inline=False)
    embed.add_field(name="📈 Expérience", value=xp_display, inline=True)
    embed.add_field(name="💀 Kills", value=str(character.kills), inline=True)
    embed.add_field(name=bosses_title, value=bosses_display, inline=True)
    embed.add_field(name="📊 Statut", value="", inline=True)
    embed.add_field(name=f"🪙 {character.currency} pièces d'or", value="", inline=True)

    embed.set_image(url="attachment://status.png")

    return embed, buf


def _generate_stats_embed(character: "Character", my_command: bool = True) -> (discord.Embed, discord.File):
    """
        Génère un embed Discord contenant les statistiques d'un personnage.

    Parameters
    ----------
    character : Character
        Le personnage dont les statistiques doivent être affichées.
    my_command : bool, optional
        Indique si la commande est utilisée pour afficher les statistiques de son propre personnage (True) ou pour afficher les statistiques d'un autre personnage (False). Par défaut à True.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les statistiques du personnage.
    discord.File
        Le fichier image contenant le bloc de statistiques du personnage.
    """

    buf = _build_stats_block(character)


    embed = discord.Embed(
        title="Mes statistiques" if my_command else f"Statistiques de {character.name}",
        color=discord.Color.from_rgb(93, 202, 165),
        timestamp=datetime.datetime.now()
    )

    embed.set_image(url="attachment://stats.png")

    return embed, buf


def _generate_inventory_embed(character: "Character", my_command: bool = True) -> discord.Embed:
    """
        Génère un embed Discord contenant l'inventaire d'un personnage.

    Parameters
    ----------
    character : Character
        Le personnage dont l'inventaire doit être affiché.
    my_command : bool, optional
        Indique si la commande est utilisée pour afficher l'inventaire de son propre personnage (True) ou pour afficher l'inventaire d'un autre personnage (False). Par défaut à True.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant l'inventaire du personnage.
    """
    stored_items = []
    equipment = {
        "Armure": None,
        "Arme (slot 1)": None,
        "Arme (slot 2)": None,
        "Artéfact": None,
        "Tête": None,
    }

    for entry in character.inventory.entries:
        item = entry.item

        if entry.equipped_quantity > 0 and item.equippable:
            raw_slot = item.equippable_slot

            if raw_slot in ("arme_une_main", "arme_deux_mains"):
                for _ in range(entry.equipped_quantity):  # 1 ou 2 fois
                    if equipment["Arme (slot 1)"] is None:
                        equipment["Arme (slot 1)"] = item
                    else:
                        equipment["Arme (slot 2)"] = item

            elif raw_slot == "armure":
                equipment["Armure"] = item

            elif raw_slot == "artefact":
                equipment["Artéfact"] = item

            elif raw_slot == "tete":
                equipment["Tête"] = item

        stored_quantity = entry.quantity - entry.equipped_quantity
        if stored_quantity > 0:
            stored_items.append((item, stored_quantity))


    grouped_items = {}
    for item, quantity in stored_items:
        tag = item.tags[0] if item.tags else "Sans tag"
        grouped_items.setdefault(TAGS_CLEAN.get(tag, "Sans tag"), []).append((item, quantity))

    # ── Équipement ───────────────────────────────────────────────

    slots_to_show = ["Tête", "Armure", "Arme (slot 1)", "Arme (slot 2)", "Artéfact"]

    equipment_lines = []
    for slot in slots_to_show:
        item = equipment[slot]
        if item:
            bonus_parts = [f"{STATS_CLEAN.get(k, k)} +{v}" for k, v in item.equipped_bonus.items() if v]
            bonus_str = f"  *({', '.join(bonus_parts)})*" if bonus_parts else ""
            equipment_lines.append(f"**{slot}**: {item.name}{bonus_str}")
        else:
            if equipment["Arme (slot 1)"] is not None and equipment["Arme (slot 1)"].equippable_slot == "arme_deux_mains" and equipment["Arme (slot 2)"] is None and slot == "Arme (slot 2)":
                equipment_lines.append(f"**{slot}**: *Indisponible (arme à deux mains équipée)*")
            else:
                equipment_lines.append(f"**{slot}**: *Vide*")

    equipment_value = "\n".join(equipment_lines) or "*Aucun équipement*"

    # ── Inventaire groupé ────────────────────────────────────────

    inventory_fields = []
    for tag, entries in grouped_items.items():
        lines = []
        for item, quantity in sorted(entries, key=lambda e: locale.strxfrm(e[0].name)):
            qty_str = f" x{quantity}" if quantity > 1 else ""
            lines.append(f"• {item.name}{qty_str}")
        inventory_fields.append((tag, "\n".join(lines)))

    slots_used = character.inventory.slots_used()
    slots_max = character.inventory.max_size

    # ── Embed ────────────────────────────────────────────────────

    embed = discord.Embed(
        title="Mon inventaire" if my_command else f"Inventaire de {character.name}",
        color=discord.Color.dark_gold(),
        timestamp=datetime.datetime.now()
    )

    embed.add_field(
        name="⚔️ Équipement",
        value=equipment_value,
        inline=False
    )

    embed.add_field(
        name="\u200b",
        value=f"**🎒 Objets** — {slots_used}/{slots_max} emplacements",
        inline=False
    )

    if inventory_fields:
        for tag, value in inventory_fields:
            embed.add_field(name=tag, value=value, inline=True)
    else:
        embed.add_field(name="Objets", value="*Inventaire vide*", inline=False)

    return embed


def _generate_powers_embed(character: "Character", my_command: bool = True) -> discord.Embed:
    """
        Génère un embed Discord contenant les pouvoir d'un joueur.

    Parameters
    ----------
    character : Character
        Le personnage dont les pouvoirs doivent être affichés.
    my_command : bool, optional
        Indique si la commande est utilisée pour afficher les pouvoirs de son propre personnage (True) ou pour afficher les pouvoirs d'un autre personnage (False). Par défaut à True.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les pouvoirs du personnage.
    """
    embed = discord.Embed(
        title="Mes pouvoirs" if my_command else f"Pouvoirs de {character.name}",
        color=discord.Color.fuchsia(),
        timestamp=datetime.datetime.now()
    )

    if character.powers:
        for power in sorted(character.powers, key=lambda p: locale.strxfrm(p.name)):
            description = power.description if power.description else "Aucune description disponible."
            embed.add_field(name=f" ❈ {power.name}", value=description, inline=False)
    else:
        embed.add_field(name="Aucun pouvoir", value="Ce personnage n'a aucun pouvoir pour le moment.", inline=False)

    return embed


def _generate_quests_embed(active: set[str], completed: set[str], npc_repo) -> discord.Embed:
    embed = discord.Embed(title="📜 Quêtes du groupe", color=COLOR_QUEST)

    if active:
        for quest_id in active:
            quest = npc_repo.get_quest(quest_id)
            if quest:
                embed.add_field(
                    name=f"🟡 {quest.title}",
                    value=f"*Donné par {quest.npc_name}*\n{quest.description}",
                    inline=False,
                )
    else:
        embed.add_field(name="🟡 En cours", value="Aucune quête active.", inline=False)

    if completed:
        embed.add_field(
            name="✅ Terminées",
            value="\n".join(
                f"• {npc_repo.get_quest(qid).title} *(par {npc_repo.get_quest(qid).npc_name})*"
                for qid in completed
                if npc_repo.get_quest(qid)
            ),
            inline=False,
        )

    return embed
