import discord
from discord.ext import commands
from discord import app_commands, Interaction

class Inventories(commands.Cog):
    """Commandes liées à l'inventaire."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.inventory_group = app_commands.Group(name="inventory", description="Commandes liées à l'inventaire.")
        bot.tree.add_command(self.inventory_group)




async def setup(bot: commands.Bot):
    await bot.add_cog(Inventories(bot))