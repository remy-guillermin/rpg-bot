import discord
from discord.ext import commands
from discord import app_commands, Interaction

import random

from utils.autocomplete import make_character_autocomplete, make_buff_autocomplete
from utils.builder_embed import (
    _generate_buff_list_embed, 
    _generate_buff_add_embed, 
    _generate_buff_remove_embed, 
    _generate_buff_clear_embed, 
    _generate_buff_decrement_embed,
    _generate_player_error_embed
)
from utils.builder_view import ConfirmBuffView, ConfirmClearBuffsView, ConfirmRemoveBuffView
from utils.admin import handle_admin_permission_error, AdminGroup
from utils.utils import de_du_nom, _extract_buff_effects, STAT_MAP
from utils.variations import DEFAULT_BUFF_SOURCES, DEFAULT_BUFF_DESCRIPTIONS

from instance.buff import BuffRepository, Buff
from instance.character import CharacterRepository, Character

class Buffs(commands.Cog):
    """Commandes liées aux buffs."""
    def __init__(self, bot):
        self.bot = bot
        self.buff_repository: BuffRepository = bot.buff_repository
        self.character_repository: CharacterRepository = bot.character_repository

        self.buff_group = AdminGroup(
            name="buff",
            description="Commandes liées aux buffs.",
            default_permissions=discord.Permissions(administrator=True)
        )
        bot.tree.add_command(self.buff_group)

    def _resolve_callback(self, member):
        """Return the underlying callable for an app_commands.Command or the member itself."""
        return getattr(member, "callback", member)

    async def character_name_autocomplete(self, interaction: Interaction, current: str):
        return await make_character_autocomplete(self.bot.character_repository)(interaction, current)


    # ── Commandes ────────────────────────────────────────────────────
    async def list_buffs(self, interaction: Interaction):
        buffs: list[Buff] = self.buff_repository.buffs
        if not buffs:
            await interaction.response.send_message(embed=_generate_player_error_embed("Aucun buff actif."), ephemeral=False)
            return

        embed = _generate_buff_list_embed(buffs)
        await interaction.response.send_message(embed=embed, ephemeral=False)


    @app_commands.describe(
        character_name="Le nom du personnage pour qui ajouter le buff.", 
        effects="Les effets du buff à ajouter.",
        buff_name="Le nom du buff (optionnel, sera généré automatiquement si non fourni).",
        description="La description du buff (optionnelle, sera générée automatiquement si non fournie).",
        source="La source du buff (optionnelle, sera générée automatiquement si non fournie)."
    )
    async def add_buff(self, interaction: Interaction, character_name: str, effects: str, buff_name: str = "", description: str = "", source: str = ""):
        character: Character = self.character_repository.get_character_by_name(character_name)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Personnage '{character_name}' non trouvé."), ephemeral=False)
            return
        if not effects:
            await interaction.response.send_message(embed=_generate_player_error_embed("Les effets ne peuvent pas être vides."), ephemeral=False)
            return

        buff_effects = _extract_buff_effects(effects)
        description_parts = []
        kwargs = {}

        if source == "":
            # On prend la première stat du buff comme stat principale
            main_stat = next(iter(buff_effects)).lower() if buff_effects else None
            pool = DEFAULT_BUFF_SOURCES.get(main_stat, DEFAULT_BUFF_SOURCES["default"])
            source = random.choice(pool)

        if description == "":
            main_stat = next(iter(buff_effects)).lower() if buff_effects else None
            pool = DEFAULT_BUFF_DESCRIPTIONS.get(main_stat, DEFAULT_BUFF_DESCRIPTIONS["default"])
            description = random.choice(pool).format(
                character=character_name,
                de_character=de_du_nom(character_name)
            )
        

        for stat, (bonus, duration) in buff_effects.items():
            if buff_name == "" and duration > 0:
                buff_name = f"Buff d'{stat.lower()}" if stat[0].lower() in ["a", "e", "i", "o", "u", "h"] else f"Buff de {stat.lower()}"

            if duration == -1:
                key = STAT_MAP.get(stat.lower())
                if key:
                    kwargs[key] = bonus

        if description == "":
            description = ", ".join(description_parts)

        embed = _generate_buff_add_embed(character_name, buff_name, description, buff_effects, source)
        view = ConfirmBuffView(self, character, buff_effects, buff_name, description, character_name, kwargs, source)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)


    @app_commands.describe(character_name="Le nom du personnage pour qui supprimer le buff.", buff_name="Le nom du buff à supprimer.")
    async def remove_buff(self, interaction: Interaction, character_name: str, buff_name: str):
        buff = self.buff_repository.get_buff_by_name_and_character(buff_name, character_name)
        if not buff:
            await interaction.response.send_message(
                embed=_generate_player_error_embed(f"Aucun buff **{buff_name}** trouvé pour '{character_name}'."), ephemeral=False
            )
            return

        embed = _generate_buff_remove_embed(character_name, buff)
        view = ConfirmRemoveBuffView(self, character_name, buff_name)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)


    @app_commands.describe(character_name="Le nom du personnage pour qui supprimer tous les buffs.")
    async def clear_buffs(self, interaction: Interaction, character_name: str):
        buffs = self.buff_repository.get_buffs_by_character(character_name)
        if not buffs:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Aucun buff actif pour '{character_name}'."), ephemeral=False)
            return

        embed = _generate_buff_clear_embed(character_name, buffs)
        view = ConfirmClearBuffsView(self, character_name)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)


    
    async def increment_buffs(self, interaction: Interaction, character_name: str):
        buffs = self.buff_repository.get_buffs_by_character(character_name)
        if not buffs:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Aucun buff actif pour '{character_name}'."), ephemeral=False)
            return 

        self.buff_repository.increment_buffs_duration(character_name)

        embed = _generate_buff_decrement_embed(character_name, buffs, decrement=False)
        await interaction.response.send_message(embed=embed, ephemeral=False)




    @app_commands.describe(character_name="Le nom du personnage pour qui décrementer tous les buffs.")
    async def decrement_buffs(self, interaction: Interaction, character_name: str):
        character = self.character_repository.get_character_by_name(character_name)
        if not character:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Personnage '{character_name}' non trouvé."), ephemeral=False)
            return

        buffs = self.buff_repository.get_buffs_by_character(character_name)
        if not buffs or buffs == []:
            await interaction.response.send_message(embed=_generate_player_error_embed(f"Aucun buff actif pour '{character_name}'."), ephemeral=False)
            return

        await self.buff_repository.decrement_buffs_duration(interaction.guild, character_name)
        
        embed = _generate_buff_decrement_embed(character_name, buffs)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    
    async def activate_buff_decrement(self, interaction: Interaction, active: bool):
        self.buff_repository.set_auto_decrement(active)

        await interaction.response.send_message(f"Décrémentation automatique des buffs {'activée' if active else 'désactivée'}.", ephemeral=False)
    



    async def buff_autocomplete(self, interaction: Interaction, current: str):
        return await make_buff_autocomplete(self.buff_repository)(interaction, current)

    async def cog_load(self):
        # --- list ---
        list_cmd = app_commands.Command(
            name="list",
            description="Affiche la liste des buffs.",
            callback=self._resolve_callback(self.list_buffs),
        )
        self.buff_group.add_command(list_cmd)

        # --- add ---
        add_cmd = app_commands.Command(
            name="add",
            description="Ajoute un buff à un personnage.",
            callback=self._resolve_callback(self.add_buff),
        )
        add_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        self.buff_group.add_command(add_cmd)   

        # --- remove ---
        remove_cmd = app_commands.Command(
            name="remove",
            description="Supprime un buff d'un personnage.",
            callback=self._resolve_callback(self.remove_buff),
        )
        remove_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        remove_cmd.autocomplete("buff_name")(self.buff_autocomplete)
        self.buff_group.add_command(remove_cmd)

        # --- clear ---
        clear_cmd = app_commands.Command(
            name="clear",
            description="Supprime tous les buffs d'un personnage.",
            callback=self._resolve_callback(self.clear_buffs),
        )
        clear_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        self.buff_group.add_command(clear_cmd)

        # --- increment ---
        increment_cmd = app_commands.Command(
            name="increment",
            description="Incrémente la durée de tous les buffs d'un personnage.",
            callback=self._resolve_callback(self.increment_buffs),
        )
        increment_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        self.buff_group.add_command(increment_cmd)  

        # --- decrement ---
        decrement_cmd = app_commands.Command(
            name="decrement",
            description="Décrémente la durée de tous les buffs d'un personnage.",
            callback=self._resolve_callback(self.decrement_buffs),
        )
        decrement_cmd.autocomplete("character_name")(self.character_name_autocomplete)
        self.buff_group.add_command(decrement_cmd)

        # --- auto-decrement ---
        auto_decrement_cmd = app_commands.Command(
            name="autodec",
            description="Active ou désactive la décrémentation automatique des buffs à chaque heure.",
            callback=self._resolve_callback(self.activate_buff_decrement),
        )
        self.buff_group.add_command(auto_decrement_cmd)
    

async def setup(bot: commands.Bot):
    await bot.add_cog(Buffs(bot))