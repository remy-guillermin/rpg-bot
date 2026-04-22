import discord
from discord.ext import commands
from discord import app_commands, Interaction

from utils.admin import handle_admin_permission_error, AdminGroup
from utils.builder_embed import _generate_player_error_embed
from utils.autocomplete import make_character_autocomplete

class Status(commands.Cog):
    """Commandes liées au statut des personnages."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.status_group = AdminGroup(
            name="status", 
            description="Commandes liées au statut des personnages.",
            default_permissions=discord.Permissions(administrator=True)
        )
        bot.tree.add_command(self.status_group)

    def _resolve_callback(self, member):
        """Return the underlying callable for an app_commands.Command or the member itself."""
        return getattr(member, "callback", member)

    
    async def character_autocomplete(self, interaction: Interaction, current: str):
        return await make_character_autocomplete(self.bot.character_repository)(interaction, current)

    # ── Commandes ────────────────────────────────────────────────────
    async def add_experience(self, interaction: Interaction, character_name: str, amount: int):
        """Ajoute de l'expérience à un personnage."""
        character = self.bot.character_repository.get_character_by_name(character_name)
        if not character:
            embed = _generate_player_error_embed(f"Personnage '{character_name}' introuvable.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        character.gain_experience(amount)
        self.bot.character_repository.update_character(character)
        await interaction.response.send_message(f"✅ {amount} points d'expérience ajoutés à {character_name}.", ephemeral=True)



    async def add_kills(self, interaction: Interaction, character_name: str, amount: int):
        """Ajoute des kills à un personnage."""
        character = self.bot.character_repository.get_character_by_name(character_name)
        if not character:
            embed = _generate_player_error_embed(f"Personnage '{character_name}' introuvable.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        character.gain_kills(amount)
        self.bot.character_repository.update_character(character)
        await interaction.response.send_message(f"✅ {amount} kills ajoutés à {character_name}.", ephemeral=True)


    async def add_coin(self, interaction: Interaction, character_name: str, amount: int):
        """Ajoute (ou retire) de la monnaie à un personnage."""
        character = self.bot.character_repository.get_character_by_name(character_name)
        if not character:
            embed = _generate_player_error_embed(f"Personnage '{character_name}' introuvable.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        character.currency += amount
        self.bot.character_repository.update_character(character)
        sign = "+" if amount >= 0 else ""
        await interaction.response.send_message(f"✅ {sign}{amount} 🪙 → {character_name} (total : {character.currency} 🪙).", ephemeral=True)


    async def add_boss_kill(self, interaction: Interaction, character_name: str, boss_id: str):
        """Ajoute un boss kill à un personnage."""
        character = self.bot.character_repository.get_character_by_name(character_name)
        if not character:
            embed = _generate_player_error_embed(f"Personnage '{character_name}' introuvable.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        character.defeat_boss(boss_id)
        self.bot.character_repository.update_character(character)
        await interaction.response.send_message(f"✅ Boss '{boss_id}' ajouté à la liste des boss tués de {character_name}.", ephemeral=True)


    
    async def cog_load(self):
        # --- add experience ---
        add_exp_cmd = app_commands.Command(
            name="add-exp",
            description="Ajoute de l'expérience à un personnage.",
            callback=self.add_experience,
        )
        add_exp_cmd.autocomplete("character_name")(self.character_autocomplete)
        self.status_group.add_command(add_exp_cmd)

        # --- add kills ---
        add_kills_cmd = app_commands.Command(
            name="add-kills",
            description="Ajoute des kills à un personnage.",
            callback=self.add_kills,
        )
        add_kills_cmd.autocomplete("character_name")(self.character_autocomplete)
        self.status_group.add_command(add_kills_cmd)

        # --- add coin ---
        add_coin_cmd = app_commands.Command(
            name="add-coin",
            description="Ajoute (ou retire si négatif) de la monnaie à un personnage.",
            callback=self.add_coin,
        )
        add_coin_cmd.autocomplete("character_name")(self.character_autocomplete)
        self.status_group.add_command(add_coin_cmd)

        # --- add boss kill ---
        add_boss_kill_cmd = app_commands.Command(
            name="add-boss-kill",
            description="Ajoute un boss kill à un personnage.",
            callback=self.add_boss_kill,
        )
        add_boss_kill_cmd.autocomplete("character_name")(self.character_autocomplete)
        self.status_group.add_command(add_boss_kill_cmd)


async def setup(bot: commands.Bot):
    await bot.add_cog(Status(bot))