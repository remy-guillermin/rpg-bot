import discord
from discord.ext import commands
from discord import app_commands, Interaction

class Settings(commands.Cog):
    """Commandes liées aux paramètres."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings_group = app_commands.Group(name="settings", description="Commandes liées aux paramètres.")
        bot.tree.add_command(self.settings_group)




async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))