import math
import random

import discord
from discord import app_commands
from discord.ext import commands

from instance.npc import NPC, Quest, NPCRepository
from instance.quest_progress import QuestProgress, QuestStatus
from instance.trade import TradeProposal, TradeEntry

from utils.autocomplete import (
    make_character_autocomplete,
    make_blacksmith_npc_autocomplete,
    make_blacksmith_rune_autocomplete,
    make_enchantable_entry_autocomplete_for_character,
    make_upgradeable_item_autocomplete,
    make_npc_autocomplete,
    make_merchant_npc_autocomplete,
    make_sale_npc_autocomplete,
    make_offer_item_autocomplete,
    make_trade_id_autocomplete,
    make_sale_id_autocomplete,
    make_accept_quest_autocomplete,
    make_active_quest_autocomplete,
)
from utils.admin import AdminGroup
from utils.builder_embed import (
    _generate_npc_embed,
    _generate_quest_embed,
    _generate_player_error_embed,
    _generate_trade_result_embed,
    _generate_npc_offer_embed,
    _generate_blacksmith_enchant_embed,
    _generate_blacksmith_upgrade_embed,
    _generate_item_forbidden_embed,
    _generate_new_item_notification_embed,
    _generate_sale_counter_offer_embed,
)
from utils.builder_view import OfferView, SaleCounterOfferView, NewItemNotificationView
from utils.utils import UPGRADE_EQUIPMENT, RUNES_COST

class NPCCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.npc_repo = bot.npc_repository
        self.quest_progress = bot.quest_progress

        self.npc_group = AdminGroup(
            name="npc", 
            description="Commandes liées aux NPCs.",
            default_permissions=discord.Permissions(administrator=True)
        )
        bot.tree.add_command(self.npc_group)


    # ------------------------------------------------------------------
    # /npc fiche
    # ------------------------------------------------------------------
    @app_commands.describe(nom="Nom du NPC")
    async def npc_fiche(self, interaction: discord.Interaction, nom: str):
        npc = self.npc_repo.get(nom)
        if not npc:
            await interaction.response.send_message(
                f"NPC « {nom} » introuvable.", ephemeral=True
            )
            return

        completed = self.quest_progress.get_completed()
        

        city_npcs = self.npc_repo.by_city(self.bot.location.city)

        embed = _generate_npc_embed(npc, completed, self.bot.character_repository.runes_rarity_discovered)

        await interaction.response.send_message(embed=embed)

    @app_commands.describe(quest_id="ID de la quête à démarrer")
    async def npc_accept_quest(self, interaction: discord.Interaction, quest_id: str):
        quest = self.npc_repo.get_quest(quest_id)
        if not quest:
            await interaction.response.send_message(
                _generate_player_error_embed(f"Quête `{quest_id}` introuvable."), ephemeral=True
            )
            return

        completed = self.quest_progress.get_completed()
        if quest.condition_quest and quest.condition_quest not in completed:
            await interaction.response.send_message(
                _generate_player_error_embed(f"La quête préalable `{quest.condition_quest}` n'a pas encore été complétée."),
                ephemeral=True
            )
            return

        success = self.quest_progress.start(quest_id)
        if not success:
            await interaction.response.send_message(
                _generate_player_error_embed(f"La quête `{quest_id}` est déjà en cours ou a déjà été faite."),
                ephemeral=True
            )
            return

        embed = _generate_quest_embed(quest, QuestStatus.ACTIVE)
        await interaction.response.send_message(content="📜 Quête démarrée !", embed=embed)


    @app_commands.describe(quest_id="ID de la quête", action="Action à effectuer")
    @app_commands.choices(action=[
        app_commands.Choice(name="Marquer comme échouée", value="fail"),
        app_commands.Choice(name="Supprimer (peut être relancée)", value="remove"),
    ])
    async def npc_cancel_quest(self, interaction: discord.Interaction, quest_id: str, action: str):
        quest = self.npc_repo.get_quest(quest_id)
        if not quest:
            await interaction.response.send_message(
                _generate_player_error_embed(f"Quête `{quest_id}` introuvable."), ephemeral=True
            )
            return

        if action == "fail":
            success = self.quest_progress.fail(quest_id)
            label = "marquée comme échouée"
        else:  # remove
            success = self.quest_progress.remove(quest_id)
            label = "supprimée (peut être relancée)"

        if not success:
            await interaction.response.send_message(
                _generate_player_error_embed(f"La quête `{quest_id}` n'est pas en cours."), ephemeral=True
            )
            return

        embed = _generate_quest_embed(quest)
        await interaction.response.send_message(content=f"❌ Quête **{quest.title}** {label}.", embed=embed)


    async def npc_finish_quest(self, interaction: discord.Interaction, quest_id: str, player: str = None, xp_repartition: str = "even"):
        quest = self.npc_repo.get_quest(quest_id)
        if not quest:
            await interaction.response.send_message(
                _generate_player_error_embed(f"Quête `{quest_id}` introuvable."), ephemeral=True
            )
            return

        if player is not None:
            completing_character = self.bot.character_repository.get_character_by_name(player)
            if not completing_character:
                await interaction.response.send_message(
                    _generate_player_error_embed(f"Personnage `{player}` introuvable."), ephemeral=True
                )
                return
        else:
            completing_character = None

        success = self.quest_progress.complete(quest_id)
        if not success:
            await interaction.response.send_message(
                _generate_player_error_embed(f"La quête `{quest_id}` n'est pas en cours."), ephemeral=True
            )
            return

        active_players = self.bot.character_repository.players  # list[str]
        active_characters = [self.bot.character_repository.get_character_by_name(p) for p in active_players]
        active_characters = [c for c in active_characters if c is not None]

        rewards = []

        if quest.reward_items:
            await interaction.response.defer()
            item_rewards_lines = []
            for qi in quest.reward_items:
                candidates = [c for c in active_characters if c.inventory and c.inventory.slots_available() >= qi.quantity]
                if not candidates:
                    await interaction.followup.send(
                        embed=_generate_player_error_embed(
                            f"Aucun joueur actif n'a assez de place pour recevoir {qi.quantity}x '{qi.item.name}'. Les récompenses ne sont pas distribuées."
                        ),
                        ephemeral=False,
                    )
                    return

                recipient = random.choice(candidates)
                has_added = await recipient.inventory.add(interaction.guild, recipient, qi.item, qi.quantity, quest=True)
                if not has_added:
                    await interaction.followup.send(
                        embed=_generate_player_error_embed(f"Impossible de donner '{qi.item.name}' à {recipient.name}."),
                        ephemeral=False,
                    )
                    return

                channel = interaction.client.get_channel(recipient.player_channel_id)
                if channel is None and interaction.guild is not None:
                    channel = interaction.guild.get_channel(recipient.player_channel_id)

                if channel is not None:
                    embed, file = _generate_new_item_notification_embed(qi.item, qi.quantity, sender=None)
                    if file is not None:
                        await channel.send(embed=embed, file=file)
                    else:
                        await channel.send(embed=embed)
                else:
                    await interaction.followup.send(
                        embed=_generate_player_error_embed(f"Impossible de notifier {recipient.name} de la réception de l'objet car son salon privé est introuvable."),
                        ephemeral=False,
                    )

                item_rewards_lines.append(f"{qi.quantity}x {qi.item.name} → {recipient.name}")

            rewards.extend(item_rewards_lines)

        if quest.reward_xp:
            individual_xp = quest.reward_xp // len(active_players) if active_players else quest.reward_xp
            for char in active_characters:
                char.gain_experience(individual_xp)
                self.bot.character_repository.update_character(char)
            rewards.append(f"{quest.reward_xp} XP → tous les joueurs actifs ({', '.join(active_players)})")

        embed = _generate_quest_embed(quest, QuestStatus.COMPLETED)
        embed.add_field(
            name="Récompenses à distribuer",
            value="\n".join(rewards) if rewards else "Aucune",
            inline=False,
        )
        if quest.reward_items:
            await interaction.followup.send(content=f"✅ Quête **{quest.title}** terminée !", embed=embed)
        else:
            await interaction.response.send_message(content=f"✅ Quête **{quest.title}** terminée !", embed=embed)


    @app_commands.describe(
        character_name="Personnage effectuant l'achat",
        npc_name="Nom du NPC marchand",
        trade_id="ID de la vente",
        monnaie="Monnaie offerte",
    )
    async def npc_sale(self, interaction: discord.Interaction, character_name: str, npc_name: str, trade_id: str, monnaie: int):
        character = self.bot.character_repository.get_character_by_name(character_name)
        if not character:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Personnage `{character_name}` introuvable."), ephemeral=True
            )
            return

        npc = self.npc_repo.get(npc_name)
        if not npc or (not npc.has_role("merchant") and not npc.has_role("blacksmith")):
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"« {npc_name} » n'est pas un marchand ou un forgeron."), ephemeral=True
            )
            return

        trade_repo = self.bot.trade_repository
        trade = trade_repo.get_trade_by_id(trade_id)
        if not trade or trade not in npc.trades:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Vente `{trade_id}` introuvable chez ce marchand."), ephemeral=True
            )
            return

        # Vérification de la monnaie
        if monnaie > character.currency:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(
                    f"Tu n'as pas assez de monnaie ({character.currency} 🪙 disponibles)."
                ),
                ephemeral=True,
            )
            return

        proposal = TradeProposal(
            trade_id=trade_id,
            offered_items=[],
            offered_value=monnaie,
            player=character.name,
        )

        roll = random.randint(1, 100)
        result, threshold = trade_repo.propose_trade(proposal, character, roll)

        if result == "Trade successful":
            character.currency -= monnaie
            for entry in trade.offered_items:
                await character.inventory.add(interaction.guild, character, entry.item, entry.quantity, trade=True)
            self.bot.character_repository.update_character(character)
            await self.bot.history.log_npc_trade(
                interaction.guild, character.name, npc_name,
                trade.offered_items, [], monnaie,
            )

            player_channel = interaction.client.get_channel(character.player_channel_id)
            if player_channel is None and interaction.guild is not None:
                player_channel = interaction.guild.get_channel(character.player_channel_id)
            if player_channel is not None:
                for entry in trade.offered_items:
                    embed, file = _generate_new_item_notification_embed(entry.item, entry.quantity, origin="npc_purchase", npc_name=npc_name)
                    view = NewItemNotificationView([(entry.item, entry.quantity)])
                    if file is not None:
                        await player_channel.send(embed=embed, file=file, view=view)
                    else:
                        await player_channel.send(embed=embed, view=view)

            embed = _generate_trade_result_embed(npc_name, trade, result, roll)
            await interaction.response.send_message(embed=embed)

        elif result == "Failed trade - offer too low":
            diff = trade.price - monnaie
            min_price = math.floor(monnaie + diff * ((threshold - roll) / threshold))
            max_price = min(min_price + math.ceil(trade.price / 10), trade.price)
            counter_price = random.randint(min_price, max_price)
            embed = _generate_sale_counter_offer_embed(npc_name, trade, counter_price, roll)
            view = SaleCounterOfferView(self.bot, character, npc_name, trade, counter_price)
            await interaction.response.send_message(embed=embed, view=view)

        else:
            embed = _generate_trade_result_embed(npc_name, trade, result, roll)
            await interaction.response.send_message(embed=embed)

    @app_commands.describe(
        character_name="Personnage qui vend l'item",
        npc_name="Nom du NPC acheteur",
        item_name="Item à vendre",
        quantity="Quantité (défaut : 1)",
    )
    async def npc_offer(self, interaction: discord.Interaction, character_name: str, npc_name: str, item_name: str, quantity: int = 1):
        character = self.bot.character_repository.get_character_by_name(character_name)
        if not character:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Personnage `{character_name}` introuvable."), ephemeral=True
            )
            return

        npc = self.npc_repo.get(npc_name)
        if not npc or not npc.has_role("merchant"):
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"« {npc_name} » n'est pas un marchand."), ephemeral=True
            )
            return

        item = self.bot.item_repository.get_item_by_name(item_name)
        if not item:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Item `{item_name}` introuvable."), ephemeral=True
            )
            return

        if item.forbidden:
            embed = _generate_item_forbidden_embed(item)
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        if character.inventory.get_quantity(item_name) < quantity:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"{character_name} n'a pas {quantity}x {item_name}."), ephemeral=True
            )
            return

        price = self.bot.trade_repository.get_offer_price(item, npc.specialty)
        embed = _generate_npc_offer_embed(npc_name, item_name, quantity, price, item.value)
        view = OfferView(self.bot, character, npc, item, quantity, price)

        await interaction.response.send_message(embed=embed, view=view)

    async def npc_update_prices(self, interaction: discord.Interaction):
        self.bot.trade_repository.update_prices()
        count = len(self.bot.trade_repository.trades)
        await interaction.response.send_message(
            f"✅ Prix mis à jour pour {count} trade(s). Les offres d'achat seront recalculées à la prochaine demande.",
            ephemeral=True
        )

    async def autocomplete_npc(self, interaction: discord.Interaction, current: str):
        return await make_npc_autocomplete(self.npc_repo, self.bot)(interaction, current)

    async def autocomplete_merchant_npc(self, interaction: discord.Interaction, current: str):
        return await make_merchant_npc_autocomplete(self.npc_repo, self.bot)(interaction, current)

    async def autocomplete_sale_npc(self, interaction: discord.Interaction, current: str):
        return await make_sale_npc_autocomplete(self.npc_repo, self.bot)(interaction, current)

    async def autocomplete_offer_item(self, interaction: discord.Interaction, current: str):
        return await make_offer_item_autocomplete(self.bot.character_repository)(interaction, current)

    async def autocomplete_trade_id(self, interaction: discord.Interaction, current: str):
        return await make_trade_id_autocomplete(self.npc_repo, self.bot.trade_repository)(interaction, current)

    async def autocomplete_sale_id(self, interaction: discord.Interaction, current: str):
        return await make_sale_id_autocomplete(self.npc_repo, self.bot.trade_repository)(interaction, current)

    async def autocomplete_blacksmith_npc(self, interaction: discord.Interaction, current: str):
        return await make_blacksmith_npc_autocomplete(self.npc_repo, self.bot)(interaction, current)

    async def autocomplete_blacksmith_rune(self, interaction: discord.Interaction, current: str):
        return await make_blacksmith_rune_autocomplete(self.bot.character_repository)(interaction, current)

    async def autocomplete_enchantable_entry(self, interaction: discord.Interaction, current: str):
        return await make_enchantable_entry_autocomplete_for_character(self.bot.character_repository)(interaction, current)

    async def autocomplete_upgradeable_item(self, interaction: discord.Interaction, current: str):
        return await make_upgradeable_item_autocomplete(self.bot.character_repository, self.bot.item_repository)(interaction, current)

    # ------------------------------------------------------------------
    # /npc blacksmith-enchant
    # ------------------------------------------------------------------
    @app_commands.describe(
        character_name="Personnage qui enchâsse la rune",
        npc_name="Nom du forgeron",
        entry_id="L'objet à enchanter (sélectionne dans la liste)",
        rune_name="La rune légendaire ou mythique à enchâsser",
    )
    async def npc_blacksmith_enchant(
        self,
        interaction: discord.Interaction,
        character_name: str,
        npc_name: str,
        entry_id: str,
        rune_name: str,
    ):
        character = self.bot.character_repository.get_character_by_name(character_name)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Personnage '{character_name}' introuvable."), ephemeral=False)
            return

        npc = self.npc_repo.get(npc_name)
        if not npc or not npc.has_role("blacksmith"):
            await interaction.response.send_message(embed=_generate_player_error_embed(f"'{npc_name}' n'est pas un forgeron."), ephemeral=False)
            return

        entry = character.inventory.get_entry_by_id(entry_id)
        if not entry or not entry.item.equippable:
            await interaction.response.send_message(embed=_generate_player_error_embed("Objet équippable introuvable."), ephemeral=False)
            return

        if entry.item.rune_slots == 0:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"**{entry.item.name}** n'a pas de slots de rune."), ephemeral=False)
            return

        if len(entry.runes) >= entry.item.rune_slots:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"**{entry.item.name}** a déjà tous ses slots remplis ({entry.item.rune_slots}/{entry.item.rune_slots})."), ephemeral=False)
            return

        rune_item = self.bot.item_repository.get_item_by_name(rune_name)
        if not rune_item or "rune" not in rune_item.tags or rune_item.rarity not in RUNES_COST:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Rune '{rune_name}' introuvable ou non enchâssable."), ephemeral=False)
            return

        if not character.inventory.has_item(rune_name):
            await interaction.response.send_message(embed=_generate_player_error_embed(f"**{character_name}** ne possède pas la rune **{rune_name}**."), ephemeral=False)
            return

        cost = RUNES_COST.get(rune_item.rarity, 0)
        if character.currency < cost:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"**{character_name}** n'a pas assez de monnaie ({character.currency}🪙 / {cost}🪙 requis)."), ephemeral=False)
            return

        applied = character.inventory.apply_rune(entry_id, rune_item)
        if not applied:
            await interaction.response.send_message(embed=_generate_player_error_embed("Impossible d'enchâsser la rune."), ephemeral=False)
            return

        removed = await character.inventory.remove(interaction.guild, character, rune_name, quantity=1)
        if not removed:
            entry.runes.pop()
            await interaction.response.send_message(embed=_generate_player_error_embed("Impossible de consommer la rune."), ephemeral=False)
            return

        character.currency -= cost
        self.bot.character_repository.update_character(character)

        await interaction.response.send_message(embed=_generate_blacksmith_enchant_embed(npc_name, rune_item, entry, cost))

    # ------------------------------------------------------------------
    # /npc blacksmith-upgrade
    # ------------------------------------------------------------------
    @app_commands.describe(
        character_name="Personnage dont améliorer l'équipement",
        npc_name="Nom du forgeron",
        item_name="L'équipement à améliorer",
    )
    async def npc_blacksmith_upgrade(
        self,
        interaction: discord.Interaction,
        character_name: str,
        npc_name: str,
        item_name: str,
    ):
        character = self.bot.character_repository.get_character_by_name(character_name)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Personnage '{character_name}' introuvable."), ephemeral=False)
            return

        npc = self.npc_repo.get(npc_name)
        if not npc or not npc.has_role("blacksmith"):
            await interaction.response.send_message(embed=_generate_player_error_embed(f"'{npc_name}' n'est pas un forgeron."), ephemeral=False)
            return

        upgrade_entry = next((u for u in UPGRADE_EQUIPMENT if u["source"] == item_name), None)
        dest_name = upgrade_entry["dest"] if upgrade_entry else None
        if not dest_name:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"**{item_name}** n'est pas améliorable par un forgeron."), ephemeral=False)
            return

        source_item = self.bot.item_repository.get_item_by_name(item_name)
        dest_item = self.bot.item_repository.get_item_by_name(dest_name)
        if not source_item or not dest_item:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Impossible de trouver les items '{item_name}' ou '{dest_name}' dans le catalogue."), ephemeral=False)
            return

        if not character.inventory.has_item(item_name):
            await interaction.response.send_message(embed=_generate_player_error_embed(f"**{character_name}** ne possède pas **{item_name}**."), ephemeral=False)
            return

        equipped = [e for e in character.inventory.get_entries_by_name(item_name) if e.equipped_quantity > 0]
        if equipped:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"**{item_name}** est actuellement équippé. Déséquippe-le d'abord."), ephemeral=False)
            return

        cost = math.ceil((dest_item.value - source_item.value) * 0.8)
        if character.currency < cost:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"**{character_name}** n'a pas assez de monnaie ({character.currency}🪙 / {cost}🪙 requis)."), ephemeral=False)
            return

        removed = await character.inventory.remove(interaction.guild, character, item_name, quantity=1)
        if not removed:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Impossible de retirer **{item_name}** de l'inventaire."), ephemeral=False)
            return

        await character.inventory.add(interaction.guild, character, dest_item, quantity=1)
        character.currency -= cost
        self.bot.character_repository.update_character(character)

        await interaction.response.send_message(embed=_generate_blacksmith_upgrade_embed(npc_name, source_item, dest_item, cost))

    async def autocomplete_accept_quest(self, interaction: discord.Interaction, current: str):
        return await make_accept_quest_autocomplete(self.npc_repo, self.quest_progress, self.bot)(interaction, current)

    async def autocomplete_active_quest(self, interaction: discord.Interaction, current: str):
        return await make_active_quest_autocomplete(self.npc_repo, self.quest_progress)(interaction, current)

    async def cog_load(self):
        fiche_cmd = app_commands.Command(
            name="fiche",
            description="Affiche la fiche d'un NPC",
            callback=self.npc_fiche,
        )
        fiche_cmd.autocomplete("nom")(self.autocomplete_npc)
        self.npc_group.add_command(fiche_cmd)

        accept_quest_cmd = app_commands.Command(
            name="accept-quest",
            description="Démarre une quête de groupe",
            callback=self.npc_accept_quest,
        )
        accept_quest_cmd.autocomplete("quest_id")(self.autocomplete_accept_quest)
        self.npc_group.add_command(accept_quest_cmd)

        cancel_quest_cmd = app_commands.Command(
            name="cancel-quest",
            description="[Admin] Annule une quête en cours",
            callback=self.npc_cancel_quest,
        )
        cancel_quest_cmd.autocomplete("quest_id")(self.autocomplete_active_quest)
        self.npc_group.add_command(cancel_quest_cmd)

        finish_quest_cmd = app_commands.Command(
            name="finish-quest",
            description="[Admin] Termine une quête et distribue les récompenses",
            callback=self.npc_finish_quest,
        )
        finish_quest_cmd.autocomplete("quest_id")(self.autocomplete_active_quest)
        finish_quest_cmd.autocomplete("player")(make_character_autocomplete(self.bot.character_repository))
        self.npc_group.add_command(finish_quest_cmd)

        sale_cmd = app_commands.Command(
            name="sale",
            description="Acheter un item à un marchand avec de la monnaie",
            callback=self.npc_sale,
        )
        sale_cmd.autocomplete("character_name")(make_character_autocomplete(self.bot.character_repository))
        sale_cmd.autocomplete("npc_name")(self.autocomplete_sale_npc)
        sale_cmd.autocomplete("trade_id")(self.autocomplete_sale_id)
        self.npc_group.add_command(sale_cmd)

        offer_cmd = app_commands.Command(
            name="offer",
            description="Le NPC propose un prix d'achat pour un item du personnage",
            callback=self.npc_offer,
        )
        offer_cmd.autocomplete("character_name")(make_character_autocomplete(self.bot.character_repository))
        offer_cmd.autocomplete("npc_name")(self.autocomplete_merchant_npc)
        offer_cmd.autocomplete("item_name")(self.autocomplete_offer_item)
        self.npc_group.add_command(offer_cmd)

        update_prices_cmd = app_commands.Command(
            name="update-prices",
            description="[Admin] Recalcule les prix de tous les trades et offres",
            callback=self.npc_update_prices,
        )
        self.npc_group.add_command(update_prices_cmd)

        bs_enchant_cmd = app_commands.Command(
            name="enchant",
            description="Fait enchâsser une rune légendaire/mythique par un forgeron",
            callback=self.npc_blacksmith_enchant,
        )
        bs_enchant_cmd.autocomplete("character_name")(make_character_autocomplete(self.bot.character_repository))
        bs_enchant_cmd.autocomplete("npc_name")(self.autocomplete_blacksmith_npc)
        bs_enchant_cmd.autocomplete("entry_id")(self.autocomplete_enchantable_entry)
        bs_enchant_cmd.autocomplete("rune_name")(self.autocomplete_blacksmith_rune)
        self.npc_group.add_command(bs_enchant_cmd)

        bs_upgrade_cmd = app_commands.Command(
            name="upgrade",
            description="Fait améliorer un équipement par un forgeron",
            callback=self.npc_blacksmith_upgrade,
        )
        bs_upgrade_cmd.autocomplete("character_name")(make_character_autocomplete(self.bot.character_repository))
        bs_upgrade_cmd.autocomplete("npc_name")(self.autocomplete_blacksmith_npc)
        bs_upgrade_cmd.autocomplete("item_name")(self.autocomplete_upgradeable_item)
        self.npc_group.add_command(bs_upgrade_cmd)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(NPCCog(bot))