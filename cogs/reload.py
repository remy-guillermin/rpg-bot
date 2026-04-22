import discord
from discord.ext import commands
from discord import app_commands, Interaction

import os

from utils.admin import AdminGroup
from utils.path import COGS_DIR, COGS

class Reload(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reload_group = AdminGroup(
            name="reload", 
            description="Commandes de rechargement.",
            default_permissions=discord.Permissions(administrator=True)
        )
        bot.tree.add_command(self.reload_group)

    
    async def reload_items(self, interaction: Interaction):
        items_count = self.bot.item_repository.reload()
        await interaction.response.send_message(f"✅ {items_count} items rechargés.", ephemeral=True)


    
    async def reload_characters(self, interaction: Interaction):
        characters_count = self.bot.character_repository.reload()
        await interaction.response.send_message(f"✅ {characters_count} personnages rechargés.", ephemeral=True)

    

    async def reload_craft(self, interaction: Interaction):
        crafts_count = self.bot.craft_repository.reload()
        await interaction.response.send_message(f"✅ {crafts_count} crafts rechargés.", ephemeral=True)


    
    async def reload_powers(self, interaction: Interaction):
        powers_count = self.bot.power_repository.reload()
        await interaction.response.send_message(f"✅ {powers_count} pouvoirs rechargés.", ephemeral=True)

    

    async def reload_lootbox(self, interaction: Interaction):
        lootboxes_count = self.bot.lootbox_repository.reload()
        await interaction.response.send_message(f"✅ {lootboxes_count} lootboxes rechargées.", ephemeral=True) 

    

    async def reload_enemy(self, interaction: Interaction):
        enemies_count = self.bot.enemy_repository.reload()
        await interaction.response.send_message(f"✅ {enemies_count} ennemis rechargés.", ephemeral=True)


    async def reload_npc(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        self.bot.trade_repository.reload()
        npc_count = self.bot.npc_repository.reload()
        quest_count = len(self.bot.npc_repository._quests)
        trade_count = len(self.bot.trade_repository.trades)
        await interaction.followup.send(
            f"✅ {npc_count} NPC(s), {quest_count} quête(s) et {trade_count} trade(s) rechargés.",
            ephemeral=True
        )


    async def reload_all(self, interaction: Interaction):
        await interaction.response.defer()
        items_count = self.bot.item_repository.reload()
        await interaction.followup.send(f"✅ {items_count} items rechargés.", ephemeral=False)
        characters_count = self.bot.character_repository.reload()
        await interaction.followup.send(f"✅ {characters_count} personnages rechargés.", ephemeral=False)
        crafts_count = self.bot.craft_repository.reload()
        await interaction.followup.send(f"✅ {crafts_count} crafts rechargés.", ephemeral=False)
        powers_count = self.bot.power_repository.reload()
        await interaction.followup.send(f"✅ {powers_count} pouvoirs rechargés.", ephemeral=False)
        lootboxes_count = self.bot.lootbox_repository.reload()
        await interaction.followup.send(f"✅ {lootboxes_count} lootboxes rechargées.", ephemeral=False)
        enemies_count = self.bot.enemy_repository.reload()
        await interaction.followup.send(f"✅ {enemies_count} ennemis rechargés.", ephemeral=False)
        self.bot.trade_repository.reload()
        npc_count = self.bot.npc_repository.reload()
        quest_count = len(self.bot.npc_repository._quests)
        trade_count = len(self.bot.trade_repository.trades)
        await interaction.followup.send(
            f"✅ {npc_count} NPC(s), {quest_count} quête(s) et {trade_count} trade(s) rechargés.",
            ephemeral=False
        )


    async def cog_load(self):
        self.reload_group.add_command(app_commands.Command(
            name="items",
            description="Recharge les items.",
            callback=self.reload_items
        ))

        self.reload_group.add_command(app_commands.Command(
            name="characters",
            description="Recharge les personnages.",
            callback=self.reload_characters
        ))

        self.reload_group.add_command(app_commands.Command(
            name="craft",
            description="Recharge les crafts.",
            callback=self.reload_craft
        ))

        self.reload_group.add_command(app_commands.Command(
            name="powers",
            description="Recharge les pouvoirs.",
            callback=self.reload_powers
        ))

        self.reload_group.add_command(app_commands.Command(
            name="lootbox",
            description="Recharge les lootboxes.",
            callback=self.reload_lootbox
        ))

        self.reload_group.add_command(app_commands.Command(
            name="enemy",
            description="Recharge les ennemis.",
            callback=self.reload_enemy
        ))
        
        self.reload_group.add_command(app_commands.Command(
            name="npc",
            description="Recharge les NPCs, quêtes et trades.",
            callback=self.reload_npc
        ))

        self.reload_group.add_command(app_commands.Command(
            name="all",
            description="Recharge tout.",
            callback=self.reload_all
        ))



async def setup(bot: commands.Bot):
    await bot.add_cog(Reload(bot))