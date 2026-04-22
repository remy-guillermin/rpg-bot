import discord
from discord.ext import commands
from discord import app_commands, Interaction

from utils.admin import admin_only

class Histories(commands.Cog):
    """Commandes liées à l'historique."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(name="backup", description="Crée une sauvegarde des fichiers locaux actuels.")
    @admin_only()
    async def backup(self, interaction: Interaction):
        await interaction.response.defer()
        try:
            self.bot.history.create_backup()
            await interaction.followup.send("Sauvegarde créée avec succès.")
        except Exception as e:
            await interaction.followup.send(f"Erreur lors de la création de la sauvegarde: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Histories(bot))