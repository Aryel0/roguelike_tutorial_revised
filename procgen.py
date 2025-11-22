from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Iterator, List, Tuple
import random

import tcod

from game_map import GameMap
import entity_factories
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


max_items_by_floor = [
    (1, 1),
    (4, 2),
]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [
        (entity_factories.health_potion, 35),
        (entity_factories.strength_potion, 50),
        (entity_factories.defense_potion, 50),
        (entity_factories.shockwave_scroll, 50),
    ],
    2: [
        (entity_factories.confusion_scroll, 10),
        (entity_factories.ice_bomb, 20),
        (entity_factories.arrow_scroll, 25),
    ],
    4: [
        (entity_factories.lightning_scroll, 25),
        (entity_factories.sword, 5),
        (entity_factories.shockwave_scroll, 20),
        (entity_factories.cross_blast_scroll, 15),
    ],
    6: [
        (entity_factories.fireball_scroll, 25),
        (entity_factories.chain_mail, 15),
        (entity_factories.diagonal_blast_scroll, 15),
    ],
}

enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80), (entity_factories.goblin_archer, 40)],
    3: [(entity_factories.troll, 15), (entity_factories.goblin_archer, 40)],
    5: [(entity_factories.troll, 30), (entity_factories.dragon, 5)],
    7: [(entity_factories.troll, 60), (entity_factories.demon, 10)],
}

class RoomTheme:
    DUNGEON = "dungeon"
    CAVE = "cave"
    TEMPLE = "temple"
    CRYPT = "crypt"
    GARDEN = "garden"


def get_max_value_for_floor(max_value_by_floor: List[Tuple[int, int]], floor: int) -> int:
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value


def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
    number_of_entities: int,
    floor: int,
) -> List[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(entities, weights=entity_weighted_chance_values, k=number_of_entities)

    return chosen_entities


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        self.theme = random.choice([
            RoomTheme.DUNGEON,
            RoomTheme.CAVE,
            RoomTheme.TEMPLE,
            RoomTheme.CRYPT,
            RoomTheme.GARDEN
        ])

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        return self.x1 <= other.x2 and self.x2 >= other.x1 and self.y1 <= other.y2 and self.y2 >= other.y1


def decorate_room(room: RectangularRoom, dungeon: GameMap) -> None:
    """Add decorative elements based on room theme."""

    if room.theme == RoomTheme.TEMPLE:
        # Add pillars in corners
        for x, y in [(room.x1 + 2, room.y1 + 2), (room.x2 - 2, room.y1 + 2),
                     (room.x1 + 2, room.y2 - 2), (room.x2 - 2, room.y2 - 2)]:
            if dungeon.in_bounds(x, y):
                dungeon.tiles[x, y] = tile_types.pillar

        # Maybe add altar in center
        if random.random() < 0.3:
            cx, cy = room.center
            if dungeon.in_bounds(cx, cy):
                dungeon.tiles[cx, cy] = tile_types.altar

    elif room.theme == RoomTheme.CRYPT:
        # Cracked floors
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                if random.random() < 0.3:
                    dungeon.tiles[x, y] = tile_types.cracked_floor

        # Random statues
        if random.random() < 0.4:
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            dungeon.tiles[x, y] = tile_types.statue

    elif room.theme == RoomTheme.GARDEN:
        # Grass floor
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                if random.random() < 0.6:
                    dungeon.tiles[x, y] = tile_types.grass

        # Small water features
        if random.random() < 0.3:
            wx = random.randint(room.x1 + 2, room.x2 - 2)
            wy = random.randint(room.y1 + 2, room.y2 - 2)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dungeon.in_bounds(wx + dx, wy + dy):
                        dungeon.tiles[wx + dx, wy + dy] = tile_types.shallow_water

    elif room.theme == RoomTheme.CAVE:
        # Stone floor with variation
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                if random.random() < 0.5:
                    dungeon.tiles[x, y] = tile_types.stone_floor


def place_lake(room: RectangularRoom, dungeon: GameMap, chance: float = 0.2):
    """Create water features with bridges."""
    if random.random() > chance:
        return

    lake_width = random.randint(3, min(6, (room.x2 - room.x1) // 2))
    lake_height = random.randint(3, min(6, (room.y2 - room.y1) // 2))

    lake_x = random.randint(room.x1 + 1, room.x2 - lake_width - 1)
    lake_y = random.randint(room.y1 + 1, room.y2 - lake_height - 1)

    # Create lake
    for x in range(lake_x, lake_x + lake_width):
        for y in range(lake_y, lake_y + lake_height):
            if dungeon.in_bounds(x, y):
                # Deep water in center, shallow at edges
                dist_from_edge = min(x - lake_x, lake_x + lake_width - x - 1,
                                    y - lake_y, lake_y + lake_height - y - 1)
                if dist_from_edge > 1:
                    dungeon.tiles[x, y] = tile_types.water
                else:
                    dungeon.tiles[x, y] = tile_types.shallow_water

    # Add a bridge across
    if random.random() < 0.7:
        bridge_y = lake_y + lake_height // 2
        for x in range(lake_x, lake_x + lake_width):
            if dungeon.in_bounds(x, bridge_y):
                dungeon.tiles[x, bridge_y] = tile_types.bridge


def place_lava_pit(room: RectangularRoom, dungeon: GameMap, chance: float = 0.15):
    """Dangerous lava pits."""
    if random.random() > chance or dungeon.engine.game_world.current_floor < 3:
        return

    pit_size = random.randint(2, 4)
    pit_x = random.randint(room.x1 + 2, room.x2 - pit_size - 2)
    pit_y = random.randint(room.y1 + 2, room.y2 - pit_size - 2)

    for x in range(pit_x, pit_x + pit_size):
        for y in range(pit_y, pit_y + pit_size):
            if dungeon.in_bounds(x, y):
                dungeon.tiles[x, y] = tile_types.lava


def tunnel_between(start: Tuple[int, int], end: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:
        corner_x, corner_y = x2, y1
    else:
        corner_x, corner_y = x1, y2

    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    engine: Engine,
) -> GameMap:
    """Generate an enhanced dungeon map."""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []
    center_of_last_room = (0, 0)

    # Choose wall style for this floor
    wall_type = random.choice([tile_types.wall, tile_types.stone_wall, tile_types.cave_wall])

    for _ in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        new_room = RectangularRoom(x, y, room_width, room_height)

        if any(new_room.intersects(other_room) for other_room in rooms):
            continue

        # Dig out room
        dungeon.tiles[new_room.inner] = tile_types.floor

        # Add decorations
        decorate_room(new_room, dungeon)
        place_lake(new_room, dungeon)
        place_lava_pit(new_room, dungeon)

        if len(rooms) == 0:
            player.place(*new_room.center, dungeon)
        else:
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor
            center_of_last_room = new_room.center

        place_entities(new_room, dungeon, engine.game_world.current_floor)
        place_blacksmith(new_room, dungeon, engine.game_world.current_floor)
        place_boss_room(dungeon, engine.game_world.current_floor)

        rooms.append(new_room)

    # Place stairs
    dungeon.tiles[center_of_last_room] = tile_types.down_stairs
    dungeon.downstairs_location = center_of_last_room

    return dungeon


def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int) -> None:
    number_of_monsters = random.randint(0, get_max_value_for_floor(max_monsters_by_floor, floor_number))
    number_of_items = random.randint(0, get_max_value_for_floor(max_items_by_floor, floor_number))

    monsters: List[Entity] = get_entities_at_random(enemy_chances, number_of_monsters, floor_number)
    items: List[Entity] = get_entities_at_random(item_chances, number_of_items, floor_number)

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not dungeon.tiles["walkable"][x, y]:
            continue

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)

def place_blacksmith(room: RectangularRoom, dungeon: GameMap, floor_number: int) -> None:
    """Place blacksmith in specific rooms on certain floors."""
    if floor_number % 3 != 2:
        return

    if random.random() < 0.3:
        cx, cy = room.center
        if not any(entity.x == cx and entity.y == cy for entity in dungeon.entities):
            entity_factories.blacksmith.spawn(dungeon, cx, cy)
            if dungeon.in_bounds(cx + 1, cy):
                dungeon.tiles[cx + 1, cy] = tile_types.altar

def place_boss_room(dungeon: GameMap, floor_number: int) -> None:
    """Create a special boss room on boss floors."""
    if floor_number % 5 != 0:
        return
    width = random.randint(10, 15)
    height = random.randint(10, 15)
    x = random.randint(dungeon.width - width - 5, dungeon.width - 10)
    y = random.randint(dungeon.height - height - 5, dungeon.height - 10)

    boss_room = RectangularRoom(x, y, width, height)

    dungeon.tiles[boss_room.inner] = tile_types.floor

    cx, cy = boss_room.center

    if floor_number % 10 == 0:
        entity_factories.demon_lord.spawn(dungeon, cx, cy)
    else:
        entity_factories.dragon_boss.spawn(dungeon, cx, cy)

    for _ in range(3):
        tx = random.randint(boss_room.x1 + 2, boss_room.x2 - 2)
        ty = random.randint(boss_room.y1 + 2, boss_room.y2 - 2)

        if not any(entity.x == tx and entity.y == ty for entity in dungeon.entities):
            loot = random.choice([
                entity_factories.greatsword,
                entity_factories.plate_armor,
                entity_factories.dragon_scale,
            ])
            loot.spawn(dungeon, tx, ty)
