import discord
from discord.ext import commands
from discord import app_commands, Interaction

import datetime
import random

from utils.builder_embed import (
    _generate_item_embed,
    _generate_player_error_embed,
    _generate_item_equip_embed,
    _generate_item_discard_embed,
    _generate_item_trade_embed,
    _generate_item_use_embed,
    _generate_relic_used_embed,
    _notify_admin_relic_used_embed,
    _generate_new_item_notification_embed,
    _generate_set_discovery_embed,
)
from utils.admin import handle_admin_permission_error, admin_only
from utils.builder_view import ItemListView, NewItemNotificationView
from utils.autocomplete import (
    make_item_autocomplete,
    make_item_info_autocomplete,
    make_items_autocomplete,
    make_equippable_item_autocomplete,
    make_unequippable_item_autocomplete,
    make_useable_item_autocomplete,
    make_character_autocomplete,
    make_enchantable_entry_autocomplete,
    make_enchanted_entry_autocomplete,
    make_rune_autocomplete,
    make_rune_on_entry_autocomplete,
    make_tag_autocomplete,
)
from utils.path import ADMIN_CHANNEL_NAME
from utils.utils import _get_resource_max_bonus, _get_active_sets, SETS, ENCHANT_THRESHOLDS, ENCHANT_COOLDOWN_MINUTES

from instance.item import Item
from instance.buff import Buff

class Items(commands.Cog):
    """Commandes liées aux objets."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.item_repository = bot.item_repository
        self.character_repository = bot.character_repository
        self.buff_repository = bot.buff_repository

        self.item_group = app_commands.Group(name="item", description="Commandes liées aux objets.")
        bot.tree.add_command(self.item_group)
        self._enchant_cooldowns: dict[int, datetime.datetime] = {}  # user_id → last failed attempt


    def _resolve_callback(self, member):
        """Return the underlying callable for an app_commands.Command or the member itself."""
        return getattr(member, "callback", member)
    

    async def item_autocomplete(self, interaction: Interaction, current: str):
        return await make_item_autocomplete(self.bot.character_repository)(interaction, current)

    async def item_info_autocomplete(self, interaction: Interaction, current: str):
        return await make_item_info_autocomplete(self.bot.character_repository)(interaction, current)
        
    async def items_autocomplete(self, interaction: Interaction, current: str):
        return await make_items_autocomplete(self.bot.item_repository)(interaction, current)
    
    async def item_equippable_autocomplete(self, interaction: Interaction, current: str):
        return await make_equippable_item_autocomplete(self.bot.character_repository)(interaction, current)

    async def item_unequippable_autocomplete(self, interaction: Interaction, current: str):
        return await make_unequippable_item_autocomplete(self.bot.character_repository)(interaction, current)

    async def item_useable_autocomplete(self, interaction: Interaction, current: str):
        return await make_useable_item_autocomplete(self.bot.character_repository)(interaction, current)

    async def character_name_autocomplete(self, interaction: Interaction, current: str):
        return await make_character_autocomplete(self.bot.character_repository)(interaction, current)

    async def enchantable_entry_autocomplete(self, interaction: Interaction, current: str):
        return await make_enchantable_entry_autocomplete(self.bot.character_repository)(interaction, current)

    async def enchanted_entry_autocomplete(self, interaction: Interaction, current: str):
        return await make_enchanted_entry_autocomplete(self.bot.character_repository)(interaction, current)

    async def rune_autocomplete(self, interaction: Interaction, current: str):
        return await make_rune_autocomplete(self.bot.character_repository)(interaction, current)

    async def rune_on_entry_autocomplete(self, interaction: Interaction, current: str):
        return await make_rune_on_entry_autocomplete(self.bot.character_repository)(interaction, current)
    

    # ── Commandes ────────────────────────────────────────────────────
    @app_commands.command(name="items", description="Affiche la liste des objets disponibles.")
    @admin_only()
    async def item_list(self, interaction: Interaction, tag: str = None):
        """Affiche la liste des objets disponibles."""
        if tag in self.item_repository.tags:
            items = sorted(self.item_repository.get_items_by_tag(tag), key=lambda x: x.name)
        else:
            items = sorted(self.item_repository.list_items(), key=lambda x: x.name)
        if not items:
            await interaction.response.send_message("Aucun objet disponible.", ephemeral=True)
            return

        view = ItemListView(items=items, author_id=interaction.user.id)
        await interaction.response.send_message(embed=view.build_embed(), view=view)

    @app_commands.command(name="give-item", description="Donne un objet à un joueur.")
    @admin_only()
    @app_commands.autocomplete(
        item_name=items_autocomplete,
        target_name=character_name_autocomplete
    )
    async def give_item(self, interaction: Interaction, item_name: str, target_name: str, quantity: int = 1):
        """Donne un objet à un joueur."""
        await interaction.response.defer()

        item = self.item_repository.get_item_by_name(item_name)
        if not item:
            await interaction.followup.send(embed=_generate_player_error_embed(f"Objet '{item_name}' non trouvé."), ephemeral=False)
            return

        target = self.character_repository.get_character_by_name(target_name)
        if not target:
            await interaction.followup.send(embed=_generate_player_error_embed(f"Le personnage '{target_name}' n'existe pas."), ephemeral=False)
            return

        if quantity < 1:
            await interaction.followup.send(embed=_generate_player_error_embed("La quantité doit être d'au moins 1."), ephemeral=False)
            return

        inventory_target = target.inventory
        if not inventory_target:
            await interaction.followup.send(embed=_generate_player_error_embed(f"Le personnage '{target_name}' n'a pas d'inventaire."), ephemeral=False)
            return

        if inventory_target.slots_available() < quantity:
            await interaction.followup.send(embed=_generate_player_error_embed(f"{target.name} n'a pas assez de place dans son inventaire pour recevoir {quantity} '{item_name}'. \n Actuellement il lui reste {inventory_target.slots_available()} emplacement{'' if inventory_target.slots_available() == 1 else 's'} de libre."), ephemeral=False)
            return

        has_added = await inventory_target.add(interaction.guild, target, item, quantity, True)
        if not has_added:
            await interaction.followup.send(embed=_generate_player_error_embed(f"Impossible de donner '{item_name}' à {target.name}."), ephemeral=False)
            return
            
        self.character_repository.update_character(target)

        await self.bot.history.log_transaction(interaction.guild, "Admin", target.name, item.name, quantity, is_gift=True)

        channel = interaction.client.get_channel(target.player_channel_id)
        if channel is None and interaction.guild is not None:
            channel = interaction.guild.get_channel(target.player_channel_id)

        if channel is not None:
            embed, file = _generate_new_item_notification_embed(item, quantity, origin="admin_give")
            view = NewItemNotificationView([(item, quantity)])
            if file is not None:
                await channel.send(embed=embed, file=file, view=view)
            else:
                await channel.send(embed=embed, view=view)
        else:
           await interaction.followup.send(embed=_generate_player_error_embed(f"Impossible de notifier {target.name} de la réception de l'objet car son salon privé est introuvable."), ephemeral=False)
        
        await interaction.followup.send(
            f"**{quantity}× {item.name}** donné à {target.name}.", ephemeral=False
        )


    @app_commands.describe(item_name="Le nom de l'objet à afficher.")
    async def item_info(self, interaction: Interaction, item_name: str):
        """Affiche les informations sur un objet."""
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas de personnage associé à ton compte."), ephemeral=False)
            return

        # Detect if value is an entry_id (equippable instance) or an item name
        entry = character.inventory.get_entry_by_id(item_name)
        if entry:
            item = entry.item
        else:
            item = self.item_repository.get_item_by_name(item_name)
            entry = None

        if not item:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Objet '{item_name}' non trouvé."), ephemeral=False)
            return


        ingredient_for = self.bot.craft_repository.find_crafts_by_ingredient(item.name)
        product_of = self.bot.craft_repository.find_crafts_by_product(item.name)

        embed, file = _generate_item_embed(item, entry, ingredient_for=ingredient_for, product_of=product_of, character=character)

        if file is not None:
            await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="equip", description="Equipe un objet de ton inventaire.")
    @app_commands.autocomplete(
        item_name=item_equippable_autocomplete,
    )
    @app_commands.describe(item_name="Le nom de l'objet à équiper.")
    async def item_equip(self, interaction: Interaction, item_name: str):
        """Equipe un objet de ton inventaire."""
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas de personnage associé à ton compte."), ephemeral=False)
            return

        inventory = character.inventory
        if not inventory or not inventory.has_item(item_name):
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Tu n'as pas l'objet '{item_name}' dans ton inventaire."), ephemeral=False)
            return

        entry = inventory.get_entry(item_name)
        if not entry or not entry.item.equippable:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"'{item_name}' n'est pas équippable."), ephemeral=False)
            return

        unequipped = [e for e in inventory.get_entries_by_name(item_name) if e.equipped_quantity == 0]
        if not unequipped:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Tu n'as pas d'exemplaire non-équippé de '{item_name}'."), ephemeral=False)
            return
        entry = unequipped[0]
    
        hp_base, hp_level, hp_item        = _get_resource_max_bonus("hp", character)
        mana_base, mana_level, mana_item  = _get_resource_max_bonus("mana", character)
        stam_base, stam_level, stam_item  = _get_resource_max_bonus("stamina", character)

        has_equipped = inventory.equip(item_name, character)
        if not has_equipped:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Impossible d'équiper '{item_name}'."), ephemeral=False)
            return


        item_bonus = entry.item.equipped_bonus

        self.character_repository.update_resources(
            character, 
            resources_max={
                "hp": hp_base + hp_level + hp_item,
                "mana": mana_base + mana_level + mana_item,
                "stamina": stam_base + stam_level + stam_item
            },
            variations = {
                "hp": item_bonus.get("hp_max", 0),
                "mana": item_bonus.get("mana_max", 0),
                "stamina": item_bonus.get("stamina_max", 0)
            }
        )

        for set_info in _get_active_sets(character):
            set_id = next((sid for sid, si in SETS.items() if si is set_info), None)
            if set_id and set_id not in character.discovered_sets:
                character.discovered_sets.append(set_id)
                channel = interaction.guild.get_channel(character.player_channel_id)
                if channel:
                    await channel.send(embed=_generate_set_discovery_embed(set_info))

        self.character_repository.update_character(character)

        embed, file = _generate_item_equip_embed(entry.item, character, False)

        if file is not None:
            await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unequip", description="Déséquipe un objet de ton équipement.")
    @app_commands.autocomplete(
        item_name=item_unequippable_autocomplete,
    )
    @app_commands.describe(item_name="Le nom de l'objet à déséquiper.")
    async def item_unequip(self, interaction: Interaction, item_name: str):
        """Déséquipe un objet de ton équipement."""
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas de personnage associé à ton compte."), ephemeral=False)
            return

        inventory = character.inventory
        if not inventory or not inventory.has_item(item_name):
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Tu n'as pas l'objet '{item_name}' dans ton inventaire."), ephemeral=False)
            return

        entry = inventory.get_entry(item_name)
        if not entry or not entry.item.equippable:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"'{item_name}' n'est pas équippable."), ephemeral=False)
            return

        equipped_entries = [e for e in inventory.get_entries_by_name(item_name) if e.equipped_quantity > 0]
        if not equipped_entries:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Tu n'as pas d'exemplaire équippé de '{item_name}'."), ephemeral=False)
            return
        entry = equipped_entries[0]

        has_unequipped = inventory.unequip(item_name)
        if not has_unequipped:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Impossible de déséquiper '{item_name}'."), ephemeral=False)
            return

        item_bonus = entry.item.equipped_bonus

        hp_base, hp_level, hp_item        = _get_resource_max_bonus("hp", character)
        mana_base, mana_level, mana_item  = _get_resource_max_bonus("mana", character)
        stam_base, stam_level, stam_item  = _get_resource_max_bonus("stamina", character)


        self.character_repository.update_resources(
            character, 
            resources_max={
                "hp": hp_base + hp_level + hp_item,
                "mana": mana_base + mana_level + mana_item,
                "stamina": stam_base + stam_level + stam_item
            }
        )

        self.character_repository.update_character(character)

        embed, file = _generate_item_equip_embed(entry.item, character, True)

        if file is not None:
            await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message(embed=embed)


    @app_commands.describe(item_name="Le nom de l'objet à afficher.", quantity="La quantité d'objets à jeter.")
    async def item_discard(self, interaction: Interaction, item_name: str, quantity: int = 1):
        """Jette un objet de ton inventaire."""
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas de personnage associé à ton compte."), ephemeral=False)
            return

        inventory = character.inventory
        entry = inventory.get_entry(item_name)
        if not inventory or not inventory.has_item(item_name) or not entry:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Tu n'as pas l'objet '{item_name}' dans ton inventaire."), ephemeral=False)
            return

        total_qty = inventory.get_quantity(item_name)
        if total_qty < quantity:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Tu n'as pas assez de '{item_name}' pour en jeter {quantity}. Actuellement tu en as {total_qty}."), ephemeral=False)
            return

        has_removed = await inventory.remove(interaction.guild, character, item_name, quantity)
        if not has_removed:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Impossible de jeter '{item_name}'."), ephemeral=False)
            return
        self.character_repository.update_character(character)

        embed, file = _generate_item_discard_embed(entry.item, character, quantity)

        if file is not None:
            await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message(embed=embed)



    @app_commands.describe(item_name="Le nom de l'objet à afficher.", target_name="Le nom du personnage à qui donner l'objet.", quantity="La quantité d'objets à donner.")
    async def item_give(self, interaction: Interaction, item_name: str, target_name: str, quantity: int = 1):
        """Donne un objet de ton inventaire à un autre utilisateur."""
        await interaction.response.defer()

        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            await interaction.followup.send(embed=_generate_player_error_embed("Tu n'as pas de personnage associé à ton compte."), ephemeral=False)
            return

        target = self.character_repository.get_character_by_name(target_name)
        if not target:
            await interaction.followup.send(embed=_generate_player_error_embed(f"Le personnage '{target_name}' n'existe pas."), ephemeral=False)
            return

        if character.name == target.name:
            await interaction.followup.send(embed=_generate_player_error_embed("Tu ne peux pas te donner un objet à toi-même."), ephemeral=False)
            return

        inventory = character.inventory
        entry = inventory.get_entry(item_name)
        if not inventory or not inventory.has_item(item_name) or not entry:
            await interaction.followup.send(embed=_generate_player_error_embed(f"Tu n'as pas l'objet '{item_name}' dans ton inventaire."), ephemeral=False)
            return

        inventory_target = target.inventory
        if not inventory_target:
            await interaction.followup.send(embed=_generate_player_error_embed(f"Le personnage '{target_name}' n'a pas d'inventaire."), ephemeral=False)
            return

        if quantity < 1:
            await interaction.followup.send(embed=_generate_player_error_embed("La quantité doit être d'au moins 1."), ephemeral=False)
            return
        
        total_qty = inventory.get_quantity(item_name)
        if total_qty < quantity:
            await interaction.followup.send(embed=_generate_player_error_embed(f"Tu n'as pas assez de '{item_name}' pour en donner {quantity}. \n Actuellement tu en as {total_qty}."), ephemeral=False)
            return

        if inventory_target.slots_available() < quantity:
            await interaction.followup.send(embed=_generate_player_error_embed(f"{target.name} n'a pas assez de place dans son inventaire pour recevoir {quantity} '{item_name}'. \n Actuellement il lui reste {inventory_target.slots_available()} emplacement{'' if inventory_target.slots_available() == 1 else 's'} de libre."), ephemeral=False)
            return

        has_removed = await inventory.remove(interaction.guild, character, item_name, quantity, True)
        if not has_removed:
            await interaction.followup.send(embed=_generate_player_error_embed(f"Impossible de donner '{item_name}'."), ephemeral=False)
            return
        
        has_added = await inventory_target.add(interaction.guild, target, entry.item, quantity, True)
        if not has_added:
            # Tentative de rollback en cas d'erreur lors de l'ajout à l'inventaire du destinataire
            await inventory.add(interaction.guild, character, entry.item, quantity, True)
            await interaction.followup.send(embed=_generate_player_error_embed(f"Impossible de donner '{item_name}' à {target.name}."), ephemeral=False)
            return
            
        self.character_repository.update_character(character)
        self.character_repository.update_character(target)
        await self.bot.history.log_transaction(interaction.guild, character.name, target.name, entry.item.name, quantity)

        channel = interaction.client.get_channel(target.player_channel_id)
        if channel is None and interaction.guild is not None:
            channel = interaction.guild.get_channel(target.player_channel_id)

        embed, file = _generate_new_item_notification_embed(entry.item, quantity, sender=character, origin="player_gift")

        if file is not None:
            await channel.send(embed=embed, file=file)
        else:
            await channel.send(embed=embed)
        
    
        embed, file = _generate_item_trade_embed(character, target, entry.item, quantity)

        if file is not None:
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(embed=embed)


    @app_commands.describe(item_name="Le nom de l'objet à utiliser.")
    async def item_use(self, interaction: Interaction, item_name: str):
        """Utilise un objet de ton inventaire."""
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed("❌ Tu n'as pas de personnage associé."), ephemeral=False)
            return

        inventory = character.inventory
        if not inventory:
            await interaction.response.send_message(embed=_generate_player_error_embed("❌ Ton inventaire est introuvable."), ephemeral=False)
            return

        entry = inventory.get_entry(item_name)
        if not entry:
            await interaction.response.send_message(embed=_generate_player_error_embed("❌ Tu n'as pas cet objet dans ton inventaire."), ephemeral=False)
            return

        if not entry.item.useable:
            await interaction.response.send_message(embed=_generate_player_error_embed("❌ Cet objet n'est pas utilisable."), ephemeral=False)
            return

        if entry.item.tags == ["relique"]:
            embed = _generate_relic_used_embed(entry.item)
            await interaction.response.send_message(embed=embed)

            channel = discord.utils.get(interaction.guild.text_channels, name=ADMIN_CHANNEL_NAME)
            if channel is not None:
                await channel.send(embed=_notify_admin_relic_used_embed(entry.item, character))
            return

        been_used, buff_dicts = await inventory.use(interaction.guild, item_name, character)
        if not been_used:
            await interaction.response.send_message(embed=_generate_player_error_embed("❌ Impossible d'utiliser cet objet."), ephemeral=False)
            return
        

        for d in buff_dicts:
            if d.get("effects"):
                if d.get("duration") > 0:
                    buff = Buff(
                        name=d.get("name", "Effet d'objet"),
                        description=d.get("description", ""),
                        effects=d.get("effects", {}),
                        duration=d.get("duration", 0) + (1 if self.buff_repository.auto_decrement else 0),  # Si l'auto-décrément est activé, on ajoute 1 tick pour compenser la décrémentation qui aura lieu à la fin de la commande
                        character_name=character.name,
                        source=d.get("source", "Objet")
                    )
                    await self.buff_repository.add_buff(interaction.guild, buff)
                else:
                    for effect, value in d.get("effects", {}).items():
                        if effect.lower() in ["hp", "mana", "stamina"]:
                            self.character_repository.change_resources(character, **{f"{effect.lower()}_change": value})
        
        await self.buff_repository.decrement_buffs_duration(interaction.guild, character.name)
        self.character_repository.update_character(character)

        embed, file = _generate_item_use_embed(entry.item, character, buff_dicts, self.buff_repository.auto_decrement)
        if file is not None:
            await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message(embed=embed)
    
    

    @app_commands.describe(
        entry_id="L'objet équippable à enchanter (sélectionne dans la liste).",
        rune_name="La rune à enchâsser."
    )

    async def item_enchant(self, interaction: Interaction, entry_id: str, rune_name: str):
        """Enchâsse une rune dans un objet équippable."""
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas de personnage associé à ton compte."), ephemeral=False)
            return

        # Vérification du cooldown
        last_fail = self._enchant_cooldowns.get(interaction.user.id)
        if last_fail:
            elapsed = (datetime.datetime.now() - last_fail).total_seconds()
            remaining = ENCHANT_COOLDOWN_MINUTES * 60 - elapsed
            if remaining > 0:
                mins, secs = divmod(int(remaining), 60)
                await interaction.response.send_message(
                    embed=_generate_player_error_embed(
                        f"Ton dernier enchâssement a échoué. Tu peux réessayer dans **{mins}m {secs:02d}s**."
                    ),
                    ephemeral=False,
                )
                return

        entry = character.inventory.get_entry_by_id(entry_id)
        if not entry or not entry.item.equippable:
            await interaction.response.send_message(embed=_generate_player_error_embed("Objet équippable introuvable."), ephemeral=False)
            return

        if entry.item.rune_slots == 0:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"**{entry.item.name}** n'a pas de slots de rune."), ephemeral=False)
            return

        if len(entry.runes) >= entry.item.rune_slots:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"**{entry.item.name}** a déjà tous ses slots de rune remplis ({entry.item.rune_slots}/{entry.item.rune_slots})."), ephemeral=False)
            return

        rune_item = self.item_repository.get_item_by_name(rune_name)
        if not rune_item or "rune" not in rune_item.tags:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Rune '{rune_name}' introuvable."), ephemeral=False)
            return

        if rune_item.rarity not in ("rare", "epic"):
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Les runes de rareté **{rune_item.rarity}** ne peuvent être enchâssées que par un maître forgeron."), ephemeral=False)
            return

        if not character.inventory.has_item(rune_name):
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Tu ne possèdes pas la rune **{rune_name}**."), ephemeral=False)
            return

        # Jet de dé
        roll = random.randint(1, 100)
        threshold = ENCHANT_THRESHOLDS[rune_item.rarity]
        natural_1 = roll == 1
        natural_100 = roll == 100
        success = natural_100 or roll > threshold

        # Échec critique (1 natif) : rune détruite
        if natural_1:
            self._enchant_cooldowns[interaction.user.id] = datetime.datetime.now()
            self.bot.dice_session.enchant_roll(rune_name, entry.item.name, roll, threshold, success=False, character_name=character.name)
            await character.inventory.remove(interaction.guild, character, rune_name, quantity=1)
            self.character_repository.update_character(character)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="💀 Échec critique !",
                    description=(
                        f"🎲 **1** — Échec critique !\n\n"
                        f"L'enchâssement a mal tourné : la **{rune_item.name}** est **détruite**. "
                        f"Tu dois attendre **{ENCHANT_COOLDOWN_MINUTES} minutes** avant de réessayer."
                    ),
                    color=discord.Color.dark_red(),
                )
            )
            return

        # Échec normal : rune conservée, cooldown
        if not success:
            self._enchant_cooldowns[interaction.user.id] = datetime.datetime.now()
            self.bot.dice_session.enchant_roll(rune_name, entry.item.name, roll, threshold, success=False, character_name=character.name)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="💥 Échec de l'enchâssement",
                    description=(
                        f"🎲 **{roll}** (seuil : > {threshold})\n\n"
                        f"La **{rune_item.name}** résiste à l'enchâssement dans **{entry.item.name}**. "
                        f"La rune est conservée mais tu dois attendre **{ENCHANT_COOLDOWN_MINUTES} minutes** avant de réessayer."
                    ),
                    color=discord.Color.red(),
                )
            )
            return

        applied = character.inventory.apply_rune(entry_id, rune_item)
        if not applied:
            await interaction.response.send_message(embed=_generate_player_error_embed("Impossible d'enchâsser la rune."), ephemeral=False)
            return

        # Succès normal : rune consommée
        if not natural_100:
            removed = await character.inventory.remove(interaction.guild, character, rune_name, quantity=1)
            if not removed:
                entry.runes.pop()
                await interaction.response.send_message(embed=_generate_player_error_embed("Impossible de consommer la rune."), ephemeral=False)
                return

        self.bot.dice_session.enchant_roll(rune_name, entry.item.name, roll, threshold, success=True, character_name=character.name)
        self.character_repository.update_character(character)

        slots_now = len(entry.runes)
        bonus_lines = ", ".join(f"{k}: +{v}" for k, v in rune_item.equipped_bonus.items()) or "aucun bonus"

        if natural_100:
            title = "💎 Enchâssement parfait !"
            extra = "\n**La rune est conservée dans ton inventaire.**"
            roll_display = f"🎲 **100** — Succès critique !\n\n"
        else:
            title = "✨ Rune enchâssée !"
            extra = ""
            roll_display = f"🎲 **{roll}** (seuil : > {threshold})\n\n"

        await interaction.response.send_message(
            embed=discord.Embed(
                title=title,
                description=(
                    f"{roll_display}"
                    f"**{rune_item.name}** a été enchâssée dans **{entry.item.name}**.{extra}\n"
                    f"Bonus : {bonus_lines}\n"
                    f"Slots : {slots_now}/{entry.item.rune_slots}"
                ),
                color=discord.Color.gold() if natural_100 else discord.Color.purple(),
            )
        )

    @app_commands.describe(
        entry_id="L'objet dont retirer la rune (sélectionne dans la liste).",
        rune_name="La rune à retirer."
    )
    async def item_unenchant(self, interaction: Interaction, entry_id: str, rune_name: str):
        """Retire une rune d'un objet équippable."""
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas de personnage associé à ton compte."), ephemeral=False)
            return

        entry = character.inventory.get_entry_by_id(entry_id)
        if not entry or not entry.item.equippable:
            await interaction.response.send_message(embed=_generate_player_error_embed("Objet équippable introuvable."), ephemeral=False)
            return

        success, recovered = character.inventory.remove_rune(entry_id, rune_name)
        if not success:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"La rune **{rune_name}** n'est pas présente sur cet objet."), ephemeral=False)
            return

        rune_item = self.item_repository.get_item_by_name(rune_name)

        if recovered:
            await character.inventory.add(interaction.guild, character, recovered, quantity=1)
            result_msg = f"**{rune_name}** retirée de **{entry.item.name}** et récupérée dans ton inventaire."
        else:
            result_msg = f"**{rune_name}** retirée de **{entry.item.name}** et détruite."

        self.character_repository.update_character(character)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔨 Rune retirée",
                description=result_msg,
                color=discord.Color.orange(),
            )
        )

    @item_list.autocomplete("tag")
    async def tag_autocomplete(self, interaction: Interaction, current: str):
        return await make_tag_autocomplete(self.item_repository)(interaction, current)

    async def cog_load(self):
        # --- info ---
        info_cmd = app_commands.Command(
            name="info",
            description="Affiche les informations sur un objet.",
            callback=self.item_info
        )
        info_cmd.autocomplete("item_name")(self.item_info_autocomplete)
        self.item_group.add_command(info_cmd)

        # --- discard ---
        discard_cmd = app_commands.Command(
            name="discard",
            description="Jette un objet de ton inventaire.",
            callback=self.item_discard
        )
        discard_cmd.autocomplete("item_name")(self.item_autocomplete)
        self.item_group.add_command(discard_cmd)

        # --- give ---
        give_cmd = app_commands.Command(
            name="give",
            description="Donne un objet de ton inventaire à un autre utilisateur.",
            callback=self.item_give
        )
        give_cmd.autocomplete("item_name")(self.item_autocomplete)
        give_cmd.autocomplete("target_name")(make_character_autocomplete(self.bot.character_repository))
        self.item_group.add_command(give_cmd)

        # --- use ---
        use_cmd = app_commands.Command(
            name="use",
            description="Utilise un objet de ton inventaire.",
            callback=self.item_use
        )
        use_cmd.autocomplete("item_name")(self.item_useable_autocomplete)
        self.item_group.add_command(use_cmd)

        # --- enchant (top-level) ---
        enchant_cmd = app_commands.Command(
            name="enchant",
            description="Enchâsse une rune dans un objet équippable.",
            callback=self.item_enchant
        )
        enchant_cmd.autocomplete("entry_id")(self.enchantable_entry_autocomplete)
        enchant_cmd.autocomplete("rune_name")(self.rune_autocomplete)
        self.bot.tree.add_command(enchant_cmd)

        # --- unenchant (top-level) ---
        unenchant_cmd = app_commands.Command(
            name="unenchant",
            description="Retire une rune d'un objet équippable.",
            callback=self.item_unenchant
        )
        unenchant_cmd.autocomplete("entry_id")(self.enchanted_entry_autocomplete)
        unenchant_cmd.autocomplete("rune_name")(self.rune_on_entry_autocomplete)
        self.bot.tree.add_command(unenchant_cmd)


async def setup(bot: commands.Bot):
    await bot.add_cog(Items(bot))