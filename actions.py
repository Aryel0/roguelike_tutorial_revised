from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import color
import engine
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item


class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.

        `self.entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()


class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")

                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(f"You picked up the {item.name}!")
                return

        raise exceptions.Impossible("There is nothing here to pick up.")


class ItemAction(Action):
    def __init__(self, entity: Actor, item: Optional[Item], target_xy: Optional[Tuple[int, int]] = None, skill = None):
        super().__init__(entity)
        self.item = item
        self.skill = skill
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item and self.item.consumable:
            self.item.consumable.activate(self)
        elif self.skill:
            self.skill.activate(self)


class DropItem(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item)

        self.entity.inventory.drop(self.item)


class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)


class WaitAction(Action):
    def perform(self) -> None:
        pass


class TakeStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.generate_floor()
            self.engine.message_log.add_message("You descend the staircase.", color.descend)


            if self.engine.game_world.current_floor == 2:
                from components.skills import BeamSkill
                from color import purple
                self.engine.player.skills.add_skill(BeamSkill(damage=10, range=8))
                self.engine.message_log.add_message("You stumble upon an ancient tome... You learned Beam!", purple)

            if self.engine.game_world.current_floor == 3:
                from components.skills import HealSkill
                from color import purple
                self.engine.player.skills.add_skill(HealSkill(amount=20))
                self.engine.message_log.add_message("You feel a divine presence... You learned Lesser Heal!", purple)
        else:
            raise exceptions.Impossible("There are no stairs here.")


class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this actions destination.."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()


class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")

        damage = self.entity.fighter.power - target.fighter.defense
        self.entity.fighter.update_temporary_buffs(self.engine.message_log)

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(f"{attack_desc} for {damage} hit points.", attack_color)
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(f"{attack_desc} but does no damage.", attack_color)


class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by an entity.
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)


class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()

        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()


class ThrowProjectileAction(ActionWithDirection):
    """Throw a basic projectile in a direction."""

    def perform(self) -> None:
        from projectiles import Projectile

        projectile = Projectile(
            engine=self.engine,
            actor= self.engine.player,
            symbol="*",
            color=(255, 200, 0),
            range=5,
            damage=self.entity.fighter.power // 2,
            dx=self.engine.player.facing_direction[0],
            dy=self.engine.player.facing_direction[1]
        )

        throw_range = projectile.range
        target_x = self.entity.x + (self.dx * throw_range)
        target_y = self.entity.y + (self.dy * throw_range)

        # Clamp to map bounds
        target_x = max(0, min(target_x, self.engine.game_map.width - 1))
        target_y = max(0, min(target_y, self.engine.game_map.height - 1))

        self.engine.active_projectiles.append(projectile)

        self.engine.message_log.add_message(
            "You throw a projectile!",
            color.player_atk
        )

class UpgradeEquipmentAction(Action):
    """Upgrade equipment at the blacksmith."""

    def __init__(self, entity: Actor, blacksmith: Actor, item: Item, cost: int):
        super().__init__(entity)
        self.blacksmith = blacksmith
        self.item = item
        self.cost = cost

    def perform(self) -> None:
        # Check if player has enough gold (you'll need to add gold system)
        # For now, just upgrade

        if not self.item.equippable:
            raise exceptions.Impossible("This item cannot be upgraded.")

        # Upgrade the item
        self.item.equippable.power_bonus += 1
        self.item.equippable.defense_bonus += 1

        self.engine.message_log.add_message(
            f"The blacksmith upgrades your {self.item.name}! (+1 ATK/DEF)",
            color.green
        )


class TalkToBlacksmithAction(ActionWithDirection):
    """Interact with blacksmith."""

    def perform(self) -> None:
        target = self.target_actor

        if not target:
            raise exceptions.Impossible("There is no one to talk to.")

        if target.name != "Blacksmith":
            raise exceptions.Impossible("This is not the blacksmith.")

        # Show upgrade menu
        self.engine.message_log.add_message(
            "The blacksmith offers to upgrade your equipment.",
            color.white
        )

        # You can expand this to show a proper upgrade menu
        # For now, auto-upgrade equipped weapon if any
        if self.entity.equipment.weapon:
            weapon = self.entity.equipment.weapon
            if weapon.equippable:
                weapon.equippable.power_bonus += 1
                self.engine.message_log.add_message(
                    f"The blacksmith upgrades your {weapon.name}! (+1 ATK)",
                    color.green
                )
        else:
            self.engine.message_log.add_message(
                "You need to equip a weapon to upgrade!",
                color.impossible
            )
