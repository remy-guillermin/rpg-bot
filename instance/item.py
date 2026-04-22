from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
import locale


from utils.path import GSHEET_ITEMS
from utils.load import load_items
from utils.utils import _normalize, SETS

@dataclass
class Item:
    """
    Représente un objet du jeu avec ses attributs, effets, et autres propriétés.
    """
    name: str
    description: str
    tags: List[str]
    image_path: str
    value: int
    unique: bool
    tradeable: bool
    useable: bool
    use_title: str
    use_effects: Dict[str, int]
    use_description: str
    equippable: bool
    equippable_slot: str
    equipped_bonus: Dict[str, int]
    rarity: str
    set_name: str
    rune_slots: int = 0
    forbidden: bool = False
    is_rune: bool = field(init=False)

    def __post_init__(self):
        self.is_rune = "rune" in self.tags

@dataclass
class ItemSet:
    """
    Représente un ensemble d'objets (set) avec des bonus associés.
    """
    name: str
    lore: str
    items: List[str]
    bonuses: Dict[str, int]

class ItemRepository:
    """
    Représente un dépôt d'objets avec des méthodes pour les charger et les rechercher.
    """    
    def __init__(self, history):
        self.items = {}
        self.sets = {}
        self.tags = set()
        self.history = history
        self.reload()
    
    def reload(self) -> int:
        self.items.clear()
        items_as_dicts = load_items(GSHEET_ITEMS)
        self.items = {item_dict["name"].lower(): Item(**item_dict) for item_dict in items_as_dicts}
        for item in self.items.values():
            self.tags.update(item.tags)
        for set_id, set_info in SETS.items():
            self.sets[set_id] = ItemSet(name=set_info["name"], lore=set_info["lore"], items=set_info["items"], bonuses=set_info["bonuses"])
        return len(self.items)
        


    def get_item_by_name(self, name: str) -> Optional[Item]:
        return self.items.get(name.lower())

    
    def search_items(self, query: str, limit: int = 25) -> list[Item]:
        needle = _normalize(query)


        if not needle:
            return list(self.items.values())[:limit]

        matches: list[Item] = []
        for item in self.items.values():
            haystack = _normalize(item.name)
            if haystack.startswith(needle) or f" {needle}" in haystack or f"'{needle}" in haystack:
                matches.append(item)
            if len(matches) >= limit:
                break

        return matches
    
    def list_items(self) -> List[Item]:
        return sorted(list(self.items.values()), key=lambda i: locale.strxfrm(i.name))

    def get_items_by_tag(self, tag: str) -> List[Item]:
        return [item for item in self.items.values() if tag in item.tags]