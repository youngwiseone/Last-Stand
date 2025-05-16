import pygame
import random
import sys
import math
import os
import subprocess
import pickle
from constants import *
from world import World

# --- Init ---
pygame.init()
pygame.mixer.init()

def adjust_sprite_for_rare(sprite, rare_type):
    """Overlay a color specific to rare_type at 50% opacity, preserving alpha."""
    new_sprite = sprite.copy()
    pixel_array = pygame.PixelArray(new_sprite)
    overlay_color = RARE_TYPE_COLORS[rare_type]  # Get color for rare type
    overlay_alpha = 0.5  # 50% opacity
    for x in range(new_sprite.get_width()):
        for y in range(new_sprite.get_height()):
            color = new_sprite.unmap_rgb(pixel_array[x, y])
            if color.a == 0:  # Skip transparent pixels
                continue
            # Blend original color with overlay color at 50% opacity
            new_r = int(color.r * (1 - overlay_alpha) + overlay_color.r * overlay_alpha)
            new_g = int(color.g * (1 - overlay_alpha) + overlay_color.g * overlay_alpha)
            new_b = int(color.b * (1 - overlay_alpha) + overlay_color.b * overlay_alpha)
            # Preserve original alpha
            new_color = pygame.Color(new_r, new_g, new_b, color.a)
            pixel_array[x, y] = new_color
    del pixel_array
    return new_sprite

# --- Screen Setup ---
view_left = 0
view_top = 0
view_right = 0
view_bottom = 0
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()

xp_texts = []
explosions = []
sparks = []
hat_particles = []

# --- Sounds ---
sound_place_land = pygame.mixer.Sound(SOUND_FILES["place_land"])
sound_plant_sapling = pygame.mixer.Sound(SOUND_FILES["plant_sapling"])
sound_place_turret = pygame.mixer.Sound(SOUND_FILES["place_turret"])

# --- Music ---
pygame.mixer.music.set_volume(MUSIC_VOLUME)

# --- Load Tile Images ---
tile_images = {
    Tile.WATER: pygame.image.load(TILE_IMAGE_FILES["WATER"]).convert(),
    Tile.LAND: pygame.image.load(TILE_IMAGE_FILES["LAND"]).convert(),
    Tile.TREE: pygame.image.load(TILE_IMAGE_FILES["TREE"]).convert_alpha(),
    Tile.SAPLING: pygame.image.load(TILE_IMAGE_FILES["SAPLING"]).convert_alpha(),
    Tile.WALL: pygame.image.load(TILE_IMAGE_FILES["WALL"]).convert(),
    Tile.TURRET: pygame.image.load(TILE_IMAGE_FILES["TURRET"]).convert_alpha(),
    Tile.BOAT: pygame.image.load(TILE_IMAGE_FILES["BOAT_TILE"]).convert(),
    Tile.USED_LAND: pygame.image.load(TILE_IMAGE_FILES["USED_LAND"]).convert(),
    "UNDER_LAND": pygame.image.load(TILE_IMAGE_FILES["UNDER_LAND"]).convert_alpha(),
    "UNDER_WOOD": pygame.image.load(TILE_IMAGE_FILES["UNDER_WOOD"]).convert_alpha(),
    Tile.LOOT: pygame.image.load(TILE_IMAGE_FILES["LOOT"]).convert_alpha(),
    Tile.BOAT_STAGE_2: pygame.image.load(TILE_IMAGE_FILES["BOAT_TILE_STAGE_2"]).convert(),
    Tile.BOAT_STAGE_3: pygame.image.load(TILE_IMAGE_FILES["BOAT_TILE_STAGE_3"]).convert(),
    "WALL_TOP": pygame.image.load(TILE_IMAGE_FILES["WALL_TOP"]).convert(),
    Tile.BOULDER: pygame.image.load(TILE_IMAGE_FILES["BOULDER"]).convert_alpha(),
    "FISHING_ROD": pygame.image.load(TILE_IMAGE_FILES["FISHING_ROD"]).convert_alpha(),
    Tile.FISH: pygame.image.load(TILE_IMAGE_FILES["FISH"]).convert_alpha(),
    "BOBBER": pygame.image.load(TILE_IMAGE_FILES["BOBBER"]).convert_alpha(),
    "BOBBER2": pygame.image.load(TILE_IMAGE_FILES["BOBBER2"]).convert_alpha(),
    "BOBBER3": pygame.image.load(TILE_IMAGE_FILES["BOBBER3"]).convert_alpha(),
    "KRAKEN": pygame.transform.scale(pygame.image.load(TILE_IMAGE_FILES["KRAKEN"]).convert_alpha(), (TILE_SIZE, TILE_SIZE)),
    Tile.STEERING_WHEEL: pygame.image.load(TILE_IMAGE_FILES["STEERING_WHEEL"]).convert_alpha(),
    "ARROW": pygame.image.load(TILE_IMAGE_FILES["ARROW"]).convert_alpha(),
}

player_image = pygame.image.load(TILE_IMAGE_FILES["PLAYER"]).convert_alpha()
player_fishing_image = pygame.image.load(TILE_IMAGE_FILES["PLAYER_FISHING"]).convert_alpha()
fish_spawn_timer = 0

# --- Water Animation Frames ---
water_frames = [pygame.image.load(frame).convert() for frame in WATER_FRAME_FILES]
water_frame = 0
water_frame_timer = 0

# --- Load Pirate Sprites ---
pirate_sprites = {
    "base": pygame.image.load(PIRATE_SPRITE_FILES["base"]).convert_alpha()
}
for level in range(1, 11):
    pirate_sprites[f"level_{level}"] = pygame.image.load(PIRATE_SPRITE_FILES[f"level_{level}"]).convert_alpha()
for rare_type in RARE_PIRATE_TYPES:
    pirate_sprites[f"base_{rare_type}"] = adjust_sprite_for_rare(
        pygame.image.load(PIRATE_SPRITE_FILES["base"]).convert_alpha(), rare_type
    )
    for level in range(1, 11):
        pirate_sprites[f"level_{level}_{rare_type}"] = adjust_sprite_for_rare(
            pygame.image.load(PIRATE_SPRITE_FILES[f"level_{level}"]).convert_alpha(), rare_type
        )

# --- Load Pirate Hat Images ---
pirate_hat_images = {
    level: pygame.image.load(PIRATE_HAT_IMAGE_FILES[level]).convert_alpha() for level in range(1, 11)
}

# --- Pre-Scale Images ---
scaled_tile_images = {}
for key, image in tile_images.items():
    scaled_tile_images[key] = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))

scaled_water_frames = [pygame.transform.scale(frame, (TILE_SIZE, TILE_SIZE)) for frame in water_frames]
scaled_tile_images[Tile.WATER] = scaled_water_frames[water_frame]

scaled_player_image = pygame.transform.scale(player_image, (TILE_SIZE, TILE_SIZE))
scaled_player_fishing_image = pygame.transform.scale(player_fishing_image, (TILE_SIZE, TILE_SIZE))

scaled_pirate_sprites = {}
for key, sprite in pirate_sprites.items():
    scaled_pirate_sprites[key] = pygame.transform.scale(sprite, (TILE_SIZE, TILE_SIZE))

scaled_pirate_hat_images = {}
for level, hat_image in pirate_hat_images.items():
    scaled_pirate_hat_images[level] = pygame.transform.scale(hat_image, (TILE_SIZE, TILE_SIZE))

scaled_waller_npc_sprite = pygame.transform.scale(
    pygame.image.load(TILE_IMAGE_FILES["NPC_WALLER"]).convert_alpha(), (TILE_SIZE, TILE_SIZE)
)
    

# Load high score
try:
    with open("score.txt", "r") as f:
        high_score = int(f.read())
except:
    high_score = 0

def get_speed_multiplier():
    """Calculate speed multiplier based on current SCALE relative to BASE_SCALE."""
    base_multiplier = SCALE / BASE_SCALE
    # Apply a minimum multiplier for SCALE = 1 to avoid being too slow
    return max(0.75, base_multiplier) if SCALE == 1 else base_multiplier

def get_music_period(game_time):
    cycle = 96.0  # Total cycle length
    t = game_time % cycle
    if 28 <= t < 52:
        return "morning"  # 7am–1pm
    elif 52 <= t < 76:
        return "afternoon"  # 1pm–7pm
    elif (76 <= t < 96) or (0 <= t < 4):
        return "night"  # 7pm–1am
    else:  # 4 <= t < 28
        return "late_night"  # 1am–7am

# --- world Setup ---
world = World()
world.clear_chunk_files()
world.initialize_starting_area()

# --- Game State ---
selected_tile = None  # Will store the (x, y) of the tile under the mouse
game_time = 28.0  # 6am is 24.0, 7am is 28.0, 8am is 32.0, etc.
minimap_base_cache = None  # Cached base layer of the minimap (tiles only)
minimap_cache_valid = False  # Flag to indicate if the cache needs to be updated
last_player_chunk = world.player_chunk  # Track the last chunk to detect movement
chunks_version = 0  # Version counter for tracking changes to chunks
last_chunks_version = 0  # Last version seen by the minimap

current_music = None  # Tracks the current music period ("morning", "afternoon", "night", "late_night")
music_fade_timer = 0  # Timer for fading out music
music_fade_duration = 1000  # 1 second fade-out

turrets_placed = 0
pirates_killed = 0
tiles_placed = 0
days_survived = 0  # Number of days survived
last_cycle_time = 0.0  # Track time of last cycle completion

player_level = 1  # Starting level
player_xp = 0  # Current XP
player_max_level = 99  # Same as turret max level
player_xp_texts = []  # Floating text for XP gains

game_over = False
kraken_game_over = False
fade_done = False
player_pos = [0.0, 0.0]  # Now in world coordinates with floating-point precision
wood = 5
selected_block = Tile.LAND
player_move_timer = 0
player_move_delay = 150
facing = [0, -1]
interaction_ui_enabled = False

has_fishing_rod = False  # Tracks if player has the fishing rod
fish_tiles = []  # List of active fish tiles: {"x": x, "y": y, "spawn_time": time}
fish_caught = 0  # Total fish caught by player
fishing_state = None  # None, "casting", or "fishing"
bobber = None  # Bobber state: {"x": x, "y": y, "target_x": x, "target_y": y, "state": "moving"/"waiting"/"biting", "bite_timer": time, "last_switch": time}
max_fish_tiles = 3  # Maximum fish tiles at a time
fish_despawn_time = 60000  # 1 minute in milliseconds
bobber_speed = 0.1  # Speed of bobber movement (tiles per frame)
bite_interval = random.uniform(2000, 5000)  # Random interval for fish bites (2–5 seconds)
bite_duration = 1000  # Duration of a fish bite (1 second)
boat_entity = None  # {"steering_pos": (x, y), "tiles": [(x, y), ...], "state": "idle"/"steering"/"moving", "direction": (dx, dy)}
steering_interaction = False  # True when interacting with steering wheel
in_boat_mode = False

last_player_pos = list(player_pos)
stationary_timer = 0
STATIONARY_DELAY = 500

krakens = []  # List to store Kraken entities

interaction_ui = {
    "left_message": "",
    "right_message": "",
    "alpha": 0,
    "offset": 20,
    "fade_timer": 0,
    "fade_duration": 500
}

wood_texts = []  # List to store floating wood gain texts

turret_cooldowns = {}
turret_levels = {}
turret_xp = {}
BASE_TURRET_FIRE_RATE = 1000
TURRET_MAX_LEVEL = 99
TURRET_RANGE = 4

projectiles = []
projectile_speed = 0.2

tree_growth = {}
sapling_growth_time = 30000

land_spread = {}
land_spread_time = 30000

pirates = []
pirate_spawn_timer = 0
spawn_delay = 3000
pirate_walk_delay = 300

wall_levels = {}
wall_damage_timers = {}  # Track last time each wall was damaged

npcs = []  # List to store NPCs
waller_npc_spawned = False  # Flag to ensure NPC spawns only once
wall_placement_mode = False  # Tracks if player is in wall placement mode
boulder_placement_mode = False  # Tracks if player is in boulder placement mode
picked_boulder_pos = None  # Stores the position of the picked-up boulder

game_surface = pygame.Surface((WIDTH, HEIGHT))

# Start initial music
current_music = get_music_period(game_time)
pygame.mixer.music.load(MUSIC_FILES[current_music])
pygame.mixer.music.play(-1)  # Loop indefinitely

# --- Drawing ---
def draw_grid():
    global game_surface
    top_left_x = player_pos[0] - VIEW_WIDTH / 2.0
    top_left_y = player_pos[1] - VIEW_HEIGHT / 2.0
    start_x, start_y = view_left, view_top

    darkness_factor = get_darkness_factor(game_time)

    # Compute brightness map
    brightness = [[0.0 for _ in range(VIEW_WIDTH)] for _ in range(VIEW_HEIGHT)]
    light_source_tiles = set()

    # Collect light sources
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = start_x + x, start_y + y
            if world.get_tile(gx, gy) in [Tile.TURRET, Tile.WALL]:
                light_source_tiles.add((gx, gy))

    player_tile = (int(player_pos[0] + 0.5), int(player_pos[1] + 0.5))
    light_source_tiles.add(player_tile)

    for dx in range(-3, 4):
        for dy in range(-3, 4):
            dist = abs(dx) + abs(dy)
            if dist <= 3:
                nx, ny = player_tile[0] + dx, player_tile[1] + dy
                local_nx = nx - start_x
                local_ny = ny - start_y
                if 0 <= local_nx < VIEW_WIDTH and 0 <= local_ny < VIEW_HEIGHT:
                    b = 0.9 if dist == 0 else 0.6 if dist == 1 else 0.4 if dist == 2 else 0.2
                    brightness[local_ny][local_nx] = max(brightness[local_ny][local_nx], b)

    for npc in npcs:
        for s in npc["ship"]:
            npc_tile = (int(s["x"] + 0.5), int(s["y"] + 0.5))
            light_source_tiles.add(npc_tile)

    for sx, sy in light_source_tiles:
        local_x = sx - start_x
        local_y = sy - start_y
        if 0 <= local_x < VIEW_WIDTH and 0 <= local_y < VIEW_HEIGHT:
            brightness[local_y][local_x] = max(brightness[local_y][local_x], 0.9)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = sx + dx, sy + dy
            local_nx = nx - start_x
            local_ny = ny - start_y
            if 0 <= local_nx < VIEW_WIDTH and 0 <= local_ny < VIEW_HEIGHT:
                brightness[local_ny][local_nx] = max(brightness[local_ny][local_nx], 0.5)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nx, ny = sx + dx, sy + dy
            local_nx = nx - start_x
            local_ny = ny - start_y
            if 0 <= local_nx < VIEW_WIDTH and 0 <= local_ny < VIEW_HEIGHT:
                brightness[local_ny][local_nx] = max(brightness[local_ny][local_nx], 0.33)

    # First pass: Render base tiles without darkness
    now = pygame.time.get_ticks()
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = start_x + x, start_y + y
            tile = world.get_tile(gx, gy)
            px = (x - (top_left_x - start_x)) * TILE_SIZE
            py = (y - (top_left_y - start_y)) * TILE_SIZE
            rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
            if tile == Tile.FISH:
                game_surface.blit(scaled_tile_images[Tile.WATER], rect)
                fish_image = scaled_tile_images[Tile.FISH].copy()
                fish_data = next((f for f in fish_tiles if f["x"] == gx and f["y"] == gy), None)
                if fish_data:
                    time_left = fish_despawn_time - (now - fish_data["spawn_time"])
                    alpha = 255 if time_left > 5000 else int(255 * (time_left / 5000))
                    fish_image.set_alpha(alpha)
                game_surface.blit(fish_image, rect)
            else:
                image = scaled_tile_images.get(tile)
                if image:
                    game_surface.blit(image, rect)
                else:
                    pygame.draw.rect(game_surface, BLACK, rect)

    # Second pass: Render underlay tiles without darkness
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = start_x + x, start_y + y
            below_y = gy + 1
            below_tile = world.get_tile(gx, below_y)
            if below_tile == Tile.WATER:
                px = (x - (top_left_x - start_x)) * TILE_SIZE
                py = (y + 1 - (top_left_y - start_y)) * TILE_SIZE
                under_rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
                tile = world.get_tile(gx, gy)
                if tile in [Tile.LAND, Tile.TURRET, Tile.USED_LAND, Tile.SAPLING, Tile.TREE, Tile.LOOT]:
                    under_land_image = scaled_tile_images.get("UNDER_LAND")
                    if under_land_image:
                        game_surface.blit(under_land_image, under_rect)
                elif tile in [Tile.BOAT, Tile.BOAT_STAGE_2, Tile.BOAT_STAGE_3]:
                    under_wood_image = scaled_tile_images.get("UNDER_WOOD")
                    if under_wood_image:
                        game_surface.blit(under_wood_image, under_rect)

    # Third pass: Render overlay tiles and turret/wall levels
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = start_x + x, start_y + y
            tile = world.get_tile(gx, gy)
            px = (x - (top_left_x - start_x)) * TILE_SIZE
            py = (y - (top_left_y - start_y)) * TILE_SIZE
            rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
            if tile in [Tile.TURRET, Tile.TREE, Tile.SAPLING, Tile.LOOT, Tile.WALL, Tile.BOULDER, Tile.STEERING_WHEEL]:
                # Render the base tile underneath
                if tile == Tile.STEERING_WHEEL:
                    # For STEERING_WHEEL, render BOAT_TILE underneath
                    boat_image = scaled_tile_images.get(Tile.BOAT)
                    if boat_image:
                        game_surface.blit(boat_image, rect)
                else:
                    # For other tiles, render LAND underneath
                    land_image = scaled_tile_images.get(Tile.LAND)
                    if land_image:
                        game_surface.blit(land_image, rect)
                # Render the overlay image
                if tile == Tile.WALL:
                    below_tile = world.get_tile(gx, gy + 1)
                    overlay_image = scaled_tile_images["WALL_TOP"] if below_tile == Tile.WALL else scaled_tile_images[Tile.WALL]
                else:
                    overlay_image = scaled_tile_images.get(tile)
                if overlay_image:
                    game_surface.blit(overlay_image, rect)
            if tile == Tile.TURRET:
                level = turret_levels.get((gx, gy), 1)
                font = pygame.font.SysFont(None, 20)
                level_text = font.render(str(level), True, WHITE)
                text_rect = level_text.get_rect(center=(px + TILE_SIZE // 2, py - 10))
                game_surface.blit(level_text, text_rect)
            if tile == Tile.WALL:
                level = wall_levels.get((gx, gy), 1)
                font = pygame.font.SysFont(None, 20)
                level_text = font.render(str(level), True, WHITE)
                text_rect = level_text.get_rect(center=(px + TILE_SIZE // 2, py - 10))
                game_surface.blit(level_text, text_rect)

    # Render pirate ships
    for p in pirates:
        for s in p["ship"]:
            sx = s["x"] - top_left_x
            sy = s["y"] - top_left_y
            if darkness_factor == 1.0 and (
                sx <= 1 or sx >= VIEW_WIDTH - 2 or sy <= 1 or sy >= VIEW_HEIGHT - 2
            ):
                continue
            if 0 <= sx < VIEW_WIDTH and 0 <= sy < VIEW_HEIGHT:
                boat_tile_image = scaled_tile_images.get(Tile.BOAT)
                if boat_tile_image:
                    boat_tile_image = boat_tile_image.copy()
                    if darkness_factor == 1.0:
                        dist_to_edge = min(sx, VIEW_WIDTH - sx, sy, VIEW_HEIGHT - sy)
                        alpha = 0 if dist_to_edge <= 2 else 255 if dist_to_edge >= 5 else int(255 * (dist_to_edge - 2) / (5 - 2))
                        boat_tile_image.set_alpha(alpha)
                    else:
                        boat_tile_image.set_alpha(255)
                    game_surface.blit(boat_tile_image, (sx * TILE_SIZE, sy * TILE_SIZE))

    # Render player
    px = player_pos[0] - top_left_x
    py = player_pos[1] - top_left_y

    if not in_boat_mode:
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            current_player_image = scaled_player_fishing_image if fishing_state else scaled_player_image
            game_surface.blit(current_player_image, (px * TILE_SIZE, py * TILE_SIZE))
    else:
        if boat_entity:
            # Render all boat tiles, including one under the steering wheel position
            for offset in boat_entity["offsets"]:
                tile_x = player_pos[0] + offset[0]
                tile_y = player_pos[1] + offset[1]
                tx = tile_x - top_left_x
                ty = tile_y - top_left_y
                if 0 <= tx < VIEW_WIDTH and 0 <= ty < VIEW_HEIGHT:
                    game_surface.blit(scaled_tile_images[Tile.BOAT], (tx * TILE_SIZE, ty * TILE_SIZE))
            
            # Render player sprite and steering wheel at player position
            if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
                game_surface.blit(scaled_player_image, (px * TILE_SIZE, py * TILE_SIZE))
                game_surface.blit(scaled_tile_images[Tile.STEERING_WHEEL], (px * TILE_SIZE, py * TILE_SIZE))

    # Render bobber
    if bobber:
        bx = bobber["x"] - top_left_x
        by = bobber["y"] - top_left_y
        if 0 <= bx < VIEW_WIDTH and 0 <= by < VIEW_HEIGHT:
            bobber_image = scaled_tile_images["BOBBER"]
            if bobber["state"] == "waiting":
                bobber_image = scaled_tile_images["BOBBER2"]
            elif bobber["state"] == "biting":
                if (now - bobber["last_switch"]) % 1000 < 500:
                    bobber_image = scaled_tile_images["BOBBER2"]
                else:
                    bobber_image = scaled_tile_images["BOBBER3"]
            game_surface.blit(bobber_image, (bx * TILE_SIZE, by * TILE_SIZE))

    # Render interaction UI
    draw_interaction_ui()

    # Render pirate characters and "Land Ahoy!" text
    for p in pirates:
        for pirate in p.get("pirates", []):
            px = pirate["x"] - top_left_x
            py = pirate["y"] - top_left_y
            if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
                level = pirate["level"]
                is_rare = pirate.get("is_rare", False)
                rare_type = pirate.get("rare_type", None)
                sprite_key = (
                    f"level_{level}_{rare_type}" if is_rare and rare_type and pirate["health"] > 1
                    else f"base_{rare_type}" if is_rare and rare_type
                    else f"level_{level}" if pirate["health"] > 1
                    else "base"
                )
                pirate_image = scaled_pirate_sprites[sprite_key]
                game_surface.blit(pirate_image, (px * TILE_SIZE, py * TILE_SIZE))
                if is_rare and rare_type == "explosive" and "fuse_count" in pirate:
                    font = pygame.font.SysFont(None, 24)
                    count_text = font.render(str(pirate["fuse_count"]), True, RED)
                    text_rect = count_text.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE - 20))
                    game_surface.blit(count_text, text_rect)
        if p["state"] == "landed":
            px = p["x"] - top_left_x
            py = p["y"] - top_left_y
            if darkness_factor == 1.0 and (
                sx <= 1 or sx >= VIEW_WIDTH - 2 or sy <= 1 or sy >= VIEW_HEIGHT - 2
            ):
                continue
            if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
                font = pygame.font.SysFont(None, 24)
                text = font.render("Land Ahoy!", True, WHITE)
                text_rect = text.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE - 10))
                game_surface.blit(text, text_rect)

    # Render NPCs
    for npc in npcs:
        for s in npc["ship"]:
            sx = s["x"] - top_left_x
            sy = s["y"] - top_left_y
            if darkness_factor == 1.0 and (
                sx <= 1 or sx >= VIEW_WIDTH - 2 or sy <= 1 or sy >= VIEW_HEIGHT - 2
            ):
                continue
            if 0 <= sx < VIEW_WIDTH and 0 <= sy < VIEW_HEIGHT:
                if npc["state"] == "boat":
                    boat_tile_image = scaled_tile_images.get(Tile.BOAT)
                    if boat_tile_image:
                        boat_tile_image = boat_tile_image.copy()
                        if darkness_factor == 1.0:
                            dist_to_edge = min(sx, VIEW_WIDTH - sx, sy, VIEW_HEIGHT - sy)
                            alpha = 0 if dist_to_edge <= 2 else 255 if dist_to_edge >= 5 else int(255 * (dist_to_edge - 2) / (5 - 2))
                            boat_tile_image.set_alpha(alpha)
                        else:
                            boat_tile_image.set_alpha(255)
                        game_surface.blit(boat_tile_image, (sx * TILE_SIZE, sy * TILE_SIZE))
                    if s["x"] == npc["x"] and s["y"] == npc["y"]:
                        npc_image = scaled_waller_npc_sprite.copy()
                        if darkness_factor == 1.0:
                            npc_image.set_alpha(alpha)
                        else:
                            npc_image.set_alpha(255)
                        game_surface.blit(npc_image, (sx * TILE_SIZE, sy * TILE_SIZE))
                elif npc["state"] == "docked":
                    game_surface.blit(scaled_waller_npc_sprite, (sx * TILE_SIZE, sy * TILE_SIZE))

    # Render krakens
    for kraken in krakens:
        if kraken["state"] in ["moving", "destroying"]:
            kx = kraken["x"] - top_left_x
            ky = kraken["y"] - top_left_y
            if 0 <= kx < VIEW_WIDTH and 0 <= ky < VIEW_HEIGHT:
                kraken_image = scaled_tile_images["KRAKEN"].copy()
                alpha = 255 if darkness_factor < 1.0 else int(255 * (1 - darkness_factor))
                kraken_image.set_alpha(alpha)
                game_surface.blit(kraken_image, (kx * TILE_SIZE, ky * TILE_SIZE))

    # Render selected tile overlay and wall placement preview
    if selected_tile:
        sel_x, sel_y = selected_tile
        sel_px = sel_x - top_left_x
        sel_py = sel_y - top_left_y
        if 0 <= sel_px < VIEW_WIDTH and 0 <= sel_py < VIEW_HEIGHT:
            player_tile_x, player_tile_y = int(player_pos[0]), int(player_pos[1])
            manhattan_dist = abs(sel_x - player_tile_x) + abs(sel_y - player_tile_y)
            overlay_color = (0, 0, 0, 16) if manhattan_dist > 3 else (0, 0, 0, 128)
            overlay_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            overlay_surface.fill(overlay_color)
            game_surface.blit(overlay_surface, (sel_px * TILE_SIZE, sel_py * TILE_SIZE))
    if wall_placement_mode and selected_tile:
        sel_x, sel_y = selected_tile
        sel_px = sel_x - top_left_x
        sel_py = sel_y - top_left_y
        if 0 <= sel_px < VIEW_WIDTH and 0 <= sel_py < VIEW_HEIGHT:
            below_tile = world.get_tile(sel_x, sel_y + 1)
            wall_image = scaled_tile_images["WALL_TOP"] if below_tile == Tile.WALL else scaled_tile_images[Tile.WALL]
            wall_image = wall_image.copy()
            wall_image.set_alpha(128)
            game_surface.blit(wall_image, (sel_px * TILE_SIZE, sel_py * TILE_SIZE))
    if boulder_placement_mode and selected_tile:
        sel_x, sel_y = selected_tile
        sel_px = sel_x - top_left_x
        sel_py = sel_y - top_left_y
        if 0 <= sel_px < VIEW_WIDTH and 0 <= sel_py < VIEW_HEIGHT:
            boulder_image = scaled_tile_images[Tile.BOULDER].copy()
            boulder_image.set_alpha(128)
            game_surface.blit(boulder_image, (sel_px * TILE_SIZE, sel_py * TILE_SIZE))

    # Render floating text and images (wood and XP)
    for text in wood_texts:
        px = text["x"] - top_left_x
        py = text["y"] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            if text.get("image_key"):  # Check for image_key instead of image
                image = scaled_tile_images.get(text["image_key"])  # Use key to get pre-scaled image
                if image:
                    image = image.copy()
                    image.set_alpha(text["alpha"])
                    game_surface.blit(image, (px * TILE_SIZE, py * TILE_SIZE - 10))
            else:
                font = pygame.font.SysFont(None, 14)
                text_surface = font.render(text["text"], True, WHITE)
                text_surface.set_alpha(text["alpha"])
                text_rect = text_surface.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE - 10))
                game_surface.blit(text_surface, text_rect)
    for text in xp_texts:
        px = text["x"] - top_left_x
        py = text["y"] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            font = pygame.font.SysFont(None, 14)
            text_surface = font.render(text["text"], True, YELLOW)
            text_surface.set_alpha(text["alpha"])
            text_rect = text_surface.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE - 20))
            game_surface.blit(text_surface, text_rect)

    # Render player XP texts
    for text in player_xp_texts:
        px = player_pos[0] - top_left_x
        py = player_pos[1] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            font = pygame.font.SysFont(None, 14)
            text_surface = font.render(text["text"], True, YELLOW)
            text_surface.set_alpha(text["alpha"])
            text_rect = text_surface.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE - 20))
            game_surface.blit(text_surface, text_rect)

    # Render hat particles
    for hat in hat_particles:
        px = hat["x"] - top_left_x
        py = hat["y"] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            hat_level = hat["level"]
            hat_image = scaled_pirate_hat_images[hat_level]
            rotated_hat = pygame.transform.rotate(hat_image, hat["rotation"])
            alpha = int((hat["timer"] / hat["initial_timer"]) * 255)
            alpha = max(0, min(255, alpha))
            hat_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            hat_surface.blit(rotated_hat, (0, 0))
            hat_surface.set_alpha(alpha)
            hat_rect = hat_surface.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE + TILE_SIZE // 2))
            game_surface.blit(hat_surface, hat_rect.topleft)

    # Render explosions
    for explosion in explosions[:]:
        explosion["timer"] -= dt
        if explosion["timer"] <= 0:
            explosions.remove(explosion)
            continue
        px = explosion["x"] - top_left_x
        py = explosion["y"] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            alpha = int((explosion["timer"] / 500) * 255)
            explosion_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(explosion_surface, (255, 0, 0, alpha), (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2)
            game_surface.blit(explosion_surface, (px * TILE_SIZE, py * TILE_SIZE))

    # Render sparks
    if sparks:
        spark_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for spark in sparks:
            px = spark["x"] - top_left_x
            py = spark["y"] - top_left_y
            if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
                initial_timer = spark.get("initial_timer", 100)
                alpha = int((spark["timer"] / initial_timer) * 255)
                alpha = max(0, min(255, alpha))
                pygame.draw.circle(spark_surface, (*spark["color"], alpha),
                                   (int(px * TILE_SIZE + TILE_SIZE // 2), int(py * TILE_SIZE + TILE_SIZE // 2)), 2)
        game_surface.blit(spark_surface, (0, 0))

    # Render projectiles
    for proj in projectiles:
        px = proj["x"] - top_left_x
        py = proj["y"] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            pygame.draw.circle(game_surface, DARK_GRAY, (int(px * TILE_SIZE + TILE_SIZE // 2), int(py * TILE_SIZE + TILE_SIZE // 2)), 4)

    # Apply darkness overlay using world-coordinate-based positioning
    darkness_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            # Compute world tile coordinates
            gx = start_x + x
            gy = start_y + y
            # Compute screen position relative to top_left
            px = (gx - top_left_x) * TILE_SIZE
            py = (gy - top_left_y) * TILE_SIZE
            # Get brightness and compute alpha
            b = brightness[y][x]
            final_brightness = b * darkness_factor + (1 - darkness_factor)
            alpha = int(255 * (1 - final_brightness))
            # Define rectangle at the computed position
            rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
            darkness_surface.fill((0, 0, 0, alpha), rect)
    game_surface.blit(darkness_surface, (0, 0))

def draw_ui():
    font = pygame.font.SysFont(None, 28)
    score = turrets_placed + pirates_killed + tiles_placed + days_survived
    wood_text = font.render(f"Wood: {wood}", True, WHITE)
    score_text = font.render(f"Score: {score}", True, WHITE)
    quit_text = font.render("Press ESC to quit", True, WHITE)
    help_color = WHITE if not interaction_ui_enabled else (150, 150, 150)
    help_text = font.render("Press I for Help", True, help_color)
    time_str = get_time_string(game_time)  # Add clock
    time_text = font.render(time_str, True, WHITE)
    day_text = font.render(f"Day: {days_survived + 1}", True, WHITE)  # +1 for 1-based day count
    level_text = font.render(f"Level: {player_level}", True, WHITE)

    screen.blit(wood_text, (10, 10))
    screen.blit(score_text, (10, 40))
    screen.blit(quit_text, (10, 70))
    screen.blit(help_text, (10, 100))
    screen.blit(time_text, (10, 130))
    screen.blit(day_text, (10, 160))
    screen.blit(level_text, (10, 190))

def draw_minimap():
    """Simplified minimap showing nearby chunks, with nighttime visibility limited to view distance."""
    global minimap_base_cache, minimap_cache_valid, last_player_chunk, last_chunks_version
    minimap_scale = 3
    minimap_size = VIEW_CHUNKS * CHUNK_SIZE * minimap_scale
    darkness_factor = get_darkness_factor(game_time)

    # Calculate the view area in world coordinates
    cx, cy = world.player_chunk
    view_left = player_pos[0] - VIEW_WIDTH / 2.0
    view_right = player_pos[0] + VIEW_WIDTH / 2.0
    view_top = player_pos[1] - VIEW_HEIGHT / 2.0
    view_bottom = player_pos[1] + VIEW_HEIGHT / 2.0

    # Determine the top-left world coordinates of the minimap
    top_left_chunk_x = cx - VIEW_CHUNKS // 2
    top_left_chunk_y = cy - VIEW_CHUNKS // 2
    top_left_world_x = top_left_chunk_x * CHUNK_SIZE
    top_left_world_y = top_left_chunk_y * CHUNK_SIZE

    # Check if the cache needs to be updated
    if (not minimap_cache_valid or world.player_chunk != last_player_chunk or 
        last_chunks_version != chunks_version):
        minimap_base_cache = pygame.Surface((minimap_size, minimap_size))
        for dy in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1):
            for dx in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1):
                chunk_key = (cx + dx, cy + dy)
                if chunk_key in world.chunks:
                    chunk = world.chunks[chunk_key]
                    for my in range(CHUNK_SIZE):
                        for mx in range(CHUNK_SIZE):
                            tile = chunk[my][mx]
                            world_x, world_y = world.chunk_to_world(cx + dx, cy + dy, mx, my)
                            color = {
                                Tile.WATER: BLUE,
                                Tile.LAND: GREEN,
                                Tile.TREE: DARK_GREEN,
                                Tile.SAPLING: (150, 255, 150),
                                Tile.WALL: BROWN,
                                Tile.TURRET: DARK_GRAY,
                                Tile.BOAT: TAN,
                                Tile.USED_LAND: LIGHT_GRAY,
                                Tile.LOOT: YELLOW,
                                Tile.BOAT_STAGE_2: (180, 200, 140),
                                Tile.BOAT_STAGE_3: (115, 220, 140),
                                Tile.BOULDER: (100, 100, 100)
                            }.get(tile, BLACK)
                            mx_map = (dx + VIEW_CHUNKS // 2) * CHUNK_SIZE + mx
                            my_map = (dy + VIEW_CHUNKS // 2) * CHUNK_SIZE + my
                            pygame.draw.rect(minimap_base_cache, color, 
                                           (mx_map * minimap_scale, my_map * minimap_scale, 
                                            minimap_scale, minimap_scale))
        minimap_cache_valid = True
        last_player_chunk = world.player_chunk
        last_chunks_version = chunks_version

    # Create the minimap surface by copying the base layer
    minimap_surface = minimap_base_cache.copy()

    # Highlight the player's position
    world_x, world_y = int(player_pos[0]), int(player_pos[1])
    mx_map = (world_x - top_left_world_x) * minimap_scale
    my_map = (world_y - top_left_world_y) * minimap_scale
    if 0 <= mx_map < minimap_size and 0 <= my_map < minimap_size:
        # Player marker fades slightly at night
        player_alpha = int(255 * (1 - darkness_factor * 0.3))  # Fade to 70% opacity at full night
        player_surface = pygame.Surface((minimap_scale, minimap_scale), pygame.SRCALPHA)
        player_surface.fill((255, 255, 255, player_alpha))
        minimap_surface.blit(player_surface, (int(mx_map), int(my_map)))

    # Draw pirates and NPCs with fading visibility
    for p in pirates:
        world_x, world_y = p["x"], p["y"]
        is_in_view = (view_left <= world_x < view_right and view_top <= world_y < view_bottom)
        mx = (world_x - top_left_world_x) * minimap_scale
        my = (world_y - top_left_world_y) * minimap_scale
        if 0 <= mx < minimap_size and 0 <= my < minimap_size:
            # Calculate alpha based on visibility
            if is_in_view:
                alpha = 255  # Always fully visible in view
            else:
                alpha = int(255 * (1 - darkness_factor))  # Fade out as darkness increases
            if alpha > 0:  # Only draw if not fully faded
                pirate_surface = pygame.Surface((minimap_scale, minimap_scale), pygame.SRCALPHA)
                pirate_surface.fill((255, 0, 0, alpha))
                minimap_surface.blit(pirate_surface, (int(mx), int(my)))
    # After drawing pirates on minimap
    for kraken in krakens:
        world_x, world_y = kraken["x"], kraken["y"]
        is_in_view = (view_left <= world_x < view_right and view_top <= world_y < view_bottom)
        mx = (world_x - top_left_world_x) * minimap_scale
        my = (world_y - top_left_world_y) * minimap_scale
        if 0 <= mx < minimap_size and 0 <= my < minimap_size:
            alpha = 255 if is_in_view else int(255 * (1 - darkness_factor))
            if alpha > 0:
                kraken_surface = pygame.Surface((minimap_scale, minimap_scale), pygame.SRCALPHA)
                kraken_surface.fill((0, 0, 255, alpha))  # Blue for Kraken
                minimap_surface.blit(kraken_surface, (int(mx), int(my)))
    for npc in npcs:
        world_x, world_y = npc["x"], npc["y"]
        is_in_view = (view_left <= world_x < view_right and view_top <= world_y < view_bottom)
        mx = (world_x - top_left_world_x) * minimap_scale
        my = (world_y - top_left_world_y) * minimap_scale
        if 0 <= mx < minimap_size and 0 <= my < minimap_size:
            if is_in_view:
                alpha = 255
            else:
                alpha = int(255 * (1 - darkness_factor))
            if alpha > 0:
                npc_surface = pygame.Surface((minimap_scale, minimap_scale), pygame.SRCALPHA)
                npc_surface.fill((255, 200, 200, alpha))
                minimap_surface.blit(npc_surface, (int(mx), int(my)))

    # Apply darkness overlay with a gradient effect
    overlay_surface = pygame.Surface((minimap_size, minimap_size), pygame.SRCALPHA)
    # Full darkness for areas outside the view rectangle
    outside_alpha = int(darkness_factor * 255)  # Max 255 alpha (fully dark) at full night
    overlay_surface.fill((0, 0, 0, outside_alpha))
    # Reduced darkness for the view area (slight dimming at night)
    view_alpha = int(darkness_factor * 128)  # Max 128 alpha (50% darkness) in view area at full night
    cam_x = (player_pos[0] - top_left_world_x - VIEW_WIDTH / 2) * minimap_scale
    cam_y = (player_pos[1] - top_left_world_y - VIEW_HEIGHT / 2) * minimap_scale
    view_rect = pygame.Rect(cam_x, cam_y, VIEW_WIDTH * minimap_scale, VIEW_HEIGHT * minimap_scale)
    overlay_surface.fill((0, 0, 0, view_alpha), view_rect)  # Apply reduced darkness in view area
    minimap_surface.blit(overlay_surface, (0, 0))

    # Draw the view rectangle on top (always fully visible)
    cam_rect = pygame.Rect(cam_x, cam_y, VIEW_WIDTH * minimap_scale, VIEW_HEIGHT * minimap_scale)
    pygame.draw.rect(minimap_surface, WHITE, cam_rect, 1)

    screen_width, _ = screen.get_size()
    minimap_x = screen_width - minimap_surface.get_width() - 10
    screen.blit(minimap_surface, (minimap_x, 10))

def show_game_over():
    global high_score, fade_done
    score = turrets_placed + pirates_killed + tiles_placed + days_survived
    if score > high_score:
        high_score = score
        with open("score.txt", "w") as f:
            f.write(str(high_score))

    base_surface = pygame.Surface((WIDTH, HEIGHT))
    base_surface.fill(BLACK)

    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 32)

    # Change the game over message based on the cause
    if kraken_game_over:
        cause_message = "You were taken by the Kraken!"
    else:
        cause_message = "A pirate caught you!"

    lines = [
        "Game Over!",
        cause_message,
        f"Score: {score}",
        f"High Score: {high_score}",
        "",
        f"Turrets Placed: {turrets_placed}",
        f"Pirates Killed: {pirates_killed}",
        f"Tiles Placed: {tiles_placed}",
        "",
        "Press SPACE to restart or ESC to quit"
    ]

    for i, line in enumerate(lines):
        text = small_font.render(line, True, WHITE)
        base_surface.blit(text, (WIDTH // 2 - text.get_width() // 2, 100 + i * 40))

    screen_w, screen_h = screen.get_size()
    max_scale_w = screen_w / WIDTH
    max_scale_h = screen_h / HEIGHT
    scale_factor = min(max_scale_w, max_scale_h)

    scaled_width = int(WIDTH * scale_factor)
    scaled_height = int(HEIGHT * scale_factor)

    offset_x = (screen_w - scaled_width) // 2
    offset_y = (screen_h - scaled_height) // 2

    for alpha in range(255, -1, -10):
        scaled_surface = pygame.transform.scale(base_surface, (scaled_width, scaled_height))
        screen.fill(BLACK)
        screen.blit(scaled_surface, (offset_x, offset_y))
        fade = pygame.Surface((screen_w, screen_h))
        fade.fill(BLACK)
        fade.set_alpha(alpha)
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.delay(20)

# --- Game Logic ---
def screen_to_world(mouse_x, mouse_y):
    """Convert screen coordinates to world coordinates."""
    screen_width, screen_height = screen.get_size()
    blit_x = (screen_width - WIDTH * SCALE) // 2
    blit_y = (screen_height - HEIGHT * SCALE) // 2

    # Adjust for the offset and scale
    world_x = (mouse_x - blit_x) / SCALE
    world_y = (mouse_y - blit_y) / SCALE

    # Convert to tile coordinates relative to the view
    top_left_x = player_pos[0] - VIEW_WIDTH / 2.0
    top_left_y = player_pos[1] - VIEW_HEIGHT / 2.0

    tile_x = world_x / TILE_SIZE
    tile_y = world_y / TILE_SIZE

    # Use math.floor for consistent tile coordinate calculation
    world_tile_x = math.floor(top_left_x + tile_x)
    world_tile_y = math.floor(top_left_y + tile_y)

    return world_tile_x, world_tile_y

def is_on_land(pos):
    """Check if all four corners of the player's hitbox are on land tiles."""
    # Define hitbox half-size (5 pixels margin ≈ 0.15625 tiles)
    hitbox_half_size = 0.15625
    
    # Calculate player's center from top-left position
    center_x = pos[0] + 0.5
    center_y = pos[1] + 0.5
    
    # Define hitbox corners relative to the center
    corners = [
        (center_x - hitbox_half_size, center_y - hitbox_half_size),  # Top-left
        (center_x + hitbox_half_size, center_y - hitbox_half_size),  # Top-right
        (center_x - hitbox_half_size, center_y + hitbox_half_size),  # Bottom-left
        (center_x + hitbox_half_size, center_y + hitbox_half_size)   # Bottom-right
    ]
    
    # Check each corner against the tile map
    for cx, cy in corners:
        tile_x = math.floor(cx)
        tile_y = math.floor(cy)
        if world.get_tile(tile_x, tile_y) not in MOVEMENT_TILES:
            return False
    return True

def find_connected_boat_tiles(start_x, start_y, max_depth=6):
    visited = set()
    frontier = [(start_x, start_y, 0)]
    connected_tiles = []
    while frontier:
        x, y, depth = frontier.pop(0)
        if (x, y) in visited or depth > max_depth:
            continue
        tile = world.get_tile(x, y)
        if tile in (Tile.BOAT, Tile.STEERING_WHEEL):  # Include STEERING_WHEEL
            visited.add((x, y))
            connected_tiles.append((x, y))
            neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
            for nx, ny in neighbors:
                if (nx, ny) not in visited:
                    frontier.append((nx, ny, depth + 1))
    return connected_tiles

def update_land_spread():
    global boat_tiles
    now = pygame.time.get_ticks()
    top_left_x = int(player_pos[0] - VIEW_WIDTH // 2)  # Floor to integer
    top_left_y = int(player_pos[1] - VIEW_HEIGHT // 2)  # Floor to integer

    if boat_entity:
        boat_tiles = set()
        for offset_x, offset_y in boat_entity["offsets"]:
            tile_x = int(player_pos[0] + offset_x + 0.5)
            tile_y = int(player_pos[1] + offset_y + 0.5)
            boat_tiles.add((tile_x, tile_y))
    else:
        boat_tiles = set()

    # Step 1: Find BOAT_TILE tiles adjacent to LAND and add to land_spread
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = top_left_x + x, top_left_y + y
            tile = world.get_tile(gx, gy)
            if tile == Tile.BOAT:
                # Check cardinal neighbors for LAND
                neighbors = [(gx, gy-1), (gx, gy+1), (gx-1, gy), (gx+1, gy)]
                has_land = False
                for nx, ny in neighbors:
                    if world.get_tile(nx, ny) == Tile.LAND:
                        has_land = True
                        break
                if has_land and (gx, gy) not in land_spread:
                    land_spread[(gx, gy)] = {"start_time": now, "stage": 0}

    # Step 2: Update stages for tiles in land_spread
    for pos in list(land_spread.keys()):
        data = land_spread[pos]
        gx, gy = pos
        # Check if the tile is still a BOAT_TILE or in a spreading stage
        current_tile = world.get_tile(gx, gy)
        if current_tile not in [Tile.BOAT, Tile.BOAT_STAGE_2, Tile.BOAT_STAGE_3]:
            del land_spread[pos]  # Tile changed (e.g., player removed it)
            continue
        elapsed = now - data["start_time"]
        stages_passed = elapsed // land_spread_time
        new_stage = min(stages_passed, 3)  # Cap at stage 3 (LAND)

        if new_stage != data["stage"]:
            data["stage"] = new_stage
            if new_stage == 1:
                world.set_tile(gx, gy, Tile.BOAT_STAGE_2)
            elif new_stage == 2:
                world.set_tile(gx, gy, Tile.BOAT_STAGE_3)
            elif new_stage == 3:
                world.set_tile(gx, gy, Tile.LAND)
                del land_spread[pos]  # Conversion complete

def spawn_fish_tiles():
    """Spawn FISH tiles within draw distance, up to a maximum of 3."""
    now = pygame.time.get_ticks()
    # Count current FISH tiles in view
    top_left_x = int(player_pos[0] - VIEW_WIDTH // 2)
    top_left_y = int(player_pos[1] - VIEW_HEIGHT // 2)
    fish_count = 0
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = top_left_x + x, top_left_y + y
            if world.get_tile(gx, gy) == Tile.FISH:
                fish_count += 1
    if fish_count >= max_fish_tiles:
        return
    # Find water tiles
    water_tiles = []
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = top_left_x + x, top_left_y + y
            if world.get_tile(gx, gy) == Tile.WATER:
                water_tiles.append((gx, gy))
    # Spawn a fish with 5% chance per second
    if water_tiles and random.random() < 0.05:
        x, y = random.choice(water_tiles)
        world.set_tile(x, y, Tile.FISH)
        fish_tiles.append({"x": x, "y": y, "spawn_time": now})

def update_fish_tiles():
    """Despawn FISH tiles after 1 minute and revert to WATER."""
    global fish_tiles
    now = pygame.time.get_ticks()
    # Identify expired fish tiles
    expired_fish = [fish for fish in fish_tiles if now - fish["spawn_time"] >= fish_despawn_time]
    # Keep only active fish tiles
    fish_tiles = [fish for fish in fish_tiles if now - fish["spawn_time"] < fish_despawn_time]
    # Revert expired fish tiles to WATER
    for fish in expired_fish:
        x, y = fish["x"], fish["y"]
        if world.get_tile(x, y) == Tile.FISH:  # Ensure it’s still a FISH tile
            world.set_tile(x, y, Tile.WATER)

def spawn_pirate():
    global pirates
    score = turrets_placed + pirates_killed + tiles_placed
    min_blocks = max(3, 1 + score // 10)
    max_blocks = max(min_blocks, 1 + score // 5)
    equivalent_level_1_pirates = random.randint(min_blocks, max_blocks)

    pirate_levels = []
    remaining = equivalent_level_1_pirates
    while remaining > 0:
        level = min(10, int(math.log2(max(1, remaining))) + 1)
        pirate_levels.append(level)
        remaining -= 2 ** (level - 1)

    cx, cy = world.player_chunk
    loaded_chunks = [(cx + dx, cy + dy) for dx in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1)
                     for dy in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1) if (dx, dy) != (0, 0)]
    water_tiles = []
    for chunk_key in loaded_chunks:
        if chunk_key in world.chunks:
            chunk = world.chunks[chunk_key]
            for ty in range(CHUNK_SIZE):
                for tx in range(CHUNK_SIZE):
                    if chunk[ty][tx] == Tile.WATER:
                        world_x, world_y = world.chunk_to_world(chunk_key[0], chunk_key[1], tx, ty)
                        water_tiles.append((world_x, world_y))
    if not water_tiles:
        print("No water tiles available for spawning!")
        return
    x, y = random.choice(water_tiles)

    block_count = max(3, len(pirate_levels))
    ship_tiles = set()
    frontier = [(x, y)]
    while len(ship_tiles) < block_count and frontier:
        cx, cy = frontier.pop(0)
        if (cx, cy) not in ship_tiles and world.get_tile(cx, cy) == Tile.WATER:
            ship_tiles.add((cx, cy))
            neighbors = [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]
            random.shuffle(neighbors)
            frontier.extend(neighbors)
    ship_tiles = list(ship_tiles)
    if not ship_tiles:
        print("No connected water tiles for ship!")
        return

    pirate_positions = random.sample(ship_tiles, min(len(pirate_levels), len(ship_tiles)))
    pirates_data = []
    for i, (px, py) in enumerate(pirate_positions):
        level = pirate_levels[i]
        is_rare = random.random() < 1/3  # 1 in 3 chance
        rare_type = random.choice(RARE_PIRATE_TYPES) if is_rare else None
        max_health = 2 ** level
        if is_rare and rare_type == "tanky":
            max_health *= 2  # Double health for Tanky
        xp_value = 2 ** (level - 1) * (2 if is_rare else 1)  # Double XP for rare
        move_duration = 300 if not (is_rare and rare_type == "speedy") else 150  # Half duration for Speedy
        pirate_data = {
            "x": float(px),
            "y": float(py),
            "start_x": float(px),
            "start_y": float(py),
            "target_x": float(px),
            "target_y": float(py),
            "move_progress": 1.0,
            "move_duration": move_duration,
            "health": max_health,
            "max_health": max_health,
            "xp_value": xp_value,
            "level": level,
            "is_rare": is_rare,
            "rare_type": rare_type,
            "has_dropped_hat": False
        }
        if is_rare and rare_type == "bridge_builder":
            pirate_data["boat_tiles_placed"] = 0  # Initialize counter for bridge_builder
        pirates_data.append(pirate_data)

    dx = player_pos[0] - x
    dy = player_pos[1] - y
    length = max(abs(dx), abs(dy)) or 1
    direction = (dx / length, dy / length)

    pirates.append({
        "x": x,
        "y": y,
        "dir": direction,
        "state": "boat",
        "ship": [{"x": sx, "y": sy} for sx, sy in ship_tiles],
        "pirates": pirates_data
    })

def spawn_kraken():
    global krakens
    if len(krakens) >= KRAKEN_LIMIT:
        return
    if random.random() > KRAKEN_SPAWN_CHANCE:
        return
    # Pick one random chunk from loaded chunks
    cx, cy = world.player_chunk
    chunk_keys = [(cx + dx, cy + dy) for dx in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1)
                  for dy in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1)]
    if not chunk_keys:
        return
    random_chunk_key = random.choice(chunk_keys)
    if random_chunk_key not in world.chunks:
        return
    # Check the selected chunk for boat tiles
    chunk = world.chunks[random_chunk_key]
    boat_tiles = []
    for ty in range(CHUNK_SIZE):
        for tx in range(CHUNK_SIZE):
            world_x, world_y = world.chunk_to_world(random_chunk_key[0], random_chunk_key[1], tx, ty)
            if world.get_tile(world_x, world_y) in [Tile.BOAT, Tile.BOAT_STAGE_2, Tile.BOAT_STAGE_3]:
                boat_tiles.append((world_x, world_y))
    if not boat_tiles:
        return
    x, y = random.choice(boat_tiles)
    krakens.append({
        "x": float(x),
        "y": float(y),
        "state": "destroying",  # Start in destroying state
        "target_tile": (int(x), int(y)),  # Target the tile it's on
        "last_destroy": pygame.time.get_ticks(),
        "last_search": 0,
        "search_cooldown": 500,  # Retain for consistency, though less critical now
        "despawn_timer": 0  # Timer for staying after failing to find a boat tile
    })

def spawn_waller_npc():
    global npcs
    # Find a water tile near the player to spawn the NPC ship
    cx, cy = world.player_chunk
    loaded_chunks = [(cx + dx, cy + dy) for dx in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1)
                     for dy in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1) if (dx, dy) != (0, 0)]
    water_tiles = []
    for chunk_key in loaded_chunks:
        if chunk_key in world.chunks:
            chunk = world.chunks[chunk_key]
            for ty in range(CHUNK_SIZE):
                for tx in range(CHUNK_SIZE):
                    if chunk[ty][tx] == Tile.WATER:
                        world_x, world_y = world.chunk_to_world(chunk_key[0], chunk_key[1], tx, ty)
                        water_tiles.append((world_x, world_y))
    if not water_tiles:
        print("No water tiles available for NPC spawning!")
        return
    x, y = random.choice(water_tiles)

    # Create a small ship (3 tiles)
    ship_tiles = set()
    frontier = [(x, y)]
    block_count = 3
    while len(ship_tiles) < block_count and frontier:
        cx, cy = frontier.pop(0)
        if (cx, cy) not in ship_tiles and world.get_tile(cx, cy) == Tile.WATER:
            ship_tiles.add((cx, cy))
            neighbors = [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]
            random.shuffle(neighbors)
            frontier.extend(neighbors)
    ship_tiles = list(ship_tiles)
    if not ship_tiles:
        print("No connected water tiles for NPC ship!")
        return

    # NPC arrives on a boat, similar to pirates
    dx = player_pos[0] - x
    dy = player_pos[1] - y
    length = max(abs(dx), abs(dy)) or 1
    direction = (dx / length, dy / length)

    npcs.append({
        "x": x,
        "y": y,
        "dir": direction,
        "state": "boat",
        "ship": [{"x": sx, "y": sy} for sx, sy in ship_tiles],
        "type": "waller",
        "sprite": pygame.image.load("Assets/npc_waller.png").convert_alpha()
    })

def update_pirates():
    global game_over, pirates, pirates_killed
    now = pygame.time.get_ticks()
    for p in pirates[:]:
        if p["state"] == "boat":
            if not p["ship"]:
                pirates.remove(p)
                continue
            # Scale the base speed (0.05) by the speed multiplier
            base_speed = 0.05
            scaled_speed = base_speed * get_speed_multiplier()
            for s in p["ship"]:
                s["x"] += p["dir"][0] * scaled_speed
                s["y"] += p["dir"][1] * scaled_speed
            for pirate in p["pirates"]:
                pirate["x"] += p["dir"][0] * scaled_speed
                pirate["y"] += p["dir"][1] * scaled_speed
                pirate["start_x"] = pirate["x"]
                pirate["start_y"] = pirate["y"]
                pirate["target_x"] = pirate["x"]
                pirate["target_y"] = pirate["y"]
                pirate["move_progress"] = 1.0
            nx = p["x"] + p["dir"][0] * scaled_speed
            ny = p["y"] + p["dir"][1] * scaled_speed
            landed = False
            landing_tile = None
            for s in p["ship"]:
                sx, sy = int(s["x"]), int(s["y"])
                if world.get_tile(sx, sy) != Tile.WATER:
                    landed = True
                    landing_tile = (sx, sy)
                    break
            if landed:
                for s in p["ship"]:
                    sx, sy = int(round(s["x"])), int(round(s["y"]))
                    if world.get_tile(sx, sy) == Tile.WATER:
                        world.set_tile(sx, sy, Tile.BOAT)
                p["ship"] = []
                p["state"] = "landed"
                p["land_time"] = now
                p["x"], p["y"] = landing_tile
            else:
                p["x"], p["y"] = nx, ny
        elif p["state"] == "landed":
            if now - p["land_time"] >= 1000:
                p["state"] = "walk"
                p["walk_timer"] = now
                for pirate in p["pirates"]:
                    pirate["start_x"] = pirate["x"]
                    pirate["start_y"] = pirate["y"]
                    pirate["target_x"] = pirate["x"]
                    pirate["target_y"] = pirate["y"]
                    pirate["move_progress"] = 1.0
        else:  # "walk" state
            if "walk_timer" not in p:
                p["walk_timer"] = 0
            for pirate in p["pirates"]:
                if pirate["move_progress"] < 1.0:
                    elapsed = dt
                    pirate["move_progress"] = min(1.0, pirate["move_progress"] + elapsed / pirate["move_duration"])
                    pirate["x"] = pirate["start_x"] + (pirate["target_x"] - pirate["start_x"]) * pirate["move_progress"]
                    pirate["y"] = pirate["start_y"] + (pirate["target_y"] - pirate["start_y"]) * pirate["move_progress"]
            if now - p["walk_timer"] < pirate_walk_delay:
                continue
            pirates_to_remove = []
            for pirate in p["pirates"]:
                is_rare = pirate.get("is_rare", False)
                rare_type = pirate.get("rare_type", None)
                # Explosive: Update fuse countdown
                if is_rare and rare_type == "explosive":
                    dx = abs(pirate["x"] - player_pos[0])
                    dy = abs(pirate["y"] - player_pos[1])
                    manhattan_dist = dx + dy
                    if manhattan_dist <= 3.0 and "fuse_timer" not in pirate:
                        pirate["fuse_timer"] = 0
                        pirate["fuse_count"] = 3
                        pirate["last_count_update"] = now
                        print(f"Fuse started for Explosive pirate at ({pirate['x']}, {pirate['y']})")
                    if "fuse_timer" in pirate:
                        pirate["fuse_timer"] += dt
                        if now - pirate["last_count_update"] >= 1000 and pirate["fuse_count"] > 0:
                            pirate["fuse_count"] -= 1
                            pirate["last_count_update"] = now
                            print(f"Fuse count: {pirate['fuse_count']} at ({pirate['x']}, {pirate['y']})")
                # Check if pirate touches the player (normal or non-turret_breaker)
                if not (is_rare and rare_type == "turret_breaker"):
                    dist = math.hypot(pirate["x"] - player_pos[0], pirate["y"] - player_pos[1])
                    if dist < 0.5:
                        game_over = True
                        return
                if pirate["move_progress"] >= 1.0:
                    # Turret Breaker: Target nearest turret
                    target_x, target_y = int(pirate["x"]), int(pirate["y"])
                    if is_rare and rare_type == "turret_breaker":
                        nearest_turret = None
                        min_dist = float("inf")
                        for y in range(-VIEW_WIDTH // 2, VIEW_WIDTH // 2 + 1):
                            for x in range(-VIEW_WIDTH // 2, VIEW_WIDTH // 2 + 1):
                                tx = int(pirate["x"]) + x
                                ty = int(pirate["y"]) + y
                                if world.get_tile(tx, ty) == Tile.TURRET:
                                    dist = math.hypot(tx - pirate["x"], ty - pirate["y"])
                                    if dist < min_dist:
                                        min_dist = dist
                                        nearest_turret = (tx, ty)
                        if nearest_turret:
                            target_x, target_y = nearest_turret
                        else:
                            target_x, target_y = int(player_pos[0]), int(player_pos[1])
                    else:
                        target_x, target_y = int(player_pos[0]), int(player_pos[1])
                    dx = target_x - pirate["x"]
                    dy = target_y - pirate["y"]
                    primary = (1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1)
                    alt = (0, 1 if dy > 0 else -1) if primary[0] != 0 else (1 if dx > 0 else -1, 0)
                    def can_walk(x, y):
                        tile = world.get_tile(x, y)
                        if tile not in MOVEMENT_TILES:
                            return False
                        for other_p in pirates:
                            for other_pirate in other_p["pirates"]:
                                if other_pirate is not pirate and int(other_pirate["x"]) == x and int(other_pirate["y"]) == y:
                                    return False
                        return True
                    moved = False
                    tx, ty = int(pirate["x"] + primary[0]), int(pirate["y"] + primary[1])
                    if is_rare and rare_type == "bridge_builder" and world.get_tile(tx, ty) == Tile.WATER:
                        if has_adjacent_boat_or_land(tx, ty) and pirate.get("boat_tiles_placed", 0) < pirate["level"]:
                            world.set_tile(tx, ty, Tile.BOAT)
                            pirate["boat_tiles_placed"] = pirate.get("boat_tiles_placed", 0) + 1
                    if is_rare and rare_type == "turret_breaker" and world.get_tile(tx, ty) == Tile.TURRET:
                        turret_pos = (tx, ty)
                        current_level = turret_levels.get(turret_pos, 1)
                        pirate_level = pirate["level"]
                        if current_level > 1:
                            new_level = max(1, current_level - pirate_level)
                            turret_levels[turret_pos] = new_level
                            if new_level == 1:
                                turret_xp[turret_pos] = 0  # Reset XP when reduced to level 1
                        else:
                            # Turret is level 1 or would drop below 1, remove it
                            world.set_tile(tx, ty, Tile.LAND)
                            if turret_pos in turret_cooldowns:
                                del turret_cooldowns[turret_pos]
                            if turret_pos in turret_levels:
                                del turret_levels[turret_pos]
                            if turret_pos in turret_xp:
                                del turret_xp[turret_pos]
                        moved = True
                    elif world.get_tile(tx, ty) == Tile.WALL:
                        wall_pos = (tx, ty)
                        last_damaged = wall_damage_timers.get(wall_pos, 0)
                        if now - last_damaged >= 1000:  # Damage every second
                            current_level = wall_levels.get(wall_pos, 1)
                            if current_level > 1:
                                wall_levels[wall_pos] = current_level - 1
                            else:
                                world.set_tile(tx, ty, Tile.BOULDER)
                                del wall_levels[wall_pos]
                                if wall_pos in wall_damage_timers:
                                    del wall_damage_timers[wall_pos]
                            wall_damage_timers[wall_pos] = now
                    elif can_walk(tx, ty):
                        pirate["start_x"] = pirate["x"]
                        pirate["start_y"] = pirate["y"]
                        pirate["target_x"] = tx
                        pirate["target_y"] = ty
                        pirate["move_progress"] = 0.0
                        moved = True
                    else:
                        ax, ay = int(pirate["x"] + alt[0]), int(pirate["y"] + alt[1])
                        if is_rare and rare_type == "bridge_builder" and world.get_tile(ax, ay) == Tile.WATER:
                            if has_adjacent_boat_or_land(ax, ay) and pirate.get("boat_tiles_placed", 0) < pirate["level"]:
                                world.set_tile(ax, ay, Tile.BOAT)
                                pirate["boat_tiles_placed"] = pirate.get("boat_tiles_placed", 0) + 1
                        if is_rare and rare_type == "turret_breaker" and world.get_tile(ax, ay) == Tile.TURRET:
                            turret_pos = (ax, ay)
                            current_level = turret_levels.get(turret_pos, 1)
                            pirate_level = pirate["level"]
                            if current_level > 1:
                                new_level = max(1, current_level - pirate_level)
                                turret_levels[turret_pos] = new_level
                                if new_level == 1:
                                    turret_xp[turret_pos] = 0  # Reset XP when reduced to level 1
                            else:
                                # Turret is level 1 or would drop below 1, remove it
                                world.set_tile(ax, ay, Tile.LAND)
                                if turret_pos in turret_cooldowns:
                                    del turret_cooldowns[turret_pos]
                                if turret_pos in turret_levels:
                                    del turret_levels[turret_pos]
                                if turret_pos in turret_xp:
                                    del turret_xp[turret_pos]
                            moved = True
                        elif world.get_tile(ax, ay) == Tile.WALL:
                            wall_pos = (ax, ay)
                            last_damaged = wall_damage_timers.get(wall_pos, 0)
                            if now - last_damaged >= 1000:  # Damage every second
                                current_level = wall_levels.get(wall_pos, 1)
                                if current_level > 1:
                                    wall_levels[wall_pos] = current_level - 1
                                else:
                                    world.set_tile(ax, ay, Tile.BOULDER)
                                    del wall_levels[wall_pos]
                                    if wall_pos in wall_damage_timers:
                                        del wall_damage_timers[wall_pos]
                                wall_damage_timers[wall_pos] = now
                        elif can_walk(ax, ay):
                            pirate["start_x"] = pirate["x"]
                            pirate["start_y"] = pirate["y"]
                            pirate["target_x"] = ax
                            pirate["target_y"] = ay
                            pirate["move_progress"] = 0.0
                            moved = True
                    if not moved:
                        for dx_try, dy_try in [primary, alt]:
                            cx, cy = int(pirate["x"] + dx_try), int(pirate["y"] + dy_try)
                            if world.get_tile(cx, cy) == Tile.TREE:
                                world.set_tile(cx, cy, Tile.LAND)
                                break
            # Second pass: Handle Explosive pirate explosions
            pirates_to_remove = []
            for pirate in p["pirates"]:
                is_rare = pirate.get("is_rare", False)
                rare_type = pirate.get("rare_type", None)
                if is_rare and rare_type == "explosive" and "fuse_timer" in pirate:
                    if now - pirate["last_count_update"] >= 3000:  # 3 seconds total
                        print(f"Explosive pirate exploding at ({pirate['x']}, {pirate['y']})")
                        px, py = int(pirate["x"]), int(pirate["y"])
                        for dy in range(-1, 2):
                            for dx in range(-1, 2):
                                tx, ty = px + dx, py + dy
                                if world.get_tile(tx, ty) != Tile.WATER:
                                    world.set_tile(tx, ty, Tile.WATER)
                        explosions.append({"x": pirate["x"], "y": pirate["y"], "timer": 500})
                        pirates_to_remove.append(pirate)
                        pirates_killed += 1
            # Remove pirates after iteration
            for pirate in pirates_to_remove:
                if pirate in p["pirates"]:
                    p["pirates"].remove(pirate)
            if p["pirates"]:
                avg_x = sum(pirate["x"] for pirate in p["pirates"]) / len(p["pirates"])
                avg_y = sum(pirate["y"] for pirate in p["pirates"]) / len(p["pirates"])
                p["x"], p["y"] = avg_x, avg_y
            p["walk_timer"] = now

def update_krakens():
    global krakens, game_over, pirates_killed, kraken_game_over  # Add kraken_game_over flag
    now = pygame.time.get_ticks()
    for kraken in krakens[:]:
        if not is_night(game_time):
            krakens.remove(kraken)  # Despawn during day
            continue
        if kraken["state"] == "destroying":
            tx, ty = kraken["target_tile"]
            if now - kraken["last_destroy"] >= KRAKEN_DESTROY_DELAY:
                # Check if the player is on the tile
                player_tile_x, player_tile_y = int(player_pos[0] + 0.5), int(player_pos[1] + 0.5)
                if (tx, ty) == (player_tile_x, player_tile_y):
                    game_over = True
                    kraken_game_over = True  # Flag to indicate Kraken caused the game over
                    return  # Exit early since game is over

                # Check for pirates on the tile
                pirates_to_remove = []
                for p in pirates[:]:
                    for pirate in p.get("pirates", [])[:]:
                        pirate_x, pirate_y = int(pirate["x"]), int(pirate["y"])
                        if (pirate_x, pirate_y) == (tx, ty):
                            # Remove the pirate and count it as killed
                            p["pirates"].remove(pirate)
                            pirates_killed += 1
                            explosions.append({"x": pirate["x"], "y": pirate["y"], "timer": 500})  # Visual feedback
                    # Update pirate group position or remove if no pirates left
                    if not p["pirates"]:
                        pirates_to_remove.append(p)
                    else:
                        avg_x = sum(pirate["x"] for pirate in p["pirates"]) / len(p["pirates"])
                        avg_y = sum(pirate["y"] for pirate in p["pirates"]) / len(p["pirates"])
                        p["x"], p["y"] = avg_x, avg_y
                for p in pirates_to_remove:
                    pirates.remove(p)

                # Destroy the boat tile
                if world.get_tile(tx, ty) in [Tile.BOAT, Tile.BOAT_STAGE_2, Tile.BOAT_STAGE_3]:
                    world.set_tile(tx, ty, Tile.WATER)
                    explosions.append({"x": tx, "y": ty, "timer": 500})

                # Look for an adjacent boat tile
                boat_tiles = []
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = int(kraken["x"]) + dx, int(kraken["y"]) + dy
                    if world.get_tile(nx, ny) in [Tile.BOAT, Tile.BOAT_STAGE_2, Tile.BOAT_STAGE_3]:
                        boat_tiles.append((nx, ny))
                if boat_tiles:
                    target_x, target_y = random.choice(boat_tiles)
                    kraken["target_tile"] = (target_x, target_y)
                    kraken["state"] = "moving"
                    kraken["despawn_timer"] = 0
                else:
                    kraken["state"] = "waiting"
                    kraken["despawn_timer"] = now
        elif kraken["state"] == "moving":
            tx, ty = kraken["target_tile"]
            dx = tx - kraken["x"]
            dy = ty - kraken["y"]
            length = math.hypot(dx, dy) or 1
            scaled_speed = KRAKEN_MOVE_SPEED * get_speed_multiplier()
            kraken["x"] += (dx / length) * scaled_speed
            kraken["y"] += (dy / length) * scaled_speed
            if math.hypot(kraken["x"] - tx, kraken["y"] - ty) < 0.1:
                kraken["state"] = "destroying"
                kraken["last_destroy"] = now
        elif kraken["state"] == "waiting":
            if now - kraken["despawn_timer"] >= KRAKEN_DESPAWN_DELAY:
                krakens.remove(kraken)

def update_npcs():
    global npcs
    now = pygame.time.get_ticks()
    for npc in npcs[:]:
        # Check if NPC is in cooldown
        if "interaction_cooldown" in npc and now < npc["interaction_cooldown"]:
            continue  # Skip movement during cooldown
        if npc["state"] == "boat":
            if not npc["ship"]:
                npcs.remove(npc)
                continue
            for s in npc["ship"]:
                s["x"] += npc["dir"][0] * 0.05
                s["y"] += npc["dir"][1] * 0.05
            nx = npc["x"] + npc["dir"][0] * 0.05
            ny = npc["y"] + npc["dir"][1] * 0.05
            landed = False
            landing_tile = None
            for s in npc["ship"]:
                sx, sy = int(s["x"]), int(s["y"])
                if world.get_tile(sx, sy) != Tile.WATER:
                    landed = True
                    landing_tile = (sx, sy)
                    break
            if landed:
                for s in npc["ship"]:
                    sx, sy = int(round(s["x"])), int(round(s["y"]))
                    if world.get_tile(sx, sy) == Tile.WATER:
                        world.set_tile(sx, sy, Tile.BOAT)
                npc["ship"] = [{"x": landing_tile[0], "y": landing_tile[1]}]
                npc["state"] = "docked"
                npc["x"], npc["y"] = landing_tile
                npc["roam_timer"] = now
                npc["move_progress"] = 1.0
                npc["start_x"] = float(landing_tile[0])
                npc["start_y"] = float(landing_tile[1])
                npc["target_x"] = float(landing_tile[0])
                npc["target_y"] = float(landing_tile[1])
            else:
                npc["x"], npc["y"] = nx, ny
        elif npc["state"] == "docked":
            # Roaming logic
            if npc["move_progress"] < 1.0:
                elapsed = dt
                npc["move_progress"] = min(1.0, npc["move_progress"] + elapsed / 300)
                npc["x"] = npc["start_x"] + (npc["target_x"] - npc["start_x"]) * npc["move_progress"]
                npc["y"] = npc["start_y"] + (npc["target_y"] - npc["start_y"]) * npc["move_progress"]
                npc["ship"][0]["x"] = npc["x"]
                npc["ship"][0]["y"] = npc["y"]
            if now - npc["roam_timer"] >= 1000 and npc["move_progress"] >= 1.0:
                neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(neighbors)
                for dx, dy in neighbors:
                    tx, ty = int(npc["x"] + dx), int(npc["y"] + dy)
                    if world.get_tile(tx, ty) in MOVEMENT_TILES:
                        npc["start_x"] = npc["x"]
                        npc["start_y"] = npc["y"]
                        npc["target_x"] = tx
                        npc["target_y"] = ty
                        npc["move_progress"] = 0.0
                        npc["roam_timer"] = now
                        break

def update_turrets():
    now = pygame.time.get_ticks()
    top_left_x = int(player_pos[0] - VIEW_WIDTH // 2)
    top_left_y = int(player_pos[1] - VIEW_HEIGHT // 2)
    for y in range(VIEW_HEIGHT + 2):
        for x in range(VIEW_WIDTH + 2):
            gx, gy = top_left_x + x, top_left_y + y
            if world.get_tile(gx, gy) == Tile.TURRET:
                turret_pos = (gx, gy)
                level = turret_levels.get(turret_pos, 1)
                time_between_shots = BASE_TURRET_FIRE_RATE * (2 ** (-0.040816 * (level - 1)))
                last_fire = turret_cooldowns.get(turret_pos, 0)
                if now - last_fire < time_between_shots:
                    continue
                for p in pirates:
                    for pirate in p.get("pirates", []):
                        dist = math.hypot(pirate["x"] - gx, pirate["y"] - gy)
                        if dist <= TURRET_RANGE:
                            dx, dy = pirate["x"] - gx, pirate["y"] - gy
                            length = math.hypot(dx, dy) or 1
                            projectiles.append({
                                "x": gx,
                                "y": gy,
                                "start_x": gx,  # Store starting position
                                "start_y": gy,
                                "dir": (dx/length, dy/length),
                                "turret_id": turret_pos,
                                "damage": level  # Damage equals turret level
                            })
                            turret_cooldowns[turret_pos] = now
                            break
                    else:
                        continue
                    break

def update_sparks():
    for spark in sparks[:]:
        spark["timer"] -= dt  
        if spark["timer"] <= 0:
            sparks.remove(spark)
            continue
        spark["x"] += spark["vel"][0]
        spark["y"] += spark["vel"][1]

def update_projectiles():
    global pirates_killed, wood
    base_projectile_speed = 0.2
    scaled_projectile_speed = base_projectile_speed * get_speed_multiplier()
    pirates_to_remove = set()
    max_distance = TURRET_RANGE

    for proj in projectiles[:]:
        next_x = proj["x"] + proj["dir"][0] * scaled_projectile_speed
        next_y = proj["y"] + proj["dir"][1] * scaled_projectile_speed
        tile_x, tile_y = int(next_x), int(next_y)

        distance_traveled = math.hypot(next_x - proj["start_x"], next_y - proj["start_y"])
        if distance_traveled > max_distance:
            projectiles.remove(proj)
            continue

        for _ in range(random.randint(1, 3)):
            spark_color = random.choice([(255, 255, 0), (255, 165, 0), (255, 0, 0)])
            spark_vel = [proj["dir"][0] * -0.05 + random.uniform(-0.02, 0.02),
                         proj["dir"][1] * -0.05 + random.uniform(-0.02, 0.02)]
            sparks.append({
                "x": proj["x"],
                "y": proj["y"],
                "vel": spark_vel,
                "timer": 100,
                "color": spark_color
            })

        if world.get_tile(tile_x, tile_y) == Tile.TREE:
            projectiles.remove(proj)
            continue
        if world.get_tile(tile_x, tile_y) == Tile.WALL:
            projectiles.remove(proj)
            continue

        proj["x"] = next_x
        proj["y"] = next_y

        hit = False
        for p in pirates[:]:
            for pirate in p["pirates"][:]:
                if abs(proj["x"] - pirate["x"]) < 0.5 and abs(proj["y"] - pirate["y"]) < 0.5:
                    # Store health before damage
                    pre_hit_health = pirate["health"]
                    pirate["health"] -= proj["damage"]
                    # Check if health reaches 1 or if this hit kills the pirate
                    if pre_hit_health > 1 and pirate["health"] == 1:
                        # Health exactly at 1, spawn hat
                        hat_particles.append({
                            "x": pirate["x"],
                            "y": pirate["y"] - 0.5,
                            "vel_x": random.uniform(-0.05, 0.05),
                            "vel_y": -0.1,
                            "rotation": 0,
                            "rotation_speed": random.uniform(-10, 10),
                            "timer": 1000,
                            "initial_timer": 1000,
                            "level": pirate["level"]
                        })
                        pirate["has_dropped_hat"] = True
                    if pirate["health"] <= 0 and not pirate.get("has_dropped_hat", False):
                        # Lethal hit and no hat dropped yet, spawn hat
                        hat_particles.append({
                            "x": pirate["x"],
                            "y": pirate["y"] - 0.5,
                            "vel_x": random.uniform(-0.05, 0.05),
                            "vel_y": -0.1,
                            "rotation": 0,
                            "rotation_speed": random.uniform(-10, 10),
                            "timer": 1000,
                            "initial_timer": 1000,
                            "level": pirate["level"]
                        })
                        pirate["has_dropped_hat"] = True
                    if pirate["health"] <= 0:
                        if pirate.get("is_rare", False) and pirate.get("rare_type") == "explosive":
                            for key in ["fuse_timer", "fuse_count", "last_count_update"]:
                                pirate.pop(key, None)
                        # Check for rare pirate loot drop
                        if pirate.get("is_rare", False):
                            pirate_tile_x, pirate_tile_y = int(pirate["x"]), int(pirate["y"])
                            tile_type = world.get_tile(pirate_tile_x, pirate_tile_y)
                            if (tile_type in MOVEMENT_TILES and 
                                tile_type not in (Tile.WATER, Tile.BOAT, Tile.TURRET) and 
                                random.random() < 0.33):
                                world.set_tile(pirate_tile_x, pirate_tile_y, Tile.LOOT)
                        p["pirates"].remove(pirate)
                        pirates_killed += 1
                        explosions.append({"x": pirate["x"], "y": pirate["y"], "timer": 500})
                        turret_id = proj.get("turret_id")
                        if turret_id and turret_id in turret_levels:
                            xp_value = pirate["xp_value"]
                            turret_xp[turret_id] = turret_xp.get(turret_id, 0) + xp_value
                            xp_texts.append({
                                "x": turret_id[0],
                                "y": turret_id[1],
                                "text": f"+{xp_value} XP",
                                "timer": 1000,
                                "alpha": 255
                            })
                            level = turret_levels[turret_id]
                            xp_needed = math.pow(2, level - 1)
                            if level < TURRET_MAX_LEVEL and turret_xp[turret_id] >= xp_needed:
                                turret_levels[turret_id] += 1
                                turret_xp[turret_id] -= xp_needed
                    hit = True
                    break
                if hit:
                    break

            for s in p["ship"][:]:
                if abs(proj["x"] - s["x"]) < 0.3 and abs(proj["y"] - s["y"]) < 0.3:
                    p["ship"].remove(s)
                    hit = True
                    break
                if hit:
                    break

            if not p["pirates"] and not p["ship"]:
                pirates_to_remove.add(id(p))

        if hit and proj in projectiles:
            projectiles.remove(proj)

    pirates[:] = [p for p in pirates if id(p) not in pirates_to_remove]

def update_fishing():
    global fishing_state, bobber, fish_tiles, wood, fish_caught
    if not fishing_state:
        return
    
    now = pygame.time.get_ticks()
    
    # Cancel fishing if player moves
    if any(pygame.key.get_pressed()[k] for k in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]):
        fishing_state = None
        bobber = None
        return
    
    # Update bobber
    if bobber["state"] == "moving":
        dx = bobber["target_x"] - bobber["x"]
        dy = bobber["target_y"] - bobber["y"]
        dist = math.hypot(dx, dy)
        if dist < bobber_speed:
            bobber["x"] = bobber["target_x"]
            bobber["y"] = bobber["target_y"]
            bobber["state"] = "waiting"
            bobber["bite_timer"] = now + random.uniform(2000, 5000)  # Next bite in 2–5s
            bobber["last_switch"] = now
            fishing_state = "fishing"  # Transition to fishing state
        else:
            bobber["x"] += (dx / dist) * bobber_speed
            bobber["y"] += (dy / dist) * bobber_speed
    elif bobber["state"] == "waiting":
        if now >= bobber["bite_timer"]:
            bobber["state"] = "biting"
            bobber["bite_timer"] = now + bite_duration
            bobber["last_switchtsam"] = now
    elif bobber["state"] == "biting":
        # Switch between bobber2.png and bobber3.png every 500ms
        if now - bobber["last_switch"] >= 500:
            bobber["last_switch"] += 500  # Increment by 500ms instead of resetting to now
        if now >= bobber["bite_timer"]:
            bobber["state"] = "waiting"
            bobber["bite_timer"] = now + random.uniform(2000, 5000)
            bobber["last_switch"] = now
    
    # Check if fish tile despawned
    fish_tile = next((fish for fish in fish_tiles if fish["x"] == bobber["target_x"] - 0.5 and fish["y"] == bobber["target_y"] - 0.5), None)
    if not fish_tile or now - fish_tile["spawn_time"] >= fish_despawn_time or world.get_tile(fish_tile["x"], fish_tile["y"]) != Tile.FISH:
        fishing_state = None
        bobber = None

def draw_interaction_ui():
    if not interaction_ui["left_message"] and not interaction_ui["right_message"]:
        return

    if not selected_tile:
        return

    # Convert selected tile to screen coordinates
    top_left_x = player_pos[0] - VIEW_WIDTH // 2
    top_left_y = player_pos[1] - VIEW_HEIGHT // 2
    sel_x, sel_y = selected_tile
    px = sel_x - top_left_x
    py = sel_y - top_left_y

    font = pygame.font.SysFont(None, 14)
    tile_center_x = px * TILE_SIZE + TILE_SIZE // 2
    tile_top_y = py * TILE_SIZE - 10 - interaction_ui["offset"]

    if interaction_ui["left_message"]:
        lines = interaction_ui["left_message"].split("\n")
        text_surfaces = [font.render(line.strip(), True, WHITE) for line in lines if line.strip()]
        total_height = sum(text.get_height() for text in text_surfaces)
        max_width = max(text.get_width() for text in text_surfaces)
        left_surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
        y_offset = 0
        for text in text_surfaces:
            left_surface.blit(text, (0, y_offset))
            y_offset += text.get_height()
        left_rect = left_surface.get_rect(right=tile_center_x - 10, centery=tile_top_y)
        left_surface.set_alpha(interaction_ui["alpha"])
        game_surface.blit(left_surface, left_rect.topleft)

    if interaction_ui["right_message"]:
        lines = interaction_ui["right_message"].split("\n")
        text_surfaces = [font.render(line.strip(), True, WHITE) for line in lines if line.strip()]
        total_height = sum(text.get_height() for text in text_surfaces)
        max_width = max(text.get_width() for text in text_surfaces)
        right_surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
        y_offset = 0
        for text in text_surfaces:
            right_surface.blit(text, (0, y_offset))
            y_offset += text.get_height()
        right_rect = right_surface.get_rect(left=tile_center_x + 10, centery=tile_top_y)
        right_surface.set_alpha(interaction_ui["alpha"])
        game_surface.blit(right_surface, right_rect.topleft)

def update_hat_particles():
    for hat in hat_particles[:]:
        hat["timer"] -= dt
        if hat["timer"] <= 0:
            hat_particles.remove(hat)
            continue
        hat["x"] += hat["vel_x"]
        hat["y"] += hat["vel_y"]
        hat["vel_y"] += 0.002
        hat["rotation"] = (hat["rotation"] + hat["rotation_speed"]) % 360

def update_wood_texts():
    for text in wood_texts[:]:
        text["timer"] -= dt
        if text["timer"] <= 0:
            wood_texts.remove(text)
            continue
        # Move text/image upward
        text["y"] -= 0.02
        # Fade out
        text["alpha"] = int((text["timer"] / 1000) * 255)
        text["alpha"] = max(0, min(255, text["alpha"]))

def update_xp_texts():
    for text in xp_texts[:]:
        text["timer"] -= dt
        if text["timer"] <= 0:
            xp_texts.remove(text)
            continue
        text["y"] -= 0.02  # Move upward
        text["alpha"] = int((text["timer"] / 1000) * 255)
        text["alpha"] = max(0, min(255, text["alpha"]))

def has_adjacent_boat_or_land(x, y):
    # Check if the tile at (x, y) has a BOAT_TILE or LAND tile in cardinal directions.
    neighbors = [(x, y-1), (x, y+1), (x-1, y), (x+1, y)]  # Up, down, left, right
    for nx, ny in neighbors:
        tile = world.get_tile(nx, ny)
        if tile in LAND_TILES:
            return True
    return False

def interact(button):
    global wood, tiles_placed, turrets_placed, wall_placement_mode, boulder_placement_mode, picked_boulder_pos, fishing_state, bobber, has_fishing_rod, fish_caught, player_xp, player_level, player_pos, player_xp_texts, pirates_killed, boat_entity, steering_interaction, in_boat_mode




    if not selected_tile:
        return
    x, y = selected_tile
    # Check Manhattan distance from player
    player_tile_x, player_tile_y = int(player_pos[0]), int(player_pos[1])
    manhattan_dist = abs(x - player_tile_x) + abs(y - player_tile_y)
    if manhattan_dist > 3:
        return  # Block interactions if too far
    tile = world.get_tile(x, y)
    
    if button == 1:  # Left-click
        # Attack pirates
        for p in pirates:
            for pirate in p["pirates"][:]:  # Iterate over copy to allow removal
                dist = math.hypot(pirate["x"] - x, pirate["y"] - y)
                if dist < 0.5:  # Within 0.5 tiles
                    pre_hit_health = pirate["health"]
                    pirate["health"] -= player_level  # Deal damage equal to player level
                    # Handle hat drop at health = 1
                    if pre_hit_health > 1 and pirate["health"] == 1 and not pirate.get("has_dropped_hat", False):
                        hat_particles.append({
                            "x": pirate["x"],
                            "y": pirate["y"] - 0.5,
                            "vel_x": random.uniform(-0.05, 0.05),
                            "vel_y": -0.1,
                            "rotation": 0,
                            "rotation_speed": random.uniform(-10, 10),
                            "timer": 1000,
                            "initial_timer": 1000,
                            "level": pirate["level"]
                        })
                        pirate["has_dropped_hat"] = True
                    if pirate["health"] <= 0:
                        if pirate.get("is_rare", False) and pirate.get("rare_type") == "explosive":
                            for key in ["fuse_timer", "fuse_count", "last_count_update"]:
                                pirate.pop(key, None)
                        # Drop loot for rare pirates
                        if pirate.get("is_rare", False):
                            pirate_tile_x, pirate_tile_y = int(pirate["x"]), int(pirate["y"])
                            tile_type = world.get_tile(pirate_tile_x, pirate_tile_y)
                            if (tile_type in MOVEMENT_TILES and 
                                tile_type not in (Tile.WATER, Tile.BOAT, Tile.TURRET) and 
                                random.random() < 0.33):
                                world.set_tile(pirate_tile_x, pirate_tile_y, Tile.LOOT)
                        # Award XP
                        xp_gained = pirate["xp_value"]
                        player_xp += xp_gained
                        player_xp_texts.append({
                            "x": player_pos[0],
                            "y": player_pos[1],
                            "text": f"+{xp_gained} XP",
                            "timer": 1000,
                            "alpha": 255
                        })
                        # Check for level-up
                        while player_level < player_max_level and player_xp >= math.pow(2, player_level - 1):
                            player_xp -= math.pow(2, player_level - 1)
                            player_level += 1
                            player_xp_texts.append({
                                "x": player_pos[0],
                                "y": player_pos[1],
                                "text": f"Level Up! Level {player_level}",
                                "timer": 1000,
                                "alpha": 255
                            })
                        p["pirates"].remove(pirate)
                        pirates_killed += 1
                        explosions.append({"x": pirate["x"], "y": pirate["y"], "timer": 500})
                    return  # Exit after attacking
        # Check if clicking the NPC
        for npc in npcs:
            if npc["type"] == "waller" and any(s["x"] == x and s["y"] == y for s in npc["ship"]):
                # Capture NPC's position at interaction
                interaction_pos_x, interaction_pos_y = npc["x"], npc["y"]
                if not has_fishing_rod and wood >= 50:
                    has_fishing_rod = True
                    wood -= 50
                    wood_texts.append({
                        "x": interaction_pos_x,
                        "y": interaction_pos_y - 0.5,
                        "text": "-50 Wood",  # Corrected from "-10 Wood" to match cost
                        "timer": 1000,
                        "alpha": 255
                    })
                    wood_texts.append({
                        "x": interaction_pos_x,
                        "y": interaction_pos_y - 0.5,
                        "text": "",  # Empty text, using image instead
                        "image_key": "FISHING_ROD",  # Use key instead of Surface
                        "timer": 1000,
                        "alpha": 255
                    })
                else:
                    wood_texts.append({
                        "x": interaction_pos_x,
                        "y": interaction_pos_y - 0.5,
                        "text": f"Fish Caught: {fish_caught}",
                        "timer": 1000,
                        "alpha": 255
                    })
                # Add interaction cooldown to pause NPC movement
                npc["interaction_cooldown"] = pygame.time.get_ticks() + 3000  # 3 seconds
                return
        # Interact with fish tile
        if tile == Tile.FISH and has_fishing_rod:
            fish_data = next((f for f in fish_tiles if f["x"] == x and f["y"] == y), None)
            if fish_data:
                if fishing_state == "fishing" and bobber and bobber["state"] == "biting" and bobber["target_x"] == x + 0.5 and bobber["target_y"] == y + 0.5:
                    # Catch fish
                    wood_gained = random.randint(5, 10)
                    wood += wood_gained
                    fish_caught += 1
                    wood_texts.append({
                        "x": x,
                        "y": y,
                        "text": f"+{wood_gained} Wood",
                        "timer": 1000,
                        "alpha": 255
                    })
                    fishing_state = None
                    bobber = None
                elif not fishing_state:
                    # Start fishing
                    fishing_state = "casting"
                    bobber = {
                        "x": player_pos[0] + 0.5,
                        "y": player_pos[1] + 0.5,
                        "target_x": x + 0.5,
                        "target_y": y + 0.5,
                        "state": "moving",
                        "bite_timer": 0,
                        "last_switch": 0
                    }
            return
        # Handle boulder placement
        if boulder_placement_mode:
            # Can only place on LAND or where the boulder was originally picked up
            if (tile == Tile.LAND or (x, y) == picked_boulder_pos):
                world.set_tile(x, y, Tile.BOULDER)
                boulder_placement_mode = False
                picked_boulder_pos = None
                interaction_ui["left_message"] = ""
                interaction_ui["alpha"] = 0
            return
        # Handle wall placement
        if wall_placement_mode:
            if tile == Tile.LAND and wood >= 100:
                world.set_tile(x, y, Tile.WALL)
                wood -= 100
                tiles_placed += 1
                wall_levels[(x, y)] = 1  # Initialize wall at level 1
                # Optionally keep mode active: wall_placement_mode = False
            return
        # Pick up boulder
        if tile == Tile.BOULDER:
            world.set_tile(x, y, Tile.LAND)  # Remove boulder from current position
            boulder_placement_mode = True
            picked_boulder_pos = (x, y)  # Store original position
            interaction_ui["left_message"] = "Click a land tile to place the boulder\nRight click to cancel"
            interaction_ui["alpha"] = 255
            return
        if tile == Tile.STEERING_WHEEL and not in_boat_mode:
            sx, sy = x, y
            connected_tiles = find_connected_boat_tiles(sx, sy)
            if connected_tiles:
                # Store relative offsets from steering wheel
                offsets = [(tx - sx, ty - sy) for tx, ty in connected_tiles]
                # Convert all connected tiles (including steering wheel) to water
                for tx, ty in connected_tiles:
                    world.set_tile(tx, ty, Tile.WATER)
                world.set_tile(sx, sy, Tile.WATER)  # Ensure steering wheel tile is also water
                # Define boat entity with offsets
                boat_entity = {"offsets": offsets}
                in_boat_mode = True
                player_pos = [sx + 0.5, sy + 0.5]  # Snap to steering wheel position
            return
        if tile == Tile.BOAT and wood >= 1:
            # Place steering wheel 
            world.set_tile(x, y, Tile.STEERING_WHEEL)
            wood -= 1 #TODO Update to correct cost later
            tiles_placed += 1                
            return
        # Place Boat Tile
        if tile == Tile.WATER and wood >= 3 and has_adjacent_boat_or_land(x, y):
            world.set_tile(x, y, Tile.BOAT)
            wood -= 3
            tiles_placed += 1
            sound_place_land.play()
        elif tile == Tile.LOOT:
            wood_gained = random.randint(5, 10)
            wood += wood_gained
            world.set_tile(x, y, Tile.LAND)
            wood_texts.append({
                "x": x,
                "y": y,
                "text": f"+{wood_gained} Wood",
                "timer": 1000,
                "alpha": 255
            })
        elif tile == Tile.TREE:
            world.set_tile(x, y, Tile.LAND)
            wood_gained = random.randint(2, 4)
            wood += wood_gained
            wood_texts.append({
                "x": x,
                "y": y,
                "text": f"+{wood_gained} Wood",
                "timer": 1000,
                "alpha": 255
            })
        elif tile == Tile.SAPLING:
            world.set_tile(x, y, Tile.LAND)
            wood += 1
            if (x, y) in tree_growth:
                del tree_growth[(x, y)]
        else:
            plant_sapling()
    
    elif button == 3:  # Right-click
        # Cancel fishing
        if fishing_state:
            fishing_state = None
            bobber = None
            return
        if boulder_placement_mode:
            # Cancel boulder placement and return it to its original position
            if picked_boulder_pos:
                world.set_tile(picked_boulder_pos[0], picked_boulder_pos[1], Tile.BOULDER)
            boulder_placement_mode = False
            picked_boulder_pos = None
            interaction_ui["left_message"] = ""
            interaction_ui["alpha"] = 0
            return
        if wall_placement_mode:
            wall_placement_mode = False
            interaction_ui["left_message"] = ""
            interaction_ui["alpha"] = 0
            return
        # Convert boulder to wall or level up existing wall
        if tile == Tile.BOULDER and wood >= 5:
            world.set_tile(x, y, Tile.WALL)
            wall_levels[(x, y)] = 1  # Start at level 1
            wood -= 5
            tiles_placed += 1
        elif tile == Tile.WALL and wood >= 5:
            current_level = wall_levels.get((x, y), 1)
            wall_levels[(x, y)] = current_level + 1  # Increase level
            wood -= 5
            tiles_placed += 1
        if steering_interaction and tile == Tile.STEERING_WHEEL:
            steering_interaction = False
            return
        if in_boat_mode:
            # Exit boat mode: Place boat tiles back
            for offset in boat_entity["offsets"]:
                tile_x = int(player_pos[0] + offset[0] + 0.5)
                tile_y = int(player_pos[1] + offset[1] + 0.5)
                world.set_tile(tile_x, tile_y, Tile.BOAT)
            # Place steering wheel at player's current position
            steering_x = int(player_pos[0] + 0.5)
            steering_y = int(player_pos[1] + 0.5)
            world.set_tile(steering_x, steering_y, Tile.STEERING_WHEEL)
            in_boat_mode = False
            boat_entity = None
            return
        turret_pos = (x, y)
        if tile == Tile.TURRET:
            level = turret_levels.get(turret_pos, 1)
            refund = 3
            world.set_tile(x, y, Tile.LAND)
            wood += refund
            turrets_placed = max(0, turrets_placed - 1)
            if turret_pos in turret_cooldowns:
                del turret_cooldowns[turret_pos]
            if turret_pos in turret_levels:
                del turret_levels[turret_pos]
            if turret_pos in turret_xp:
                del turret_xp[turret_pos]
        elif tile == Tile.LAND and wood >= 3:
            world.set_tile(x, y, Tile.TURRET)
            wood -= 3
            turrets_placed += 1
            turret_levels[turret_pos] = 1
            turret_xp[turret_pos] = 0
            sound_place_turret.play()

def update_interaction_ui():
    global wood, interaction_ui, stationary_timer, last_player_pos, has_fishing_rod
    if not interaction_ui_enabled:
        interaction_ui["alpha"] = 0
        interaction_ui["offset"] = 20
        interaction_ui["fade_timer"] = 0
        return

    # Check if the player has moved
    current_pos = list(player_pos)
    if current_pos != last_player_pos:
        interaction_ui["alpha"] = 0
        interaction_ui["offset"] = 20
        interaction_ui["fade_timer"] = 0
        stationary_timer = 0
        last_player_pos = current_pos
        return
    else:
        stationary_timer += dt
        if stationary_timer < STATIONARY_DELAY:
            interaction_ui["alpha"] = 0
            interaction_ui["offset"] = 20
            interaction_ui["fade_timer"] = 0
            return

    if not selected_tile:
        interaction_ui["left_message"] = ""
        interaction_ui["right_message"] = ""
        interaction_ui["alpha"] = 0
        interaction_ui["offset"] = 20
        interaction_ui["fade_timer"] = 0
        return

    x, y = selected_tile
    tile = world.get_tile(x, y)
    interaction_ui["left_message"] = ""
    interaction_ui["right_message"] = ""

    # Show boulder placement message when in boulder placement mode
    if boulder_placement_mode:
        interaction_ui["left_message"] = "Click a land tile to place the boulder\nRight click to cancel"
        interaction_ui["alpha"] = 255
        return

    # Show NPC interaction message
    for npc in npcs:
        if npc["type"] == "waller" and any(s["x"] == x and s["y"] == y for s in npc["ship"]):
            if not has_fishing_rod and wood >= 50:
                has_fishing_rod = True
                wood -= 50
                wood_texts.append({
                    "x": player_pos[0],
                    "y": player_pos[1] - 0.5,
                    "text": "-50 Wood",  # Corrected from "-10 Wood"
                    "timer": 1000,
                    "alpha": 255
                })
                wood_texts.append({
                    "x": player_pos[0],
                    "y": player_pos[1] - 0.5,
                    "text": "",  # Empty text, using image instead
                    "image_key": "FISHING_ROD",  # Use key instead of Surface
                    "timer": 1000,
                    "alpha": 255
                })
            else:
                wood_texts.append({
                    "x": player_pos[0],
                    "y": player_pos[1] - 0.5,
                    "text": f"Fish Caught: {fish_caught}",
                    "timer": 1000,
                    "alpha": 255
                })
            return
        
    # Show fish tile interaction
    if tile == Tile.FISH and has_fishing_rod:
        interaction_ui["left_message"] = "Fish for Wood\n(Left Click)"
        interaction_ui["alpha"] = 255
    elif steering_interaction and tile == Tile.STEERING_WHEEL:
        interaction_ui["left_message"] = "Click to move boat\nRight click to cancel"
        interaction_ui["alpha"] = 255
        return
    elif tile == Tile.BOAT and wood >= 150 and not boat_entity:
        interaction_ui["right_message"] = "Place Steering Wheel\n-150 Wood"
    elif tile == Tile.STEERING_WHEEL:
        interaction_ui["left_message"] = "Steer Boat"
    # Show boulder pickup message
    elif tile == Tile.BOULDER:
        interaction_ui["left_message"] = "Pick up Boulder"
        if wood >= 5:
            interaction_ui["right_message"] = "Convert to Wall\n-5 Wood\n(Level 1)"
    elif tile == Tile.WALL:
        level = wall_levels.get((x, y), 1)
        if wood >= 5:
            interaction_ui["right_message"] = f"Upgrade Wall\n-5 Wood\n(Level {level + 1})"
    elif tile == Tile.WATER and wood >= 3 and has_adjacent_boat_or_land(x, y):
        interaction_ui["left_message"] = "Place Boat Tile\n-3 Wood\n(Next to Boat/Land)"
    elif tile == Tile.LOOT:
        interaction_ui["left_message"] = "Collect\n+5-10 Wood"
    elif tile == Tile.TREE:
        interaction_ui["left_message"] = "Chop\n+2-4 Wood"
    elif tile == Tile.SAPLING:
        interaction_ui["left_message"] = "Uproot\n+1 Wood"
    elif tile == Tile.TURRET:
        turret_pos = (x, y)
        level = turret_levels.get(turret_pos, 1)
        interaction_ui["right_message"] = "Pickup\n+3 Wood"
    elif tile == Tile.LAND:
        if wood >= 1:
            interaction_ui["left_message"] = "Plant Sapling\n-1 Wood"
        if wood >= 3:
            interaction_ui["right_message"] = "Place Turret\n-3 Wood"

    if not interaction_ui["left_message"] and not interaction_ui["right_message"]:
        interaction_ui["alpha"] = 0
        interaction_ui["offset"] = 20
        interaction_ui["fade_timer"] = 0
    else:
        if interaction_ui["fade_timer"] < interaction_ui["fade_duration"]:
            interaction_ui["fade_timer"] += dt
            progress = min(1.0, interaction_ui["fade_timer"] / interaction_ui["fade_duration"])
            interaction_ui["alpha"] = int(progress * 255)
            interaction_ui["offset"] = 20 * (1 - progress)

def plant_sapling():
    global wood
    if not selected_tile:
        return
    x, y = selected_tile
    if world.get_tile(x, y) == Tile.LAND and wood >= 1:
        world.set_tile(x, y, Tile.SAPLING)
        tree_growth[(x, y)] = pygame.time.get_ticks()
        wood -= 1
        sound_plant_sapling.play()

def update_trees():
    now = pygame.time.get_ticks()
    to_grow = [pos for pos, t in tree_growth.items() if now - t >= sapling_growth_time]
    for pos in to_grow:
        world.set_tile(pos[0], pos[1], Tile.TREE)
        del tree_growth[pos]

def update_player_movement():
    global player_pos, facing, fishing_state, bobber, in_boat_mode, boat_entity
    keys = pygame.key.get_pressed()
    
    # Initialize dx and dy at the start
    dx, dy = 0.0, 0.0
    
    if in_boat_mode:
        base_speed = 0.05  # Match pirate ship speed
        speed = base_speed * get_speed_multiplier()
        if keys[pygame.K_w]:
            dy -= speed
        if keys[pygame.K_s]:
            dy += speed
        if keys[pygame.K_a]:
            dx -= speed
        if keys[pygame.K_d]:
            dx += speed
        # Check for movement to cancel fishing
        if dx != 0 or dy != 0:
            fishing_state = None
            bobber = None
            new_x = player_pos[0] + dx
            new_y = player_pos[1] + dy
            # Check if all boat tiles can move to new positions
            can_move = True
            for offset in boat_entity["offsets"]:
                tile_x = int(new_x + offset[0] + 0.5)
                tile_y = int(new_y + offset[1] + 0.5)
                tile = world.get_tile(tile_x, tile_y)
                if tile not in (Tile.WATER, Tile.FISH):
                    can_move = False
                    break
            if can_move:
                old_chunk = world.player_chunk
                player_pos[0] = new_x
                player_pos[1] = new_y
                world.update_player_chunk(player_pos)
                new_chunk = world.player_chunk
                if old_chunk != new_chunk:
                    world.manage_chunks(player_pos)
    else:
        base_speed = 0.15
        speed = base_speed * get_speed_multiplier()
        if keys[pygame.K_w]:
            dy -= speed
        if keys[pygame.K_s]:
            dy += speed
        if keys[pygame.K_a]:
            dx -= speed
        if keys[pygame.K_d]:
            dx += speed
        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            if length > 0:
                dx, dy = dx / length * speed, dy / length * speed
            facing = [dx, dy] if dx != 0 or dy != 0 else facing
        new_x, new_y = player_pos[0] + dx, player_pos[1] + dy
        if is_on_land((new_x, new_y)):
            old_chunk = world.player_chunk
            player_pos[0], player_pos[1] = new_x, new_y
            world.update_player_chunk(player_pos)
            new_chunk = world.player_chunk
            if old_chunk != new_chunk:
                world.manage_chunks(player_pos)

def update_player_xp_texts():
    for text in player_xp_texts[:]:
        text["timer"] -= dt
        if text["timer"] <= 0:
            player_xp_texts.remove(text)
            continue
        text["y"] -= 0.02  # Move upward
        text["alpha"] = int((text["timer"] / 1000) * 255)
        text["alpha"] = max(0, min(255, text["alpha"]))

def get_darkness_factor(game_time):
    cycle = 96.0  # Total cycle length: 48s day + 48s night
    t = game_time % cycle
    # Day: 7am (28s) to 7pm (76s)
    if 28 <= t < 76:
        return 0.0  # Full day
    # Fade-in: 7pm (76s) to 8pm (80s)
    elif 76 <= t < 80:
        progress = (t - 76) / 4  # 4-second fade (doubled from 2s)
        return progress
    # Full night: 8pm (80s) to 6am (24s next cycle)
    elif (80 <= t < 96) or (0 <= t < 24):
        return 1.0  # Full night
    # Fade-out: 6am (24s) to 7am (28s)
    elif 24 <= t < 28:
        progress = (t - 24) / 4  # 4-second fade (doubled from 2s)
        return 1.0 - progress
    return 0.0

def is_night(game_time):
    t = game_time % 96
    return t >= 76 or t < 28  # Night from 76s (7pm) to 28s (7am)

def get_time_string(game_time):
    cycle = 96.0
    total_minutes = (game_time % cycle) * 15  # Each second = 15 minutes
    hour = int(total_minutes // 60) % 24
    minute = total_minutes % 60
    display_hour = hour % 12
    if display_hour == 0:
        display_hour = 12
    period = "am" if hour < 12 else "pm"
    # Map minutes to 15-minute increments
    if minute < 7.5:
        minute_str = "00"
    elif minute < 22.5:
        minute_str = "15"
    elif minute < 37.5:
        minute_str = "30"
    else:
        minute_str = "45"
    return f"{display_hour}:{minute_str}{period}"
    
def update_music():
    global current_music, music_fade_timer
    new_period = get_music_period(game_time)
    
    if new_period != current_music:
        if music_fade_timer == 0:
            # Start fading out current music
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(music_fade_duration)
            music_fade_timer = music_fade_duration
        else:
            # Continue fading
            music_fade_timer -= dt
            if music_fade_timer <= 0:
                # Fade complete, switch to new music
                music_fade_timer = 0
                current_music = new_period
                pygame.mixer.music.load(MUSIC_FILES[current_music])
                pygame.mixer.music.play(-1)  # Loop indefinitely

# --- Game Loop ---
running = True
while running:
    dt = clock.get_time()  # Compute delta time once per frame
    if game_over:
        if not fade_done:
            show_game_over()
            fade_done = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                world.clear_chunk_files()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    world.clear_chunk_files()
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_SPACE:
                    subprocess.Popen([sys.executable, os.path.abspath(__file__)])
                    world.clear_chunk_files()
                    pygame.quit()
                    sys.exit()
        continue

    game_time += dt / 1000.0  # Convert milliseconds to seconds
    cycle_length = 96.0  # One day-night cycle in seconds
    if game_time - last_cycle_time >= cycle_length:
        days_survived += 1
        last_cycle_time = game_time - (game_time % cycle_length)  # Align to cycle boundary
    game_surface.fill(BLACK)
    update_music()
    update_sparks()
    update_wood_texts()
    update_xp_texts()
    update_player_xp_texts()
    update_hat_particles()
    water_frame_timer += dt
    if water_frame_timer >= WATER_FRAME_DELAY:
        water_frame = (water_frame + 1) % len(water_frames)
        water_frame_timer = 0
        scaled_tile_images[Tile.WATER] = scaled_water_frames[water_frame]
    # Update selected tile based on mouse position
    mouse_x, mouse_y = pygame.mouse.get_pos()
    world_tile_x, world_tile_y = screen_to_world(mouse_x, mouse_y)
    # Ensure the tile is within the viewable area
    if (0 <= (world_tile_x - (player_pos[0] - VIEW_WIDTH // 2)) < VIEW_WIDTH and
        0 <= (world_tile_y - (player_pos[1] - VIEW_HEIGHT // 2)) < VIEW_HEIGHT):
        selected_tile = (world_tile_x, world_tile_y)
    else:
        selected_tile = None
    draw_grid()
    scaled_surface = pygame.transform.scale(game_surface, (WIDTH * SCALE, HEIGHT * SCALE))
    screen_width, screen_height = screen.get_size()
    blit_x = (screen_width - WIDTH * SCALE) // 2
    blit_y = (screen_height - HEIGHT * SCALE) // 2
    screen.fill(BLACK)
    screen.blit(scaled_surface, (blit_x, blit_y))
    draw_ui()
    draw_minimap()
    pygame.display.flip()

    update_trees()
    update_land_spread()
    update_interaction_ui()
    update_pirates()
    update_krakens()
    update_npcs()
    update_turrets()
    update_projectiles()
    update_fish_tiles()
    update_fishing()

    fish_spawn_timer += dt
    if fish_spawn_timer >= FISH_SPAWN_INTERVAL:
        spawn_fish_tiles()
        fish_spawn_timer = 0    

    if wood >= 50 and not waller_npc_spawned:
        spawn_waller_npc()
        waller_npc_spawned = True

    pirate_spawn_timer += dt
    t = game_time % 96
    if pirate_spawn_timer >= spawn_delay and ((t > 24 and t < 28) or (t >= 76 and t < 96)):
        spawn_pirate()
        spawn_kraken()
        pirate_spawn_timer = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            score = turrets_placed + pirates_killed + tiles_placed
            if score > high_score:
                with open("score.txt", "w") as f:
                    f.write(str(score))
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_i:
                interaction_ui_enabled = not interaction_ui_enabled
                if not interaction_ui_enabled:
                    interaction_ui["alpha"] = 0
                    interaction_ui["offset"] = 20
                    interaction_ui["fade_timer"] = 0
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in [1, 3]:  # Left or right click
                interact(event.button)
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0 and SCALE < MAX_SCALE:
                SCALE += 1
            elif event.y < 0 and SCALE > MIN_SCALE:
                SCALE -= 1
    
    update_player_movement()
    view_left = int(player_pos[0] - VIEW_WIDTH // 2)
    view_top = int(player_pos[1] - VIEW_HEIGHT // 2)
    view_right = view_left + VIEW_WIDTH
    view_bottom = view_top + VIEW_HEIGHT

    clock.tick(60)

pygame.quit()