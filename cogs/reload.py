import discord
from discord.ext import commands
from discord import app_commands, Interaction

from utils.admin import AdminGroup

_SIMPLE_RELOADS = [
    ("items",      "item_repository",      "{n} items rechargés.",       "Recharge les items."),
    ("characters", "character_repository", "{n} personnages rechargés.", "Recharge les personnages."),
    ("craft",      "craft_repository",     "{n} crafts rechargés.",      "Recharge les crafts."),
    ("powers",     "power_repository",     "{n} pouvoirs rechargés.",    "Recharge les pouvoirs."),
    ("lootbox",    "lootbox_repository",   "{n} lootboxes rechargées.",  "Recharge les lootboxes."),
    ("enemy",      "enemy_repository",     "{n} ennemis rechargés.",     "Recharge les ennemis."),
]


class Reload(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reload_group = AdminGroup(
            name="reload",
            description="Commandes de rechargement.",
            default_permissions=discord.Permissions(administrator=True)
        )
        bot.tree.add_command(self.reload_group)

    def _make_reload_callback(self, repo_attr: str, template: str):
        async def callback(interaction: Interaction):
            n = getattr(self.bot, repo_attr).reload()
            await interaction.response.send_message(f"✅ {template.format(n=n)}", ephemeral=True)
        return callback

    async def _reload_npc(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        self.bot.trade_repository.reload()
        npc_count = self.bot.npc_repository.reload()
        quest_count = len(self.bot.npc_repository._quests)
        trade_count = len(self.bot.trade_repository.trades)
        await interaction.followup.send(
            f"✅ {npc_count} NPC(s), {quest_count} quête(s) et {trade_count} trade(s) rechargés.",
            ephemeral=True
        )

    async def _reload_all(self, interaction: Interaction):
        await interaction.response.defer()
        for _, repo_attr, template, _ in _SIMPLE_RELOADS:
            n = getattr(self.bot, repo_attr).reload()
            await interaction.followup.send(f"✅ {template.format(n=n)}", ephemeral=False)
        self.bot.trade_repository.reload()
        npc_count = self.bot.npc_repository.reload()
        quest_count = len(self.bot.npc_repository._quests)
        trade_count = len(self.bot.trade_repository.trades)
        await interaction.followup.send(
            f"✅ {npc_count} NPC(s), {quest_count} quête(s) et {trade_count} trade(s) rechargés.",
            ephemeral=False
        )

    async def cog_load(self):
        for name, repo_attr, template, description in _SIMPLE_RELOADS:
            self.reload_group.add_command(app_commands.Command(
                name=name,
                description=description,
                callback=self._make_reload_callback(repo_attr, template),
            ))
        self.reload_group.add_command(app_commands.Command(
            name="npc",
            description="Recharge les NPCs, quêtes et trades.",
            callback=self._reload_npc,
        ))
        self.reload_group.add_command(app_commands.Command(
            name="all",
            description="Recharge tout.",
            callback=self._reload_all,
        ))


async def setup(bot: commands.Bot):
    await bot.add_cog(Reload(bot))
