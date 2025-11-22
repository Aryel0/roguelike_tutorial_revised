from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, List
import color

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor
    from tcod.console import Console


class Projectile:
    """Base projectile class for all moving visual effects."""

    def __init__(
        self,
        engine: Engine,
        actor: Actor,
        symbol: str | List[str],
        color: Tuple[int, int, int],
        range: int,
        damage: int = 0,
        dx: int = 0,
        dy: int = 0,
        can_hit_self: bool = False,
    ):
        self.engine = engine
        self.actor = actor
        self.x = actor.x
        self.y = actor.y
        self.symbol = symbol
        self.char = symbol if isinstance(symbol, str) else symbol[0]
        self.color = color
        self.range = range
        self.damage = damage
        self.dx = dx
        self.dy = dy
        self.distance_travelled = 0
        self.done = False
        self.can_hit_self = can_hit_self
        self.hit_actors: set[Actor] = set()

    def check_collision(self, x: int, y: int) -> bool:
        """Check if projectile hits an actor at given position."""
        if not self.engine.game_map.in_bounds(x, y):
            return False

        target_actor = self.engine.game_map.get_actor_at_location(x, y)
        if target_actor and target_actor not in self.hit_actors:
            if target_actor == self.actor and not self.can_hit_self:
                return False

            self.hit_actors.add(target_actor)
            damage_dealt = max(0, self.damage - target_actor.fighter.defense)

            if damage_dealt > 0:
                self.engine.message_log.add_message(
                    f"The projectile hits {target_actor.name} for {damage_dealt} damage!",
                    color.player_atk if self.actor == self.engine.player else color.enemy_atk
                )
                target_actor.fighter.take_damage(damage_dealt)
            else:
                self.engine.message_log.add_message(
                    f"The projectile bounces off {target_actor.name}!",
                    color.player_atk if self.actor == self.engine.player else color.enemy_atk
                )
            return True
        return False

    def move(self):
        """Base movement (straight line)."""
        self.x += self.dx
        self.y += self.dy
        self.distance_travelled += 1

        # Check collision
        if self.engine.game_map.in_bounds(self.x, self.y):
            self.check_collision(self.x, self.y)

            # Check if hit a wall
            if not self.engine.game_map.tiles["walkable"][self.x, self.y]:
                self.done = True
                return

        # Remove if out of bounds or max range reached
        if not self.engine.game_map.in_bounds(self.x, self.y) or self.distance_travelled >= self.range:
            self.done = True

    def update(self):
        """Update projectile state - CALLED EVERY FRAME."""
        if not self.done:
            self.move()

    def render(self, console: Console) -> None:
        """Render the projectile."""
        if self.done:
            return

        if self.engine.game_map.in_bounds(self.x, self.y):
            if self.engine.game_map.visible[self.x, self.y]:
                console.print(self.x, self.y, self.char, fg=self.color)


class DirectionalProjectile(Projectile):
    """Projectile that moves in the direction the actor is facing with animated symbol."""

    def __init__(
        self,
        engine: Engine,
        actor: Actor,
        symbol: List[str],
        projectile_color: Tuple[int, int, int],
        projectile_range: int,
        damage: int = 0,
    ):
        dx, dy = actor.facing_direction
        super().__init__(engine, actor, symbol, projectile_color, projectile_range, damage, dx, dy)
        self.frame_index = 0

    def render(self, console: Console) -> None:
        """Render with animated symbol."""
        if self.done:
            return

        # Cycle through symbols for animation
        if isinstance(self.symbol, list):
            self.char = self.symbol[self.frame_index % len(self.symbol)]
            self.frame_index += 1

        super().render(console)


class ShockwaveProjectile(Projectile):
    """Expanding shockwave that hits everything in its radius."""

    def __init__(
        self,
        engine: Engine,
        actor: Actor,
        symbol: str,
        projectile_color: Tuple[int, int, int],
        projectile_range: int,
        damage: int = 0,
    ):
        super().__init__(engine, actor, symbol, projectile_color, projectile_range, damage)
        self.expanding_radius = 0

    def update(self):
        """Expand the shockwave radius."""
        if self.done:
            return

        self.expanding_radius += 1
        if self.expanding_radius > self.range:
            self.done = True
            return

        # Check collisions in the expanding ring
        for dx in range(-self.expanding_radius, self.expanding_radius + 1):
            for dy in range(-self.expanding_radius, self.expanding_radius + 1):
                # Only check the outer ring
                if abs(dx) == self.expanding_radius or abs(dy) == self.expanding_radius:
                    x = self.actor.x + dx
                    y = self.actor.y + dy
                    self.check_collision(x, y)

    def render(self, console: Console) -> None:
        """Render the expanding ring."""
        if self.done:
            return

        for dx in range(-self.expanding_radius, self.expanding_radius + 1):
            for dy in range(-self.expanding_radius, self.expanding_radius + 1):
                if abs(dx) == self.expanding_radius or abs(dy) == self.expanding_radius:
                    x = self.actor.x + dx
                    y = self.actor.y + dy
                    if self.engine.game_map.in_bounds(x, y) and self.engine.game_map.visible[x, y]:
                        console.print(x, y, self.char, fg=self.color)


class CrossProjectile(Projectile):
    """Expanding cross pattern (+ shape)."""

    def __init__(
        self,
        engine: Engine,
        actor: Actor,
        symbol: str,
        projectile_color: Tuple[int, int, int],
        projectile_range: int,
        damage: int = 0,
    ):
        super().__init__(engine, actor, symbol, projectile_color, projectile_range, damage)

    def update(self):
        """Expand the cross."""
        if self.done:
            return

        self.distance_travelled += 1
        if self.distance_travelled > self.range:
            self.done = True
            return

        # Check collisions in the cross pattern
        cx, cy = self.actor.x, self.actor.y
        for dx in range(-self.distance_travelled, self.distance_travelled + 1):
            self.check_collision(cx + dx, cy)
        for dy in range(-self.distance_travelled, self.distance_travelled + 1):
            self.check_collision(cx, cy + dy)

    def render(self, console: Console) -> None:
        """Render the cross pattern."""
        if self.done:
            return

        cx, cy = self.actor.x, self.actor.y
        for dx in range(-self.distance_travelled, self.distance_travelled + 1):
            x = cx + dx
            if self.engine.game_map.in_bounds(x, cy) and self.engine.game_map.visible[x, cy]:
                console.print(x, cy, self.char, fg=self.color)
        for dy in range(-self.distance_travelled, self.distance_travelled + 1):
            y = cy + dy
            if self.engine.game_map.in_bounds(cx, y) and self.engine.game_map.visible[cx, y]:
                console.print(cx, y, self.char, fg=self.color)


class DiagonalProjectile(Projectile):
    """Expanding X pattern (diagonal cross)."""

    def __init__(
        self,
        engine: Engine,
        actor: Actor,
        symbol: str,
        projectile_color: Tuple[int, int, int],
        projectile_range: int,
        damage: int = 0,
    ):
        super().__init__(engine, actor, symbol, projectile_color, projectile_range, damage)

    def update(self):
        """Expand the diagonal cross."""
        if self.done:
            return

        self.distance_travelled += 1
        if self.distance_travelled > self.range:
            self.done = True
            return

        # Check collisions in the X pattern
        cx, cy = self.actor.x, self.actor.y
        for d in range(-self.distance_travelled, self.distance_travelled + 1):
            for (dx, dy) in [(d, d), (d, -d), (-d, d), (-d, -d)]:
                x = cx + dx
                y = cy + dy
                self.check_collision(x, y)

    def render(self, console: Console) -> None:
        """Render the X pattern."""
        if self.done:
            return

        cx, cy = self.actor.x, self.actor.y
        for d in range(-self.distance_travelled, self.distance_travelled + 1):
            for (dx, dy) in [(d, d), (d, -d)]:
                x = cx + dx
                y = cy + dy
                if self.engine.game_map.in_bounds(x, y) and self.engine.game_map.visible[x, y]:
                    console.print(x, y, self.char, fg=self.color)