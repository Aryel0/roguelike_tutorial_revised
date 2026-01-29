from __future__ import annotations

import time
from enum import Enum, auto
from typing import TYPE_CHECKING
import lzma
import pickle

from tcod.console import Console
from tcod.map import compute_fov

from message_log import MessageLog
import exceptions
import render_functions
import color

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld


class GameState(Enum):
    EXPLORATION = auto()
    TURN_BASED = auto()


class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player
        self.active_projectiles = []
        self.game_state = GameState.EXPLORATION
        self.last_enemy_turn_time = time.monotonic()
        self.enemy_turn_interval = 1.0  # Enemies move once per second in realtime
        self.last_player_move_time = time.monotonic()
        self.player_move_interval = 0.1  # Limit player moves to 10 per second


    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass  # Ignore impossible action exceptions from AI.

    def update_projectiles(self) -> None:
        """Update all active projectiles - call this EVERY FRAME."""
        for projectile in list(self.active_projectiles):
            projectile.update()
            if projectile.done:
                self.active_projectiles.remove(projectile)

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        self.game_map.render(console)

        self.message_log.render(console=console, x=21, y=45, width=40, height=5)

        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )

        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 47),
        )

        render_functions.render_names_at_mouse_location(console=console, x=21, y=44, engine=self)

        # Only RENDER projectiles here, don't update them
        for projectile in self.active_projectiles:
            projectile.render(console)


    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)

    def update_realtime(self) -> None:
        """
        Update the game in real-time.
        - Check for interruptions (enemies coming into view).
        - Update non-player entities periodically.
        """
        # Check if we should switch to turn-based mode
        # If any hostile enemy is visible, switch to TURN_BASED
        for entity in self.game_map.actors:
            if entity != self.player and entity.ai and self.game_map.visible[entity.x, entity.y]:
                # Found a visible enemy
                if self.game_state == GameState.EXPLORATION:
                    self.game_state = GameState.TURN_BASED
                    self.message_log.add_message("Enemy spotted! Combat started.", color.enemy_atk)
                return  # Stay in turn-based or just switched

        # If we are here, no enemies are visible. Ensure we are in EXPLORATION mode
        if self.game_state == GameState.TURN_BASED:
            # Check if there are really no enemies?
            # The loop above returns if ANY is visible. So if we are here, NONE are visible.
            self.game_state = GameState.EXPLORATION
            self.message_log.add_message("Combat ended.", color.welcome_text)

        # Handle ambient enemy movement (slowly)
        current_time = time.monotonic()
        if current_time - self.last_enemy_turn_time >= self.enemy_turn_interval:
            self.handle_enemy_turns()
            self.last_enemy_turn_time = current_time

        self.update_projectiles()
