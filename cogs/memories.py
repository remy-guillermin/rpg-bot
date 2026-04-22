import discord
from discord.ext import commands
from discord import app_commands, Interaction

from pathlib import Path
import datetime

from utils.admin import admin_only
from utils.autocomplete import make_character_autocomplete, make_fragment_id_autocomplete
from utils.builder_embed import (
    _generate_memory_fragment_embed,
)
from utils.path import MAP_FILE

class Memories(commands.Cog):
    """Commandes liées aux souvenirs."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    def _resolve_callback(self, member):
        """Return the underlying callable for an app_commands.Command or the member itself."""
        return getattr(member, "callback", member)

    async def character_name_autocomplete(self, interaction: Interaction, current: str):
        return await make_character_autocomplete(self.bot.character_repository)(interaction, current)

    async def fragment_id_autocomplete(self, interaction: Interaction, current: str):
        return await make_fragment_id_autocomplete(self.bot.memory)(interaction, current)

    # ── Commandes ────────────────────────────────────────────────────


    @app_commands.command(name="give-memory", description="Donner un fragment de mémoire à un personnage")
    @admin_only()
    @app_commands.autocomplete(
        character_name=character_name_autocomplete,
        fragment_id=fragment_id_autocomplete
    )
    async def memory_give(self, interaction: Interaction, character_name: str, fragment_id: int):
        character = self.bot.character_repository.get_character_by_name(character_name)
        if character is None:
            await interaction.response.send_message(
                f"Personnage `{character_name}` introuvable.", ephemeral=True
            )
            return

        fragment = self.bot.memory.get_fragment(character_name, fragment_id)
        if fragment is None:
            await interaction.response.send_message(
                f"Fragment `{fragment_id}` introuvable pour {character_name}.", ephemeral=True
            )
            return

        player_channel = interaction.guild.get_channel(character.player_channel_id)
        if player_channel is None:
            await interaction.response.send_message(
                f"Salon introuvable pour {character_name}.", ephemeral=True
            )
            return

        await player_channel.send(embed=_generate_memory_fragment_embed(fragment, my_command=False))

        character.memory_fragments.append(f"{character.name}_{fragment.id}")
        self.bot.character_repository.update_character(character)
        await interaction.response.send_message(
            f"Fragment **{fragment.name}** envoyé à {character_name}.", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Memories(bot))