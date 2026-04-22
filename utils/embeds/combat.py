import discord
import datetime
import random
import os
import logging

logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from instance.enemy import Enemy

from utils.builder_combat import draw_combat
from utils.path import ASSETS_FOLDER
from utils.variations_combat import (
    COMBAT_END,
    _get_spawn_variations,
    _get_attack_variations,
)


def _generate_admin_enemy_spawn_embed(instances: ["Enemy"], count: int) -> discord.Embed:
    """
    Génère un embed Discord pour confirmer l'apparition d'un ou plusieurs ennemis par un administrateur.

    Parameters
    ----------
    instances : [Enemy]
        La liste des ennemis qui vont apparaître.
    count : int
        Le nombre d'ennemis à faire apparaître.

    Returns
    -------
    discord.Embed
        L'embed Discord confirmant l'apparition des ennemis.
    """
    e = instances[0]
    det = "Spawnée" if e.genre == "F" else "Spawné"
    if count > 1:
        det = "Spawnées" if e.genre == "F" else "Spawnés"

    iids = ", ".join(f"`{i.instance_id}`" for i in instances)

    embed = discord.Embed(
        title=f"⚔️ {count}× {e.name} {det}" if count > 1 else f"⚔️ {e.name} {det}",
        description=f"**Instances :** {iids}",
        color=discord.Color.dark_red() if e.boss else discord.Color.red(),
    )
    embed.add_field(name="HP",  value=str(e.max_hp), inline=True)
    embed.add_field(name="ATK", value=str(e.atk),    inline=True)
    embed.add_field(name="DEF", value=str(e.defense), inline=True)
    embed.add_field(name="Biome", value=e.biome,     inline=True)
    embed.add_field(name="Boss",  value="✅" if e.boss else "❌", inline=True)
    embed.set_footer(text=f"ID catalogue : {e.enemy_id}")

    return embed


def _generate_enemy_list_embed(enemies: list["Enemy"]) -> discord.Embed:
    """
    Génère un embed Discord listant les ennemis présents dans la zone.

    Parameters
    ----------
    enemies : list
        La liste des ennemis à afficher.

    Returns
    -------
    discord.Embed
        L'embed Discord listant les ennemis présents dans la zone.
    """
    import locale
    embed = discord.Embed(
        title="👹 Ennemis présents",
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.now()
    )

    for enemy in sorted(enemies, key=lambda e: locale.strxfrm(e.name)):
        hp_str = f"{enemy.current_hp}/{enemy.max_hp}"
        embed.add_field(
            name=f"{enemy.name} (ID : `{enemy.instance_id}`)",
            value=f"HP : {hp_str} | ATK : {enemy.atk} | DEF : {enemy.defense} | Biome : {enemy.biome} | {'Boss' if enemy.boss else 'Non-boss'}",
            inline=False
        )

    embed.set_footer(text=f"{len(enemies)} ennemi{'s' if len(enemies) > 1 else ''} présent{'s' if len(enemies) > 1 else ''}")
    return embed


def _generate_admin_damage_enemy_embed(enemy: "Enemy", character_name: str, result: dict) -> discord.Embed:
    """
    Génère un embed Discord pour afficher les dégâts infligés à un ennemi.

    Parameters
    ----------
    enemy : "Enemy"
        L'ennemi attaqué.
    character_name : str
        Le nom du personnage.
    result : dict
        Un dictionnaire contenant les résultats du calcul de dégâts, avec les clés suivantes :
        - "raw" : les dégâts bruts avant absorption
        - "absorbed" : les dégâts absorbés par la défense
        - "actual" : les dégâts réels infligés après absorption
        - "hp_before" : les HP de l'ennemi avant l'attaque
        - "hp_after" : les HP de l'ennemi après l'attaque
        - "alive" : bool indiquant si l'ennemi est encore vivant après l'attaque

    Returns
    -------
    discord.Embed
        L'embed Discord affichant les dégâts infligés à l'ennemi.
    """
    status = "💀 Mort" if not result["alive"] else (
        "🩸 Critique" if enemy.hp_ratio() < 0.25 else "🗡️ Blessé"
    )

    embed = discord.Embed(
        title=f"🗡️ {character_name} attaque {enemy.article()} {enemy.name}",
        color=discord.Color.dark_red() if result["alive"] else discord.Color.dark_gray(),
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="Dégâts bruts",    value=str(result["raw"]),      inline=True)
    embed.add_field(name="Absorbés (DEF)",  value=str(result["absorbed"]), inline=True)
    embed.add_field(name="Dégâts réels",    value=str(result["actual"]),   inline=True)
    embed.add_field(
        name="HP",
        value=f"{result['hp_before']} → **{result['hp_after']}**/{enemy.max_hp}",
        inline=True
    )
    embed.add_field(name="Statut", value=status, inline=True)

    # Log des dégâts de ce combat
    log_lines = [
        f"{name} : {dmg}" for name, dmg in
        sorted(enemy.damage_log.items(), key=lambda x: -x[1])
        if not (dmg == 0 and result["alive"])
    ]

    embed.add_field(name="Log dégâts", value="\n".join(log_lines), inline=False)
    return embed


def _generate_admin_heal_enemy_embed(enemy: "Enemy", result: dict) -> discord.Embed:
    """
    Génère un embed Discord pour afficher le soin appliqué à un ennemi.

    Parameters
    ----------
    enemy : Enemy
        L'ennemi soigné.
    result : dict
        Un dictionnaire contenant les résultats du calcul de soin, avec les clés suivantes :
        - "amount" : le montant du soin
        - "hp_before" : les HP de l'ennemi avant le soin
        - "hp_after" : les HP de l'ennemi après le soin

    Returns
    -------
    discord.Embed
        L'embed Discord affichant le soin appliqué à l'ennemi.
    """
    embed = discord.Embed(
        title=f"💚 {enemy.article(capitalize=True)} {enemy.name} est soigné{'e' if enemy.genre == 'F' else ''}",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="Soin",  value=str(result["amount"]), inline=True)
    embed.add_field(
        name="HP",
        value=f"{result['hp_before']} → **{result['hp_after']}**/{enemy.max_hp}",
        inline=True
    )
    return embed


def _generate_enemy_spawn_embed(instances: list, count: int,) -> tuple[discord.Embed, discord.File | None]:
    """
    Génère un embed Discord pour confirmer l'apparition d'un ou plusieurs ennemis.

    Parameters
    ----------
    instances : list
        La liste des instances d'ennemis qui vont apparaître (doivent être du même type).
    count : int
        Le nombre d'ennemis à faire apparaître.

    Returns
    -------
    tuple[discord.Embed, discord.File | None]
        L'embed Discord et le fichier image associé.
    """
    enemy = instances[0]
    var = _get_spawn_variations(enemy, count)

    embed = discord.Embed(
        title=random.choice(var["titles"]),
        description=random.choice(var["descriptions"]),
        color=var["color"],
        timestamp=datetime.datetime.now()
    )

    embed.add_field(
        name=f"{count}× {enemy.name}" if count > 1 else enemy.name,
        value=enemy.description,
        inline=False
    )
    embed.add_field(name="ATK", value=str(enemy.atk),      inline=True)
    embed.add_field(name="DEF", value=str(enemy.defense),  inline=True)
    embed.add_field(name="HP",  value=str(enemy.max_hp),   inline=True)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    image_path = os.path.join(project_root, ASSETS_FOLDER, "enemies", f"{enemy.enemy_id}.png")
    logger.debug(f"Enemy image path: {image_path}")
    file = None
    if os.path.exists(image_path):
        file = discord.File(image_path, filename="enemy.png")
        embed.set_image(url="attachment://enemy.png")

    return embed, file


def _generate_hp_tracker_embed(
    actifs: list,
    player_positions: dict[str, tuple[int, int]],
    dead_enemies: list[dict],
) -> tuple[discord.Embed, discord.File]:
    enemies_dict = {}
    for enemy in actifs:
        marker = enemy.marker or "?"
        enemy_name = f"[{marker}] {enemy.name}" if not enemy.boss else enemy.name
        enemies_dict[enemy_name] = {
            "position": enemy.position if enemy.position is not None else (0, -4),
            "id": enemy.instance_id if enemy.instance_id else "N/A",
            "hp_current": enemy.current_hp,
            "hp_max": enemy.max_hp,
            "boss": enemy.boss,
            "label": marker,
        }

    filename = draw_combat(enemies_dict, player_positions, dead_enemies=dead_enemies)
    filepath = os.path.join("data", "combat_images", filename)

    embed = discord.Embed(
        title="⚔️ Combat en cours",
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.now()
    )
    file = discord.File(filepath, filename="tracker.png")
    embed.set_image(url="attachment://tracker.png")
    return embed, file


def _generate_combat_rewards_embed(rewards: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🏆 Récompenses de combat",
        color=discord.Color.gold(),
        timestamp=datetime.datetime.now()
    )

    # Ennemis vaincus
    if rewards.get("defeated_enemies"):
        lines = []
        for e in rewards["defeated_enemies"]:
            prefix = "👑" if e["is_boss"] else "💀"
            lines.append(f"{prefix} {e['name']}")
        embed.add_field(name="Ennemis vaincus", value="\n".join(lines), inline=False)

    # Récompenses par joueur (triées par XP décroissant)
    xp_lines = sorted(rewards["xp"].items(), key=lambda x: -x[1])
    for char_name, xp in xp_lines:
        dmg = rewards.get("total_damage", {}).get(char_name, 0)
        boss_ids = rewards["boss_kills"].get(char_name, [])
        parts = [f"+{xp} XP", f"{dmg} dégâts"]
        embed.add_field(name=char_name, value=" | ".join(parts), inline=False)

    return embed


def _generate_combat_end_embed() -> discord.Embed:
    var = COMBAT_END
    return discord.Embed(
        title=random.choice(var["titles"]),
        description=random.choice(var["descriptions"]),
        color=var["color"],
        timestamp=datetime.datetime.now()
    )


def _generate_enemy_attack_embed(enemy, character_name: str, result: dict) -> discord.Embed:
    var = _get_attack_variations(result["actual"])
    title = random.choice(var["titles"]).format(
        enemy=enemy.name, character=character_name
    )
    description = random.choice(var["descriptions"]).format(
        enemy=enemy.name, character=character_name
    )
    embed = discord.Embed(
        title=title,
        description=description,
        color=var["color"],
        timestamp=datetime.datetime.now()
    )
    attack_type = result.get("attack_type", "physique")
    absorbed_label = "Absorbés (RES)" if attack_type == "magique" else "Absorbés (DEF)"
    type_label = "Magique ✨" if attack_type == "magique" else "Physique ⚔️"
    embed.add_field(name="Type",                    value=type_label,              inline=True)
    embed.add_field(name=f"Dé (d{result['die']})", value=str(result["roll"]),     inline=True)
    embed.add_field(name="Dégâts bruts",            value=str(result["raw"]),      inline=True)
    embed.add_field(name=absorbed_label,            value=str(result["absorbed"]), inline=True)
    embed.add_field(name="Dégâts réels",            value=str(result["actual"]),   inline=True)
    embed.add_field(
        name="HP",
        value=f"{result['hp_before']} → **{result['hp_after']}**",
        inline=True
    )
    return embed


def _generate_damage_history_embed(result: dict, enemy, character, enemy_attack=False, timestamp=None) -> discord.Embed:
    if enemy_attack:
        title = f"⚔️ {enemy.name} attaque {character.name}"
        description = f"{enemy.name} a infligé des dégâts à {character.name}"
        color = discord.Color.blue()
        hp_line = f"{character.resources['hp'] + result['actual']} → **{character.resources['hp']}**"
    else:
        title = f"🗡️ {character.name} attaque {enemy.name}"
        description = f"{character.name} a infligé des dégâts à {enemy.name}"
        color = discord.Color.dark_red() if result["alive"] else discord.Color.dark_gray()
        hp_line = f"{enemy.current_hp + result['actual']} → **{enemy.current_hp}**"

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=timestamp or datetime.datetime.now()
    )
    embed.add_field(name="Dégâts bruts",    value=str(result["raw"]),      inline=True)
    embed.add_field(name="Absorbés (DEF)",  value=str(result["absorbed"]), inline=True)
    embed.add_field(name="Dégâts réels",    value=str(result["actual"]),   inline=True)
    embed.add_field(
        name="HP",
        value=hp_line,
        inline=True
    )
    return embed

def _generate_spawn_history_embed(enemy, instance_id, timestamp=None) -> discord.Embed:
    embed = discord.Embed(
        title=f"👹 {enemy.name} est apparu{'e' if enemy.genre == 'F' else ''} !",
        description=f"{enemy.article(capitalize=True)} {enemy.name} a spawn à l'instance `{instance_id}`.",
        color=discord.Color.gold(),
        timestamp=timestamp or datetime.datetime.now()
    )
    embed.add_field(name="HP",  value=str(enemy.max_hp),   inline=True)
    embed.add_field(name="ATK", value=str(enemy.atk),      inline=True)
    embed.add_field(name="DEF", value=str(enemy.defense),  inline=True)
    return embed