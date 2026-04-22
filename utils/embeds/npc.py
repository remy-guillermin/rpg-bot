import discord
import datetime

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from instance.npc import NPC, Quest
    from instance.item import Item
    from instance.inventory import InventoryEntry

from utils.utils import (
    COLOR_NPC,
    COLOR_QUEST,
    COLOR_SUCCESS,
    STATS_CLEAN,
    RARITY_CLEAN_ITEM,
    RUNES_COST,
    UPGRADE_EQUIPMENT,
    roles_display,
)
from instance.quest_progress import QuestStatus


def _generate_npc_embed(npc: "NPC", completed: set[str] | None = None, runes_rarity_discovered: set[str] | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=npc.name,
        description="",
        color=COLOR_NPC,
    )
    role = npc.roles

    if role == ["black_market_dealer"]:
        if npc.quests and npc.quests[0].quest_id not in (completed or set()):
            role = ["merchant"]

    embed.add_field(name="📍 Localisation", value=npc.location, inline=True)
    embed.add_field(name="Rôles", value=roles_display(role), inline=True)

    embed.add_field(name="Description", value=npc.description or "Aucune description.", inline=False)

    if npc.has_role("quest_giver") and npc.quests:
        npc_available = npc.visible_quests(completed or set())
        npc_completed = [q for q in npc.quests if q.quest_id in (completed or set())]
        npc_available = [q for q in npc_available if q.quest_id not in (completed or set())]

        if npc_available:
            embed.add_field(
                name="📜 Quêtes disponibles",
                value="\n".join(f"• **{q.title}**" for q in npc_available),
                inline=True,
            )
        else:
            embed.add_field(
                name="📜 Quêtes",
                value="Aucune quête disponible.",
                inline=True,
            )
        if npc_completed:
            embed.add_field(
                name="✅ Quêtes complétées",
                value="\n".join(f"• **{q.title}**" for q in npc_completed),
                inline=True,
            )
    if npc.has_role("merchant") or npc.has_role("black_market_dealer") and npc.trades:

        npc_available = npc.visible_quests(completed or set())
        npc_completed = [q for q in npc.quests if q.quest_id in (completed or set())]
        npc_available = [q for q in npc_available if q.quest_id not in (completed or set())]

        if npc_available:
            embed.add_field(
                name="📜 Quêtes disponibles",
                value="\n".join(f"• **{q.title}**" for q in npc_available),
                inline=True,
            )
        elif npc_completed:
            embed.add_field(
                name="✅ Quêtes complétées",
                value="\n".join(f"• **{q.title}**" for q in npc_completed),
                inline=True,
            )
        else:
            embed.add_field(name="\u200b", value="\u200b", inline=False)
        

        trades = [t for t in npc.trades if t.type == "trade" and not t.blackmarket]
        trades_lines = []
        sales = [t for t in npc.trades if t.type == "sale" and not t.blackmarket]
        sales_lines = []

        black_market_sales = [t for t in npc.trades if t.type == "sale" and t.blackmarket]
        black_market_sales_lines = []

        for trade in trades:
            requests = " & ".join(f"{entry.quantity}x {entry.item.name}" for entry in trade.requested_items)
            line = f"✦ **{trade.offered_items[0].quantity}x {trade.offered_items[0].item.name}** - en échange de {requests} - {trade.quantity} en stock"
            trades_lines.append(line)

        for sale in sales:
            line = f"✦ **{sale.offered_items[0].quantity}x {sale.offered_items[0].item.name}** - {sale.price} 🪙 - {sale.quantity} en stock"
            sales_lines.append(line)

        for bm_sale in black_market_sales:
            line = f"✦ **{bm_sale.offered_items[0].quantity}x {bm_sale.offered_items[0].item.name}** - {bm_sale.price} 🪙 - {bm_sale.quantity} en stock"
            black_market_sales_lines.append(line)

        if sales_lines:
            embed.add_field(
                name=f"💰 {'Vente' if len(sales_lines) == 1 else 'Ventes'} :",
                value="\n".join(sales_lines),
                inline=False,
            )

        if trades_lines:
            embed.add_field(
                name=f"🤝 {'Échange' if len(trades_lines) == 1 else 'Échanges'} :",
                value="\n".join(trades_lines),
                inline=False,
            )

        if black_market_sales_lines and npc.quests and npc.quests[0].quest_id in (completed or set()):
            embed.add_field(
                name=f"🕵️‍♂️ {'Vente du marché noir' if len(black_market_sales_lines) == 1 else 'Ventes du marché noir'} :",
                value="\n".join(black_market_sales_lines),
                inline=False,
            )

    if npc.has_role("blacksmith"):
        runes_lines = []
        _rarity_order = ["rare", "epic", "legendary", "mythic"]
        for r in sorted(runes_rarity_discovered, key=lambda x: _rarity_order.index(x) if x in _rarity_order else 99):
            runes_lines.append(f"✦ **{RARITY_CLEAN_ITEM.get(r, r)}** - en échange de {RUNES_COST.get(r, '?')} 🪙")

        embed.add_field(
            name="💎 Enchâssements",
            value="\n".join(runes_lines),
            inline=False
        )

        upgrades_lines = []
        for upgrade in UPGRADE_EQUIPMENT:
            upgrades_lines.append(f"✦ **{upgrade['dest']}** - amélioration de {upgrade['source']} pour {upgrade['cost']} 🪙")

        embed.add_field(
            name="⚒️ Améliorations",
            value="\n".join(upgrades_lines),
            inline=False
        )

        sales_lines = []
        for sale in npc.trades:
            line = f"✦ **{sale.offered_items[0].quantity}x {sale.offered_items[0].item.name}** - {sale.price} 🪙 - {sale.quantity} en stock"
            sales_lines.append(line)

        if sales_lines:
            embed.add_field(
                name=f"⚒️ Vente d'équipements :",
                value="\n".join(sales_lines),
                inline=False,
            )
        

    return embed


def _generate_quest_embed(quest: "Quest", status: "QuestStatus | None" = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"📜 {quest.title}",
        description=quest.description,
        color=COLOR_QUEST,
    )
    embed.add_field(name="ID", value=f"`{quest.quest_id}`", inline=True)
    embed.add_field(name="NPC", value=quest.npc_name, inline=True)

    if status:
        labels = {
            QuestStatus.ACTIVE: "🟡 En cours",
            QuestStatus.COMPLETED: "✅ Complétée",
            QuestStatus.FAILED: "❌ Échouée",
        }
        embed.add_field(name="Statut", value=labels.get(status, status), inline=True)

    conditions = []
    if quest.condition_quest:
        conditions.append(f"Quête préalable : `{quest.condition_quest}`")
    if quest.condition_items:
        items_str = ", ".join(f"{qi.quantity}x {qi.item.name}" for qi in quest.condition_items)
        conditions.append(f"Items requis : {items_str}")
    if conditions:
        embed.add_field(name="Conditions", value="\n".join(conditions), inline=False)

    rewards = []
    if quest.reward_xp:
        rewards.append(f"{quest.reward_xp} XP")
    if quest.reward_items:
        items_str = ", ".join(f"{qi.quantity}x {qi.item.name}" for qi in quest.reward_items)
        rewards.append(items_str)
    if rewards:
        embed.add_field(name="Récompenses", value=" · ".join(rewards), inline=False)

    return embed


def _generate_npc_trade_history_embed(
    character_name: str,
    npc_name: str,
    received_items: list,
    given_items: list,
    currency: int,
    timestamp: "datetime.datetime",
) -> discord.Embed:
    embed = discord.Embed(
        title=f"🤝 {character_name} ↔ {npc_name}",
        color=discord.Color.blurple(),
        timestamp=timestamp,
    )
    if received_items:
        embed.add_field(
            name=f"{character_name} reçoit",
            value="\n".join(f"{e.quantity}x **{e.item.name}**" for e in received_items),
            inline=True,
        )
    if given_items:
        embed.add_field(
            name=f"{npc_name} reçoit",
            value="\n".join(f"{e.quantity}x **{e.item.name}**" for e in given_items),
            inline=True,
        )
    if currency:
        embed.add_field(name="Monnaie échangée", value=f"{currency} 🪙", inline=True)
    return embed


def _generate_npc_offer_history_embed(
    character_name: str,
    npc_name: str,
    item_name: str,
    quantity: int,
    price_per_unit: int,
    timestamp: "datetime.datetime",
) -> discord.Embed:
    total = price_per_unit * quantity
    embed = discord.Embed(
        title=f"💰 {character_name} vend à {npc_name}",
        description=f"**{quantity}x {item_name}** vendu pour **{total} 🪙** ({price_per_unit} 🪙/unité)",
        color=discord.Color.gold(),
        timestamp=timestamp,
    )
    return embed


def _generate_npc_offer_embed(npc_name: str, item_name: str, quantity: int, price: int, base_price: int, last_offer: bool = False) -> discord.Embed:
    total = price * quantity
    offer = price - base_price
    offer_display = f"{offer/base_price:+.0%}" if offer != 0 else "0"
    embed = discord.Embed(
        title=f"🏷️ Offre de {npc_name}",
        description=f"**{npc_name}** propose d'acheter **{quantity}x {item_name}** pour **{total} 🪙** ({price} 🪙 / unité). Différence par rapport au prix de base : {offer_display}",
        color=discord.Color.gold() if not last_offer else discord.Color.blue(),
    )
    if last_offer:
        embed.set_footer(text=f"**{npc_name}** propose une dernière offre à {price} 🪙/unité (offre initiale : {base_price} 🪙/unité)")
    else:
        embed.set_footer(text="Cette offre est valable jusqu'à la prochaine mise à jour des prix.")
    return embed


def _generate_player_counter_offer_embed(npc_name: str, item_name: str, quantity: int, counter_price: int) -> discord.Embed:
    total = counter_price * quantity
    embed = discord.Embed(
        title=f"🔁 Contre-offre acceptée par {npc_name}",
        description=f"Tu proposes de vendre **{quantity}x {item_name}** pour **{total} 🪙** ({counter_price} 🪙 / unité) et {npc_name} accepte ta contre-offre !",
        color=discord.Color.green(),
    )
    return embed


def _generate_sale_counter_offer_embed(npc_name: str, trade: "Trade", counter_price: int, roll: int) -> discord.Embed:
    received = " · ".join(f"{e.quantity}x **{e.item.name}**" for e in trade.offered_items)
    embed = discord.Embed(
        title=f"🔁 Contre-offre de {npc_name}",
        description=(
            f"Ton offre a été refusée (jet : {roll}), mais **{npc_name}** accepterait de te vendre {received} "
            f"pour **{counter_price} 🪙**.\n\nVeux-tu accepter ?"
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"NPC : {npc_name}")
    return embed


def _generate_trade_result_embed(
    npc_name: str,
    trade: "Trade",
    result: str,
    roll: int,
) -> discord.Embed:
    if result == "Trade successful":
        color = discord.Color.green()
        title = "✅ Échange conclu"
        received = " · ".join(f"{e.quantity}x **{e.item.name}**" for e in trade.offered_items)
        description = f"Tu reçois : {received}"
    elif result == "Failed trade - offer too low":
        color = discord.Color.red()
        title = "❌ Offre refusée"
        description = f"**{npc_name}** n'a pas accepté ton offre. (jet : {roll})"
    elif result == "Not available":
        color = discord.Color.orange()
        title = "⚠️ Indisponible"
        description = "Cet article n'est plus disponible."
    else:
        color = discord.Color.greyple()
        title = "❓ Résultat inconnu"
        description = result

    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f"NPC : {npc_name}")
    return embed


def _generate_blacksmith_enchant_embed(npc_name: str, rune: "Item", item_entry: "InventoryEntry", cost: int) -> discord.Embed:
    bonus_lines = "\n".join(
        f"• {STATS_CLEAN.get(s, s)}: +{b}" for s, b in rune.equipped_bonus.items()
    ) or "Aucun bonus"
    slots_now = len(item_entry.runes)
    embed = discord.Embed(
        title="⚒️ Enchâssement réussi",
        description=(
            f"**{rune.name}** a été enchâssée dans **{item_entry.item.name}** par {npc_name}.\n\n"
            f"**Bonus apportés :**\n{bonus_lines}\n\n"
            f"Slots : {slots_now}/{item_entry.item.rune_slots}"
        ),
        color=discord.Color.purple(),
        timestamp=datetime.datetime.now(),
    )
    embed.set_footer(text=f"Coût : {cost}🪙 | Forgeron : {npc_name}")
    return embed


def _generate_blacksmith_upgrade_embed(npc_name: str, source_item: "Item", dest_item: "Item", cost: int) -> discord.Embed:
    def bonus_str(item: "Item") -> str:
        if not item.equipped_bonus:
            return "Aucun"
        return ", ".join(f"{STATS_CLEAN.get(s, s)}: {b:+d}" for s, b in item.equipped_bonus.items())

    embed = discord.Embed(
        title="⚒️ Équipement amélioré",
        description=f"{npc_name} a amélioré l'équipement de ton personnage.",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now(),
    )
    embed.add_field(name=f"Avant — {source_item.name}", value=bonus_str(source_item), inline=True)
    embed.add_field(name=f"Après — {dest_item.name}", value=bonus_str(dest_item), inline=True)
    embed.set_footer(text=f"Coût : {cost}🪙 | Forgeron : {npc_name}")
    return embed


def _generate_memory_fragment_embed(fragment, my_command: bool = True) -> discord.Embed:
    embed = discord.Embed(
        title=f"🧩 {f'{fragment.id} - ' if my_command else ''}{fragment.name}",
        description=fragment.content,
        color=discord.Color.gold() if my_command else discord.Color.dark_purple(),
        timestamp=datetime.datetime.now()
    )
    return embed
