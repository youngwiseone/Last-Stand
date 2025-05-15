"""
Game constants for the Pygame-based island survival game.
Contains all static values like tile sizes, colors, file paths, and game mechanics settings.
"""

import pygame

# --- Paths ---
CHUNK_DIR = "chunks"

# --- Scale Settings ---
SCALE = 2
BASE_SCALE = 2
MIN_SCALE = 1
MAX_SCALE = 4

# --- Tile Settings ---
TILE_SIZE = 32
VIEW_WIDTH = 30
VIEW_HEIGHT = 30
WIDTH = VIEW_WIDTH * TILE_SIZE
HEIGHT = VIEW_HEIGHT * TILE_SIZE

# --- Colors ---
BLUE = (50, 150, 255)
GREEN = (50, 200, 50)
DARK_GREEN = (50, 150, 50)
BROWN = (139, 69, 19)
DARK_GRAY = (80, 80, 80)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
TAN = (210, 180, 140)
LIGHT_GRAY = (200, 200, 200)

# --- Rare Pirate Types and Colors ---
RARE_PIRATE_TYPES = ["bridge_builder", "turret_breaker", "tanky", "speedy", "explosive"]
RARE_TYPE_COLORS = {
    "bridge_builder": pygame.Color(0, 255, 0),  # Green
    "turret_breaker": pygame.Color(255, 255, 0),  # Yellow
    "tanky": pygame.Color(128, 0, 128),  # Purple
    "speedy": pygame.Color(0, 0, 255),  # Blue
    "explosive": pygame.Color(255, 0, 0)  # Red
}

# --- Tile Types ---
WATER, LAND, TREE, SAPLING, WALL, TURRET, BOAT_TILE, USED_LAND, LOOT, BOAT_TILE_STAGE_2, BOAT_TILE_STAGE_3, BOULDER, FISH, STEERING_WHEEL = range(14)

# --- Movement and Land Tiles ---
MOVEMENT_TILES = (BOAT_TILE, BOAT_TILE_STAGE_2, BOAT_TILE_STAGE_3, LAND, USED_LAND, LOOT, SAPLING, TURRET, BOULDER, STEERING_WHEEL)
LAND_TILES = (BOAT_TILE, BOAT_TILE_STAGE_2, BOAT_TILE_STAGE_3, LAND, USED_LAND, LOOT, SAPLING, TREE, TURRET, BOULDER, STEERING_WHEEL)

# --- Sound Files ---
SOUND_FILES = {
    "place_land": "Assets/sound/place_land.wav",
    "plant_sapling": "Assets/sound/plant_sapling.wav",
    "place_turret": "Assets/sound/place_turret.wav"
}

# --- Music Files ---
MUSIC_FILES = {
    "morning": "Assets/music/Morning.wav",
    "afternoon": "Assets/music/Afternoon.wav",
    "night": "Assets/music/Night.wav",
    "late_night": "Assets/music/Late_night.wav"
}

# --- Tile Image Files ---
TILE_IMAGE_FILES = {
    "WATER": "Assets/water.png",
    "LAND": "Assets/land.png",
    "TREE": "Assets/tree.png",
    "SAPLING": "Assets/sapling.png",
    "WALL": "Assets/wall.png",
    "TURRET": "Assets/turret.png",
    "BOAT_TILE": "Assets/boat_tile.png",
    "USED_LAND": "Assets/used_land.png",
    "UNDER_LAND": "Assets/under_land.png",
    "UNDER_WOOD": "Assets/under_wood.png",
    "LOOT": "Assets/loot.png",
    "BOAT_TILE_STAGE_2": "Assets/boat_tile2.png",
    "BOAT_TILE_STAGE_3": "Assets/boat_tile3.png",
    "WALL_TOP": "Assets/wall_top.png",
    "BOULDER": "Assets/boulder.png",
    "FISHING_ROD": "Assets/fishing_rod.png",
    "FISH": "Assets/fish.png",
    "BOBBER": "Assets/bobber.png",
    "BOBBER2": "Assets/bobber2.png",
    "BOBBER3": "Assets/bobber3.png",
    "KRAKEN": "Assets/kraken.png",
    "STEERING_WHEEL": "Assets/steering_wheel.png",
    "ARROW": "Assets/arrow.png",
    "PLAYER": "Assets/player.png",
    "PLAYER_FISHING": "Assets/player_fishing.png",
    "NPC_WALLER": "Assets/npc_waller.png"
}

# --- Water Animation Frames ---
WATER_FRAME_FILES = [
    "Assets/water.png",
    "Assets/water1.png",
    "Assets/water2.png"
]

# --- Pirate Sprite Files ---
PIRATE_SPRITE_FILES = {
    "base": "Assets/pirate/pirate.png"
}
for level in range(1, 11):
    PIRATE_SPRITE_FILES[f"level_{level}"] = f"Assets/pirate/pirate{level}.png"

# --- Pirate Hat Image Files ---
PIRATE_HAT_IMAGE_FILES = {
    level: f"Assets/pirate/pirate_hat{level}.png" for level in range(1, 11)
}

# --- Kraken Settings ---
KRAKEN_SPAWN_CHANCE = 0.50  # 50% chance per night spawn cycle
KRAKEN_MOVE_SPEED = 0.05  # Same as pirate ship speed
KRAKEN_DESTROY_DELAY = 1000  # 1 second to destroy a boat tile
KRAKEN_LIMIT = 3  # Maximum number of krakens allowed at once
KRAKEN_DESPAWN_DELAY = 2000  # 2 seconds between kraken spawns

# --- Game Timing ---
WATER_FRAME_DELAY = 1200  # Water animation frame delay
FISH_SPAWN_INTERVAL = 1000  # 1 second
FISH_DESPAWN_TIME = 60000  # 1 minute in milliseconds
SAPLING_GROWTH_TIME = 30000  # 30 seconds
LAND_SPREAD_TIME = 30000  # 30 seconds
SPAWN_DELAY = 3000  # Pirate spawn delay
PIRATE_WALK_DELAY = 300  # Pirate movement delay
MUSIC_FADE_DURATION = 1000  # 1 second fade-out
BOBBER_SPEED = 0.1  # Speed of bobber movement
BITE_DURATION = 1000  # Duration of a fish bite
STATIONARY_DELAY = 500  # Delay before interaction UI appears
BASE_TURRET_FIRE_RATE = 1000  # Base turret fire rate
MUSIC_VOLUME = 0.5  # Music volume level

# --- Game Mechanics ---
CHUNK_SIZE = 16  # Each chunk is 16x16 tiles
VIEW_CHUNKS = 5  # Load a 5x5 chunk grid around the player
TURRET_RANGE = 4  # Turret attack range
TURRET_MAX_LEVEL = 99  # Maximum turret level
PLAYER_MAX_LEVEL = 99  # Maximum player level
PROJECTILE_SPEED = 0.2  # Base projectile speed
PLAYER_MOVE_DELAY = 150  # Player movement delay
MAX_FISH_TILES = 3  # Maximum fish tiles at a time

# --- UI Settings ---
INTERACTION_FADE_DURATION = 500  # Interaction UI fade duration