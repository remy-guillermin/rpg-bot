import discord
from discord.ext import commands
from discord import app_commands, Interaction

from utils.builder_embed import (
    _generate_basic_dice_embed,
    _generate_stat_dice_embed,
    _generate_player_error_embed,
    _generate_session_summary_embed,
)
from utils.autocomplete import make_stat_dice_autocomplete
from utils.utils import _get_stat_bonus, clean_dice_summary
from utils.admin import admin_only
from utils.path import GM_NAMES

class Dices(commands.Cog):
    """Commandes liées aux dés."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dice_session = bot.dice_session
        self.buff_repository = bot.buff_repository

    def _resolve_callback(self, member):
        """Return the underlying callable for an app_commands.Command or the member itself."""
        return getattr(member, "callback", member)

    # ── Commandes ────────────────────────────────────────────────────
    @app_commands.command(name="d", description="Lance un dé .")
    @app_commands.describe(dice="Le dé à lancer, au format XdY+Z (ex: 2d6 pour lancer 2 dés à 6 faces et 0 de bonus).")
    async def basic_dice(self, interaction: Interaction, dice: str = "1d20"):
        character = self.bot.character_repository.get_character_by_user_id(interaction.user.id)
        if character is None:
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas de personnage associé à ton compte."), ephemeral=False)
            return

        await self.buff_repository.decrement_buffs_duration(interaction.guild, character.name)

        roll = self.dice_session.roll(dice, character_name=character.name)
        embed = _generate_basic_dice_embed(roll)
        await interaction.response.send_message(embed=embed, ephemeral=False)


    @app_commands.command(name="dstats", description="Lance un dé de statistiques.")
    @app_commands.describe(
        stat="La statistique à tester (force, agilité, attaque, défense ou charisme).", 
        faces="Le nombre de faces du dé à lancer (par défaut 20).", 
        bonus="Un bonus à ajouter au résultat du dé (par défaut 0)."
    )
    async def stats_dice(self, interaction: Interaction, stat: str, faces: int = 20, bonus: int = 0):
        character = self.bot.character_repository.get_character_by_user_id(interaction.user.id)
        if character is None:
            await interaction.response.send_message(embed=_generate_player_error_embed("Tu n'as pas de personnage associé à ton compte."), ephemeral=False)
            return
        
        base_bonus, level_bonus, item_bonus, buff_bonus = _get_stat_bonus(stat, character)
        total_bonus = base_bonus + level_bonus + item_bonus + buff_bonus + bonus

        await self.buff_repository.decrement_buffs_duration(interaction.guild, character.name, force=True)
        self.bot.character_repository.reload_buffs()

        expression = f"1d{faces}+{total_bonus}" if total_bonus > 0 else f"1d{faces}{total_bonus}" if total_bonus < 0 else f"1d{faces}"

        roll = self.dice_session.stat_roll(expression, stat_name=stat, character_name=character.name)

        embed = _generate_stat_dice_embed(character.name, stat, roll, {"base": base_bonus, "level": level_bonus, "item": item_bonus, "buff": buff_bonus, "admin": bonus}, faces)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @stats_dice.autocomplete("stat")
    async def stat_dice_autocomplete(self, interaction: Interaction, current: str):
        return await make_stat_dice_autocomplete()(interaction, current)

    @app_commands.command(name="dsummary", description="Affiche un résumé des jets de dés de la session en cours.")
    @admin_only()
    async def dice_summary(self, interaction: Interaction):
        to_remove = GM_NAMES
        names = [p for p in self.bot.character_repository.get_all_character_names() if p not in to_remove]
        summary = self.dice_session.summary(characters=names)
        
        summary = clean_dice_summary(summary)
        
        
        embed = _generate_session_summary_embed(summary)
        await interaction.response.send_message(embed=embed, ephemeral=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Dices(bot))