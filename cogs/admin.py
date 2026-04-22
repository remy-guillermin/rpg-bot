import discord
from discord.ext import commands, tasks
from discord import app_commands, Interaction

from utils.utils import _send_embed, update_bot_status
from utils.admin import handle_admin_permission_error, admin_only, AdminGroup
from utils.autocomplete import make_character_autocomplete, make_realm_autocomplete, make_city_autocomplete
from utils.path import PLAYER_VOICE_CHANNELS, GENERAL_CHANNEL_NAME
from utils.builder_embed import _generate_city_arrival_embed

class Admin(commands.Cog):
    """Commandes d'administration du bot."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.clear_group = AdminGroup(
            name="clear", 
            description="Commandes de nettoyage.",
            default_permissions=discord.Permissions(administrator=True)
        )
        bot.tree.add_command(self.clear_group)
        self.location_group = AdminGroup(
            name="location",
            description="Commandes de gestion des lieux.",
            default_permissions=discord.Permissions(administrator=True)
        )
        bot.tree.add_command(self.location_group)

    def _resolve_callback(self, member):
        """Return the underlying callable for an app_commands.Command or the member itself."""
        return getattr(member, "callback", member)

    async def character_name_autocomplete(self, interaction: Interaction, current: str):
        return await make_character_autocomplete(self.bot.character_repository)(interaction, current)

    # ── Commandes ────────────────────────────────────────────────────
    @app_commands.command(name="ping", description="Vérifie si le bot répond.")
    @admin_only()
    async def ping(self, interaction: Interaction):
        embed = discord.Embed(title="Pong!", description="Le bot est opérationnel.", color=discord.Color.green())
        await _send_embed(interaction, embed)

    @app_commands.command(name="add-player", description="Ajoute un joueur à cette session de jeu.")
    @admin_only()
    @app_commands.describe(player_name="Le nom du joueur à ajouter.")
    @app_commands.autocomplete(player_name=character_name_autocomplete)
    async def add_player(self, interaction: Interaction, player_name: str):
        self.bot.character_repository.players.append(player_name)
        embed = discord.Embed(
            title="Joueur ajouté",
            description=f"✅ **{player_name}** a été ajouté à la session.",
            color=discord.Color.green()
        )
        await _send_embed(interaction, embed)

    @app_commands.command(name="remove-player", description="Supprime un joueur de cette session de jeu.")
    @admin_only()
    @app_commands.describe(player_name="Le nom du joueur à supprimer.")
    @app_commands.autocomplete(player_name=character_name_autocomplete)
    async def remove_player(self, interaction: Interaction, player_name: str):
        if player_name in self.bot.character_repository.players:
            self.bot.character_repository.players.remove(player_name)
            embed = discord.Embed(
                title="Joueur supprimé",
                description=f"✅ **{player_name}** a été supprimé de la session.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Joueur non trouvé",
                description=f"❌ **{player_name}** n'est pas dans la session.",
                color=discord.Color.red()
            )
        await _send_embed(interaction, embed)
    
    @app_commands.command(name="update-players", description="Recharge les joueurs depuis les salons vocaux.")
    @admin_only()
    async def update_players(self, interaction: Interaction):
        self.bot.character_repository.players.clear()
        added = []
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                if channel.name not in PLAYER_VOICE_CHANNELS:
                    continue
                for member in channel.members:
                    char = self.bot.character_repository.get_character_by_user_id(member.id)
                    if char and char.name not in self.bot.character_repository.players and char.name != "Rémy":
                        self.bot.character_repository.players.append(char.name)
                        added.append(f"✅ **{char.name}** ({channel.name})")

        await update_bot_status(self.bot)

        if added:
            embed = discord.Embed(
                title="Session mise à jour",
                description="\n".join(added),
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Aucun joueur trouvé",
                description="❌ Aucun joueur trouvé dans les salons vocaux.",
                color=discord.Color.red()
            )
        await _send_embed(interaction, embed)

    @app_commands.command(name="show-players", description="Affiche la liste des joueurs de cette session.")
    @admin_only()
    async def show_players(self, interaction: Interaction):
        players = self.bot.character_repository.players
        if not players:
            embed = discord.Embed(
                title="Aucun joueur",
                description="❌ Aucun joueur n'est actuellement dans la session.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="Joueurs de la session",
                description="\n".join(f"✅ **{player}**" for player in players),
                color=discord.Color.green()
            )
        await _send_embed(interaction, embed)

    async def clear_messages(self, interaction: Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Erreur",
                    description="Cette commande ne fonctionne que dans les channels de texte.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            deleted = await channel.purge(limit=None)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Confirmation",
                    description=f"✅ **{len(deleted)}** messages supprimés du channel.",
                    color=discord.Color.green()
                ),
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Erreur",
                    description="❌ Permissions insuffisantes pour supprimer des messages.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Erreur",
                    description=f"❌ Erreur lors de la suppression : {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


    async def show_current(self, interaction: Interaction):
        loc = self.bot.location
        realm = loc.realm or "*(aucun)*"
        city = loc.city or "*(aucune)*"
    
        channel = discord.utils.get(interaction.guild.text_channels, name=GENERAL_CHANNEL_NAME)
        if channel:
            embed = _generate_city_arrival_embed(self.bot, False)

            await channel.send(
                embed=embed
            )

        embed = discord.Embed(
            title="Localisation actuelle",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Royaume", value=realm, inline=True)
        embed.add_field(name="Ville", value=city, inline=True)
        await _send_embed(interaction, embed)


    async def change_realm(self, interaction: Interaction, realm_name: str):
        self.bot.location.set_realm(realm_name)
        embed = discord.Embed(
            title="Royaume modifié",
            description=f"✅ Le groupe se trouve maintenant dans **{realm_name}**.\nLa ville a été réinitialisée.",
            color=discord.Color.green()
        )
        await _send_embed(interaction, embed)

    async def enter_city(self, interaction: Interaction, city_name: str):
        self.bot.location.set_city(city_name)

        channel = discord.utils.get(interaction.guild.text_channels, name=GENERAL_CHANNEL_NAME)
        if channel:
            embed, file = _generate_city_arrival_embed(self.bot, True)

            if file is not None:
                await channel.send(embed=embed, file=file)
            else:
                await channel.send(embed=embed)

        embed = discord.Embed(
            title="Entrée en ville",
            description=f"✅ Le groupe entre dans **{city_name}**.",
            color=discord.Color.green()
        )
        await _send_embed(interaction, embed)

    async def leave_city(self, interaction: Interaction):
        old_city = self.bot.location.city or "la ville"
        self.bot.location.clear_city()
        embed = discord.Embed(
            title="Sortie de ville",
            description=f"✅ Le groupe quitte **{old_city}**.",
            color=discord.Color.green()
        )
        await _send_embed(interaction, embed)

    async def cog_load(self):
        channel_cmd = app_commands.Command(
            name="messages",
            description="Nettoie les messages.",
            callback=self.clear_messages
        )
        self.clear_group.add_command(channel_cmd)

        # --- location commands ---
        show_cmd = app_commands.Command(
            name="show",
            description="Affiche le royaume et la ville actuelle.",
            callback=self.show_current,
        )
        self.location_group.add_command(show_cmd)

        realm_autocomplete = make_realm_autocomplete()
        change_realm_cmd = app_commands.Command(
            name="realm",
            description="Change le royaume actuel (réinitialise la ville).",
            callback=self.change_realm,
        )
        change_realm_cmd.autocomplete("realm_name")(realm_autocomplete)
        self.location_group.add_command(change_realm_cmd)

        city_autocomplete = make_city_autocomplete(self.bot.location)
        enter_city_cmd = app_commands.Command(
            name="enter",
            description="Entre dans une ville.",
            callback=self.enter_city,
        )
        enter_city_cmd.autocomplete("city_name")(city_autocomplete)
        self.location_group.add_command(enter_city_cmd)

        leave_city_cmd = app_commands.Command(
            name="leave",
            description="Quitte la ville actuelle.",
            callback=self.leave_city,
        )
        self.location_group.add_command(leave_city_cmd)

        self.auto_update_players.start()

    def cog_unload(self):
        self.auto_update_players.cancel()

    @tasks.loop(minutes=5)
    async def auto_update_players(self):
        self.bot.character_repository.players.clear()
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                if channel.name not in PLAYER_VOICE_CHANNELS:
                    continue
                for member in channel.members:
                    char = self.bot.character_repository.get_character_by_user_id(member.id)
                    if char and char.name not in self.bot.character_repository.players and char.name != "Rémy":
                        self.bot.character_repository.players.append(char.name)
        await update_bot_status(self.bot)

    @auto_update_players.before_loop
    async def before_auto_update_players(self):
        await self.bot.wait_until_ready()
        


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))