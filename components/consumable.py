from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Tuple

from components.base_component import BaseComponent
from exceptions import Impossible
from input_handlers import ActionOrHandler, AreaRangedAttackHandler, SingleRangedAttackHandler
import actions
import color
import components.ai
import components.inventory

if TYPE_CHECKING:
    from entity import Actor, Item


class Consumable(BaseComponent):
    parent: Item

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        """Try to return the action for this item."""
        return actions.ItemAction(consumer, self.parent)

    def activate(self, action: actions.ItemAction) -> None:
        """Invoke this items ability.

        `action` is the context for this activation.
        """
        raise NotImplementedError()

    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory):
            inventory.items.remove(entity)


class ConfusionConsumable(Consumable):
    def __init__(self, number_of_turns: int):
        self.number_of_turns = number_of_turns

    def get_action(self, consumer: Actor) -> SingleRangedAttackHandler:
        self.engine.message_log.add_message("Select a target location.", color.needs_target)
        return SingleRangedAttackHandler(
            self.engine,
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        target = action.target_actor

        if not self.engine.game_map.visible[action.target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")
        if not target:
            raise Impossible("You must select an enemy to target.")
        if target is consumer:
            raise Impossible("You cannot confuse yourself!")

        self.engine.message_log.add_message(
            f"The eyes of the {target.name} look vacant, as it starts to stumble around!",
            color.status_effect_applied,
        )
        target.ai = components.ai.ConfusedEnemy(
            entity=target,
            previous_ai=target.ai,
            turns_remaining=self.number_of_turns,
        )
        self.consume()


class FireballDamageConsumable(Consumable):
    def __init__(self, damage: int, radius: int):
        self.damage = damage
        self.radius = radius

    def get_action(self, consumer: Actor) -> AreaRangedAttackHandler:
        self.engine.message_log.add_message("Select a target location.", color.needs_target)
        return AreaRangedAttackHandler(
            self.engine,
            radius=self.radius,
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: actions.ItemAction) -> None:
        target_xy = action.target_xy

        if not self.engine.game_map.visible[target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")

        targets_hit = False
        for actor in self.engine.game_map.actors:
            if actor.distance(*target_xy) <= self.radius:
                self.engine.message_log.add_message(
                    f"The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage!"
                )
                actor.fighter.take_damage(self.damage)
                targets_hit = True

        if not targets_hit:
            raise Impossible("There are no targets in the radius.")
        self.consume()


class HealingConsumable(Consumable):
    def __init__(self, amount: int):
        self.amount = amount

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        amount_recovered = consumer.fighter.heal(self.amount)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"You consume the {self.parent.name}, and recover {amount_recovered} HP!",
                color.health_recovered,
            )
            self.consume()
        else:
            raise Impossible("Your health is already full.")


class LightningDamageConsumable(Consumable):
    def __init__(self, damage: int, maximum_range: int):
        self.damage = damage
        self.maximum_range = maximum_range

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        target = None
        closest_distance = self.maximum_range + 1.0

        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.parent.gamemap.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if distance < closest_distance:
                    target = actor
                    closest_distance = distance

        if target:
            self.engine.message_log.add_message(
                f"A lighting bolt strikes the {target.name} with a loud thunder, for {self.damage} damage!"
            )
            target.fighter.take_damage(self.damage)
            self.consume()
        else:
            raise Impossible("No enemy is close enough to strike.")


class StrengthPotionConsumable(Consumable):
    def __init__(self, number_of_turns: int, power_boost: int):
        self.number_of_turns = number_of_turns
        self.power_boost = power_boost

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        fighter = consumer.fighter

        if not hasattr(fighter, "temporary_buffs"):
            fighter.temporary_buffs = {}

        if "strength" in fighter.temporary_buffs:
            raise Impossible("You already feel unnaturally strong!")

        fighter.temporary_buffs["strength"] = {
    "turns_left": self.number_of_turns,
    "on_expire": lambda fighter: setattr(fighter, "base_power", fighter.base_power - self.power_boost),
    "message": "You feel your power getting neutralized, your strength boost has worn off.",
    "color": color.red, }


        fighter.base_power += self.power_boost

        self.engine.message_log.add_message(
            f"You drink the {self.parent.name}. Power surges through your veins! (+{self.power_boost} ATK for {self.number_of_turns} turns)",
            color.green,
        )

        self.consume()


class DefensePotionConsumable(Consumable):
    def __init__(self, number_of_turns: int, defense_boost: int):
        self.number_of_turns = number_of_turns
        self.defense_boost = defense_boost

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        fighter = consumer.fighter
        if not hasattr(fighter, "temporary_buffs"):
            fighter.temporary_buffs = {}

        if "defense" in fighter.temporary_buffs:
            raise Impossible("You already feel unusually protected!")

        fighter.temporary_buffs["defense"] = {
            "turns_left": self.number_of_turns,
            "on_expire": lambda f: setattr(f, "base_defense", f.base_defense - self.defense_boost),
            "message": f"You feel unsafe again, your defense boost has worn off!",
            "color": color.red
        }

        fighter.base_defense += self.defense_boost

        self.engine.message_log.add_message(
            f"You drink the {self.parent.name}. A protective aura surrounds you! (+{self.defense_boost} DEF for {self.number_of_turns} turns)",
            color.green
        )
        self.consume()


class IceBombConsumable(Consumable):
    def __init__(self, number_of_turns: int, radius: int):
        self.number_of_turns = number_of_turns
        self.radius = radius

    def get_action(self, consumer: Actor) -> AreaRangedAttackHandler:
        self.engine.message_log.add_message("Select a target location for the ice bomb.", color.needs_target)
        return AreaRangedAttackHandler(
            self.engine,
            radius=self.radius,
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        target_xy = action.target_xy

        if not self.engine.game_map.visible[target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")

        targets_hit = False
        for actor in self.engine.game_map.actors:
            # Don't freeze the consumer (player can't be affected by their own ice bomb)
            if actor is consumer:
                continue

            if actor.distance(*target_xy) <= self.radius:
                self.engine.message_log.add_message(
                    f"The {actor.name} is frozen solid and cannot move!",
                    color.status_effect_applied,
                )
                # Apply paralysis by replacing AI with ParalyzedEnemy
                actor.ai = components.ai.ParalyzedEnemy(
                    entity=actor,
                    previous_ai=actor.ai,
                    turns_remaining=self.number_of_turns,
                )
                targets_hit = True

        if not targets_hit:
            raise Impossible("There are no targets in the radius.")
        self.consume()


class DirectionalProjectileConsumable(Consumable):
    """Fires an animated projectile in facing direction."""

    def __init__(self, damage: int, projectile_range: int, symbols: List[str], projectile_color: Tuple[int, int, int]):
        self.damage = damage
        self.range = projectile_range
        self.symbols = symbols
        self.projectile_color = projectile_color

    def activate(self, action: actions.ItemAction) -> None:
        from projectiles import DirectionalProjectile

        consumer = action.entity

        projectile = DirectionalProjectile(
            engine=self.engine,
            actor=consumer,
            symbol=self.symbols,
            projectile_color=self.projectile_color,
            projectile_range=self.range,
            damage=self.damage,
        )

        self.engine.active_projectiles.append(projectile)
        self.engine.message_log.add_message(
            f"You fire the {self.parent.name}!",
            color.player_atk
        )
        self.consume()


class ShockwaveConsumable(Consumable):
    """Creates an expanding shockwave."""

    def __init__(self, damage: int, radius: int):
        self.damage = damage
        self.radius = radius

    def activate(self, action: actions.ItemAction) -> None:
        from projectiles import ShockwaveProjectile

        consumer = action.entity

        projectile = ShockwaveProjectile(
            engine=self.engine,
            actor=consumer,
            symbol="○",
            projectile_color=(100, 200, 255),
            projectile_range=self.radius,
            damage=self.damage,
        )

        self.engine.active_projectiles.append(projectile)
        self.engine.message_log.add_message(
            f"A shockwave emanates from you!",
            color.player_atk
        )
        self.consume()


class CrossBlastConsumable(Consumable):
    """Creates an expanding cross blast."""

    def __init__(self, damage: int, projectile_range: int):
        self.damage = damage
        self.range = projectile_range

    def activate(self, action: actions.ItemAction) -> None:
        from projectiles import CrossProjectile

        consumer = action.entity

        projectile = CrossProjectile(
            engine=self.engine,
            actor=consumer,
            symbol="+",
            projectile_color=(255, 100, 100),
            projectile_range=self.range,
            damage=self.damage,
        )

        self.engine.active_projectiles.append(projectile)
        self.engine.message_log.add_message(
            f"A cross-shaped blast erupts!",
            color.player_atk
        )
        self.consume()


class DiagonalBlastConsumable(Consumable):
    """Creates an expanding diagonal blast (X pattern)."""

    def __init__(self, damage: int, projectile_range: int):
        self.damage = damage
        self.range = projectile_range

    def activate(self, action: actions.ItemAction) -> None:
        from projectiles import DiagonalProjectile

        consumer = action.entity

        projectile = DiagonalProjectile(
            engine=self.engine,
            actor=consumer,
            symbol="×",
            projectile_color=(200, 100, 255),
            projectile_range=self.range,
            damage=self.damage,
        )

        self.engine.active_projectiles.append(projectile)
        self.engine.message_log.add_message(
            f"An X-shaped blast erupts!",
            color.player_atk
        )
        self.consume()
