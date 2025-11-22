New Additions and Improvements
New Boss Enemy

A dedicated boss entity was added with higher stats, new behavior, and integration into the existing combat system.

Blacksmith NPC

A non-hostile NPC (blacksmith) was added. This character can interact with the player and is placed on the map like any other entity.

Improved Map Visuals

new tile type, colors, and layout were updated to improve readability and overall visual quality of the dungeon map.

New Consumables

Several new consumable items were added:

Strength potion

Defense potion

Ice bomb

Projectile-based consumable

Each item integrates with the existing consumable system and performs its own action when used.

Projectile Logic and Rendering Cleanup

Projectile update logic was removed from the render phase and moved into the new real-time update phase to prevent freezing and ensure smooth movement.

Enemy Timing Adjustments

Enemies now act on a time interval instead of being tied to only the player's actions. This supports the hybrid turn/real-time design.