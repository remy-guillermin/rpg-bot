from collections.abc import Callable
import datetime

import discord
from discord import app_commands, Interaction

async def handle_admin_permission_error(
    interaction,
    error: app_commands.AppCommandError,
    message: str = "Tu dois être administrateur pour utiliser cette commande.",
) -> bool:
    """Handle MissingPermissions errors, returning True when handled."""
    if isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(
            title="Erreur",
            description=message,
            color=discord.Color.red(),
                timestamp=datetime.datetime.now(),
            )
        await interaction.response.send_message(embed=embed, ephemeral=False)
        return True
    return False

def admin_only() -> Callable:
    """Decorator combining admin visibility and runtime permission check."""

    def decorator(func: Callable) -> Callable:
        wrapped = app_commands.default_permissions(administrator=True)(func)
        wrapped = app_commands.checks.has_permissions(administrator=True)(wrapped)
        return wrapped

    return decorator

class AdminGroup(app_commands.Group):
    """Groupe de commandes réservé aux admins."""

    async def interaction_check(self, interaction: Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Tu n'as pas la permission d'utiliser cette commande.",
                ephemeral=True
            )
            return False
        return True

    async def on_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title="Erreur",
                description="Tu dois être administrateur pour utiliser cette commande.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            raise error