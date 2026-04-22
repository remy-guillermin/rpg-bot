import random
import json
from pathlib import Path
from datetime import datetime

from utils.load import load_lootboxes
from utils.path import GSHEET_LOOTBOXES

class LootBox:
    def __init__(
        self, 
        id: str,
        name: str,
        type: str,
        items: list[tuple[str, tuple[int, int]]],
        rarity: int
    ):
        self.id = id
        self.name = name
        self.type = type
        self.items = items
        self.rarity = rarity
        

class LootBoxRepository:
    BASE_DIR = Path("history/lootboxes")
    def __init__(self, history):
        self.lootboxes = {}  # id -> LootBox
        self.history = history
        self.reload()

        today = datetime.now().strftime("%Y-%m-%d")
        self._dir = self.BASE_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / f"session_{today}.json"

        if self._path.exists():
            with self._path.open() as f:
                self._data = json.load(f)
        else:
            self._data = {
                "date": today,
                "started_at": datetime.now().isoformat(),
                "lootboxes": [],
            }
            self._save()

    
    def reload(self) -> int:
        self.lootboxes.clear()
        for lootbox_data in load_lootboxes(GSHEET_LOOTBOXES):
            lootbox = LootBox(
                id=lootbox_data["id"],
                name=lootbox_data["name"],
                type=lootbox_data["type"],
                items=lootbox_data["items"],
                rarity=lootbox_data["rarity"]
            )
            self.add_lootbox(lootbox)
        return len(self.lootboxes)



    def add_lootbox(self, lootbox: LootBox):
        self.lootboxes[lootbox.id] = lootbox

    def get_lootbox(self, lootbox_id: str) -> LootBox | None:
        return self.lootboxes.get(lootbox_id)

    def get_lootbox_by_name(self, name: str) -> LootBox | None:
        return next((lb for lb in self.lootboxes.values() if lb.name == name), None)
        
    def list_lootboxes(self) -> list[LootBox]:
        return list(self.lootboxes.values())

    def open_lootbox(self, lootbox_id: str, lootbox_quantity: int, character_name: str) -> list[tuple[str, int]]:
        lootbox = self.get_lootbox(lootbox_id)
        if not lootbox:
            raise ValueError(f"LootBox with id {lootbox_id} not found.")
        
        items_pool = []
        weights = []
        for item, (quantity, rarity) in lootbox.items:
            items_pool.append((item, quantity))
            weights.append(rarity)


        rewards = random.choices(items_pool, weights=weights, k=lootbox_quantity)

        self._data["lootboxes"].append({
            "timestamp": datetime.now().isoformat(),
            "lootbox_id": lootbox_id,
            "quantity": lootbox_quantity,
            "rewards": rewards,
            "character_name": character_name
        })
        self._save()

        return rewards

    def get_history(self) -> list[dict]:
        lootboxes = self._data["lootboxes"]
        lootboxes.sort(key=lambda x: x["timestamp"], reverse=True)
        return lootboxes

    def summary(self)  -> dict:
        summary = {}
        for entry in self._data["lootboxes"]:
            lootbox_id = entry["lootbox_id"]
            quantity = entry["quantity"]
            rewards = entry["rewards"]

            if lootbox_id not in summary:
                summary[lootbox_id] = {
                    "name": self.get_lootbox(lootbox_id).name if self.get_lootbox(lootbox_id) else "Unknown",
                    "opened": 0,
                    "rewards": {}
                }
            summary[lootbox_id]["opened"] += quantity
            for item, qty in rewards:
                if item not in summary[lootbox_id]["rewards"]:
                    summary[lootbox_id]["rewards"][item] = 0
                summary[lootbox_id]["rewards"][item] += qty

        return summary

    def _save(self):
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)