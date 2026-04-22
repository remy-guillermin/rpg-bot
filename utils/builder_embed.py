from utils.embeds.character import (
    _generate_character_embed,
    _generate_stats_embed,
    _generate_inventory_embed,
    _generate_powers_embed,
    _generate_quests_embed,
)
from utils.embeds.item import (
    _generate_item_embed,
    _generate_item_equip_embed,
    _generate_item_discard_embed,
    _generate_item_trade_embed,
    _generate_item_use_embed,
    _generate_new_item_notification_embed,
    _generate_new_item_from_lootbox_notification_embed,
    _generate_relic_used_embed,
    _generate_item_update_history_embed,
    _generate_transaction_history_embed,
    _notify_admin_relic_used_embed,
    _generate_item_forbidden_embed,
    _generate_set_potential_embed,
    _generate_set_discovery_embed,
)
from utils.embeds.craft import (
    _generate_craft_list_embed,
    _generate_craft_info_embed,
    _generate_craft_executed_embed,
    _generate_craft_execution_history_embed,
)
from utils.embeds.buff import (
    _generate_buff_list_embed,
    _generate_buffs_embed,
    _generate_buff_add_embed,
    _generate_buff_clear_embed,
    _generate_buff_remove_embed,
    _generate_buff_decrement_embed,
    _generate_buff_application_history_embed,
    _generate_buff_expiration_history_embed,
)
from utils.embeds.power import (
    _generate_power_embed,
    _generate_power_use_embed,
    _generate_power_use_history_embed,
    _generate_stat_dice_embed,
)
from utils.embeds.combat import (
    _generate_admin_enemy_spawn_embed,
    _generate_enemy_list_embed,
    _generate_admin_damage_enemy_embed,
    _generate_admin_heal_enemy_embed,
    _generate_enemy_spawn_embed,
    _generate_hp_tracker_embed,
    _generate_combat_end_embed,
    _generate_enemy_attack_embed,
    _generate_combat_rewards_embed,
    _generate_damage_history_embed,
    _generate_spawn_history_embed
)
from utils.embeds.lootbox import (
    _generate_lootbox_list_embed,
    _generate_lootbox_info_embed,
    _generate_lootbox_open_history_embed,
)
from utils.embeds.npc import (
    _generate_npc_embed,
    _generate_quest_embed,
    _generate_memory_fragment_embed,
    _generate_trade_result_embed,
    _generate_npc_offer_embed,
    _generate_npc_trade_history_embed,
    _generate_npc_offer_history_embed,
    _generate_player_counter_offer_embed,
    _generate_sale_counter_offer_embed,
    _generate_blacksmith_enchant_embed,
    _generate_blacksmith_upgrade_embed,
)
from utils.embeds.misc import (
    _generate_basic_dice_embed,
    _generate_session_summary_embed,
    _generate_player_error_embed,
    _generate_help_embed,
    _generate_city_arrival_embed,
)
