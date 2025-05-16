# Game constants for the Pygame-based island survival game.
# Contains all static values such as tile sizes, colors, file paths, and game mechanics settings.
# Organized into logical sections for readability and maintenance.

import pygame
from enum import IntEnum

# --- Paths ---
CHUNK_DIR = "chunks"  # Directory for storing chunk data files

# --- Chunk generation settings ---
LAND_FRACTION = 0.05  # 5% of chunk tiles are land
MIN_LAND_MASS_SIZE = 8
MAX_LAND_MASS_SIZE = 20
TREE_CHANCE = 0.2
LOOT_CHANCE = 0.05
BOULDER_CHANCE = 0.03
STARTING_AREA_LAND_MIN = 10
STARTING_AREA_LAND_MAX = 16
STARTING_AREA_FEATURES_MIN = 1
STARTING_AREA_FEATURES_MAX = 3
SAVE_CHUNK_INTERVAL = 5000

# --- Scale Settings ---
SCALE = 2  # Current scaling factor for game rendering (pixels per tile)
BASE_SCALE = 2  # Default scaling factor for speed and rendering calculations
MIN_SCALE = 1  # Minimum allowed scale for zooming out
MAX_SCALE = 4  # Maximum allowed scale for zooming in

# --- Tile Settings ---
TILE_SIZE = 32  # Size of each tile in pixels
VIEW_WIDTH = 30  # Number of tiles in the viewable width
VIEW_HEIGHT = 30  # Number of tiles in the viewable height
WIDTH = VIEW_WIDTH * TILE_SIZE  # Screen width in pixels
HEIGHT = VIEW_HEIGHT * TILE_SIZE  # Screen height in pixels

# --- Colors ---
# RGB color tuples for rendering game elements. Used for tiles, UI, and visual effects.
BLUE = (50, 150, 255)  # Color for water tiles
GREEN = (50, 200, 50)  # Color for land tiles
DARK_GREEN = (50, 150, 50)  # Color for trees
BROWN = (139, 69, 19)  # Color for walls
DARK_GRAY = (80, 80, 80)  # Color for turrets
WHITE = (255, 255, 255)  # Color for text and highlights
BLACK = (0, 0, 0)  # Color for backgrounds and overlays
YELLOW = (255, 255, 0)  # Color for loot and XP text
RED = (255, 0, 0)  # Color for damage and explosive pirates
ORANGE = (255, 165, 0)  # Color for sparks and effects
TAN = (210, 180, 140)  # Color for boat tiles
LIGHT_GRAY = (200, 200, 200)  # Color for used land tiles

# --- Rare Pirate Types and Colors ---
# Rare pirate types and their associated overlay colors for visual distinction.
# Each type has a unique behavior (e.g., bridge_builder places boat tiles).
RARE_PIRATE_TYPES = ["bridge_builder", "turret_breaker", "tanky", "speedy", "explosive"]  # List of rare pirate behaviors
RARE_TYPE_COLORS = {
    "bridge_builder": pygame.Color(0, 255, 0),  # Green: Pirates that place boat tiles
    "turret_breaker": pygame.Color(255, 255, 0),  # Yellow: Pirates that destroy turrets
    "tanky": pygame.Color(128, 0, 128),  # Purple: Pirates with double health
    "speedy": pygame.Color(0, 0, 255),  # Blue: Pirates with faster movement
    "explosive": pygame.Color(255, 0, 0)  # Red: Pirates that explode on proximity
}

# --- Tile Types ---
# Enum for tile types in the game world. Each represents a distinct tile with specific behavior or appearance.
class Tile(IntEnum):
    WATER = 0  # Water tile, impassable without boat
    LAND = 1  # Basic land tile for building
    TREE = 2  # Tree tile, yields wood when chopped
    SAPLING = 3  # Sapling tile, grows into tree
    WALL = 4  # Wall tile, blocks movement
    TURRET = 5  # Turret tile, attacks pirates
    BOAT = 6  # Boat tile, allows movement over water
    USED_LAND = 7  # Land tile after resource use
    LOOT = 8  # Loot tile, yields wood when collected
    BOAT_STAGE_2 = 9  # Boat tile transitioning to land (stage 2)
    BOAT_STAGE_3 = 10  # Boat tile transitioning to land (stage 3)
    BOULDER = 11  # Boulder tile, can be moved or converted
    FISH = 12  # Fish tile, can be caught for wood
    STEERING_WHEEL = 13  # Steering wheel tile for boat control

# --- Movement and Land Tiles ---
# Tile sets defining valid tiles for movement and boat tile adjacency. Used for pathfinding and placement rules.
MOVEMENT_TILES = (
    Tile.BOAT, Tile.BOAT_STAGE_2, Tile.BOAT_STAGE_3, Tile.LAND,
    Tile.USED_LAND, Tile.LOOT, Tile.SAPLING, Tile.TURRET,
    Tile.BOULDER, Tile.STEERING_WHEEL
)  # Tiles that entities can move onto
LAND_TILES = (
    Tile.BOAT, Tile.BOAT_STAGE_2, Tile.BOAT_STAGE_3, Tile.LAND,
    Tile.USED_LAND, Tile.LOOT, Tile.SAPLING, Tile.TREE,
    Tile.TURRET, Tile.BOULDER, Tile.STEERING_WHEEL
)  # Tiles considered adjacent for boat placement

# --- Sound Files ---
# File paths for sound effects played during gameplay actions.
SOUND_FILES = {
    "place_land": "Assets/sound/place_land.wav",  # Sound for placing boat tiles
    "plant_sapling": "Assets/sound/plant_sapling.wav",  # Sound for planting saplings
    "place_turret": "Assets/sound/place_turret.wav"  # Sound for placing turrets
}

# --- Music Files ---
# File paths for background music tracks played during different times of day.
MUSIC_FILES = {
    "morning": "Assets/music/Morning.wav",  # Music for morning (7am–1pm)
    "afternoon": "Assets/music/Afternoon.wav",  # Music for afternoon (1pm–7pm)
    "night": "Assets/music/Night.wav",  # Music for night (7pm–1am)
    "late_night": "Assets/music/Late_night.wav"  # Music for late night (1am–7am)
}

# --- Tile Image Files ---
# File paths for tile and sprite images used in rendering.
# Keys are tile types or special identifiers (e.g., 'PLAYER', 'FISHING_ROD').
TILE_IMAGE_FILES = {
    "WATER": "Assets/water.png",  # Image for water tiles
    "LAND": "Assets/land.png",  # Image for land tiles
    "TREE": "Assets/tree.png",  # Image for tree tiles
    "SAPLING": "Assets/sapling.png",  # Image for sapling tiles
    "WALL": "Assets/wall.png",  # Image for wall tiles
    "TURRET": "Assets/turret.png",  # Image for turret tiles
    "BOAT_TILE": "Assets/boat_tile.png",  # Image for boat tiles
    "USED_LAND": "Assets/used_land.png",  # Image for used land tiles
    "UNDER_LAND": "Assets/under_land.png",  # Image for land underlay
    "UNDER_WOOD": "Assets/under_wood.png",  # Image for boat tile underlay
    "LOOT": "Assets/loot.png",  # Image for loot tiles
    "BOAT_TILE_STAGE_2": "Assets/boat_tile2.png",  # Image for boat tile stage 2
    "BOAT_TILE_STAGE_3": "Assets/boat_tile3.png",  # Image for boat tile stage 3
    "WALL_TOP": "Assets/wall_top.png",  # Image for top of stacked walls
    "BOULDER": "Assets/boulder.png",  # Image for boulder tiles
    "FISHING_ROD": "Assets/fishing_rod.png",  # Image for fishing rod
    "FISH": "Assets/fish.png",  # Image for fish tiles
    "BOBBER": "Assets/bobber.png",  # Image for fishing bobber (default)
    "BOBBER2": "Assets/bobber2.png",  # Image for fishing bobber (waiting)
    "BOBBER3": "Assets/bobber3.png",  # Image for fishing bobber (biting)
    "KRAKEN": "Assets/kraken.png",  # Image for kraken entity
    "STEERING_WHEEL": "Assets/steering_wheel.png",  # Image for steering wheel tile
    "ARROW": "Assets/arrow.png",  # Image for steering direction arrow
    "PLAYER": "Assets/player.png",  # Image for player sprite
    "PLAYER_FISHING": "Assets/player_fishing.png",  # Image for player fishing sprite
    "NPC_WALLER": "Assets/npc_waller.png",  # Image for waller NPC sprite
    "NPC_TRADER": "assets/npc_trader.png"  # Add Trader sprite
}

# --- Water Animation Frames ---
# File paths for water animation frames used in rendering water tiles.
WATER_FRAME_FILES = [
    "Assets/water.png",  # Default water frame
    "Assets/water1.png",  # Water animation frame 1
    "Assets/water2.png"  # Water animation frame 2
]

# --- Pirate Sprite Files ---
# File paths for pirate sprites, including base and level-specific variants.
PIRATE_SPRITE_FILES = {
    "base": "Assets/pirate/pirate.png"  # Base pirate sprite (hatless)
}
for level in range(1, 11):
    PIRATE_SPRITE_FILES[f"level_{level}"] = f"Assets/pirate/pirate{level}.png"  # Pirate sprite for level {level}

# --- Pirate Hat Image Files ---
# File paths for pirate hat sprites, corresponding to pirate levels.
PIRATE_HAT_IMAGE_FILES = {
    level: f"Assets/pirate/pirate_hat{level}.png" for level in range(1, 11)  # Hat sprite for level {level}
}

# --- Kraken Settings ---
# Settings for kraken entity behavior and spawning.
KRAKEN_SPAWN_CHANCE = 0.50  # Probability of kraken spawning per night cycle (50%)
KRAKEN_MOVE_SPEED = 0.05  # Movement speed in tiles per frame
KRAKEN_DESTROY_DELAY = 1000  # Time to destroy a boat tile (milliseconds)
KRAKEN_LIMIT = 3  # Maximum number of krakens active simultaneously
KRAKEN_DESPAWN_DELAY = 2000  # Time before despawning if no boat tiles found (milliseconds)

# --- Game Timing ---
# Timing constants for animations, spawning, and game mechanics (in milliseconds unless specified).
WATER_FRAME_DELAY = 1200  # Delay between water animation frames
FISH_SPAWN_INTERVAL = 1000  # Interval for spawning fish tiles
FISH_DESPAWN_TIME = 60000  # Time before fish tiles despawn
SAPLING_GROWTH_TIME = 30000  # Time for saplings to grow into trees
LAND_SPREAD_TIME = 30000  # Time for boat tiles to convert to land
SPAWN_DELAY = 3000  # Delay between pirate spawns
PIRATE_WALK_DELAY = 300  # Delay between pirate movements
MUSIC_FADE_DURATION = 1000  # Duration of music fade-out
BOBBER_SPEED = 0.1  # Bobber movement speed in tiles per frame
BITE_DURATION = 1000  # Duration of a fish bite during fishing
STATIONARY_DELAY = 500  # Delay before interaction UI appears
BASE_TURRET_FIRE_RATE = 1000  # Base time between turret shots
MUSIC_VOLUME = 0.5  # Music volume level (0.0 to 1.0)

# --- Game Mechanics ---
# Constants controlling core gameplay mechanics and balance.
CHUNK_SIZE = 16  # Size of each chunk in tiles (16x16)
VIEW_CHUNKS = 5  # Number of chunks loaded around the player (5x5 grid)
TURRET_RANGE = 4  # Range of turret attacks in tiles
TURRET_MAX_LEVEL = 99  # Maximum level for turret upgrades
PLAYER_MAX_LEVEL = 99  # Maximum level for player progression
PROJECTILE_SPEED = 0.2  # Base speed of turret projectiles in tiles per frame
PLAYER_MOVE_DELAY = 150  # Delay between player movement inputs (milliseconds)
MAX_FISH_TILES = 3  # Maximum number of fish tiles active at once

# --- UI Settings ---
# Constants for user interface behavior and rendering.
INTERACTION_FADE_DURATION = 500  # Duration of interaction UI fade-in/out (milliseconds)