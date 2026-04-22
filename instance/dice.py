import json
import math
from datetime import datetime
from pathlib import Path
import numpy as np

from utils.path import ROLL_DIR
from utils.utils import parse_dice, roll_dice, get_outcome, get_base_outcome, get_craft_outcome


class DiceSession:
    BASE_DIR = Path("history/dice")

    def __init__(self):
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
                "rolls": [],
            }
            self._save()

    def roll(self, expression: str, roll_type: str = "free", character_name: str | None = None) -> dict:
        result = roll_dice(expression)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "character": character_name,
            "type": roll_type,
            "outcome": get_outcome(result),
            "expression": expression,
            **result,
        }
        self._data["rolls"].append(entry)
        self._save()
        return entry

    def power_roll(self, power_name: str, expression: str, character_name: str | None = None) -> dict:
        result = roll_dice(expression)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "character": character_name,
            "type": "power_use",
            "power": power_name,
            "outcome": "normal",
            "expression": expression,
            "total": result["total"],
        }
        self._data["rolls"].append(entry)
        self._save()
        return entry
    
    def stat_roll(self, expression, stat_name, character_name: str | None = None) -> dict:
        result = roll_dice(expression)
        natural = result["base_total"]
        total = result["total"]
        faces = int(result["results"][0]["expression"].split("d")[1])

        modifier = result["modifier"]

        if natural == 1:
            outcome = "natural_fail"
            total = 0
            modifier = 0
        elif natural == faces and stat_name.lower() in ["attaque", "défense"]:
            outcome = "natural_success"
            total = math.ceil(natural * 1.5) + (modifier if modifier > 0 else 0)
        elif natural == faces:
            outcome = "natural_success"
            total = faces
            modifier = 0
        elif total <= 1:
            outcome = "critical_fail"
            total = 1
        elif total >= faces and stat_name.lower() in ["attaque", "défense"]:
            outcome = "critical_success"
        elif total >= faces:
            total = faces
            outcome = "critical_success"
        else:
            outcome = "normal"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "character": character_name,
            "type": "stat",
            "stat": stat_name,
            "outcome": outcome,
            "expression": expression,
            "base_total": natural,
            "modifier": modifier,
            "total": total,
        }
        
        self._data["rolls"].append(entry)
        self._save()
        return entry

    def enchant_roll(self, rune_name: str, item_name: str, roll: int, threshold: int, success: bool, character_name: str | None = None) -> dict:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "character": character_name,
            "type": "enchant",
            "rune": rune_name,
            "item": item_name,
            "outcome": "success" if success else "failure",
            "expression": "1d100",
            "base_total": roll,
            "modifier": 0,
            "total": roll,
        }
        self._data["rolls"].append(entry)
        self._save()
        return entry

    def craft_roll(self, craft_name: str, expression: str, has_failure: bool = False, has_success: bool = False, character_name: str | None = None) -> dict:
        result = roll_dice(expression)
        outcome = get_craft_outcome(result, has_failure=has_failure, has_success=has_success)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "character": character_name,
            "type": "craft",
            "craft": craft_name,
            "outcome": outcome,
            "expression": expression,
            "base_total": result["base_total"],
            "modifier": result["modifier"],
            "total": result["total"],
        }
        self._data["rolls"].append(entry)
        self._save()
        return entry

    def get_history(self, roll_type: str | None = None) -> list[dict]:
        rolls = self._data["rolls"]
        if roll_type:
            rolls = [r for r in rolls if r.get("type") == roll_type]
        return rolls

    def get_character_history(self, character_name: str) -> list[dict]:
        rolls = [r for r in self._data["rolls"] if r.get("character") == character_name]
        return rolls

    def summary(self, characters: list[str]) -> dict:
        summary = {}
        for c in characters:
            rolls = self.get_character_history(c)
            outcomes = [r.get("outcome") for r in rolls if "outcome" in r]
            types = [r.get("type") for r in rolls if "type" in r]
            faces = np.array([parse_dice(r.get("expression"))['dice'][0][1] for r in rolls if "expression" in r])
            coefs = 1 / (faces/20)
            corrected_faces = coefs * faces
            modifiers = np.array([r.get("modifier", 0) for r in rolls])
            corrected_modifiers = coefs * modifiers
            base_totals = np.array([r.get("base_total", 0) for r in rolls])
            corrected_base_totals = coefs * base_totals
            totals = np.array([r.get("total", 0) for r in rolls if "total" in r])
            corrected_totals = coefs * totals

            summary[c] = {
                "total_rolls": len(rolls),
                "outcomes": {o: outcomes.count(o) for o in set(outcomes)},
                "types": {t: types.count(t) for t in set(types)},
                "average_faces": np.round(sum(faces) / len(faces) if len(faces) != 0 else 0, 2),
                "average_modifier": np.round(sum(corrected_modifiers) / len(corrected_modifiers) if len(corrected_modifiers) != 0 else 0, 2),
                "average_base_total": np.round(sum(corrected_base_totals) / len(corrected_base_totals) if len(corrected_base_totals) != 0 else 0, 2),
                "average_total": np.round(sum(corrected_totals) / len(corrected_totals) if len(corrected_totals) != 0 else 0, 2),
            }

        return summary

    def _save(self) -> None:
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)