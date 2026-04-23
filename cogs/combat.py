import asyncio
import datetime
import locale
import random

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from instance.combat import Combat as CombatState
from utils.builder_combat import chess_to_hex
from utils.admin import AdminGroup, admin_only
from utils.builder_embed import (
    _generate_admin_enemy_spawn_embed,
    _generate_admin_damage_enemy_embed,
    _generate_admin_heal_enemy_embed,
    _generate_enemy_list_embed,
    _generate_enemy_spawn_embed,
    _generate_combat_end_embed,
    _generate_hp_tracker_embed,
    _generate_enemy_attack_embed,
    _generate_combat_rewards_embed,
)
from utils.path import COMBAT_CHANNEL_NAME
from utils.utils import _get_stat_bonus
from utils.autocomplete import (
    make_active_player_autocomplete,
    make_active_enemy_autocomplete,
    make_catalog_enemy_autocomplete,
    make_combat_target_autocomplete,
)


class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enemy_repository = self.bot.enemy_repository
        self.combat = CombatState()

        self._tracker_lock = asyncio.Lock()

        self.enemy_group = AdminGroup(
            name="enemy",
            description="Commandes liées aux ennemis.",
            default_permissions=discord.Permissions(administrator=True)
        )
        bot.tree.add_command(self.enemy_group)

    # ── Autocomplete ──────────────────────────────────────────────────────────

    async def character_name_autocomplete(self, interaction: Interaction, current: str):
        return await make_active_player_autocomplete(self.bot.character_repository)(interaction, current)

    async def active_enemy_autocomplete(self, interaction: Interaction, current: str):
        return await make_active_enemy_autocomplete(self.bot.enemy_repository)(interaction, current)

    async def catalog_autocomplete(self, interaction: Interaction, current: str):
        return await make_catalog_enemy_autocomplete(self.bot.enemy_repository)(interaction, current)

    async def combat_target_autocomplete(self, interaction: Interaction, current: str):
        return await make_combat_target_autocomplete(self.bot.enemy_repository, self.combat)(interaction, current)

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _get_combat_channel(self, interaction: discord.Interaction) -> discord.TextChannel | None:
        channel = discord.utils.get(interaction.guild.text_channels, name=COMBAT_CHANNEL_NAME)
        if channel is None:
            await interaction.response.send_message(
                f"Channel `{COMBAT_CHANNEL_NAME}` introuvable.", ephemeral=False
            )
        return channel

    def _process_kill(self, enemy, instance_id: str):
        """Enregistre la mort d'un ennemi dans l'instance Combat et retire des actifs."""
        self.combat.register_kill(enemy)
        self.enemy_repository.kill(instance_id)

    async def _refresh_tracker(self, channel: discord.TextChannel):
        async with self._tracker_lock:
            if self.enemy_repository.tracker_message is not None:
                try:
                    await self.enemy_repository.tracker_message.delete()
                except discord.NotFound:
                    pass
                self.enemy_repository.tracker_message = None

            actifs = self.enemy_repository.list_active()

            if not actifs:
                rewards = self.combat.collect_rewards()
                self.enemy_repository.room_type = None
                if rewards["xp"]:
                    for char_name, xp in rewards["xp"].items():
                        fighter = self.bot.character_repository.get_character_by_name(char_name)
                        if fighter:
                            fighter.gain_experience(xp)
                            if char_name in rewards["kills"]:
                                fighter.gain_kills()
                            for boss_id in rewards["boss_kills"].get(char_name, []):
                                fighter.defeat_boss(boss_id)
                            self.bot.character_repository.update_character(fighter)
                    rewards_embed = _generate_combat_rewards_embed(rewards)
                    await channel.send(embed=rewards_embed)

                embed = _generate_combat_end_embed()
                self.enemy_repository.tracker_message = await channel.send(embed=embed)
                return

            embed, file = _generate_hp_tracker_embed(
                actifs,
                self.combat.player_positions,
                self.combat.dead_enemies,
                room_type=self.enemy_repository.room_type or 'cavern',
            )
            self.enemy_repository.tracker_message = await channel.send(file=file, embed=embed)

    # ── Commandes Admin ───────────────────────────────────────────────────────

    async def enemy_list(self, interaction: Interaction):
        actifs = self.enemy_repository.list_active()
        if not actifs:
            await interaction.response.send_message("Aucun ennemi actif.", ephemeral=False)
            return
        embed = _generate_enemy_list_embed(actifs)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="spawn", description="Faire apparaître un ou plusieurs ennemis")
    @admin_only()
    @app_commands.autocomplete(enemy_id=catalog_autocomplete)
    async def spawn(self, interaction: Interaction, enemy_id: str, count: int = 1):
        channel = await self._get_combat_channel(interaction)
        if channel is None:
            return
        await interaction.response.defer(ephemeral=True)
        try:
            extra_occupied = set(self.combat.player_positions.values())
            extra_occupied |= {d["position"] for d in self.combat.dead_enemies if d.get("position")}
            instances = self.enemy_repository.spawn(enemy_id, count, self.bot.character_repository.players, extra_occupied=extra_occupied)
        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral=True)
            return

        self.combat.start(self.bot.character_repository.players)

        player_embed, file = _generate_enemy_spawn_embed(instances, count)
        if file:
            await channel.send(file=file, embed=player_embed)
        else:
            await channel.send(embed=player_embed)

        await self._refresh_tracker(channel)

        await self.bot.history.log_spawn(interaction.guild, instances)
        await interaction.delete_original_response()

    @app_commands.command(name="damage", description="Infliger des dégâts à un ennemi")
    @admin_only()
    @app_commands.autocomplete(
        instance_id=active_enemy_autocomplete,
        character_name=character_name_autocomplete
    )
    async def damage(self, interaction: Interaction, instance_id: str, character_name: str, valeur: int):
        channel = await self._get_combat_channel(interaction)
        if channel is None:
            return
        await interaction.response.defer(ephemeral=True)
        enemy = self.enemy_repository.get(instance_id)
        if enemy is None:
            await interaction.followup.send(f"Ennemi `{instance_id}` introuvable.", ephemeral=True)
            return

        result = enemy.take_damage(valeur)
        if result["alive"]:
            enemy.damage_log[character_name] = (
                enemy.damage_log.get(character_name, 0) + result["actual"]
            )
        else:
            enemy.damage_log[character_name] = (
                enemy.damage_log.get(character_name, 0) + result["hp_before"]
            )
            self._process_kill(enemy, instance_id)

        character = self.bot.character_repository.get_character_by_name(character_name)
        if not character:
            await interaction.followup.send(f"Personnage `{character_name}` introuvable.", ephemeral=True)
            return

        await self.bot.history.log_damage(interaction.guild, enemy, character, result, enemy_attack=False)

        await self._refresh_tracker(channel)
        await interaction.delete_original_response()

    @app_commands.command(name="heal", description="Soigner un ennemi actif")
    @admin_only()
    @app_commands.autocomplete(instance_id=active_enemy_autocomplete)
    async def heal(self, interaction: Interaction, instance_id: str, valeur: int):
        channel = await self._get_combat_channel(interaction)
        if channel is None:
            return
        enemy = self.enemy_repository.get(instance_id)
        if enemy is None:
            await interaction.response.send_message(
                f"Ennemi `{instance_id}` introuvable.", ephemeral=False
            )
            return

        result = enemy.heal(valeur)
        admin_embed = _generate_admin_heal_enemy_embed(enemy, result)
        await interaction.response.send_message(embed=admin_embed, ephemeral=False)
        await self._refresh_tracker(channel)

    @app_commands.command(name="attack", description="Faire attaquer un ennemi contre un joueur")
    @admin_only()
    @app_commands.autocomplete(
        instance_id=active_enemy_autocomplete,
        character_name=character_name_autocomplete
    )
    @app_commands.choices(attack_type=[
        app_commands.Choice(name="Physique", value="physique"),
        app_commands.Choice(name="Magique",  value="magique"),
    ])
    async def attack(self, interaction: Interaction, instance_id: str, character_name: str, attack_type: str = "physique", bonus: int = 0):
        channel = await self._get_combat_channel(interaction)
        if channel is None:
            return
        await interaction.response.defer(ephemeral=True)

        enemy = self.enemy_repository.get(instance_id)
        if enemy is None:
            await interaction.followup.send(f"Ennemi `{instance_id}` introuvable.", ephemeral=True)
            return

        character = self.bot.character_repository.get_character_by_name(character_name)
        if character is None:
            await interaction.followup.send(f"Personnage `{character_name}` introuvable.", ephemeral=True)
            return

        die = 20 if enemy.boss else 5
        roll = random.randint(1, die)
        raw = roll + enemy.atk + bonus
        stat_name = "Résistance" if attack_type == "magique" else "Défense"
        mitigation = sum(_get_stat_bonus(stat_name, character))
        actual = max(1, raw - mitigation)
        absorbed = raw - actual
        hp_before = character.resources.get("hp", 0)

        self.bot.character_repository.change_resources(character, hp_change=-actual)
        hp_after = character.resources.get("hp", 0)

        result = {
            "roll":        roll,
            "die":         die,
            "atk":         enemy.atk,
            "bonus":       bonus,
            "raw":         raw,
            "attack_type": attack_type,
            "defense":     mitigation,
            "absorbed":    absorbed,
            "actual":      actual,
            "hp_before":   hp_before,
            "hp_after":    hp_after,
        }

        await self.bot.history.log_damage(interaction.guild, enemy, character, result, enemy_attack=True)

        player_embed = _generate_enemy_attack_embed(enemy, character_name, result)
        await channel.send(embed=player_embed)

        await interaction.delete_original_response()

    @app_commands.command(name="kill", description="Tuer un ennemi actif")
    @admin_only()
    @app_commands.autocomplete(instance_id=active_enemy_autocomplete)
    async def kill(self, interaction: Interaction, instance_id: str):
        channel = await self._get_combat_channel(interaction)
        if channel is None:
            return
        enemy = self.enemy_repository.get(instance_id)
        if enemy is None:
            await interaction.response.send_message(
                f"Ennemi `{instance_id}` introuvable.", ephemeral=False
            )
            return

        self._process_kill(enemy, instance_id)

        admin_embed = _generate_admin_damage_enemy_embed(enemy, "Admin", {
            "hp_before": enemy.current_hp,
            "hp_after": 0,
            "actual": enemy.current_hp,
            "raw": enemy.current_hp,
            "absorbed": 0,
            "alive": False,
        })
        await interaction.response.send_message(embed=admin_embed, ephemeral=False)
        await self._refresh_tracker(channel)

    @app_commands.command(name="move", description="Déplacer un ennemi ou un joueur vers une case (ex: L12)")
    @admin_only()
    @app_commands.autocomplete(cible=combat_target_autocomplete)
    async def move(self, interaction: Interaction, cible: str, position: str):
        channel = await self._get_combat_channel(interaction)
        if channel is None:
            return

        try:
            new_q, new_r = chess_to_hex(position)
        except (ValueError, IndexError):
            await interaction.response.send_message(
                f"Position `{position}` invalide. Format attendu : lettre + nombre (ex: `L12`).",
                ephemeral=True,
            )
            return

        # Essayer comme ennemi actif d'abord
        enemy = self.enemy_repository.get(cible)
        if enemy is not None:
            occupied = {e.position for e in self.enemy_repository.list_active() if e.position and e.instance_id != cible}
            occupied |= set(self.combat.player_positions.values())
            occupied |= {d['position'] for d in self.combat.dead_enemies}
            if (new_q, new_r) in occupied:
                await interaction.response.send_message(
                    f"Case `{position.upper()}` déjà occupée.", ephemeral=True
                )
                return
            enemy.position = (new_q, new_r)
            await interaction.response.send_message(
                f"✅ **{enemy.name}** déplacé en `{position.upper()}`.",
                ephemeral=True,
            )
            await self._refresh_tracker(channel)
            return

        # Essayer comme joueur
        if cible in self.combat.player_positions:
            occupied = {e.position for e in self.enemy_repository.list_active() if e.position}
            occupied |= {pos for name, pos in self.combat.player_positions.items() if name != cible}
            occupied |= {d['position'] for d in self.combat.dead_enemies}
            if (new_q, new_r) in occupied:
                await interaction.response.send_message(
                    f"Case `{position.upper()}` déjà occupée.", ephemeral=True
                )
                return
            self.combat.player_positions[cible] = (new_q, new_r)
            await interaction.response.send_message(
                f"✅ **{cible}** déplacé en `{position.upper()}`.",
                ephemeral=True,
            )
            await self._refresh_tracker(channel)
            return

        await interaction.response.send_message(
            f"Cible `{cible}` introuvable parmi les ennemis actifs et les joueurs en combat.",
            ephemeral=True,
        )

    async def cog_load(self):
        list_cmd = app_commands.Command(
            name="list",
            description="Afficher la liste des ennemis actifs.",
            callback=self.enemy_list,
        )
        self.enemy_group.add_command(list_cmd)


async def setup(bot: commands.Bot):
    await bot.add_cog(Combat(bot))
