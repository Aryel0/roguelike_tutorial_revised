from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple
import random
import color

import numpy as np
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction

if TYPE_CHECKING:
    from entity import Actor


class BaseAI(Action):
    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Compute and return a path to the target position.

        If there is no valid path then returns an empty list.
        """
        # Copy the walkable array.
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # Check that an enitiy blocks movement and the cost isn't zero (blocking.)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in
                # hallways.  A higher number means enemies will take longer paths in
                # order to surround the player.
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass that graph to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # Start position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]


class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity,
                dest_x - self.entity.x,
                dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()


class ConfusedEnemy(BaseAI):
    """
    A confused enemy will stumble around aimlessly for a given number of turns, then revert back to its previous AI.
    If an actor occupies a tile it is randomly moving into, it will attack.
    """

    def __init__(self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(f"The {self.entity.name} is no longer confused.")
            self.entity.ai = self.previous_ai
        else:
            # Pick a random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Northwest
                    (0, -1),  # North
                    (1, -1),  # Northeast
                    (-1, 0),  # West
                    (1, 0),  # East
                    (-1, 1),  # Southwest
                    (0, 1),  # South
                    (1, 1),  # Southeast
                ]
            )

            self.turns_remaining -= 1

            # The actor will either try to move or attack in the chosen random direction.
            # Its possible the actor will just bump into the wall, wasting a turn.
            return BumpAction(
                self.entity,
                direction_x,
                direction_y,
            ).perform()


class ParalyzedEnemy(BaseAI):
    """
    A paralyzed enemy cannot move or act for a given number of turns.
    After the effect wears off, it reverts to its previous AI.
    """

    def __init__(self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int):
        super().__init__(entity)
        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.entity.name} breaks free from the ice!",
                color.status_effect_applied
            )
            self.entity.ai = self.previous_ai
        else:
            # Decrement turns and do nothing (paralyzed = skip turn)
            self.turns_remaining -= 1
            return WaitAction(self.entity).perform()


class HostileEnemyWithProjectile(BaseAI):
    """Enemy that can throw projectiles at the player."""

    def __init__(self, entity: Actor, projectile_chance: float = 0.3, projectile_range: int = 6):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []
        self.projectile_chance = projectile_chance  # Chance to throw projectile each turn
        self.projectile_range = projectile_range
        self.projectile_cooldown = 0  # Turns until can throw again

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            # Reduce cooldown
            if self.projectile_cooldown > 0:
                self.projectile_cooldown -= 1

            # Melee range - attack
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            # Medium range - maybe throw projectile
            elif distance <= self.projectile_range and self.projectile_cooldown == 0:
                import random
                if random.random() < self.projectile_chance:
                    self.throw_projectile()
                    self.projectile_cooldown = 3  # Wait 3 turns before throwing again
                    return WaitAction(self.entity).perform()

            # Otherwise pathfind toward player
            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity,
                dest_x - self.entity.x,
                dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()

    def throw_projectile(self) -> None:
        """Throw a projectile at the player."""
        from projectiles import Projectile

        target = self.engine.player

        # Calculate direction to player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y

        # Normalize direction
        import math
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > 0:
            dx = int(dx / distance * 10)  # Scale for range
            dy = int(dy / distance * 10)

        projectile = Projectile(
            engine=self.engine,
            actor=self.entity,
            symbol="*",
            color=(255, 100, 100),  # Red enemy projectile
            range=self.projectile_range,
            damage=self.entity.fighter.power // 2,
            dx=1 if dx > 0 else (-1 if dx < 0 else 0),
            dy=1 if dy > 0 else (-1 if dy < 0 else 0),
            can_hit_self=False,
        )

        self.engine.active_projectiles.append(projectile)
        self.engine.message_log.add_message(
            f"The {self.entity.name} throws a projectile!",
            color.enemy_atk
        )


class RangedEnemy(BaseAI):
    """Enemy that prefers to keep distance and throw projectiles."""

    def __init__(self, entity: Actor, preferred_distance: int = 4):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []
        self.preferred_distance = preferred_distance
        self.projectile_cooldown = 0

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if self.projectile_cooldown > 0:
                self.projectile_cooldown -= 1

            # Too close - back away
            if distance <= 2:
                # Move away from player
                retreat_dx = -1 if dx > 0 else (1 if dx < 0 else 0)
                retreat_dy = -1 if dy > 0 else (1 if dy < 0 else 0)
                return MovementAction(self.entity, retreat_dx, retreat_dy).perform()

            # Good distance - throw projectile
            elif distance <= 6 and self.projectile_cooldown == 0:
                self.throw_projectile()
                self.projectile_cooldown = 2
                return WaitAction(self.entity).perform()

            # Too far - move closer
            else:
                self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity,
                dest_x - self.entity.x,
                dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()

    def throw_projectile(self) -> None:
        """Throw a projectile at the player."""
        from projectiles import Projectile

        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y

        # Normalize
        import math
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > 0:
            norm_dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
            norm_dy = 1 if dy > 0 else (-1 if dy < 0 else 0)

            projectile = Projectile(
                engine=self.engine,
                actor=self.entity,
                symbol="○",
                color=(150, 255, 150),  # Green ranged projectile
                range=8,
                damage=self.entity.fighter.power,
                dx=norm_dx,
                dy=norm_dy,
                can_hit_self=False,
            )

            self.engine.active_projectiles.append(projectile)
            self.engine.message_log.add_message(
                f"The {self.entity.name} fires at you!",
                color.enemy_atk
            )

class BlacksmithAI(BaseAI):
    """NPC that allows upgrading equipment."""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        """Blacksmith doesn't move or attack."""
        return WaitAction(self.entity).perform()


class BossAI(BaseAI):
    """Enhanced AI for boss enemies with special abilities."""

    def __init__(self, entity: Actor, special_attack_chance: float = 0.3):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []
        self.special_attack_chance = special_attack_chance
        self.cooldown = 0

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if self.cooldown > 0:
                self.cooldown -= 1

            # Melee range - powerful attack
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            # Special attack at medium range
            elif distance <= 5 and self.cooldown == 0 and random.random() < self.special_attack_chance:
                self.special_attack()
                self.cooldown = 5
                return WaitAction(self.entity).perform()

            # Chase player
            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity,
                dest_x - self.entity.x,
                dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()

    def special_attack(self) -> None:
        """Boss special attack - area damage."""
        from projectiles import ShockwaveProjectile

        projectile = ShockwaveProjectile(
            engine=self.engine,
            actor=self.entity,
            symbol=chr(15),  # ☼
            projectile_color=(255, 0, 0),
            projectile_range=4,
            damage=self.entity.fighter.power * 2,
        )

        self.engine.active_projectiles.append(projectile)
        self.engine.message_log.add_message(
            f"The {self.entity.name} unleashes a devastating attack!",
            color.enemy_atk
        )
