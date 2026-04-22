import discord

from typing import Optional, Dict, List, Tuple, TYPE_CHECKING
import locale


from utils.path import GSHEET_POWER
from utils.load import load_powers
from utils.utils import _normalize, STAT_MAP


if TYPE_CHECKING:
    from instance.character import Character
    from instance.history import History
    from instance.dice import DiceSession

class Power:
    """
    Représente un pouvoir du jeu avec ses attributs, effets, et autres propriétés.
    """    
    def __init__(
        self,
        id: int,
        name: str,
        description: str,
        category: str,
        cost: dict[str, int],
        dice: str,
        bonus: dict[str, int],
        duration: int,
        image_path: str,
        target: bool = False,
        target_effect: dict | None = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.cost = cost
        self.dice = dice
        self.bonus = bonus
        self.duration = duration
        self.image_path = image_path
        self.target = target
        self.target_effect = target_effect

class PowerRepository:
    """
    Représente un dépôt de pouvoirs avec des méthodes pour les charger et les rechercher.
    """    
    def __init__(self, history: "History", dice_session: "DiceSession"):
        self.powers = {}
        self.history = history
        self.dice_session = dice_session
        self.reload()
    
    def reload(self) -> int:
        self.powers.clear()
        powers_as_dicts = load_powers(GSHEET_POWER)
        self.powers = {power_dict["name"].lower(): Power(**power_dict) for power_dict in powers_as_dicts}
        return len(self.powers)

    def get_power_by_name(self, name: str) -> Optional[Power]:
        return self.powers.get(name.lower())
    
    def get_powers(self) -> List[Power]:
        return sorted(list(self.powers.values()), key=lambda p: locale.strxfrm(p.name))

    async def power_use(self, guild: discord.Guild, character: "Character", power_name: str) -> tuple:
        """Utilise un pouvoir et log son utilisation dans l'historique."""
        power = self.get_power_by_name(power_name)
        if power is None:
            return None, None, None, {}

        character.resources = {k: character.resources[k] - power.cost[k] for k in character.resources}

        # Créer et retourner le buff associé au pouvoir
        buff_dict = None
        roll = None
        power_effects = None
        instant_resources = {}  # effets instantanés hp/mana/stamina sur le lanceur
        if power.bonus:
            power_effects = {}
            buff_effects = {}
            for stat, raw_value in power.bonus.items():
                value = raw_value
                if value == 0 and power.dice:
                    roll = self.dice_session.power_roll(power.name, power.dice, character_name=character.name)
                    value = roll["total"]

                power_effects[stat] = value

                resource_key = STAT_MAP.get(stat.lower())
                if resource_key:
                    instant_resources[resource_key] = value
                else:
                    buff_effects[stat] = value

            if buff_effects:
                buff_dict = {
                    "name": power.name,
                    "description": power.description,
                    "duration": power.duration,
                    "effects": buff_effects,
                    "character_name": character.name,
                    "source": f"Pouvoir: {power.name}"
                }
        elif power.dice:
            roll = self.dice_session.power_roll(power.name, power.dice, character_name=character.name)

        await self.history.log_power_use(guild, character.name, power.name, power_effects, roll)

        return buff_dict, power_effects, roll, instant_resources