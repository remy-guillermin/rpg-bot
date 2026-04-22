import discord
from discord.ext import commands
from discord import app_commands, Interaction
import datetime


from utils.builder_embed import (
    _generate_character_embed, 
    _generate_stats_embed, 
    _generate_inventory_embed,
    _generate_powers_embed,
    _generate_buffs_embed,
    _generate_memory_fragment_embed,
    _generate_player_error_embed,
    _generate_quests_embed,
)
from utils.builder_view import PowersView
from utils.admin import handle_admin_permission_error

class My(commands.Cog):
    """Commandes liées aux joueurs."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.character_repository = bot.character_repository

        self.my_group = app_commands.Group(name="my", description="Commandes liées aux joueurs.")
        bot.tree.add_command(self.my_group)


# ── Commandes ────────────────────────────────────────────────────
    async def my_character(self, interaction: Interaction):
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            embed = _generate_player_error_embed("Tu n'as pas de personnage assigné.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        embed, buf = _generate_character_embed(character)
        
        await interaction.response.send_message(
            embed=embed, 
            file=discord.File(buf, filename="status.png"),
            ephemeral=False
        )
    
    async def my_inventory(self, interaction: Interaction):
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            embed = _generate_player_error_embed("Tu n'as pas de personnage assigné.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
            
        embed = _generate_inventory_embed(character)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=False
        )

    async def my_stats(self, interaction: Interaction):
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            embed = _generate_player_error_embed("Tu n'as pas de personnage assigné.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        embed, buf = _generate_stats_embed(character)

        await interaction.response.send_message(
            embed=embed, 
            file=discord.File(buf, filename="stats.png"),
            ephemeral=False
        )

    async def my_powers(self, interaction: Interaction):
        await interaction.response.defer()  # ← acquitte immédiatement, donne 15 min

        character = self.character_repository.get_character_by_user_id(interaction.user.id)

        if not character:
            embed = _generate_player_error_embed("Tu n'as pas de personnage assigné.")
            await interaction.followup.send(embed=embed)
            return

        if not character.powers:
            embed = _generate_player_error_embed("Tu n'as aucun pouvoir assigné.")
            await interaction.followup.send(embed=embed)
            return

        if not character.powers:
            embed = _generate_player_error_embed("Tu n'as aucun pouvoir assigné.")
            await interaction.followup.send(embed=embed)
            return

        embed = _generate_powers_embed(character)
        view = PowersView(character)
        await interaction.followup.send(embed=embed, view=view)

    async def my_buffs(self, interaction: Interaction):
        character = self.character_repository.get_character_by_user_id(interaction.user.id)
        if not character:
            embed = _generate_player_error_embed("Tu n'as pas de personnage assigné.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
        
        character_buffs = character.buffs
        if not character_buffs:
            embed = _generate_player_error_embed("Tu n'as aucun buff actif.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        embed = _generate_buffs_embed(character)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    async def my_memory(self, interaction: Interaction):
        character = self.bot.character_repository.get_character_by_user_id(interaction.user.id)
        if character is None:
            await interaction.response.send_message(
                "Aucun personnage trouvé.", ephemeral=False
            )
            return

        if not character.memory_fragments:
            await interaction.response.send_message(
                "Tu n'as aucun souvenir pour l'instant.", ephemeral=False
            )
            return

        fragments = []
        for entry in character.memory_fragments:
            name, fragment_id = entry.rsplit("_", 1)
            fragment = self.bot.memory.get_fragment(name, int(fragment_id))
            if fragment is not None:
                fragments.append(fragment)

        if not fragments:
            await interaction.response.send_message(
                "Tu n'as aucun souvenir pour l'instant.", ephemeral=False
            )
            return

        await interaction.response.defer(ephemeral=False)
        for fragment in fragments:
            await interaction.followup.send(
                embed=_generate_memory_fragment_embed(fragment), ephemeral=False
            )

    async def my_quests(self, interaction: Interaction):
        active = self.bot.quest_progress.get_active()
        completed = self.bot.quest_progress.get_completed()

        embed = _generate_quests_embed(active, completed, self.bot.npc_repository)
        await interaction.response.send_message(embed=embed, ephemeral=False)


    async def cog_load(self):
        character_cmd = app_commands.Command(
            name="character",
            description="Affiche les informations de votre personnage.",
            callback=self.my_character,
        )
        self.my_group.add_command(character_cmd)

        inventory_cmd = app_commands.Command(
            name="inventory",
            description="Affiche votre inventaire.",
            callback=self.my_inventory,
        )
        self.my_group.add_command(inventory_cmd)

        stats_cmd = app_commands.Command(
            name="stats",
            description="Affiche vos statistiques.",
            callback=self.my_stats,
        )
        self.my_group.add_command(stats_cmd)    

        powers_cmd = app_commands.Command(
            name="powers",
            description="Affiche vos pouvoirs.",
            callback=self.my_powers,
        )
        self.my_group.add_command(powers_cmd)   

        buffs_cmd = app_commands.Command(
            name="buffs",
            description="Affiche vos buffs.",
            callback=self.my_buffs,
        )
        self.my_group.add_command(buffs_cmd)

        memory_cmd = app_commands.Command(
            name="memory",
            description="Affiche vos fragments de mémoire.",
            callback=self.my_memory,
        )
        self.my_group.add_command(memory_cmd)

        quests_cmd = app_commands.Command(
            name="quests",
            description="Affiche les quêtes du groupe.",
            callback=self.my_quests,
        )
        self.my_group.add_command(quests_cmd)

async def setup(bot: commands.Bot):
    await bot.add_cog(My(bot))