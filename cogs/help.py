import discord
from discord.ext import commands
from discord import app_commands, Interaction

from utils.builder_embed import _generate_help_embed

class Help(commands.Cog):
    """Commandes d'aide du bot."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Commandes ────────────────────────────────────────────────────
    @app_commands.command(name="help", description="Affiche l'aide du bot.")
    async def help(self, interaction: Interaction):
        embed = _generate_help_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))