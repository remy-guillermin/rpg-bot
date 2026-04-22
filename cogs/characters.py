import discord
from discord.ext import commands
from discord import app_commands, Interaction

import datetime

from instance.character import Character

from utils.utils import _send_embed
from utils.admin import handle_admin_permission_error, AdminGroup
from utils.autocomplete import make_character_autocomplete
from utils.builder_embed import (
    _generate_character_embed, 
    _generate_stats_embed, 
    _generate_inventory_embed, 
    _generate_powers_embed,
    _generate_buffs_embed,
    _generate_player_error_embed,
    _generate_quests_embed
)
from utils.builder_view import PowersView


class Characters(commands.Cog):
    """Commandes liées aux personnages."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.character_repository = bot.character_repository

        self.character_group = AdminGroup(
            name="character", 
            description="Commandes liées aux personnages.",
            default_permissions=discord.Permissions(administrator=True)
        )
        bot.tree.add_command(self.character_group)

    def _resolve_callback(self, member):
        """Return the underlying callable for an app_commands.Command or the member itself."""
        return getattr(member, "callback", member)

    async def character_name_autocomplete(self, interaction: Interaction, current: str):
        return await make_character_autocomplete(self.bot.character_repository)(interaction, current)

    # ── Commandes ────────────────────────────────────────────────────
    async def list_characters(self, interaction: Interaction):
        embed = discord.Embed(title="Liste des personnages", description="Voici la liste de tous les personnages disponibles.", color=discord.Color.purple(), timestamp=datetime.datetime.now())

        characters = self.character_repository.get_all_characters()
        if not characters:
            embed.description = "Aucun personnage trouvé."
        else:
            assigned_characters = [f"- {char.name} (<@{char.user_id}>)" for char in characters if char.user_id is not None]
            unassigned_characters = [f"- {char.name}" for char in characters if char.user_id is None]
            if assigned_characters:
                embed.add_field(name="Personnages assignés", value="\n".join(assigned_characters), inline=False)
            if unassigned_characters:
                embed.add_field(name="Personnages non assignés", value="\n".join(unassigned_characters), inline=False)
            
            
        await _send_embed(interaction, embed)


    @app_commands.describe(character_name="Le nom du personnage à afficher.")
    async def info_character(self, interaction: Interaction, character_name: str):
        character: Character = self.character_repository.get_character_by_name(character_name)
        if not character:
            embed = _generate_player_error_embed(f"Aucun personnage nommé '{character_name}' n'a été trouvé.")
            await _send_embed(interaction, embed)
            return

        embed, buf = _generate_character_embed(character, my_command=False)
        
        await interaction.response.send_message(
            embed=embed, 
            file=discord.File(buf, filename="status.png"),
            ephemeral=False
        )
    

    @app_commands.describe(character_name="Le nom du personnage à afficher.")
    async def stat_character(self, interaction: Interaction, character_name: str):
        character: Character = self.character_repository.get_character_by_name(character_name)
        if not character:
            embed = _generate_player_error_embed(f"Aucun personnage nommé '{character_name}' n'a été trouvé.")
            await _send_embed(interaction, embed)
            return
        
        embed, buf = _generate_stats_embed(character, my_command=False)

        await interaction.response.send_message(
            embed=embed, 
            file=discord.File(buf, filename="stats.png"),
            ephemeral=False
        )


    @app_commands.describe(character_name="Le nom du personnage à afficher.")
    async def inventory_character(self, interaction: Interaction, character_name: str):
        character: Character = self.character_repository.get_character_by_name(character_name)
        if not character:
            embed = _generate_player_error_embed(f"Aucun personnage nommé '{character_name}' n'a été trouvé.")
            await _send_embed(interaction, embed)
            return
        
        embed = _generate_inventory_embed(character, my_command=False)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=False
        )


    @app_commands.describe(character_name="Le nom du personnage à afficher.")
    async def powers_character(self, interaction: Interaction, character_name: str):
        await interaction.response.defer()
        
        character: Character = self.character_repository.get_character_by_name(character_name)
        if not character:
            embed = _generate_player_error_embed(f"Aucun personnage nommé '{character_name}' n'a été trouvé.")
            await _send_embed(interaction, embed)
            return
        
        embed = _generate_powers_embed(character, my_command=False)
        view = PowersView(character)
        await interaction.followup.send(
            embed=embed, 
            view=view,
            ephemeral=False
        )


    @app_commands.describe(character_name="Le nom du personnage à afficher.")
    async def buffs_character(self, interaction: Interaction, character_name: str):
        character: Character = self.character_repository.get_character_by_name(character_name)
        
        if not character:
            embed = _generate_player_error_embed(f"Aucun personnage nommé '{character_name}' n'a été trouvé.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
        
        character_buffs = character.buffs
        if not character_buffs:
            embed = _generate_player_error_embed(f"Le personnage '{character_name}' n'a aucun buff actif.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        embed = _generate_buffs_embed(character)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.describe(character_name="Le nom du personnage à afficher.")
    async def quests_character(self, interaction: Interaction, character_name: str):
        active = self.bot.quest_progress.get_active()
        completed = self.bot.quest_progress.get_completed()

        embed = _generate_quests_embed(active, completed, self.bot.npc_repository)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    async def cog_load(self):
        # --- list ---
        list_cmd = app_commands.Command(
            name="list",
            description="Affiche la liste des personnages.",
            callback=self._resolve_callback(self.list_characters),
        )
        self.character_group.add_command(list_cmd)

        # --- buffs ---
        buffs_cmd = app_commands.Command(
            name="buffs",
            description="Affiche les buffs actifs d'un personnage.",
            callback=self._resolve_callback(self.buffs_character),
        )
        buffs_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        self.character_group.add_command(buffs_cmd)

        # --- info ---
        info_cmd = app_commands.Command(
            name="info",
            description="Affiche les informations d'un personnage.",
            callback=self._resolve_callback(self.info_character),
        )
        info_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        self.character_group.add_command(info_cmd)

        # --- inventory ---
        inventory_cmd = app_commands.Command(
            name="inventory",
            description="Affiche l'inventaire d'un personnage.",
            callback=self._resolve_callback(self.inventory_character),
        )
        inventory_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        self.character_group.add_command(inventory_cmd)

        # --- powers ---
        powers_cmd = app_commands.Command(
            name="powers",
            description="Affiche les pouvoirs d'un personnage.",
            callback=self._resolve_callback(self.powers_character),
        )
        powers_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        self.character_group.add_command(powers_cmd)

        # --- stats ---
        stat_cmd = app_commands.Command(
            name="stats",
            description="Affiche les statistiques d'un personnage.",
            callback=self._resolve_callback(self.stat_character),
        )
        stat_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        self.character_group.add_command(stat_cmd)

        # --- quests ---
        quests_cmd = app_commands.Command(
            name="quests",
            description="Affiche les quêtes d'un personnage.",
            callback=self._resolve_callback(self.quests_character),
        )
        quests_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        self.character_group.add_command(quests_cmd)

async def setup(bot: commands.Bot):
    await bot.add_cog(Characters(bot))