import discord
import datetime
import locale

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from instance.character import Character
    from instance.buff import Buff

from utils.utils import EMOJI_BY_BUFF


def _generate_buff_list_embed(buffs: list["Buff"]) -> discord.Embed:
    """
    Génère un embed Discord listant les buffs actifs sur les personnages.

    Parameters
    ----------
    buffs : list
        La liste des buffs actifs à afficher.

    Returns
    -------
    discord.Embed
        L'embed Discord listant les buffs actifs sur les personnages.
    """
    embed = discord.Embed(
        title="🔮 Buffs actifs",
        color=discord.Color.blue()
    )

    by_character = {}
    for buff in buffs:
        by_character.setdefault(buff.character_name, []).append(buff)

    for character_name, character_buffs in by_character.items():
        lines = []
        for buff in sorted(character_buffs, key=lambda b: locale.strxfrm(b.name)):
            effects_str = ", ".join(f"`{stat}` +{bonus}" for stat, bonus in buff.effects.items())
            lines.append(f"**{buff.name}** — {buff.duration} tours\n{effects_str}\n*Source : {buff.source}*")
        embed.add_field(
            name=f"👤 {character_name}",
            value="\n\n".join(lines),
            inline=False
        )

    embed.set_footer(text=f"{len(buffs)} buff(s) actif(s)")
    return embed


def _generate_buffs_embed(character: "Character", my_command: bool = True) -> discord.Embed:
    """
    Génère un embed Discord listant les buffs actifs sur un personnage.

    Parameters
    ----------
    character : Character
        Le personnage dont on veut afficher les buffs.
    my_command : bool, optional
        Indique si l'embed est utilisé dans la commande `/my buffs`.

    Returns
    -------
    discord.Embed
        L'embed Discord listant les buffs actifs sur le personnage.
    """
    # Regrouper par stat
    by_stat = {}
    for buff in character.buffs:
        for stat, bonus in buff.effects.items():
            by_stat.setdefault(stat, []).append((buff, bonus))

    embed = discord.Embed(
        title="✨ Mes buffs actifs" if my_command else f"✨ Buffs actifs de {character.name}",
        color=discord.Color.brand_green(),
        timestamp=datetime.datetime.now()
    )

    for stat, entries in by_stat.items():
        emoji = EMOJI_BY_BUFF.get(stat.lower(), "🔮")
        total = sum(bonus for _, bonus in entries)
        sign = "+" if total >= 0 else ""

        lines = []
        for buff, bonus in sorted(entries, key=lambda x: locale.strxfrm(x[0].name)):
            b_sign = "+" if bonus >= 0 else ""
            lines.append(f"**{buff.name}** ({b_sign}{bonus}) — {buff.duration} tour{'s' if buff.duration > 1 else ''} · *{buff.source}*")

        embed.add_field(
            name=f"{emoji} {stat}  ·  Total {sign}{total}",
            value="\n".join(lines),
            inline=False
        )

    embed.set_footer(text=f"{len(character.buffs)} buff{'s' if len(character.buffs) > 1 else ''} actif{'s' if len(character.buffs) > 1 else ''}")
    return embed


def _generate_buff_add_embed(character_name: str, buff_name: str, description: str, buff_effects: dict, source: str) -> discord.Embed:
    """
    Génère un embed Discord pour confirmer l'ajout d'un buff à un personnage.

    Parameters
    ----------
    character_name : str
        Le nom du personnage qui reçoit le buff.
    buff_name : str
        Le nom du buff ajouté.
    description : str
        La description du buff.
    buff_effects : dict
        Les effets du buff.

    Returns
    -------
    discord.Embed
        L'embed Discord confirmant l'ajout du buff au personnage.
    """
    embed = discord.Embed(
        title=f"🔮 {buff_name}",
        description=description,
        color=discord.Color.gold()
    )
    embed.add_field(name="Personnage", value=character_name, inline=True)
    embed.add_field(name="Source", value=source, inline=True)

    lines = []
    for stat, (bonus, duration) in buff_effects.items():
        sign = "+" if bonus >= 0 else ""
        durée_str = f"{duration} tours" if duration > 0 else "permanent"
        lines.append(f"`{stat}` {sign}{bonus} — {durée_str}")
    embed.add_field(name="🌀 Effets", value="\n".join(lines), inline=False)
    embed.set_footer(text="Confirme ou annule l'application des buffs.")

    return embed


def _generate_buff_clear_embed(character_name: str, buffs: list) -> discord.Embed:
    """
    Génère un embed Discord pour confirmer la suppression de tous les buffs d'un personnage.

    Parameters
    ----------
    character_name : str
        Le nom du personnage dont les buffs vont être supprimés.
    buffs : list
        La liste des buffs à supprimer.

    Returns
    -------
    discord.Embed
        L'embed Discord confirmant la suppression des buffs du personnage.
    """
    embed = discord.Embed(
        title=f"🗑️ Supprimer les buffs de {character_name}",
        description=f"Les {len(buffs)} buff(s) suivants vont être supprimés :",
        color=discord.Color.red()
    )

    lines = []
    for buff in buffs:
        effects_str = ", ".join(f"`{stat}` +{bonus}" for stat, bonus in buff.effects.items())
        lines.append(f"**{buff.name}** — {buff.duration} tours\n{effects_str}\n*Source : {buff.source}*")
    embed.add_field(name="Buffs actifs", value="\n\n".join(lines), inline=False)
    embed.set_footer(text="Cette action est irréversible.")

    return embed


def _generate_buff_remove_embed(character_name: str, buff: "Buff") -> discord.Embed:
    embed = discord.Embed(
        title=f"🗑️ Supprimer le buff de {character_name}",
        description=f"Le buff suivant va être supprimé :",
        color=discord.Color.orange()
    )
    effects_str = ", ".join(f"`{stat}` +{bonus}" for stat, bonus in buff.effects.items())
    embed.add_field(
        name=buff.name,
        value=f"{effects_str}\nDurée : {buff.duration} tours\n*Source : {buff.source}*\n*{buff.description}*",
        inline=False
    )
    embed.set_footer(text="Cette action est irréversible.")
    return embed


def _generate_buff_decrement_embed(character_name: str, buffs: list["Buff"], decrement: bool = True) -> discord.Embed:
    embed = discord.Embed(
        title=f"⏳ {('Décrémenter') if decrement else 'Incrémenter'} {('les buffs') if len(buffs) > 1 else 'le buff'} de {character_name}",
        description=f"{'Les buffs suivants vont' if len(buffs) > 1 else 'Le buff suivant va'} être {'décrémenté' if decrement else 'incrémenté'}{('s') if len(buffs) > 1 else ''}  d'un tour :",
        color=discord.Color.yellow()
    )
    for buff in buffs:
        effects_str = ", ".join(f"`{stat}` +{bonus}" for stat, bonus in buff.effects.items())
        embed.add_field(
            name=buff.name,
            value=f"{effects_str}\nDurée actuelle : {buff.duration} tours\n*Source : {buff.source}*",
            inline=False
        )

    embed.set_footer(text="Si la durée atteint 0, le buff sera supprimé.")
    return embed


def _generate_buff_application_history_embed(character_name: str, buff_name: str, buff_source: str, buff_duration: int, buff_effects: dict, buff_auto_decrement: bool, timestamp: datetime.datetime) -> discord.Embed:
    """
    Génère un embed Discord pour afficher une entrée d'historique d'application de buff.

    Parameters
    ----------
    character_name : str
        Le nom du personnage qui a reçu le buff.
    buff_name : str
        Le nom du buff appliqué.
    buff_source : str
        La source du buff.
    buff_duration : int
        La durée du buff.
    buff_effects : dict
        Les effets du buff.
    timestamp : datetime.datetime
        L'horodatage de l'application du buff.

    Returns
    -------
    discord.Embed
        L'embed Discord affichant l'entrée d'historique.
    """
    title = f"🔮 {buff_name} appliqué à {character_name}"
    description = f"Le buff **{buff_name}** a été appliqué à **{character_name}**."

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue(),
        timestamp=timestamp
    )

    embed.add_field(name="📌 Source", value=buff_source, inline=False)
    effects_str = "\n".join(f"`{stat}` +{bonus}" for stat, bonus in buff_effects.items())
    embed.add_field(name="🌀 Effets", value=effects_str, inline=True)
    embed.add_field(name="⏳ Durée", value=f"{buff_duration - (1 if buff_auto_decrement else 0)} tour{'s' if buff_duration > 1 else ''}", inline=True)

    return embed


def _generate_buff_expiration_history_embed(character_name: str, buff_name: str, buff_source: str, buff_effects: dict, timestamp: datetime.datetime) -> discord.Embed:
    """
    Génère un embed Discord pour afficher une entrée d'historique d'expiration de buff.

    Parameters
    ----------
    character_name : str
        Le nom du personnage dont le buff a expiré.
    buff_name : str
        Le nom du buff qui a expiré.
    buff_source : str
        La source du buff.
    buff_effects : dict
        Les effets du buff.
    timestamp : datetime.datetime
        L'horodatage de l'expiration du buff.

    Returns
    -------
    discord.Embed
        L'embed Discord affichant l'entrée d'historique.
    """
    title = f"⌛ {buff_name} expiré sur {character_name}"
    description = f"Le buff **{buff_name}** a expiré sur **{character_name}**."

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.dark_gray(),
        timestamp=timestamp
    )

    embed.add_field(name="📌 Source", value=buff_source, inline=False)
    effects_str = "\n".join(f"`{stat}` +{bonus}" for stat, bonus in buff_effects.items())
    embed.add_field(name="🌀 Effets perdus", value=effects_str, inline=True)

    return embed
