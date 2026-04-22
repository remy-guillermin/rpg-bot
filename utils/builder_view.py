import discord
import logging
from discord.ui import View, Button
from discord import Interaction

logger = logging.getLogger(__name__)
import math
import datetime
import os
import random

from instance.power import Power
from instance.buff import Buff
from instance.item import Item
from instance.lootbox import LootBox
from instance.trade import TradeProposal

from utils.builder_embed import (
    _generate_power_embed,
    _generate_item_embed,
    _generate_player_counter_offer_embed,
    _generate_sale_counter_offer_embed,
    _generate_player_error_embed
)
from utils.embeds.power import _generate_power_use_embed
from utils.path import ASSETS_FOLDER
from utils.utils import ITEMS_PER_PAGE, price_offer, STAT_MAP


# --- Powers --------------------------------
class PowersView(View):
    def __init__(self, character, my_command: bool = True):
        super().__init__(timeout=120)
        for i, power in enumerate(sorted(character.powers, key=lambda p: p.name)):
            button = PowerButton(power, index=i)
            self.add_item(button)


class PowerButton(Button):
    def __init__(self, power: Power, index: int):
        super().__init__(
            label=power.name,
            style=discord.ButtonStyle.secondary,
            custom_id=f"power_{index}",
            row=index // 5
        )
        self.power = power

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        await interaction.message.edit(view=self.view)

        embed = _generate_power_embed(self.power)

        if self.power.image_path is not None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            thumbnail_path = os.path.join(project_root, ASSETS_FOLDER, "powers", f"{self.power.image_path}.png")
            
            if os.path.isfile(thumbnail_path):
                file = discord.File(thumbnail_path, filename="power.png")
                embed.set_thumbnail(url="attachment://power.png")
                await interaction.response.send_message(embed=embed, file=file, ephemeral=False)
                return
            else:
                await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=False)


# --- Target Selection --------------------------------

class TargetSelectionView(View):
    def __init__(self, cog, power, caster, targets, guild, original_user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.power = power
        self.caster = caster
        self.guild = guild
        self.original_user_id = original_user_id

        options = [
            discord.SelectOption(label=char.name, value=char.name)
            for char in targets[:25]
        ]
        select = discord.ui.Select(
            placeholder="Choisir une cible...",
            options=options,
        )
        select.callback = self.on_target_selected
        self.add_item(select)

    async def on_target_selected(self, interaction: discord.Interaction):
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message("Ce menu ne vous appartient pas.", ephemeral=True)
            return

        await interaction.response.defer()

        target_name = interaction.data["values"][0]
        target = self.cog.character_repository.get_character_by_name(target_name)

        # Débit des ressources du lanceur + calcul de ses propres effets
        await self.cog.buff_repository.decrement_buffs_duration(self.guild, self.caster.name)
        buff_dict, power_effects, roll, instant_resources = await self.cog.power_repository.power_use(
            self.guild, self.caster, self.power.name
        )
        if buff_dict:
            caster_buff = Buff(**buff_dict)
            await self.cog.buff_repository.add_buff(self.guild, caster_buff)
        if instant_resources:
            self.cog.character_repository.change_resources(self.caster, **instant_resources)
        self.cog.character_repository.update_character(self.caster)

        # Effets sur la cible unique (count=1)
        for stat, (bonus, duration, count) in self.power.target_effect.items():
            if count != 1:
                continue
            if duration == -1:
                key = STAT_MAP.get(stat.lower())
                if key:
                    self.cog.character_repository.change_resources(target, **{key: bonus})
            else:
                target_buff = Buff(
                    name=self.power.name,
                    description=self.power.description,
                    duration=duration,
                    effects={stat: bonus},
                    character_name=target.name,
                    source=f"Pouvoir: {self.power.name} par {self.caster.name}",
                )
                await self.cog.buff_repository.add_buff(self.guild, target_buff)
        self.cog.character_repository.update_character(target)

        # Effets sur tous les joueurs actifs (count=-1)
        all_characters = [
            self.cog.character_repository.get_character_by_name(name)
            for name in self.cog.character_repository.players
        ]
        for aoe_target in all_characters:
            for stat, (bonus, duration, count) in self.power.target_effect.items():
                if count != -1:
                    continue
                if duration == -1:
                    key = STAT_MAP.get(stat.lower())
                    if key:
                        self.cog.character_repository.change_resources(aoe_target, **{key: bonus})
                else:
                    aoe_buff = Buff(
                        name=self.power.name,
                        description=self.power.description,
                        duration=duration,
                        effects={stat: bonus},
                        character_name=aoe_target.name,
                        source=f"Pouvoir: {self.power.name} par {self.caster.name}",
                    )
                    await self.cog.buff_repository.add_buff(self.guild, aoe_buff)
            self.cog.character_repository.update_character(aoe_target)

        embed = _generate_power_use_embed(
            self.power, self.caster.name, power_effects, roll,
            target_name=target_name, target_effect=self.power.target_effect,
        )
        await interaction.edit_original_response(content=None, embed=embed, view=None)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


# --- Buffs --------------------------------

class ConfirmBuffView(View):
    def __init__(self, cog, character, buff_effects, buff_name, description, character_name, kwargs, source):
        super().__init__(timeout=60)
        self.cog = cog
        self.character = character
        self.buff_effects = buff_effects
        self.buff_name = buff_name
        self.description = description
        self.character_name = character_name
        self.kwargs = kwargs
        self.source = source

    @discord.ui.button(label="Appliquer les buffs", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: Interaction, button: Button):
        for stat, (bonus, duration) in self.buff_effects.items():
            if duration > 0:
                new_buff = Buff(
                    name=self.buff_name,
                    description=self.description,
                    duration=duration,
                    effects={stat: bonus},
                    character_name=self.character_name,
                    source=self.source,
                )
                try:
                    await self.cog.buff_repository.add_buff(interaction.guild, new_buff)
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout du buff: {e}")
                self.cog.character_repository.update_character(self.character)
        if self.kwargs:
            self.cog.character_repository.change_resources(self.character, **self.kwargs)
        await interaction.response.edit_message(content="✅ Buffs appliqués avec succès.", embed=None, view=None)

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: Interaction, button: Button):
        await interaction.response.edit_message(content="❌ Application des buffs annulée.", embed=None, view=None)


class ConfirmRemoveBuffView(View):
    def __init__(self, cog, character_name: str, buff_name: str):
        super().__init__(timeout=60)
        self.cog = cog
        self.character_name = character_name
        self.buff_name = buff_name

    @discord.ui.button(label="Supprimer le buff", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: Interaction, button: Button):
        self.cog.buff_repository.remove_buff_by_name_and_character(self.buff_name, self.character_name)
        self.cog.character_repository.update_character(self.cog.character_repository.get_character_by_name(self.character_name))
        await interaction.response.edit_message(
            content=f"🗑️ Le buff **{self.buff_name}** de **{self.character_name}** a été supprimé.",
            embed=None, view=None
        )

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: Interaction, button: Button):
        await interaction.response.edit_message(content="❌ Suppression annulée.", embed=None, view=None)


class ConfirmClearBuffsView(View):
    def __init__(self, cog, character_name: str):
        super().__init__(timeout=60)
        self.cog = cog
        self.character_name = character_name

    @discord.ui.button(label="Supprimer les buffs", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: Interaction, button: Button):
        self.cog.buff_repository.clear_buffs_by_character(self.character_name)
        await interaction.response.edit_message(
            content=f"🗑️ Tous les buffs de **{self.character_name}** ont été supprimés.",
            embed=None, view=None
        )

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: Interaction, button: Button):
        await interaction.response.edit_message(content="❌ Suppression annulée.", embed=None, view=None)

# --- Items --------------------------------
class ItemListView(discord.ui.View):
    def __init__(self, items: list, author_id: int):
        super().__init__(timeout=60)
        self.items = items
        self.author_id = author_id
        self.page = 0
        self.total_pages = math.ceil(len(items) / ITEMS_PER_PAGE)
        self._update_buttons()

    def _update_buttons(self):
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= self.total_pages - 1

    def build_embed(self) -> discord.Embed:
        start = self.page * ITEMS_PER_PAGE
        page_items = self.items[start:start + ITEMS_PER_PAGE]

        embed = discord.Embed(
            title="🎒 Liste des objets",
            description="\n".join(
                f"- **{item.name}**"
                for i, item in enumerate(page_items)
            ),
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Page {self.page + 1} / {self.total_pages}  •  {len(self.items)} objets au total")
        return embed

    async def _check_author(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Ce menu ne vous appartient pas.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: Interaction, button: discord.ui.Button):
        if not await self._check_author(interaction):
            return
        self.page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: Interaction, button: discord.ui.Button):
        if not await self._check_author(interaction):
            return
        self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self):
        # Désactive les boutons après expiration
        for child in self.children:
            child.disabled = True


# --- Lootboxes --------------------------------

class LootBoxOpenedView(View):
    def __init__(self, lootbox: LootBox, rewards: list[tuple[Item, int]]):
        super().__init__(timeout=120)
        self.lootbox = lootbox
        self.rewards = rewards
        self.unique_items = list({item for item, qty in rewards})
        for i, item in enumerate(sorted(self.unique_items, key=lambda p: p.name)):
            button = LootBoxRewardButton(item, index=i)
            self.add_item(button)


class LootBoxRewardButton(Button):
    def __init__(self, item: Item, index: int):
        super().__init__(
            label=item.name,
            style=discord.ButtonStyle.secondary,
            disabled=False,
            row=index // 5
        )
        self.item = item

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        await interaction.message.edit(view=self.view)

        embed, file = _generate_item_embed(self.item)


        if file is not None:
            await interaction.response.send_message(embed=embed, file=file, ephemeral=False)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=False)


# --- Item notification --------------------------------

class NewItemNotificationView(View):
    def __init__(self, items: list[tuple[Item, int]]):
        super().__init__(timeout=120)
        for i, (item, _) in enumerate(items):
            self.add_item(LootBoxRewardButton(item, index=i))


# --- Crafting --------------------------------

class CraftInfoView(discord.ui.View):
    def __init__(self, craftable: bool):
        super().__init__()
        self.execute_button.disabled = not craftable
        self.execute_button.label = "⚒️ Exécuter le craft" if craftable else "❌ Craft non réalisable"
        self.execute_button.style = discord.ButtonStyle.green if craftable else discord.ButtonStyle.secondary

    @discord.ui.button(label="⚒️ Exécuter le craft", style=discord.ButtonStyle.green)
    async def execute_button(self, interaction: Interaction, button: discord.ui.Button):
        pass

# --- NPCs --------------------------------
class SaleCounterOfferView(discord.ui.View):
    def __init__(self, bot, character, npc_name: str, trade, counter_price: int):
        super().__init__(timeout=60)
        self.bot = bot
        self.character = character
        self.npc_name = npc_name
        self.trade = trade
        self.counter_price = counter_price

    def _disable_all(self, clicked: discord.ui.Button):
        for child in self.children:
            child.disabled = True
            if child is not clicked:
                child.style = discord.ButtonStyle.secondary

    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.success)
    async def accept(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
        if self.character.currency < self.counter_price:
            await btn_interaction.response.send_message(
                embed=_generate_player_error_embed(f"Tu n'as pas assez de monnaie ({self.character.currency} 🪙 disponibles)."),
                ephemeral=True,
            )
            return

        self._disable_all(button)
        await btn_interaction.message.edit(view=self)

        self.character.currency -= self.counter_price
        for entry in self.trade.offered_items:
            await self.character.inventory.add(btn_interaction.guild, self.character, entry.item, entry.quantity, trade=True)
        self.bot.character_repository.update_character(self.character)
        await self.bot.history.log_npc_trade(
            btn_interaction.guild, self.character.name, self.npc_name,
            self.trade.offered_items, [], self.counter_price,
        )
        self.stop()

        received = " · ".join(f"{e.quantity}x **{e.item.name}**" for e in self.trade.offered_items)
        await btn_interaction.response.send_message(
            content=f"✅ **{self.character.name}** achète {received} pour **{self.counter_price} 🪙**.",
        )

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger)
    async def decline(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
        self._disable_all(button)
        await btn_interaction.message.edit(view=self)
        self.stop()
        await btn_interaction.response.send_message(content="❌ Contre-offre refusée.")


class OfferView(discord.ui.View):
    def __init__(self, bot, character, npc, item, quantity, price, first_offer=True):
        super().__init__(timeout=60)
        self.bot = bot
        self.character = character
        self.npc = npc
        self.item = item
        self.quantity = quantity
        self.price = price
        if not first_offer:
            self.remove_item(self.counter_offer)

    def _disable_all(self, clicked: discord.ui.Button):
        for child in self.children:
            child.disabled = True
            if child is not clicked:
                child.style = discord.ButtonStyle.secondary

    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.success)
    async def accept(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
        self._disable_all(button)
        await btn_interaction.message.edit(view=self)
        await self.character.inventory.remove(btn_interaction.guild, self.character, self.item.name, self.quantity, trade=True)
        self.character.currency += self.price * self.quantity
        self.bot.character_repository.update_character(self.character)
        await self.bot.history.log_npc_offer(
            btn_interaction.guild, self.character.name, self.npc.name, self.item.name, self.quantity, self.price
        )
        self.stop()
        await btn_interaction.response.send_message(
            content=f"✅ **{self.character.name}** vend **{self.quantity}x {self.item.name}** pour **{self.price * self.quantity} 🪙**.",
        )

    @discord.ui.button(label="Contre-offre", style=discord.ButtonStyle.primary)
    async def counter_offer(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
        self._disable_all(button)
        await btn_interaction.message.edit(view=self)
        await btn_interaction.response.send_modal(
            CounterOfferModal(self.bot, self.character, self.npc, self.item, self.quantity, self.price, btn_interaction)
        )

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger)
    async def decline(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
        self._disable_all(button)
        await btn_interaction.message.edit(view=self)
        self.stop()
        await btn_interaction.response.send_message(content="❌ Offre refusée.")


class CounterOfferModal(discord.ui.Modal, title="Contre-offre"):
    price = discord.ui.TextInput(
        label="Ton prix proposé (par unité, en 🪙)",
        placeholder="ex: 50",
        min_length=1,
        max_length=6,
    )

    def __init__(self, bot, character, npc, item, quantity, original_price, original_interaction: discord.Interaction):
        super().__init__()
        self.bot = bot
        self.character = character
        self.npc = npc
        self.item = item
        self.quantity = quantity
        self.original_price = original_price
        self.original_interaction = original_interaction

    async def on_submit(self, interaction: discord.Interaction):
        from utils.embeds.npc import _generate_npc_offer_embed

        try:
            counter_price = int(self.price.value)
        except ValueError:
            await interaction.response.send_message("❌ Prix invalide.", ephemeral=True)
            return

        if counter_price <= 0:
            await interaction.response.send_message("❌ Le prix doit être supérieur à 0.", ephemeral=True)
            return


        charisma_bonus = self.character.stat_points.get("Charisme", 0)
        
        # Calcul du seuil : plus le prix est haut par rapport à l'offre initiale, plus c'est dur
        if counter_price <= self.original_price:
            threshold = 0  # Toujours accepté si on offre plus que le prix du NPC
        else:
            ratio = max(1, min(100, int(self.original_price / counter_price * 100)))
            threshold = price_offer(ratio) * (1 - 2 * charisma_bonus / 100)


        roll = random.randint(1, 100)
        success = roll >= threshold
        last_offer = False
        if not success:
            if roll >= threshold / 2:
                last_offer = True
                last_price = random.randint(self.original_price+1, counter_price-1)

        if success:
            await self.character.inventory.remove(interaction.guild, self.character, self.item.name, self.quantity, trade=True)
        
            proposal = TradeProposal(
                trade_id="offer",
                offered_items=[],
                offered_value=counter_price * self.quantity,
                player=self.character.name,
            )
            self.character.currency += counter_price * self.quantity
            self.bot.character_repository.update_character(self.character)

            await self.bot.history.log_npc_offer(
                interaction.guild, self.character.name, self.npc.name, self.item.name, self.quantity, counter_price
            )
            self.stop()

            embed = _generate_player_counter_offer_embed(self.npc.name, self.item.name, self.quantity, counter_price)
            embed.set_footer(text=f"Contre-offre proposée à {counter_price} 🪙/unité (offre initiale : {self.original_price} 🪙/unité)")

            await interaction.response.send_message(embed=embed, view=None)
        elif last_offer:
            embed = _generate_npc_offer_embed(self.npc.name, self.item.name, self.quantity, last_price, self.item.value, last_offer=True)
            embed.set_footer(text=f"{self.npc.name} propose une dernière offre à {last_price} 🪙/unité (offre initiale : {self.original_price} 🪙/unité)")
            await interaction.response.send_message(embed=embed, view=OfferView(self.bot, self.character, self.npc, self.item, self.quantity, last_price, first_offer=False))
        else:
            embed = discord.Embed(
                title="Offre refusée",
                description=f"❌ **{self.npc.name}** refuse ta contre-offre de **{counter_price} 🪙/unité**.\n\n"
                            f"Roll: {roll} (seuil de réussite: {threshold})",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, view=None)

