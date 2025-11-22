from typing import Tuple
import numpy as np

graphic_dt = np.dtype(
    [
        ("ch", np.int32),
        ("fg", "3B"),
        ("bg", "3B"),
    ]
)

tile_dt = np.dtype(
    [
        ("walkable", bool),
        ("transparent", bool),
        ("dark", graphic_dt),
        ("light", graphic_dt),
    ]
)

def new_tile(
    *,
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)

SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

# Regular floor
floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(" "), (255, 255, 255), (50, 50, 150)),
    light=(ord(" "), (255, 255, 255), (200, 180, 50)),
)

# Stone floor (darker variant)
stone_floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("·"), (100, 100, 120), (40, 40, 50)),
    light=(ord("·"), (150, 150, 170), (80, 80, 90)),
)

# Cracked floor
cracked_floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("'"), (120, 100, 80), (45, 45, 140)),
    light=(ord("'"), (180, 160, 140), (190, 170, 40)),
)

# Grass floor
grass = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord('"'), (0, 100, 0), (0, 50, 0)),
    light=(ord('"'), (50, 200, 50), (20, 120, 20)),
)

# Wall variants
wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("#"), (100, 100, 120), (0, 0, 100)),
    light=(ord("#"), (200, 200, 220), (130, 110, 50)),
)

stone_wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("█"), (80, 80, 100), (0, 0, 80)),
    light=(ord("█"), (150, 150, 170), (100, 90, 40)),
)

cave_wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("▓"), (100, 80, 60), (20, 15, 10)),
    light=(ord("▓"), (180, 150, 120), (80, 60, 40)),
)

# Water (dangerous)
water = new_tile(
    walkable=False,
    transparent=True,
    dark=(ord("≈"), (0, 100, 200), (0, 0, 50)),
    light=(ord("≈"), (50, 150, 255), (0, 50, 100)),
)

shallow_water = new_tile(
    walkable=True,  # Can walk through but slows down
    transparent=True,
    dark=(ord("~"), (0, 80, 160), (0, 20, 60)),
    light=(ord("~"), (100, 180, 255), (20, 80, 140)),
)

# Lava
lava = new_tile(
    walkable=False,
    transparent=True,
    dark=(ord("≈"), (200, 50, 0), (100, 0, 0)),
    light=(ord("≈"), (255, 100, 0), (200, 50, 0)),
)

# Bridge
bridge = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("="), (100, 80, 60), (50, 40, 30)),
    light=(ord("="), (180, 150, 120), (120, 100, 80)),
)

# Decorative (walkable)
pillar = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("O"), (150, 150, 150), (30, 30, 30)),
    light=(ord("O"), (220, 220, 220), (100, 100, 100)),
)

altar = new_tile(
    walkable=False,
    transparent=True,
    dark=(ord("π"), (150, 100, 200), (30, 20, 40)),
    light=(ord("π"), (200, 150, 255), (80, 60, 120)),
)

statue = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("♣"), (120, 120, 120), (20, 20, 20)),
    light=(ord("♣"), (200, 200, 200), (80, 80, 80)),
)

# Stairs
down_stairs = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(">"), (0, 0, 100), (50, 50, 150)),
    light=(ord(">"), (255, 255, 255), (200, 180, 50)),
)

up_stairs = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("<"), (0, 0, 100), (50, 50, 150)),
    light=(ord("<"), (255, 255, 255), (200, 180, 50)),
)

# Trap (hidden until triggered)
trap = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("^"), (150, 0, 0), (50, 50, 150)),
    light=(ord("^"), (255, 50, 50), (200, 180, 50)),
)
