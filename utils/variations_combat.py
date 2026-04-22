import discord



def _get_spawn_variations(enemy, count: int) -> dict:
    if enemy.boss:
        return SPAWN_BOSS
    if count >= 4:
        return SPAWN_HORDE
    if count > 1:
        return SPAWN_GROUP
    return SPAWN_SOLO


def _get_attack_variations(dmg: int) -> dict:
    if dmg <= 5:
        return ATTACK_WEAK
    if dmg <= 14:
        return ATTACK_NORMAL
    if dmg <= 20:
        return ATTACK_STRONG
    return ATTACK_DEVASTATING


# --------------------------------------------
# ----------------  SPAWN  -------------------
# --------------------------------------------

SPAWN_SOLO = {
    "titles": [
        "Un ennemi se dresse devant vous...",
        "Une présence menaçante surgit de l'ombre.",
        "Le silence se brise. Quelque chose approche.",
    ],
    "descriptions": [
        "Vous sentez le danger avant même de le voir.",
        "L'air se fige. L'ennemi vous a dans sa ligne de mire.",
        "Il n'y a nulle part où fuir.",
    ],
    "color": discord.Color.dark_red(),
}

SPAWN_GROUP = {
    "titles": [
        "Un groupe hostile se rapproche.",
        "Ils sont plusieurs. Et ils n'ont pas l'air commode.",
        "Des silhouettes émergent de l'obscurité.",
    ],
    "descriptions": [
        "Le nombre joue en leur faveur. Restez groupés.",
        "Chaque mouvement compte face à plusieurs adversaires.",
        "Ils se coordonnent. Il va falloir faire de même.",
    ],
    "color": discord.Color.orange(),
}

SPAWN_HORDE = {
    "titles": [
        "Une horde déferle sur vous !",
        "Ils sont partout. La situation est critique.",
        "Le sol tremble sous leurs pas.",
    ],
    "descriptions": [
        "Difficile de savoir où donner de la tête.",
        "Vous êtes submergés. Chaque seconde compte.",
        "Une vague de chair et d'acier fond sur vous.",
    ],
    "color": discord.Color.red(),
}

SPAWN_BOSS = {
    "titles": [
        "...",
        "Une présence écrasante envahit les lieux.",
        "Le sol lui-même semble céder sous son poids.",
    ],
    "descriptions": [
        "Vous avez fait une grave erreur en venant ici.",
        "Il vous regarde comme si vous étiez déjà morts.",
        "Quelque chose en vous vous dit de fuir. Maintenant.",
    ],
    "color": discord.Color.from_rgb(60, 0, 80),
}

# --------------------------------------------
# ---------------  ATTACK  -------------------
# --------------------------------------------

ATTACK_WEAK = {
    "titles": [
        "{enemy} effleure {character}.",
        "Un coup hésitant de {enemy} touche {character}.",
        "{character} esquive presque l'attaque de {enemy}.",
    ],
    "descriptions": [
        "À peine une égratignure.",
        "La douleur est vite oubliée.",
        "Un avertissement plus qu'une vraie blessure.",
    ],
    "color": discord.Color.yellow(),
}

ATTACK_NORMAL = {
    "titles": [
        "{enemy} frappe {character} de plein fouet.",
        "L'attaque de {enemy} atteint {character}.",
        "{character} encaisse un coup solide de {enemy}.",
    ],
    "descriptions": [
        "La douleur est réelle.",
        "Un coup qui se fera sentir.",
        "Il faudra faire attention.",
    ],
    "color": discord.Color.orange(),
}

ATTACK_STRONG = {
    "titles": [
        "{enemy} assène un coup violent à {character} !",
        "Une frappe dévastatrice de {enemy} percute {character} !",
        "{character} reçoit un coup brutal de {enemy} !",
    ],
    "descriptions": [
        "La blessure est sérieuse.",
        "Un tel coup pourrait changer le cours du combat.",
        "{character} chancelle sous l'impact.",
    ],
    "color": discord.Color.dark_orange(),
}

ATTACK_DEVASTATING = {
    "titles": [
        "{enemy} écrase {character} avec une force terrifiante !",
        "Un coup monstrueux de {enemy} s'abat sur {character} !",
        "{character} est balayé par la puissance de {enemy} !",
    ],
    "descriptions": [
        "La douleur est insoutenable.",
        "Peu survivent à un tel impact.",
        "Le sol lui-même semble trembler sous le coup.",
    ],
    "color": discord.Color.dark_red(),
}

# --------------------------------------------
# -----------------  END  --------------------
# --------------------------------------------


COMBAT_END = {
    "titles": [
        "Le silence retombe.",
        "La menace est écartée.",
        "Le combat est terminé.",
    ],
    "descriptions": [
        "Les ennemis ont été vaincus. Le calme revient, pour l'instant.",
        "La bataille est gagnée. Prenez soin de vos blessures.",
        "Plus rien ne bouge. La victoire est vôtre.",
    ],
    "color": discord.Color.dark_green(),
}