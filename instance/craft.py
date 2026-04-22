from typing import Dict, List, Optional, TYPE_CHECKING
import locale

import discord

if TYPE_CHECKING:
    from instance.character import Character
    from instance.inventory import Inventory
    from instance.item import Item


from utils.path import GSHEET_CRAFT
from utils.load import load_crafts
from utils.utils import METHOD_CLEAN

class Craft:
    def __init__(self, 
        name: str, 
        description: str, 
        method: str, 
        ingredients:List[Dict], 
        base_products:List[Dict], 
        success_products: List[Dict],
        failure_products: List[Dict],
        difficulty:int, 
        success_bonus: int = 0,
        experience_gain: int = 0,
        visible:bool=False
    ):
        self.name = name
        self.description = description
        self.method = method          
        self.ingredients = ingredients
        self.base_products = base_products
        self.success_products = success_products
        self.failure_products = failure_products
        self.difficulty = difficulty 
        self.visible = visible
        self.success_bonus = success_bonus
        self.experience_gain = experience_gain


class CraftRepository:
    def __init__(self, history: "History", dice_session: "DiceSession", item_repository: "ItemRepository"):
        self.crafts = {}
        self.history = history
        self.dice_session = dice_session
        self.item_repository = item_repository
        self.methods = set()
        self.difficulties = set()
        self.reload()

    def reload(self) -> int:
        self.crafts.clear()
        crafts_as_dicts = load_crafts(GSHEET_CRAFT)
        self.crafts = {craft_dict["name"]: Craft(**craft_dict) for craft_dict in crafts_as_dicts}
        for craft in self.crafts.values():
            self.methods.add(craft.method)
            self.difficulties.add(craft.difficulty)

        # for item in self.item_repository.items.values():
        #     if "ressource" in item.tags:
        #         print(f"Item: {item.name}, utilisé dans {len(self.find_crafts_by_ingredient(item.name))} crafts, produit dans {len(self.find_crafts_by_product(item.name))} crafts")

        return len(self.crafts)

    def get_craft_by_name(self, name: str) -> Craft:
        return self.crafts.get(name)

    def get_visible_crafts(self) -> List[Craft]:
        crafts = [craft for craft in self.crafts.values() if craft.visible]
        return sorted(crafts, key=lambda c: locale.strxfrm(c.name))

    def find_crafts_by_ingredient(self, ingredient_name: str) -> list[Craft]:
        return [craft for craft in self.crafts.values() if ingredient_name in [ingredient['item'] for ingredient in craft.ingredients]]
    
    def find_crafts_by_product(self, product_name: str) -> list[Craft]:
        return [craft for craft in self.crafts.values() if product_name in [product['item'] for product in craft.base_products]]

    def find_crafts_by_method(self, method: str) -> list[Craft]:
        return [craft for craft in self.crafts.values() if craft.method == method]

    def find_crafts_by_difficulty(self, difficulty: int) -> list[Craft]:
        return [craft for craft in self.crafts.values() if craft.difficulty == difficulty]
        
    def can_craft(self, character: "Character", craft: Craft) -> bool:
        for ingredient in craft.ingredients:
            ingredient_name, required_qty = ingredient['item'], ingredient['quantity']
            if character.inventory.get_quantity(ingredient_name) < required_qty:
                return False
        return True

    def find_craftable_crafts(self, character: "Character") -> list[Craft]:
        return [craft for craft in self.crafts.values() if self.can_craft(character, craft)]

    def find_craftable_quantities(self, character: "Character") -> Dict[str, int]:
        craftable_crafts = self.find_craftable_crafts(character)
        craftable_quantities = {}
        for craft in craftable_crafts:
            max_quantity = float('inf')
            for ingredient in craft.ingredients:
                ingredient_name, required_qty = ingredient['item'], ingredient['quantity']
                available = character.inventory.get_quantity(ingredient_name)
                if available > 0:
                    max_quantity = min(max_quantity, available // required_qty)
                else:
                    max_quantity = 0
                    break
            craftable_quantities[craft.name] = max_quantity
        return craftable_quantities

    def get_craftable_quantity(self, character: "Character") -> dict[str, int]:
        result = {}
        for craft in self.crafts.values():
            if not craft.visible:
                continue
            max_craftable = min(
                character.inventory.get_quantity(component["item"]) // component["quantity"]
                for component in craft.ingredients
            )
            if max_craftable > 0:
                result[craft.name] = max_craftable
        return result
    
    async def execute_craft(self, guild: discord.Guild, character: "Character", item_repository: "ItemRepository", craft: Craft, quantity: int) -> (bool, str, dict, dict):
        max_craftable = self.get_craftable_quantity(character).get(craft.name, 0)
        if quantity > max_craftable:
            return False, "Not enough materials", {}, {}

        craft_bonus = character.craft_points.get(METHOD_CLEAN.get(craft.method, craft.method), 0) - craft.difficulty

        has_failure = craft.failure_products != []
        has_success = craft.success_products != []

        roll = self.dice_session.craft_roll(craft.name, f"1d20+{craft_bonus}", has_failure=has_failure, has_success=has_success, character_name=character.name)
        craft_status = roll["outcome"]


        if craft_status == "natural_failure" or craft_status == "critical_failure":
            products = craft.failure_products
        elif craft_status == "normal":
            products = craft.base_products
        elif craft_status == "success":     
            products = []
            for product in craft.base_products:
                products.append({"item": product["item"], "quantity": product["quantity"] + craft.success_bonus})       
        elif craft_status == "natural_success" or craft_status == "critical_success":
            if craft_bonus != 0 and craft_status == "natural_success":
                products = []
                for product in craft.success_products:
                    products.append({"item": product["item"], "quantity": product["quantity"] + craft.success_bonus}) 
            else:
                products = craft.success_products
        else:
            return False, "Unknown craft status", {}, {}


        if character.inventory.slots_available() < len(products):
            products = products[:character.inventory.slots_available()]

        for component in craft.ingredients:
            has_removed = await character.inventory.remove(guild, character, component["item"], component["quantity"] * quantity, craft=True)

        
        for product in products:
            item = item_repository.get_item_by_name(product["item"])
            has_added = await character.inventory.add(guild, character, item, product["quantity"] * quantity, craft=True)

        return (True, craft_status, products, roll)