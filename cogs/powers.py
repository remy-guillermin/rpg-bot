import discord
from discord.ext import commands
from discord import app_commands, Interaction

import datetime

from utils.builder_embed import (
    _generate_power_embed,
    _generate_power_use_embed,
    _generate_player_error_embed,
)
from utils.builder_view import TargetSelectionView
from utils.utils import STAT_MAP
from utils.admin import handle_admin_permission_error, admin_only
from utils.autocomplete import make_power_autocomplete, make_all_powers_autocomplete, make_character_autocomplete
from utils.db import get_connection

from instance.character import Character
from instance.power import Power
from instance.buff import Buff

class Powers(commands.Cog):
    """Commandes liées aux pouvoirs."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.power_repository = bot.power_repository
        self.character_repository = bot.character_repository
        self.buff_repository = bot.buff_repository

        self.power_group = app_commands.Group(name="power", description="Commandes liées aux pouvoirs.")
        bot.tree.add_command(self.power_group)

    def _resolve_callback(self, member):
        """Return the underlying callable for an app_commands.Command or the member itself."""
        return getattr(member, "callback", member)

    
    async def power_autocomplete(self, interaction: Interaction, current: str):
        return await make_power_autocomplete(self.bot.character_repository)(interaction, current)

    async def all_powers_autocomplete(self, interaction: Interaction, current: str):
        return await make_all_powers_autocomplete(self.power_repository)(interaction, current)

    async def character_autocomplete(self, interaction: Interaction, current: str):
        return await make_character_autocomplete(self.character_repository)(interaction, current)

    # ── Commandes ────────────────────────────────────────────────────
    @app_commands.command(name="powers", description="Affiche la liste des pouvoirs disponibles.")
    @admin_only()
    async def power_list(self, interaction: Interaction):
        """Affiche la liste des pouvoirs disponibles."""
        embed = discord.Embed(
            title="Liste des pouvoirs", 
            description="Voici les pouvoirs disponibles.", 
            color=discord.Color.dark_magenta(),
            timestamp=datetime.datetime.now()
        )

        assigned_powers = {}
        for character in self.character_repository.characters.values():
            for power in character.powers:
                assigned_powers.setdefault(power.name, []).append(character.name)
        
        powers = assigned_powers.copy()

        for power in self.power_repository.powers.values():
            if power.name not in assigned_powers:
                powers.setdefault(power.name, [])


        for power, characters in sorted(powers.items()):
            character_list = ", ".join(characters) if characters else "Aucun personnage"
            embed.add_field(name=power, value=character_list, inline=True)

        await interaction.response.send_message(embed=embed)

    
    @app_commands.describe(power_name="Le nom du pouvoir à afficher.")
    async def power_info(self, interaction: Interaction, power_name: str):
        """Affiche les informations sur un pouvoir."""
        character: Character = self.character_repository.get_character_by_user_id(interaction.user.id)
        power: Power = self.power_repository.get_power_by_name(power_name)

        if not character:
            embed = _generate_player_error_embed("Tu n'as pas de personnage assigné.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
        
        if power_name not in [power.name for power in character.powers]:
            embed = _generate_player_error_embed(f"Tu ne possédes pas le pouvoir **{power_name}**.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        if not power:
            embed = _generate_player_error_embed(f"Le pouvoir **{power_name}** n'existe pas dans la base de données.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
        
        embed = _generate_power_embed(power)

        await interaction.response.send_message(embed=embed, ephemeral=False)


    @app_commands.describe(power_name="Le nom du pouvoir à utiliser.")
    async def power_use(self, interaction: Interaction, power_name: str):
        """Utilise un pouvoir."""
        character: Character = self.character_repository.get_character_by_user_id(interaction.user.id)
        power: Power = self.power_repository.get_power_by_name(power_name)

        if not character:
            embed = _generate_player_error_embed("Tu n'as pas de personnage assigné.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
        
        if power_name not in [power.name for power in character.powers]:
            embed = _generate_player_error_embed(f"Tu ne possédes pas le pouvoir **{power_name}**.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        if not power:
            embed = _generate_player_error_embed(f"Le pouvoir **{power_name}** n'existe pas dans la base de données.")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        insufficient = {k: power.cost[k] - character.resources[k] for k in power.cost if character.resources[k] < power.cost[k]}
        if insufficient:
            insufficient_str = ", ".join(f"{k}: {v}" for k, v in insufficient.items())
            embed = _generate_player_error_embed(f"Tu n'as pas assez de ressources pour utiliser ce pouvoir. Ressources manquantes: {insufficient_str}")
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        if power.target_effect:
            needs_selection = any(count == 1 for _, (_, _, count) in power.target_effect.items())
            if needs_selection:
                targets = [
                    self.character_repository.get_character_by_name(name)
                    for name in self.character_repository.players
                    if name != character.name
                ]
                view = TargetSelectionView(
                    cog=self,
                    power=power,
                    caster=character,
                    targets=targets,
                    guild=interaction.guild,
                    original_user_id=interaction.user.id,
                )
                await interaction.response.send_message(
                    content=f"🎯 **{power.name}** — Choisis une cible :",
                    view=view,
                    ephemeral=False,
                )
                return

            # Effets sur tous les joueurs actifs (count=-1), pas de sélection
            await self.buff_repository.decrement_buffs_duration(interaction.guild, character.name)
            buff_dict, power_effects, roll, instant_resources = await self.power_repository.power_use(interaction.guild, character, power.name)
            if buff_dict:
                buff = Buff(**buff_dict)
                await self.buff_repository.add_buff(interaction.guild, buff)
            if instant_resources:
                self.character_repository.change_resources(character, **instant_resources)
            self.character_repository.update_character(character)

            all_characters = [
                self.character_repository.get_character_by_name(name)
                for name in self.character_repository.players
            ]
            for aoe_target in all_characters:
                for stat, (bonus, duration, count) in power.target_effect.items():
                    if count != -1:
                        continue
                    if duration == -1:
                        key = STAT_MAP.get(stat.lower())
                        if key:
                            self.character_repository.change_resources(aoe_target, **{key: bonus})
                    else:
                        aoe_buff = Buff(
                            name=power.name,
                            description=power.description,
                            duration=duration,
                            effects={stat: bonus},
                            character_name=aoe_target.name,
                            source=f"Pouvoir: {power.name} par {character.name}",
                        )
                        await self.buff_repository.add_buff(interaction.guild, aoe_buff)
                self.character_repository.update_character(aoe_target)

            embed = _generate_power_use_embed(power, character.name, power_effects, roll, target_effect=power.target_effect)
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        await self.buff_repository.decrement_buffs_duration(interaction.guild, character.name)

        buff_dict, power_effects, roll, instant_resources = await self.power_repository.power_use(interaction.guild, character, power.name)
        if buff_dict:
            buff = Buff(**buff_dict)
            await self.buff_repository.add_buff(interaction.guild, buff)
        if instant_resources:
            self.character_repository.change_resources(character, **instant_resources)

        self.character_repository.update_character(character)

        embed = _generate_power_use_embed(power, character.name, power_effects, roll)

        await interaction.response.send_message(embed=embed, ephemeral=False)


    @app_commands.describe(
        character_name="Personnage auquel assigner le pouvoir.",
        power_name="Pouvoir à assigner."
    )
    async def give_power(self, interaction: Interaction, character_name: str, power_name: str):
        """Assigne un pouvoir à un personnage."""
        character = self.character_repository.get_character_by_name(character_name)
        if not character:
            embed = _generate_player_error_embed(f"Personnage '{character_name}' introuvable.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        power = self.power_repository.get_power_by_name(power_name)
        if not power:
            embed = _generate_player_error_embed(f"Le pouvoir '{power_name}' n'existe pas.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if any(p.name == power.name for p in character.powers):
            await interaction.response.send_message(
                f"⚠️ **{character_name}** possède déjà le pouvoir **{power.name}**.", ephemeral=True
            )
            return

        character.powers.append(power)
        with get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO power_assignments (character_name, power_name) VALUES (?, ?)",
                (character.name, power.name),
            )
        self.character_repository.characters[character.name] = character

        await interaction.response.send_message(
            f"✅ Pouvoir **{power.name}** assigné à **{character_name}**.", ephemeral=True
        )

    async def cog_load(self):
        # --- info ---
        info_cmd = app_commands.Command(
            name="info",
            description="Affiche les informations sur un pouvoir.",
            callback=self.power_info,
        )
        info_cmd.autocomplete("power_name")(self.power_autocomplete)
        self.power_group.add_command(info_cmd)  

        # --- use ---
        use_cmd = app_commands.Command(
            name="use",
            description="Utilise un pouvoir.",
            callback=self.power_use,
        )
        use_cmd.autocomplete("power_name")(self.power_autocomplete)
        self.power_group.add_command(use_cmd)

        # --- give-power ---
        give_power_cmd = app_commands.Command(
            name="give-power",
            description="Assigne un pouvoir à un personnage.",
            callback=self.give_power,
        )
        give_power_cmd.default_permissions = discord.Permissions(administrator=True)
        give_power_cmd.autocomplete("character_name")(self.character_autocomplete)
        give_power_cmd.autocomplete("power_name")(self.all_powers_autocomplete)
        self.bot.tree.add_command(give_power_cmd)

async def setup(bot: commands.Bot):
    await bot.add_cog(Powers(bot))