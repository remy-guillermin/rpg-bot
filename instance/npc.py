import locale
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

from utils.load import load_quests, load_npcs
from utils.path import GSHEET_NPCS, GSHEET_QUESTS
if TYPE_CHECKING:
    from instance.trade import Trade
    from instance.item import Item, ItemRepository
    from instance.inventory import Inventory

@dataclass
class QuestItem:
    item: "Item"
    quantity: int = 1

@dataclass
class Quest:
    quest_id: str
    npc_name: str
    title: str
    description: str
    condition_quest: str
    condition_items: list[QuestItem]
    reward_xp: int
    reward_items: list[QuestItem]

    def is_available(self, completed_quests: set[str], inventory: "Inventory") -> bool:
        if self.condition_quest and self.condition_quest not in completed_quests:
            return False
        for quest_item in self.condition_items:
            if inventory.get_quantity(quest_item.item.name) < quest_item.quantity:
                return False
        return True


@dataclass
class NPC:
    name: str
    description: str
    location: str
    roles: list[str]  # ex. ['quest_giver', 'merchant', 'blacksmith']
    city: str = ""  # ex. 'Rivertown', 'Stonehaven', etc.
    realm: str = "" # ex. 'Kingdom of Eldoria', 'Empire of Drakoria', etc.
    specialty: str = ""  # ex. 'alchemist', 'warrior trainer', etc.
    image_name: str | None = None
    quests: list[Quest] = field(default_factory=list)
    trades: list["Trade"] = field(default_factory=list)
    upgrades: list["Upgrade"] = field(default_factory=list)

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def available_quests(
        self,
        completed_quests: set[str],
        active_quests: set[str],
        inventory: "Inventory",
    ) -> list[Quest]:
        return [
            q for q in self.quests
            if q.quest_id not in completed_quests
            and q.quest_id not in active_quests
            and q.is_available(completed_quests, inventory)
        ]

    def visible_quests(self, completed_quests: set[str]) -> list[Quest]:
        return [
            q for q in self.quests
            if not q.condition_quest or q.condition_quest in completed_quests
        ]

    

class NPCRepository:
    def __init__(self, trade_repository: "TradeRepository", item_repository: "ItemRepository"):
        self._npcs: dict[str, NPC] = {}
        self._quests: dict[str, Quest] = {}
        self.locations: set[str] = set()
        self.cities: set[str] = set()
        self.realms: set[str] = set()
        self.roles: set[str] = set()
        self.trade_repository = trade_repository
        self.item_repository = item_repository
        self.reload()

    def reload(self) -> int:
        self._npcs.clear()
        self._quests.clear()
        self.locations.clear()
        self.cities.clear()
        self.realms.clear()
        self.roles.clear()

        quests_as_dict = load_quests(GSHEET_QUESTS)
        for q in quests_as_dict:
            condition_items = [QuestItem(item=item, quantity=entry.get("quantity", 1)) for entry in q["condition_items"] if (item := self.item_repository.get_item_by_name(entry["item"])) is not None]
            reward_items = [QuestItem(item=item, quantity=entry.get("quantity", 1)) for entry in q["reward_items"] if (item := self.item_repository.get_item_by_name(entry["item"])) is not None]
            q["condition_items"] = condition_items
            q["reward_items"] = reward_items
            quest = Quest(
                quest_id=q["quest_id"],
                npc_name=q["npc_name"],
                title=q["title"],
                description=q["description"],
                condition_quest=q["condition_quest"],
                condition_items=condition_items,
                reward_xp=q["reward_xp"],
                reward_items=reward_items,
            )
            self._quests[quest.quest_id] = quest

        npcs_as_dict = load_npcs(GSHEET_NPCS)
        for npc_data in npcs_as_dict:
            npc_quests = [
                self._quests[q_id] for q_id in npc_data["quest_ids"] if q_id in self._quests
            ]
            npc_trades = [
                self.trade_repository.get_trade_by_id(t_id) for t_id in npc_data["trade_ids"]
            ]
            npc_trades = [t for t in npc_trades if t is not None]  # Filter
            npc = NPC(
                name=npc_data["name"],
                description=npc_data["description"],
                location=npc_data["location"],
                roles=npc_data["roles"],
                specialty=npc_data["specialty"],
                quests=npc_quests,
                trades=npc_trades,
                city=npc_data["city"],
                realm=npc_data["realm"],
            )
            self._npcs[npc.name] = npc
            self.locations.add(npc.location)
            self.cities.add(npc.city)
            self.realms.add(npc.realm)
            self.roles.update(npc.roles)
        return len(self._npcs)
    # ------------------------------------------------------------------
    # Accès
    # ------------------------------------------------------------------

    def get(self, name: str) -> NPC | None:
        return self._npcs.get(name)

    def all(self) -> list[NPC]:
        return sorted(self._npcs.values(), key=lambda n: locale.strxfrm(n.name))

    def by_role(self, role: str) -> list[NPC]:
        return sorted(
            [n for n in self._npcs.values() if n.has_role(role)],
            key=lambda n: locale.strxfrm(n.name),
        )

    def by_realm(self, realm: str) -> list[NPC]:
        if realm not in self.realms:
            return []
        return sorted(
            [n for n in self._npcs.values() if n.realm == realm],
            key=lambda n: locale.strxfrm(n.name),
        )

    def by_realm_outside_city(self, realm: str) -> list[NPC]:
        if realm not in self.realms:
            return []
        return sorted(
            [n for n in self._npcs.values() if n.realm == realm and not n.city],
            key=lambda n: locale.strxfrm(n.name),
        )

    def by_city(self, city: str) -> list[NPC]:
        if city not in self.cities:
            return []
        return sorted(
            [n for n in self._npcs.values() if n.city == city],
            key=lambda n: locale.strxfrm(n.name),
        )

    def get_quest(self, quest_id: str) -> Quest | None:
        return self._quests.get(quest_id)


    # ------------------------------------------------------------------
    # Autocomplete helpers
    # ------------------------------------------------------------------

    def npc_names(self) -> list[str]:
        return [n.name for n in self.all()]

    def quest_ids_for_npc(self, npc_name: str) -> list[str]:
        npc = self.get(npc_name)
        if not npc:
            return []
        return [q.quest_id for q in npc.quests]
