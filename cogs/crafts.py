import discord
import logging
from discord.ext import commands
from discord import app_commands, Interaction

import math

logger = logging.getLogger(__name__)

from utils.builder_embed import (
    _generate_craft_list_embed,
    _generate_craft_info_embed,
    _generate_craft_executed_embed,
    _generate_player_error_embed
)
from utils.builder_view import (
    CraftInfoView
)
from utils.admin import handle_admin_permission_error
from utils.autocomplete import make_craft_filter_autocomplete, make_craft_autocomplete, make_craftable_craft_autocomplete

class Crafts(commands.Cog):
    """Commandes liées au craft."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.character_repository = bot.character_repository
        self.craft_repository = bot.craft_repository
        self.item_repository = bot.item_repository
        self.buff_repository = bot.buff_repository
        
        self.craft_group = app_commands.Group(name="craft", description="Commandes liées aux crafts.")
        bot.tree.add_command(self.craft_group)

    def _resolve_callback(self, member):
        """Return the underlying callable for an app_commands.Command or the member itself."""
        return getattr(member, "callback", member)

    
    async def craft_filter_autocomplete(self, interaction: Interaction, current: str):
        return await make_craft_filter_autocomplete(self.bot.craft_repository)(interaction, current)
    
    async def craft_autocomplete(self, interaction: Interaction, current: str):
        return await make_craft_autocomplete(self.bot.craft_repository)(interaction, current)

    async def craftable_craft_autocomplete(self, interaction: Interaction, current: str):
        return await make_craftable_craft_autocomplete(self.bot.craft_repository, self.bot.character_repository)(interaction, current)

    # ── Commandes ────────────────────────────────────────────────────
    @app_commands.describe(filtre="Filtre pour n'afficher que certains crafts (ex: 'craftable', 'Alchimie', '3', etc.)")
    async def list_crafts(self, interaction: Interaction, filtre: str = None):
        character = self.bot.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            embed = _generate_player_error_embed("Tu n'as pas de personnage assigné.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        logger.debug(f"Craftable crafts for {character}: {self.bot.craft_repository.find_craftable_craft(character)}")
            
        craftable_quantities = self.bot.craft_repository.find_craftable_quantities(character)
        crafts = self.bot.craft_repository.get_visible_crafts()

        if filtre == "craftable":
            crafts = [c for c in crafts if c.name in craftable_quantities]
        elif filtre in self.bot.craft_repository.methods:
            crafts = [c for c in crafts if c.method == filtre]
        elif filtre and filtre.isdigit():
            crafts = [c for c in crafts if str(c.difficulty) == filtre]

        if not crafts:
            await interaction.response.send_message(embed=_generate_player_error_embed("Aucun craft trouvé."), ephemeral=False)
            return

        embed = _generate_craft_list_embed(crafts, craftable_quantities)

        await interaction.response.send_message(embed=embed, ephemeral=False)
        
    
    @app_commands.describe(craft_name="Le nom de la recette à afficher.")
    async def craft_info(self, interaction: Interaction, craft_name: str):
        craft = self.bot.craft_repository.get_craft_by_name(craft_name)
        if not craft or not craft.visible:
            await interaction.response.send_message(embed=_generate_player_error_embed("Recette introuvable."), ephemeral=False)
            return

        character = self.bot.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas de personnage assigné."), ephemeral=False)
            return

        craftable_quantity = self.bot.craft_repository.get_craftable_quantity(character)
        craftable = craftable_quantity.get(craft.name, 0) > 0

        embed = _generate_craft_info_embed(craft, character)
        view = CraftInfoView(craftable=craftable)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)


    @app_commands.describe(craft_name="Le nom de la recette à réaliser.", quantity="La quantité de crafts à exécuter.")
    async def execute_craft(self, interaction: Interaction, craft_name: str, quantity: int = 1):
        craft = self.bot.craft_repository.get_craft_by_name(craft_name)
        if not craft or not craft.visible:
            await interaction.response.send_message(embed=_generate_player_error_embed("Recette introuvable."), ephemeral=False)
            return


        character = self.bot.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas de personnage assigné."), ephemeral=False)
            return

        if not self.bot.craft_repository.can_craft(character, craft):
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas les ingrédients nécessaires"), ephemeral=False)
            return
            

        has_crafted, craft_status, products, roll = await self.bot.craft_repository.execute_craft(interaction.guild, character, self.item_repository, craft, quantity)


        if craft_status == "natural_failure" or craft_status == "critical_failure":
            character.gain_experience(1)
        elif craft_status == "critical_success":
            character.gain_experience(craft.experience_gain)
        elif craft_status == "natural_success":
            character.gain_experience(math.ceil(craft.experience_gain * 1.5))
        else:
            character.gain_experience(math.ceil(craft.experience_gain * max(20, roll["total"]) / 20))

        await interaction.response.defer()

        await self.bot.history.log_craft(interaction.guild, character.name, craft, quantity, craft_status, products, roll)
        self.bot.character_repository.update_character(character)

        await self.buff_repository.decrement_buffs_duration(interaction.guild, character.name)

        embed = _generate_craft_executed_embed(craft, quantity, craft_status, products)
        await interaction.followup.send(embed=embed, ephemeral=False)


    async def cog_load(self):
        # --- list ---
        list_cmd = app_commands.Command(
            name="list",
            description="Affiche la liste des crafts disponibles.",
            callback=self.list_crafts,
        )
        list_cmd.autocomplete("filtre")(self.craft_filter_autocomplete)
        self.craft_group.add_command(list_cmd)

        # --- info ---
        info_cmd = app_commands.Command(
            name="info",
            description="Affiche les informations sur un craft.",
            callback=self.craft_info,
        )
        info_cmd.autocomplete("craft_name")(self.craft_autocomplete)
        self.craft_group.add_command(info_cmd)  

        # --- execute ---
        execute_cmd = app_commands.Command(
            name="execute",
            description="Exécute un craft.",
            callback=self.execute_craft,
        )
        execute_cmd.autocomplete("craft_name")(self.craftable_craft_autocomplete)

        self.craft_group.add_command(execute_cmd)



async def setup(bot: commands.Bot):
    await bot.add_cog(Crafts(bot))