# Last Stand

A survival mini-game built with Python and Pygame. Start on an island, expand your territory, gather wood, and defend against pirates and krakens. Build turrets, walls, and boulders, fish for resources, and level up to survive as long as possible!

---

## Requirements
- Python 3.x
- Pygame (`pip install pygame`)

## Installation
1. Clone/download the repository.
2. Ensure `Assets/` folder is in the same directory as `last_stand.py`.
3. Run: `python last_stand.py`

## Gameplay
- **Goal**: Survive by expanding land, gathering wood, and defending against pirates and krakens.
- **Resources**: Wood for boat tiles (3), saplings (1), turrets (3), walls (5/upgrade), fishing rod (50).
- **Score**: Turrets placed + pirates killed + tiles placed + days survived. High score saved in `score.txt`.
- **Mechanics**:
  - **Day/Night (96s cycle)**: Pirates/krakens spawn at night (7pm–7am). Darkness reduces visibility.
  - **Tiles**: Water, land, boat tiles (convert to land in 90s), trees (2–4 wood), saplings (1 wood, grow in 30s), loot (5–10 wood), turrets, walls, boulders, fish.
  - **Pirates**: Spawn at night; rare types (bridge builder, turret breaker, tanky, speedy, explosive). Drop loot (33% if rare).
  - **Krakens**: Nighttime (10% chance, max 3); destroy boat tiles; game over if they reach you.
  - **NPC (Waller)**: Spawns at 50 wood; sells fishing rod (50 wood) or shows fish caught.
  - **Fishing**: Catch fish (5–10 wood) with rod on fish tiles (despawn in 60s).
  - **Leveling**: Player (max 99, damage), turrets (max 99, fire rate/damage), walls (durability).

## Controls
- **WASD**: Move (on land/boat tiles).
- **I**: Toggle help (hints after 0.5s stationary).
- **Mouse Scroll**: Zoom (scale 1–4).
- **Left Click** (within 3 tiles):
  - Water: Boat tile (3 wood, needs land/boat nearby).
  - Land: Plant sapling (1 wood).
  - Loot: 5–10 wood.
  - Tree: 2–4 wood.
  - Sapling: 1 wood.
  - Fish: Cast rod/catch fish.
  - Boulder: Pick up.
  - Pirate: Attack (player level damage).
  - NPC: Buy rod (50 wood) or view fish caught.
  - Boulder/Wall Mode: Place boulder/wall (100 wood).
- **Right Click** (within 3 tiles):
  - Land: Place turret (3 wood).
  - Turret: Refund 3 wood.
  - Boulder: Convert to wall (5 wood, level 1).
  - Wall: Upgrade (5 wood).
  - Boulder/Wall/Fishing Mode: Cancel.
- **SPACE**: Restart (game-over screen).
- **ESC**: Quit.

## Features
- **Graphics**: Tile-based sprites, animated water, minimap (5x5 chunks, night visibility reduction).
- **Effects**: Floating text (wood/XP), explosions, sparks, pirate hats.
- **Audio**: Sound effects (land, sapling, turret); music (morning, afternoon, night, late-night).
- **World**: Chunk-based (16x16 tiles), saved as `.pkl` in `chunks/`. Generated with 5% land, trees (20%), loot (5%), boulders (3%).

## Notes
- Fullscreen, 60 FPS.
- Strategic wall/boulder placement blocks pirates; turrets automate defense.
- Fishing requires timing for catches.
- NPC unlocks late-game fishing.

---