import discord
import logging
from discord.ext import commands
from discord import app_commands, Interaction

from utils.admin import handle_admin_permission_error, AdminGroup

logger = logging.getLogger(__name__)
from utils.builder_embed import (
    _generate_player_error_embed,
    _generate_lootbox_list_embed,
    _generate_lootbox_info_embed,
    _generate_new_item_from_lootbox_notification_embed,
)
from utils.builder_view import LootBoxOpenedView
from utils.autocomplete import make_lootbox_autocomplete, make_character_autocomplete

class Lootboxes(commands.Cog):
    """Commandes liées aux lootboxes."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lootbox_repository = bot.lootbox_repository
        self.character_repository = bot.character_repository
        self.history = bot.history

        self.lootbox_group = AdminGroup(
            name="lootbox",
            description="Commandes liées aux lootboxes.",
            default_permissions=discord.Permissions(administrator=True)
        )
        bot.tree.add_command(self.lootbox_group)


    def _resolve_callback(self, member):
        """Return the underlying callable for an app_commands.Command or the member itself."""
        return getattr(member, "callback", member)
    

    async def lootbox_autocomplete(self, interaction: Interaction, current: str):
        return await make_lootbox_autocomplete(self.bot.lootbox_repository)(interaction, current)

    async def character_autocomplete(self, interaction: Interaction, current: str):
        return await make_character_autocomplete(self.bot.character_repository)(interaction, current)

    # ── Commandes ────────────────────────────────────────────────────
    @app_commands.describe(lootbox_name="Le nom de la lootbox à afficher.")
    async def lootbox_info(self, interaction: Interaction, lootbox_name: str):
        """Affiche les informations sur une lootbox."""
        lootbox = self.lootbox_repository.get_lootbox_by_name(lootbox_name)
        if lootbox is None:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Lootbox « {lootbox_name} » introuvable."),
                ephemeral=True
            )
            return

        await interaction.response.send_message(embed=_generate_lootbox_info_embed(lootbox))


    @app_commands.describe(lootbox_name="Le nom de la lootbox à ouvrir.", character_name="Le nom du personnage pour qui ouvrir la lootbox.", quantity="La quantité de lootboxes à ouvrir.")
    async def lootbox_open(self, interaction: Interaction, lootbox_name: str, character_name: str, quantity: int = 1):
        """Ouvre une lootbox pour un personnage."""
        character = self.bot.character_repository.get_character_by_name(character_name)
        if character is None:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Personnage « {character_name} » introuvable."),
                ephemeral=True
            )
            return

        lootbox = self.lootbox_repository.get_lootbox_by_name(lootbox_name)
        if lootbox is None:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Lootbox « {lootbox_name} » introuvable."),
                ephemeral=True
            )
            return

        inventory_target = character.inventory
        if not inventory_target:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Le personnage '{character.name}' n'a pas d'inventaire."),
                ephemeral=True
            )
            return
        
        rewards = self.lootbox_repository.open_lootbox(lootbox.id, quantity, character.name)
        if not rewards:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Une erreur est survenue lors de l'ouverture de la lootbox."),
                ephemeral=True
            )
            return
        
        total_quantity = sum(qty for _, qty in rewards)
        if total_quantity == 0:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Une erreur est survenue lors de l'ouverture de la lootbox. La quantité totale d'objets obtenus est de 0."),
                ephemeral=True
            )
            return
        
        if inventory_target.slots_available() < total_quantity:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Le personnage '{character.name}' n'a pas assez de place dans son inventaire pour recevoir les récompenses ({total_quantity} objets à ajouter, {inventory_target.slots_available()} slots disponibles)."),
                ephemeral=True
            )
            return

        items_to_add = []
        has_added_all = True
        for item_name, item_quantity in rewards:
            item = self.bot.item_repository.get_item_by_name(item_name)
            if item is None:
                await interaction.response.send_message(
                    embed=_generate_player_error_embed(f"Une erreur est survenue lors de l'ajout de l'objet '{item_name}' à l'inventaire du personnage '{character.name}' : objet introuvable dans la base de données."),
                    ephemeral=True
                )
                return
            has_added = await inventory_target.add(interaction.guild, character, item, item_quantity, loot=True)
            has_added_all *= has_added
            items_to_add.append((item, item_quantity))
        
        if not has_added_all:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Une erreur est survenue lors de l'ajout des récompenses à l'inventaire du personnage '{character.name}'."),
                ephemeral=True
            )
            return
        
        self.character_repository.update_character(character)
        await self.history.log_lootbox(interaction.guild, character.name, lootbox_name, quantity, rewards)

        channel = interaction.client.get_channel(character.player_channel_id)
        if channel is None and interaction.guild is not None:
            channel = interaction.guild.get_channel(character.player_channel_id)

        embed = _generate_new_item_from_lootbox_notification_embed(items_to_add, lootbox=lootbox)
        view = LootBoxOpenedView(lootbox=lootbox, rewards=items_to_add)
        await channel.send(embed=embed, view=view)

        embed = discord.Embed(
            title=f"Tu as ouvert {quantity}x {lootbox.name} pour {character.name} !",
            description=f"Récompenses obtenues :\n" + "\n".join([f"- {item_name} x{item_quantity}" for item_name, item_quantity in rewards]),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)


    async def lootbox_summary(self, interaction: Interaction):
        """Affiche un résumé des lootboxes ouvertes."""
        summary = self.lootbox_repository.summary()
        logger.debug(f"Lootbox summary: {summary}")
        # TODO: Implémenter l'affichage du résumé des lootboxes ouvertes
        await interaction.response.send_message("🚧 Pas encore implémenté.", ephemeral=True)

    async def lootbox_list(self, interaction: Interaction):
        """Affiche la liste des lootboxes disponibles."""
        lootboxes = self.lootbox_repository.list_lootboxes()
        if not lootboxes:
            await interaction.response.send_message(embed=_generate_player_error_embed("Aucune lootbox disponible pour le moment."), ephemeral=True)
            return

        embed = _generate_lootbox_list_embed(lootboxes)
        await interaction.response.send_message(embed=embed)
        


    async def cog_load(self):
        # --- info ---
        info_cmd = app_commands.Command(
            name="info",
            description="Affiche les informations sur une lootbox.",
            callback=self.lootbox_info,
        )
        info_cmd.autocomplete("lootbox_name")(self.lootbox_autocomplete)
        self.lootbox_group.add_command(info_cmd)

        # --- open ---
        open_cmd = app_commands.Command(
            name="open",
            description="Ouvre une lootbox pour un personnage.",
            callback=self.lootbox_open,
        )
        open_cmd.autocomplete("lootbox_name")(self.lootbox_autocomplete)
        open_cmd.autocomplete("character_name")(self.character_autocomplete)
        self.lootbox_group.add_command(open_cmd)

        # --- list ---
        list_cmd = app_commands.Command(
            name="list",
            description="Affiche la liste des lootboxes disponibles.",
            callback=self.lootbox_list,
        )
        self.lootbox_group.add_command(list_cmd)

        # -- summary ---
        summary_cmd = app_commands.Command(
            name="summary",
            description="Affiche un résumé des lootboxes ouvertes.",
            callback=self.lootbox_summary,
        )
        self.lootbox_group.add_command(summary_cmd)

async def setup(bot: commands.Bot):
    await bot.add_cog(Lootboxes(bot))