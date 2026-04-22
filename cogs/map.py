import discord
from discord.ext import commands
from discord import app_commands, Interaction

from pathlib import Path
import datetime

from utils.path import MAP_FILE

class Map(commands.Cog):
    """Commandes liées à la carte."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # ── Commandes ────────────────────────────────────────────────────
    @app_commands.command(name="map", description="Affiche la carte du monde.")
    async def map_display(self, interaction: Interaction):
        """Affiche la carte du monde."""
        await interaction.response.defer(ephemeral=False)

        path = Path(MAP_FILE).resolve()
        if not path.exists():
            embed = discord.Embed(
                title="Carte introuvable",
                description=f"Le fichier de carte n'a pas été trouvé: `{path}`",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            await interaction.followup.send(embed=embed, ephemeral=False)
            return

        file = discord.File(path, filename="map.png")
        embed = discord.Embed(
            title="🗺️ Carte",
            description="Voici la carte.",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_image(url="attachment://map.png")
        await interaction.followup.send(embed=embed, file=file, ephemeral=False)


    


async def setup(bot: commands.Bot):
    await bot.add_cog(Map(bot))