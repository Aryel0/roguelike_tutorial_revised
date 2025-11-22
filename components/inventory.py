from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple
from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item
    from components.consumable import Consumable

class Inventory(BaseComponent):
    parent: Actor

    def __init__(self, capacity: int):
        self.capacity = capacity
        # Always store items as (Item, qty) tuples
        self.items: List[Tuple[Item, int]] = []

    def add(self, item: Item, quantity: int = 1):
        """Add an item to the inventory. Stack if possible."""
        if item.equippable:
            if len(self.items) >= self.capacity:
                print("Inventory full")
                return False
            self.items.append((item, 1))
            return True

        for i, (inv_item, qty) in enumerate(self.items):
            if inv_item.name == item.name and isinstance(item.consumable, Consumable):
                self.items[i] = (inv_item, qty + quantity)
                return True

        if len(self.items) >= self.capacity:
            print("Inventory full")
            return False
        self.items.append((item, quantity))
        return True

    def remove(self, item: Item, quantity: int = 1):
        """Remove an item from inventory. Decrease stack or remove entirely."""
        for i, (inv_item, qty) in enumerate(self.items):
            if inv_item == item:
                if qty > quantity:
                    self.items[i] = (inv_item, qty - quantity)
                else:
                    del self.items[i]
                return True
        return False
    
    def drop(self, item: Item, quantity: int = 1) -> None:
        """Drop some or all of an item onto the map."""
        if self.remove(item, quantity):
            item.place(self.parent.x, self.parent.y, self.gamemap)
            self.engine.message_log.add_message(f"You dropped {quantity} {item.name}(s).")