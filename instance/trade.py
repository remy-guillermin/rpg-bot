from dataclasses import dataclass, field

from typing import Dict, List, Optional, TYPE_CHECKING

from random import randint

if TYPE_CHECKING:
    from instance.character import Character
    from instance.history import History
    from instance.dice import DiceSession
    from instance.item import Item, ItemRepository

from utils.path import GSHEET_TRADES
from utils.load import load_trades
from utils.db import get_connection
from utils.utils import SPECIALTY_TAGS_BONUS, price_offer

import json
import datetime


@dataclass
class TradeEntry:
    item: "Item"
    quantity: int = 1

class Trade:
    def __init__(self, requested_items: list[TradeEntry], offered_items: list[TradeEntry], price: int, quantity: int, trade_id: str):
        self.requested_items = requested_items
        self.offered_items = offered_items
        self.base_price = price
        self.price = 0
        self.quantity = quantity
        self.trade_id = trade_id
        self.type = "trade" if requested_items and offered_items else "sale" if offered_items else "other"
        self.blackmarket = trade_id.split("_")[-2] == "bm"

    def _decrease_quantity(self, amount: int = 1):
        self.quantity = max(0, self.quantity - amount)

    def success_threshold(self, given_value: int) -> int:
        """Retourne le roll minimum requis sur d100 pour réussir."""
        return self.price - given_value

    def update_price(self):
        self.price = self.base_price * randint(80, 120) // 100  # Simule une fluctuation de prix entre -20% et +20%

@dataclass
class TradeProposal:
    trade_id: str
    offered_items: list[TradeEntry]
    offered_value: int
    player: str


@dataclass
class PastTrade:
    trade_id: str
    item_received_by_player: list[TradeEntry]
    item_received_by_merchant: list[TradeEntry]
    currency: int
    player: str
    timestamp: str



class TradeRepository:
    def __init__(self, item_repository: "ItemRepository", history: "History", dice_session: "DiceSession"):
        self.trades: dict[str, Trade] = {}
        self.past_trades: dict[str, list[PastTrade]] = {}
        self.item_repository = item_repository
        self.history = history
        self.dice_session = dice_session
        self.reload()

    def reload(self):
        self.trades.clear()
        self.past_trades.clear()
        self.offer_prices: dict[str, int] = {}
        trades_as_dict, past_trades_as_dict = load_trades(GSHEET_TRADES)
        for d in trades_as_dict:
            requested_items = [TradeEntry(item=item, quantity=entry.get("quantity", 1)) for entry in d["requested_items"] if (item := self.item_repository.get_item_by_name(entry["item"])) is not None]
            offered_items = [TradeEntry(item=item, quantity=entry.get("quantity", 1)) for entry in d["offered_items"] if (item := self.item_repository.get_item_by_name(entry["item"])) is not None]
            if requested_items == [] and offered_items != []:
                price = sum(entry.item.value * entry.quantity for entry in offered_items)
            else:
                price = 0
            trade = Trade(
                requested_items=requested_items,
                offered_items=offered_items,
                price=price,
                quantity=d["quantity"],
                trade_id=d["trade_id"]
            )
            self.trades[d["trade_id"]] = trade

        for d in past_trades_as_dict:
            received_items = [TradeEntry(item=item, quantity=entry.get("quantity", 1)) for entry in d["item_received_by_player"] if (item := self.item_repository.get_item_by_name(entry["item"])) is not None]
            given_items = [TradeEntry(item=item, quantity=entry.get("quantity", 1)) for entry in d["item_received_by_merchant"] if (item := self.item_repository.get_item_by_name(entry["item"])) is not None]
            trade = PastTrade(
                trade_id=d["trade_id"],
                item_received_by_player=received_items,
                item_received_by_merchant=given_items,
                currency=d["currency"],
                player=d["player"],
                timestamp=d["timestamp"]
            )
            self.trades[d["trade_id"]]._decrease_quantity()
            self.past_trades.setdefault(d["player"], []).append(trade)

        self.trades = {tid: t for tid, t in self.trades.items() if t.quantity > 0}

        self.update_prices()

        

    def list_trades(self) -> list[Trade]:
        return list(self.trades.values())

    def list_past_trades_for_player(self, player: str) -> list[PastTrade]:
        return self.past_trades.get(player, [])


    def get_trade_by_id(self, trade_id: str) -> Trade:
        return self.trades.get(trade_id)

    def get_past_trade_by_id_for_player(self, player: str, trade_id: str) -> list[PastTrade] | None:
        trades = [trade for trade in self.list_past_trades_for_player(player) if trade.trade_id == trade_id]
        return trades if trades else None

    def list_past_trades_ids(self) -> list[str]:
        return list({trade.trade_id for trades in self.past_trades.values() for trade in trades})


    def get_offer_price(self, item: "Item", specialty: str | None) -> int:
        bonus = 0
        if specialty and specialty in SPECIALTY_TAGS_BONUS:
            for tag in item.tags:
                bonus += SPECIALTY_TAGS_BONUS[specialty].get(tag, 0)

        if item.name not in self.offer_prices:
            self.offer_prices[item.name] = item.value * randint(80+bonus, 120+bonus) // 100
        return self.offer_prices[item.name]

    def update_prices(self):
        self.offer_prices.clear()
        for trade in self.trades.values():
            trade.update_price()

    
    def propose_trade(self, trade_offer: TradeProposal, player: "Character", roll: int) -> tuple[str, float | None]:
        trade = self.get_trade_by_id(trade_offer.trade_id)
        if not trade:
            return "No trade", None

        if trade.quantity <= 0:
            return "Not available", None


        charisma_bonus = player.stat_points.get("Charisme", 0)

        threshold = None
        if trade_offer.offered_value < trade.price:
            ratio = max(1, min(100, int(trade_offer.offered_value / trade.price * 100)))
            threshold = price_offer(ratio) * (1 - 2 * charisma_bonus / 100)

            if roll < threshold:
                return "Failed trade - offer too low", threshold

        past_trade = PastTrade(
            trade_id=trade_offer.trade_id,
            item_received_by_player=trade.offered_items,
            item_received_by_merchant=trade_offer.offered_items,
            currency=trade_offer.offered_value,
            player=player.name,
            timestamp=str(datetime.datetime.now())
        )
        self._append_past_trade(past_trade)
        trade._decrease_quantity()
        self.trades[trade_offer.trade_id] = trade
        return "Trade successful", threshold


    def _append_past_trade(self, trade: PastTrade) -> None:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO past_trades
                   (trade_id, item_received_by_player, item_received_by_merchant, currency, player, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    trade.trade_id,
                    json.dumps([{"item": e.item.name, "quantity": e.quantity} for e in trade.item_received_by_player], ensure_ascii=False),
                    json.dumps([{"item": e.item.name, "quantity": e.quantity} for e in trade.item_received_by_merchant], ensure_ascii=False),
                    trade.currency,
                    trade.player,
                    trade.timestamp,
                ),
            )

    