import discord
import datetime
import random

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from instance.power import Power

from utils.variations import (
    COLOR_BY_OUTCOME,
    OUTCOME_STATUS,
    STAT_DICE_OUTCOMES,
    POWER_USE_PHRASES,
    POWER_USE_PHRASES_DEFAULT,
)
from utils.utils import de_du_nom


def _generate_power_embed(power: "Power") -> discord.Embed:
    """
    Génère un embed Discord contenant le détail d'un pouvoir.

    Parameters
    ----------
    power : Power
        Le pouvoir à afficher.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant le détail du pouvoir.
    """
    embed = discord.Embed(
        title=f"{power.name}",
        description=power.description or "Aucune description disponible.",
        color=discord.Color.pink(),
        timestamp=datetime.datetime.now()
    )

    if power.cost:
        cost_str = "\n".join(f"{k} : {v}" for k, v in power.cost.items() if v != 0)
        if cost_str:
            embed.add_field(name="💰 Coût", value=cost_str, inline=True)

    if power.duration:
        embed.add_field(name="⏳ Durée", value=power.duration, inline=True)

    if power.bonus:
        bonus_str = "\n".join(
            f"{k} : +{v}" if v != 0 else f"{k} : +dé"
            for k, v in power.bonus.items()
        )
        embed.add_field(name="⚡ Bonus", value=bonus_str, inline=True)

    if power.dice:
        embed.add_field(name="🎲 Dé", value=power.dice, inline=True)

    return embed


def _generate_power_use_embed(power: "Power", character_name: str, power_effects: dict | None, roll: dict | None, target_name: str | None = None, target_effect: dict | None = None) -> discord.Embed:
    """
    Génère un embed Discord narratif lors de l'utilisation d'un pouvoir.

    Parameters
    ----------
    power : Power
        Le pouvoir utilisé.
    character_name : str
        Le nom du personnage qui utilise le pouvoir.
    roll_result : int | None
        Le résultat brut du dé (si applicable).
    computed_effects : dict[str, int] | None
        Les effets calculés après application des bonus
        (ex. {"dégâts": 12, "soin": 5}).

    Returns
    -------
    discord.Embed
        L'embed Discord narratif décrivant l'utilisation du pouvoir.
    """
    phrases = POWER_USE_PHRASES.get(power.category, POWER_USE_PHRASES_DEFAULT)
    narrative = random.choice(phrases).format(
        character=character_name,
        de_character=de_du_nom(character_name),
        power=power.name,
    )

    embed = discord.Embed(
        title=power.name,
        description=narrative,
        color=discord.Color.pink(),
        timestamp=datetime.datetime.now(),
    )

    # Effets calculés
    if power_effects:
        effects_str = "\n".join(
            f"{k} : **{v:+}**" for k, v in power_effects.items()
        )
        embed.add_field(name="🌀 Effets", value=effects_str, inline=True)

    # Résultat du dé
    if roll is not None:
        embed.add_field(
            name=f"🎲 Jet de dé ({roll['expression']})",
            value=f"**{roll['total']}**",
            inline=True,
        )

    # Coût dépensé
    if power.cost:
        cost_str = "\n".join(
            f"{k} : {v}" for k, v in power.cost.items() if v != 0
        )
        if cost_str:
            embed.add_field(name="💰 Coût", value=cost_str, inline=True)

    # Effets sur les cibles
    if target_effect:
        lines = []
        for stat, (bonus, duration, count) in target_effect.items():
            suffix = "*(instantané)*" if duration == -1 else f"*({duration} tours)*"
            scope = f"→ **{target_name}**" if count == 1 and target_name else "→ **Tous les joueurs**"
            lines.append(f"{stat} : **{bonus:+}** {suffix} {scope}")
        embed.add_field(name="✨ Effets sur les cibles", value="\n".join(lines), inline=True)

    embed.set_footer(text=f"Pouvoir utilisé par {character_name}")

    return embed


def _generate_power_use_history_embed(character_name: str, power_name: str, power_effects: dict, roll: dict, timestamp: datetime.datetime) -> discord.Embed:
    """
    Génère un embed Discord pour afficher une entrée d'historique d'utilisation de pouvoir.

    Parameters
    ----------
    character_name : str
        Le nom du personnage qui a utilisé le pouvoir.
    power_name : str
        Le nom du pouvoir utilisé.
    power_effects : dict
        Les effets du pouvoir utilisé.
    timestamp : datetime.datetime
        L'horodatage de l'utilisation du pouvoir.

    Returns
    -------
    discord.Embed
        L'embed Discord affichant l'entrée d'historique.
    """
    title = f"❈ {power_name} utilisé par {character_name}"
    description = f"Le pouvoir **{power_name}** a été utilisé par **{character_name}**."

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.purple(),
        timestamp=timestamp
    )

    if power_effects is not None:
        effects_str = "\n".join(f"`{stat}` +{bonus}" for stat, bonus in power_effects.items())
        embed.add_field(name="🌀 Effets", value=effects_str, inline=True)

    if roll is not None:
        embed.add_field(name=f"🎲 Lancer de dé *{roll['expression']}*", value=f"**{roll['total']}**", inline=True)

    return embed


def _generate_stat_dice_embed(character_name: str, stat_name: str, roll_result: dict, bonus: dict[str, int], faces: int) -> discord.Embed:
    """
    Génère un embed Discord contenant les résultats d'un lancer de dés pour une statistique.

    Parameters
    ----------
    character_name : str
        Le nom du personnage.
    stat_name : str
        Le nom de la statistique.
    result : int
        Le résultat du lancer de dés.
    bonus : dict[str, int]
        Les bonus à appliquer à la statistique.
    faces : int
        Le nombre de faces du dé.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les résultats du lancer de dés.
    """
    outcome = roll_result["outcome"]
    outcome_info = OUTCOME_STATUS.get(outcome, OUTCOME_STATUS["normal"])
    outcome_color = COLOR_BY_OUTCOME.get(outcome, COLOR_BY_OUTCOME["normal"])
    stat_outcomes = STAT_DICE_OUTCOMES.get(stat_name.lower(), STAT_DICE_OUTCOMES.get(stat_name.casefold()))
    if stat_outcomes:
        outcome_phrases = stat_outcomes.get(outcome) or stat_outcomes.get("normal")
        description = random.choice(outcome_phrases).format(
            character=character_name,
            de_character=f"de {character_name}",
        )
    else:
        description = f"{character_name} lance les dés."
    modifier = sum(bonus.values())
    modifier_display = f"+{modifier}" if modifier > 0 else str(modifier) if modifier != 0 else "0"

    if outcome == "natural_fail" and sum(bonus.values()) > 0:
        bonus_lines = "❌ Bonus annulés — échec critique"
    elif outcome == "natural_success" and sum(bonus.values()) < 0:
        bonus_lines = "✅ Malus annulés — succès critique"
    else:
        bonus_lines = (
            f"🧬 Stat        {bonus['base']:+}\n"
            f"⬆️ Niveau     {bonus['level']:+}\n"
            f"⚔️ Équipement {bonus['item']:+}\n"
            f"✨ Buff        {bonus.get('buff', 0):+}\n"
            f"📜 Histoire   {bonus['admin']:+}\n"
            f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            f"**Total        {modifier_display}**"
        )

    if outcome == "natural_success" and stat_name.lower() in ["attaque", "défense"]:
        result_value = f"**{roll_result['total']}** *(base {roll_result['base_total']} × 1.5{f' {modifier_display} bonus' if modifier > 0 else ''})*"
    elif outcome == "natural_success":
        result_value = f"**{roll_result['total']}**"
    elif outcome == "natural_fail":
        result_value = f"**0**"
    else:
        result_value = f"**{roll_result['total']}**"

    natural_roll = roll_result["base_total"]

    embed = discord.Embed(
        title=f"🎲 Lancer de dé — {stat_name}",
        description=description,
        color=outcome_color,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="Statut", value=outcome_info, inline=False)
    embed.add_field(name="Modificateurs", value=bonus_lines, inline=False)
    embed.add_field(name="Résultat", value=result_value, inline=False)
    embed.set_footer(text=f"🎯 {roll_result['expression']} · [{natural_roll}/d{faces}]")
    return embed
