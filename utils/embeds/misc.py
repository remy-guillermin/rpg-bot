import discord
import datetime
import random
import os

from utils.variations import (
    BASIC_DICE_OUTCOMES,
    CHRONICLE_TITLES,
    MOST_ROLLS_FLAVOR,
    BEST_ROLLER_FLAVOR,
    WORST_ROLLER_FLAVOR,
    MOST_GOOD_FLAVOR,
    MOST_GOOD_NONE_FLAVOR,
    MOST_BAD_FLAVOR,
    MOST_BAD_NONE_FLAVOR,
    COMBAT_TITLES,
    CRIT_SUCCESS_FLAVOR,
    CRIT_SUCCESS_NONE_FLAVOR,
    NATURAL_SUCCESS_FLAVOR,
    NATURAL_SUCCESS_NONE_FLAVOR,
    NATURAL_FAIL_FLAVOR,
    NATURAL_FAIL_NONE_FLAVOR,
    BEST_DAMAGE_FLAVOR,
    WORST_DAMAGE_FLAVOR,
    MOST_DAMAGE_FLAVOR,
    LEAST_DAMAGE_FLAVOR,
)

from utils.utils import (
    ROLE_CLEAN, 
    ROLE_ICONS,
)
from utils.locations import (
    CITIES_DATA,
    COLOR_BY_TYPE,
)
from utils.path import (
    ASSETS_FOLDER,
)


def _generate_basic_dice_embed(roll_result: dict) -> discord.Embed:
    """
        Génère un embed Discord contenant les résultats d'un lancer de dés.

    Parameters
    ----------
    roll_result : dict
        Le résultat du lancer de dés, contenant les détails du lancer et le total.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les résultats du lancer de dés.
    """
    natural_roll = roll_result["base_total"]
    faces = int(roll_result["results"][0]["expression"].split("d")[1])
    modifier = roll_result["modifier"]
    outcome = roll_result["outcome"]

    outcome_info = BASIC_DICE_OUTCOMES.get(outcome, BASIC_DICE_OUTCOMES["normal"])

    modifier = roll_result["modifier"]
    modifier_display = f"+{modifier}" if modifier > 0 else str(modifier) if modifier != 0 else "0"

    embed = discord.Embed(
        title="🎲 Lancer de dés",
        description=random.choice(outcome_info["descriptions"]),
        color=outcome_info["color"],
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="Statut",      value=outcome_info["status"],                inline=False)
    embed.add_field(name="Base",        value=str(roll_result["base_total"]),   inline=True)
    embed.add_field(name="Bonus/Malus", value=modifier_display,                 inline=True)
    embed.add_field(name="Total",       value=f"**{roll_result['total']}**",     inline=True)
    embed.set_footer(text=roll_result["results"][0]["expression"])

    return embed


def _generate_session_summary_embed(stats: dict) -> discord.Embed:
    embed = discord.Embed(
        title=random.choice(CHRONICLE_TITLES),
        description="*Les étoiles ont parlé. Les dés ont tranché. Voici ce qu'il en reste.*",
        color=discord.Color.gold()
    )

    best_name, best_avg   = stats['best_roller']
    worst_name, worst_avg = stats['worst_roller']
    most_name, most_count = stats['most_rolls']

    nat_success_name, nat_success_count   = stats['most_natural_success']
    crit_success_name, crit_success_count = stats['most_critical_success']
    good_name, good_count                 = stats['most_good']
    bad_name, bad_count                   = stats['most_bad']
    crit_fail_name, crit_fail_count       = stats['most_critical_fail']
    nat_fail_name, nat_fail_count         = stats['most_natural_fail']

    # Best / Worst
    embed.add_field(
        name="🏆 Meilleur lanceur",
        value=f"**{best_name}** — moy. `{best_avg:.2f}`\n*{random.choice(BEST_ROLLER_FLAVOR)}*",
        inline=True
    )
    embed.add_field(
        name="💀 Pire lanceur",
        value=f"**{worst_name}** — moy. `{worst_avg:.2f}`\n*{random.choice(WORST_ROLLER_FLAVOR)}*",
        inline=True
    )

    embed.add_field(name="\u200b", value="\u200b", inline=False)  # separator

    # Most rolls
    embed.add_field(
        name="🎲 Dé-pendant officiel",
        value=f"**{most_name}** — `{most_count}` jets\n*{random.choice(MOST_ROLLS_FLAVOR)}*",
        inline=False
    )

    # Outcomes
    def outcome_line(name, count, emoji, label, flavor_none, flavor_some):
        if name is None or count == 0:
            return f"{emoji} **{label}** — *{flavor_none}*"
        return f"{emoji} **{label}** — **{name}** (`{count}`)\n*{flavor_some}*"

    embed.add_field(
        name="✨ Succès naturel",
        value=outcome_line(
            nat_success_name, nat_success_count, "✨", "Touché par les dieux",
            "Personne n'a été béni. Triste.",
            "Les astres étaient alignés. Probablement un accident."
        ),
        inline=True
    )
    embed.add_field(
        name="💥 Succès critique",
        value=outcome_line(
            crit_success_name, crit_success_count, "💥", "Maître du chaos chanceux",
            "Aucun critique positif. Séance difficile.",
            "A explosé ses jets avec style. Ou de la triche."
        ),
        inline=True
    )

    embed.add_field(name="\u200b", value="\u200b", inline=False)

    embed.add_field(
        name="🟢 Bon résultat",
        value=outcome_line(
            good_name, good_count, "🟢", "Régulier au-dessus",
            MOST_GOOD_NONE_FLAVOR,
            random.choice(MOST_GOOD_FLAVOR)
        ),
        inline=True
    )
    embed.add_field(
        name="🟠 Mauvais résultat",
        value=outcome_line(
            bad_name, bad_count, "🟠", "Régulier en dessous",
            MOST_BAD_NONE_FLAVOR,
            random.choice(MOST_BAD_FLAVOR)
        ),
        inline=True
    )

    embed.add_field(name="\u200b", value="\u200b", inline=False)

    embed.add_field(
        name="💔 Échec critique",
        value=outcome_line(
            crit_fail_name, crit_fail_count, "💔", "Favori des mauvaises étoiles",
            "Personne n'a touché le fond. Cette fois.",
            "A raté si fort que les dés en rougissent encore."
        ),
        inline=True
    )
    embed.add_field(
        name="🕳️ Échec naturel",
        value=outcome_line(
            nat_fail_name, nat_fail_count, "🕳️", "Champion de l'impuissance",
            "Aucun échec naturel. Les dés sont cléments.",
            "Un talent rare pour le désastre pur."
        ),
        inline=True
    )

    embed.set_footer(text="Que vos prochains jets soient... légèrement meilleurs.")
    return embed


def _generate_combat_summary_embed(stats: dict) -> discord.Embed:
    embed = discord.Embed(
        title=random.choice(COMBAT_TITLES),
        description="*Le sang a coulé. Les dés ont parlé. Voici qui s'est illustré.*",
        color=discord.Color.dark_red(),
        timestamp=datetime.datetime.now(),
    )

    def ranking_field(ranking: list[tuple], some_flavor: list[str], none_flavor: str):
        if not ranking:
            return f"*{none_flavor}*"
        top_name, top_count = ranking[0]
        lines = "\n".join(f"{i+1}. **{name}** — `{count}`" for i, (name, count) in enumerate(ranking))
        return f"{lines}\n*{random.choice(some_flavor)}*"

    embed.add_field(
        name="💥 Succès critiques",
        value=ranking_field(stats.get("critical_success_ranking", []), CRIT_SUCCESS_FLAVOR, CRIT_SUCCESS_NONE_FLAVOR),
        inline=True,
    )
    embed.add_field(
        name="✨ Succès naturels (20)",
        value=ranking_field(stats.get("natural_success_ranking", []), NATURAL_SUCCESS_FLAVOR, NATURAL_SUCCESS_NONE_FLAVOR),
        inline=True,
    )
    embed.add_field(
        name="🕳️ Échecs naturels (1)",
        value=ranking_field(stats.get("natural_fail_ranking", []), NATURAL_FAIL_FLAVOR, NATURAL_FAIL_NONE_FLAVOR),
        inline=True,
    )

    embed.add_field(name="​", value="​", inline=False)

    best_name,  best_avg  = stats.get("best_damage",  (None, 0))
    worst_name, worst_avg = stats.get("worst_damage", (None, 0))
    most_name,  most_tot  = stats.get("most_damage",  (None, 0))
    least_name, least_tot = stats.get("least_damage", (None, 0))

    if best_name:
        embed.add_field(
            name="⚔️ Lame la plus affûtée",
            value=f"**{best_name}** — moy. `{best_avg:.1f}` dégâts/coup\n*{random.choice(BEST_DAMAGE_FLAVOR)}*",
            inline=True,
        )
    if worst_name:
        embed.add_field(
            name="🪨 Lame la plus émoussée",
            value=f"**{worst_name}** — moy. `{worst_avg:.1f}` dégâts/coup\n*{random.choice(WORST_DAMAGE_FLAVOR)}*",
            inline=True,
        )

    embed.add_field(name="​", value="​", inline=False)

    if most_name:
        embed.add_field(
            name="🩸 Bain de sang",
            value=f"**{most_name}** — `{most_tot}` au total\n*{random.choice(MOST_DAMAGE_FLAVOR)}*",
            inline=True,
        )
    if least_name and least_name != most_name:
        embed.add_field(
            name="🕊️ Main légère",
            value=f"**{least_name}** — `{least_tot}` au total\n*{random.choice(LEAST_DAMAGE_FLAVOR)}*",
            inline=True,
        )

    embed.set_footer(text="Les dégâts moyens excluent les échecs naturels (attaque ratée).")
    return embed


def _generate_player_error_embed(message: str) -> discord.Embed:
    """
        Génère un embed Discord pour afficher un message d'erreur lié à une action du joueur.

    Parameters
    ----------
    message : str
        Le message d'erreur à afficher.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant le message d'erreur.
    """
    embed = discord.Embed(
        title="❌ Erreur",
        description=message,
        color=discord.Color.red(),
        timestamp=datetime.datetime.now()
    )
    return embed


def _generate_help_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📖 Commandes disponibles",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.now()
    )

    embed.add_field(name="🎲 Dés", value=(
        "`/d` — Lancer un ou plusieurs dés\n"
        "`/dstats` — Lancer un dé basé sur une statistique"
    ), inline=False)

    embed.add_field(name="⚗️ Artisanat", value=(
        "`/craft info` — Consulter une recette\n"
        "`/craft list` — Lister les recettes disponibles\n"
        "`/craft execute` — Exécuter une recette"
    ), inline=False)

    embed.add_field(name="🎒 Objets", value=(
        "`/item info` — Consulter un objet\n"
        "`/equip` — Équiper un objet\n"
        "`/unequip` — Déséquiper un objet\n"
        "`/enchant` — Enchanter un objet\n"
        "`/unenchant` — Retirer une rune d'un objet\n"
        "`/item use` — Utiliser un objet\n"
        "`/item give` — Donner un objet à un autre joueur\n"
        "`/item discard` — Jeter un objet"
    ), inline=False)

    embed.add_field(name="👤 Personnage", value=(
        "`/my character` — Voir sa fiche personnage\n"
        "`/my buffs` — Voir ses buffs actifs\n"
        "`/my inventory` — Voir son inventaire\n"
        "`/my memory` — Voir ses fragments de mémoire\n"
        "`/my powers` — Voir ses pouvoirs\n"
        "`/my quests` — Voir les quêtes du groupe\n"
        "`/my stats` — Voir ses statistiques"
    ), inline=False)

    embed.add_field(name="✨ Pouvoirs", value=(
        "`/power info` — Consulter un pouvoir\n"
        "`/power use` — Utiliser un pouvoir"
    ), inline=False)

    embed.add_field(name="🗺️ Carte", value=(
        "`/map` — Afficher la carte du monde"
    ), inline=False)

    return embed


def _generate_city_arrival_embed(bot, arrival: bool = True) -> (discord.Embed, discord.File | None):
    embed = discord.Embed(
        title="🏙️ Arrivée en ville" if arrival else "🏙️ Actuellement en ville",
        description=f"Le groupe arrive à **{bot.location.city}**." if arrival else f"Le groupe est actuellement à **{bot.location.city}**.",
        color=COLOR_BY_TYPE.get(CITIES_DATA.get(bot.location.city, {}).get("type", ""), discord.Color.greyple())
    )

    embed.add_field(name="Royaume", value=bot.location.realm or "*(aucun)*", inline=True)

    embed.add_field(name="Population", value=str(CITIES_DATA.get(bot.location.city, {}).get("population", "Inconnue")), inline=True)

    embed.add_field(name="Description", value=CITIES_DATA.get(bot.location.city, {}).get("lore", "Aucune description disponible."), inline=False)

    NPCs = sorted(bot.npc_repository.by_city(bot.location.city), key=lambda x: x.roles[0])

    past_trades = bot.trade_repository.list_past_trades_ids()

    past_quests = bot.quest_progress.get_completed()
    

    met_npcs = []
    for npc in NPCs:
        npc_qid = [q.quest_id for q in npc.quests]
        npc_tid = [t.trade_id for t in npc.trades]
        if any(q in past_quests for q in npc_qid) or any(t in past_trades for t in npc_tid) and npc not in met_npcs:
            met_npcs.append(npc)

    embed.add_field(
        name=f"Personnages rencontrés [{len(met_npcs)}/{len(NPCs)}]", 
        value=(
            "\n".join(f"- {ROLE_ICONS.get(npc.roles[0], '👤')} **{npc.name}**" for npc in met_npcs)
            or "Aucun personnage notable rencontré."
        ), 
        inline=True
    )

    locations = CITIES_DATA.get(bot.location.city, {}).get("POIs", [])
    visited_locations = sorted(set(npc.location for npc in met_npcs))

    embed.add_field(
        name=f"Lieux visités [{len(visited_locations)}/{len(locations)}]", 
        value=(
            "\n".join(f"- 📍 **{loc}**" for loc in visited_locations)
            or "Aucun lieu notable visité."
        ), 
        inline=True
    )
    file = None
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    thumbnail_path = os.path.join(project_root, ASSETS_FOLDER, "cities", f"{bot.location.city.lower()}.png")

    if os.path.isfile(thumbnail_path):
        file = discord.File(thumbnail_path, filename="thumbnail.png")
        embed.set_image(url="attachment://thumbnail.png")

    return embed, file