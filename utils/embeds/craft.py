import discord
import datetime
import random
import locale

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from instance.character import Character
    from instance.craft import Craft

from utils.utils import (
    METHOD_CLEAN,
    EMOJI_BY_METHOD,
)
from utils.variations import (
    CRAFT_STATUS_STYLE,
    CRAFT_STATUS_DESCRIPTION,
)


def _generate_craft_list_embed(crafts: list["Craft"], craftable_quantity: dict[str, int]) -> discord.Embed:
    """
    Génère un embed Discord contenant la liste des crafts disponibles.

    Parameters
    ----------
    crafts : list[Craft]
        La liste des crafts à afficher.
    craftable_quantity : dict[str, int]
        Dictionnaire {nom_craft: quantité craftable} pour le personnage.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant la liste des crafts disponibles.
    """
    embed = discord.Embed(title="📜 Recettes disponibles", color=discord.Color.dark_gold())

    by_method = {}
    for craft in crafts:
        by_method.setdefault(METHOD_CLEAN.get(craft.method, craft.method), []).append(craft)

    for method, method_crafts in sorted(by_method.items(), key=lambda x: locale.strxfrm(x[0])):
        lines = []
        for craft in sorted(method_crafts, key=lambda c: locale.strxfrm(c.name)):
            stars = "★" * craft.difficulty + "☆" * (5 - craft.difficulty)
            qty = craftable_quantity.get(craft.name, 0)
            quantity_str = f" *[{qty} craftable]*" if qty > 0 else ""
            lines.append(f"{stars} - **{craft.name}**{quantity_str}")
        embed.add_field(name=f"{EMOJI_BY_METHOD.get(method, '')} {method.capitalize()}", value="\n".join(lines), inline=False)

    return embed


def _generate_craft_info_embed(craft: "Craft", character: "Character") -> discord.Embed:
    """
    Génère un embed Discord contenant les informations sur un craft.

    Parameters
    ----------
    craft : Craft
        La recette pour laquelle afficher les informations.
    character : Character
        Le personnage pour lequel afficher les informations.

    Returns
    -------
    discord.Embed
        L'embed Discord contenant les informations sur le craft.
    """
    method_clean = METHOD_CLEAN.get(craft.method, craft.method)
    emoji = EMOJI_BY_METHOD.get(method_clean, "")
    stars = "★" * craft.difficulty + "☆" * (5 - craft.difficulty)

    embed = discord.Embed(
        title=f"{emoji} {craft.name}",
        description="",
        color=discord.Color.dark_gold()
    )
    embed.add_field(name="Méthode", value=method_clean, inline=True)
    embed.add_field(name="Difficulté", value=stars, inline=True)

    embed.add_field(name="Description", value=craft.description, inline=False)

    ingredient_lines = []
    for component in craft.ingredients:
        owned = character.inventory.get_quantity(component["item"])
        required = component["quantity"]
        ingredient_lines.append(f"{component['item']} : {owned}/{required}")
    embed.add_field(name="🧺 Ingrédients", value="\n".join(ingredient_lines), inline=True)

    product_lines = [f"{p['item']} x{p['quantity']}" for p in craft.base_products]
    embed.add_field(name="🎁 Produit", value="\n".join(product_lines), inline=True)

    return embed


def _generate_craft_executed_embed(craft: "Craft", quantity: int, craft_status: str, products: list[dict]) -> discord.Embed:
    """
    Génère un embed Discord narratif décrivant l'exécution d'un craft.

    Parameters
    ----------
    craft : Craft
        La recette qui a été exécutée.
    quantity : int
        La quantité de crafts exécutés.
    craft_status : str
        Le statut du craft (succès, échec, etc.) déterminé par le résultat du jet de dés.
    products : list[dict]
        La liste des produits obtenus suite à l'exécution du craft, avec leur nom et quantité.

    Returns
    -------
    discord.Embed
        L'embed Discord décrivant l'exécution du craft.
    """
    method_clean = METHOD_CLEAN.get(craft.method, craft.method)
    emoji_method = EMOJI_BY_METHOD.get(method_clean, "")
    stars = "★" * craft.difficulty + "☆" * (5 - craft.difficulty)

    style = CRAFT_STATUS_STYLE.get(craft_status, CRAFT_STATUS_STYLE["normal"])
    description = random.choice(CRAFT_STATUS_DESCRIPTION.get(craft_status, CRAFT_STATUS_DESCRIPTION["normal"]))


    embed = discord.Embed(
        title=f"{style['emoji']} {style['label']} — {craft.name}",
        description=description,
        color=style["color"],
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name=f"{emoji_method} Méthode", value=method_clean, inline=True)
    embed.add_field(name="Difficulté", value=stars, inline=True)

    if products:
        product_lines = [f"{p['item']} x{p['quantity'] * quantity}" for p in products]
        embed.add_field(name="🎁 Produit obtenu", value="\n".join(product_lines), inline=False)
    else:
        embed.add_field(name="🎁 Produit obtenu", value="*Aucun produit obtenu.*", inline=False)

    return embed


def _generate_craft_execution_history_embed(character_name: str, craft: "Craft", quantity: int, timestamp: datetime.datetime, craft_status: str, products: list[dict], roll: dict) -> discord.Embed:
    """
    Génère un embed Discord pour afficher une entrée d'historique d'exécution de craft.

    Parameters
    ----------
    character_name : str
        Le nom du personnage qui a exécuté le craft.
    craft : Craft
        L'objet craft exécuté.
    quantity : int
        La quantité de crafts exécutés.
    timestamp : datetime.datetime
        L'horodatage de l'exécution du craft.
    craft_status : str
        Le statut du craft (ex. "success", "failure", "critical_success", "critical_failure").
    products : list[dict]
        La liste des produits obtenus par le craft, chaque produit étant un dictionnaire avec les clés "item" (nom de l'objet) et "quantity" (quantité obtenue).
    roll : dict
        Les détails du lancer de dés utilisé pour exécuter le craft.

    Returns
    -------
    discord.Embed
        L'embed Discord affichant l'entrée d'historique.
    """
    method_clean = METHOD_CLEAN.get(craft.method, craft.method)

    title = f"🔨 {character_name} — {quantity}x {craft.name}"

    ingredients_lines = "".join(f"- {ingredient['item']} x{ingredient['quantity'] * quantity}\n" for ingredient in craft.ingredients)
    description = f"**Ingrédients consommés :**\n{ingredients_lines}"

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue(),
        timestamp=timestamp
    )

    embed.add_field(name="Méthode", value=method_clean, inline=True)
    embed.add_field(name="Statut", value=craft_status, inline=True)

    roll_value = f"`{roll['base_total']}`"
    if roll["modifier"] != 0:
        sign = "+" if roll["modifier"] > 0 else ""
        roll_value += f" ({sign}{roll['modifier']}) = `{roll['total']}`"
    embed.add_field(name="🎲 Lancer", value=roll_value, inline=True)

    if products:
        product_lines = "\n".join(f"- {p['item']} x{p['quantity'] * quantity}" for p in products)
    else:
        product_lines = "*Aucun produit obtenu.*"
    embed.add_field(name="🎁 Produits obtenus", value=product_lines, inline=False)

    return embed
