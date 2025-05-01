import pygame
import random
import sys
import math
import os
import subprocess
import pickle
import shutil

# --- Init ---
pygame.init()
pygame.mixer.init()

# Define the chunk directory path
CHUNK_DIR = "chunks"

# Create the directory if it doesn't exist
if not os.path.exists(CHUNK_DIR):
    try:
        os.makedirs(CHUNK_DIR)
    except OSError as e:
        print(f"Error: Could not create chunk directory: {e}")
        sys.exit(1)

# Delete all files inside the chunks directory
for filename in os.listdir(CHUNK_DIR):
    file_path = os.path.join(CHUNK_DIR, filename)
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
    except PermissionError as e:
        print(f"Warning: Could not delete file {file_path} due to permission error: {e}")
    except OSError as e:
        print(f"Warning: Could not delete file {file_path}: {e}")

SCALE = 2
MIN_SCALE = 1
MAX_SCALE = 4

TILE_SIZE = 32
VIEW_WIDTH, VIEW_HEIGHT = 20, 20
WIDTH, HEIGHT = VIEW_WIDTH * TILE_SIZE, VIEW_HEIGHT * TILE_SIZE
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()

xp_texts = []
explosions = []
sparks = []
hat_particles = []

# --- Sounds ---
sound_place_land = pygame.mixer.Sound("Assets/sound/place_land.wav")
sound_plant_sapling = pygame.mixer.Sound("Assets/sound/plant_sapling.wav")
sound_place_turret = pygame.mixer.Sound("Assets/sound/place_turret.wav")

# --- Colors ---
BLUE = (50, 150, 255)
GREEN = (50, 200, 50)
BROWN = (139, 69, 19)
DARK_GRAY = (80, 80, 80)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
TAN = (210, 180, 140)
LIGHT_GRAY = (200, 200, 200)

# --- Tile Types ---
WATER, LAND, TREE, SAPLING, WALL, TURRET, BOAT_TILE, USED_LAND, LOOT = range(9)

# --- Load Tile Images ---
tile_images = {
    WATER: pygame.image.load("Assets/water.png").convert(),
    LAND: pygame.image.load("Assets/land.png").convert(),
    TREE: pygame.image.load("Assets/tree.png").convert_alpha(),
    SAPLING: pygame.image.load("Assets/sapling.png").convert_alpha(),
    WALL: pygame.image.load("Assets/wall.png").convert(),
    TURRET: pygame.image.load("Assets/turret.png").convert_alpha(),
    BOAT_TILE: pygame.image.load("Assets/boat_tile.png").convert(),
    USED_LAND: pygame.image.load("Assets/used_land.png").convert(),
    "UNDER_LAND": pygame.image.load("Assets/under_land.png").convert_alpha(),
    "UNDER_WOOD": pygame.image.load("Assets/under_wood.png").convert_alpha(),
    LOOT: pygame.image.load("Assets/loot.png").convert_alpha()
}

water_frames = [
    pygame.image.load("Assets/water.png").convert(),
    pygame.image.load("Assets/water1.png").convert(),
    pygame.image.load("Assets/water2.png").convert()
]
water_frame = 0
water_frame_timer = 0
water_frame_delay = 1200

player_image = pygame.image.load("Assets/player.png").convert_alpha()
# Load base pirate (hatless) and level-specific pirates and hats
pirate_sprites = {
    "base": pygame.image.load("Assets/pirate/pirate.png").convert_alpha()
}
for level in range(1, 11):
    pirate_sprites[f"level_{level}"] = pygame.image.load(f"Assets/pirate/pirate{level}.png").convert_alpha()

pirate_hat_images = {
    level: pygame.image.load(f"Assets/pirate/pirate_hat{level}.png").convert_alpha() for level in range(1, 11)
}

# Load high score
try:
    with open("score.txt", "r") as f:
        high_score = int(f.read())
except:
    high_score = 0

# --- Chunk System ---
CHUNK_SIZE = 16  # Each chunk is 16x16 tiles
VIEW_CHUNKS = 3  # Load a 3x3 chunk grid around the player

chunks = {}  # Dictionary: {(cx, cy): [[tile]]}
player_chunk = (0, 0)  # Player's current chunk

def world_to_chunk(x, y):
    """Convert world coordinates to chunk coordinates."""
    return x // CHUNK_SIZE, y // CHUNK_SIZE

def chunk_to_world(cx, cy, tx, ty):
    """Convert chunk coordinates and tile offsets to world coordinates."""
    return cx * CHUNK_SIZE + tx, cy * CHUNK_SIZE + ty

def generate_chunk(cx, cy):
    """Generate a new chunk with medium-sized land masses and occasional trees."""
    chunk = [[WATER for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]
    total_tiles = CHUNK_SIZE * CHUNK_SIZE  # 256 tiles in a 16x16 chunk
    target_land_tiles = int(total_tiles * 0.1)  # 10% land = ~26 tiles per chunk
    min_mass_size = 5
    max_mass_size = 15
    land_tiles_placed = 0

    # Keep generating land masses until we reach the target number of land tiles
    while land_tiles_placed < target_land_tiles:
        # Pick a random starting point that is water
        available_positions = [(tx, ty) for ty in range(CHUNK_SIZE) for tx in range(CHUNK_SIZE) if chunk[ty][tx] == WATER]
        if not available_positions:
            break  # No more space for new land masses

        start_x, start_y = random.choice(available_positions)
        
        # Calculate the remaining tiles needed
        remaining_tiles = target_land_tiles - land_tiles_placed
        
        # Determine the size of this land mass
        if remaining_tiles < min_mass_size:
            mass_size = remaining_tiles  # Use the remaining tiles, even if less than min_mass_size
        else:
            mass_size = random.randint(min_mass_size, min(max_mass_size, remaining_tiles))
        
        if mass_size <= 0:
            break  # No more tiles to place

        # Use flood-fill to create a land mass
        land_mass = set()
        frontier = [(start_x, start_y)]
        chunk[start_y][start_x] = LAND
        land_mass.add((start_x, start_y))
        land_tiles_placed += 1

        while len(land_mass) < mass_size and frontier:
            cx, cy = frontier.pop(0)
            # Check neighboring tiles (up, down, left, right)
            neighbors = [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]
            random.shuffle(neighbors)  # Randomize to make shapes more natural
            for nx, ny in neighbors:
                if len(land_mass) >= mass_size:
                    break
                if (0 <= nx < CHUNK_SIZE and 0 <= ny < CHUNK_SIZE and
                        chunk[ny][nx] == WATER and (nx, ny) not in land_mass):
                    chunk[ny][nx] = LAND
                    land_mass.add((nx, ny))
                    frontier.append((nx, ny))
                    land_tiles_placed += 1

    # Add trees to some land tiles
    tree_chance = 0.2  # 20% chance for a tree on each land tile
    for ty in range(CHUNK_SIZE):
        for tx in range(CHUNK_SIZE):
            if chunk[ty][tx] == LAND and random.random() < tree_chance:
                chunk[ty][tx] = TREE

    # Add loot to some land tiles (rarer than trees)
    loot_chance = 0.05  # 5% chance for loot on each land tile
    for ty in range(CHUNK_SIZE):
        for tx in range(CHUNK_SIZE):
            if chunk[ty][tx] == LAND and random.random() < loot_chance:
                chunk[ty][tx] = LOOT

    return chunk

def delete_chunks():
    if os.path.exists(CHUNK_DIR):
        shutil.rmtree(CHUNK_DIR)

def get_tile(x, y):
    cx, cy = world_to_chunk(x, y)
    tx, ty = x % CHUNK_SIZE, y % CHUNK_SIZE
    if tx < 0: tx += CHUNK_SIZE
    if ty < 0: ty += CHUNK_SIZE
    if (cx, cy) not in chunks:
        loaded_data = load_chunk(cx, cy)
        if loaded_data is not None:
            chunks[(cx, cy)] = loaded_data
        else:
            chunks[(cx, cy)] = generate_chunk(cx, cy)
    return chunks[(cx, cy)][ty][tx]

def set_tile(x, y, tile_type):
    cx, cy = world_to_chunk(x, y)
    tx, ty = x % CHUNK_SIZE, y % CHUNK_SIZE
    if tx < 0: tx += CHUNK_SIZE
    if ty < 0: ty += CHUNK_SIZE
    if (cx, cy) not in chunks:
        loaded_data = load_chunk(cx, cy)
        if loaded_data is not None:
            chunks[(cx, cy)] = loaded_data
        else:
            chunks[(cx, cy)] = generate_chunk(cx, cy)
    chunks[(cx, cy)][ty][tx] = tile_type

# --- Initialize Starting Area ---
def initialize_starting_area():
    """Set up the initial 3x3 chunk area around (0, 0) with a land patch."""
    for cx in range(-1, 2):
        for cy in range(-1, 2):
            chunks[(cx, cy)] = generate_chunk(cx, cy)
    # Ensure a 3x3 land area at the origin
    for y in range(-1, 2):
        for x in range(-1, 2):
            set_tile(x, y, LAND)

initialize_starting_area()

def load_chunk(cx, cy):
    filename = f"{CHUNK_DIR}/chunk_{cx}_{cy}.pkl"
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return pickle.load(f)
    return None  # Return None if the chunk doesn’t exist yet

# --- Manage Chunks ---
def update_player_chunk():
    """Update the player's current chunk based on position."""
    global player_chunk
    player_chunk = world_to_chunk(player_pos[0], player_pos[1])

def manage_chunks():
    cx, cy = player_chunk  # Player’s current chunk coordinates
    loaded_chunks = set()
    VIEW_CHUNKS = 3  # Example: 3x3 grid around player

    # Load nearby chunks
    for dx in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1):
        for dy in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1):
            chunk_key = (cx + dx, cy + dy)
            loaded_chunks.add(chunk_key)
            if chunk_key not in chunks:  # 'chunks' is your in-memory chunk dictionary
                loaded_data = load_chunk(cx + dx, cy + dy)
                if loaded_data is not None:
                    chunks[chunk_key] = loaded_data
                else:
                    chunks[chunk_key] = generate_chunk(cx + dx, cy + dy)  # Generate if new

    # Save and unload distant chunks
    for key in list(chunks.keys()):
        if key not in loaded_chunks:
            save_chunk(key[0], key[1], chunks[key])
            del chunks[key]  # Remove from memory

# --- Game State ---
selected_tile = None  # Will store the (x, y) of the tile under the mouse

turrets_placed = 0
pirates_killed = 0
tiles_placed = 0

game_over = False
fade_done = False
player_pos = [0, 0]  # Now in world coordinates
wood = 5
selected_block = LAND
player_move_timer = 0
player_move_delay = 150
facing = [0, -1]
interaction_ui_enabled = False

last_player_pos = list(player_pos)
stationary_timer = 0
STATIONARY_DELAY = 500

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

pirates = []
pirate_spawn_timer = 0
spawn_delay = 5000
pirate_walk_delay = 300



game_surface = pygame.Surface((WIDTH, HEIGHT))

# --- Drawing ---
def draw_grid():
    """Render the visible portion of the infinite world."""
    top_left_x = player_pos[0] - VIEW_WIDTH // 2
    top_left_y = player_pos[1] - VIEW_HEIGHT // 2

    # Step 1: Draw base tiles
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = top_left_x + x, top_left_y + y
            tile = get_tile(gx, gy)
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            image = tile_images.get(tile)
            if image:
                game_surface.blit(pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE)), rect)
            else:
                pygame.draw.rect(game_surface, BLACK, rect)

    # Step 2: Draw under textures
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = top_left_x + x, top_left_y + y
            tile = get_tile(gx, gy)
            below_y = gy + 1
            below_tile = get_tile(gx, below_y)
            if below_tile == WATER:
                if tile in [LAND, TURRET, USED_LAND, SAPLING, TREE, LOOT]:
                    under_land_image = tile_images.get("UNDER_LAND")
                    if under_land_image:
                        under_rect = pygame.Rect(x * TILE_SIZE, (y + 1) * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        game_surface.blit(pygame.transform.scale(under_land_image, (TILE_SIZE, TILE_SIZE)), under_rect)
                elif tile == BOAT_TILE:
                    under_wood_image = tile_images.get("UNDER_WOOD")
                    if under_wood_image:
                        under_rect = pygame.Rect(x * TILE_SIZE, (y + 1) * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        game_surface.blit(pygame.transform.scale(under_wood_image, (TILE_SIZE, TILE_SIZE)), under_rect)

    # Step 3: Draw overlay tiles and entities
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = top_left_x + x, top_left_y + y
            tile = get_tile(gx, gy)
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if tile in [TURRET, TREE, SAPLING, LOOT]:
                land_image = tile_images.get(LAND)
                if land_image:
                    game_surface.blit(pygame.transform.scale(land_image, (TILE_SIZE, TILE_SIZE)), rect)
                overlay_image = tile_images.get(tile)
                if overlay_image:
                    game_surface.blit(pygame.transform.scale(overlay_image, (TILE_SIZE, TILE_SIZE)), rect)
            if tile == TURRET:
                level = turret_levels.get((gx, gy), 1)
                font = pygame.font.SysFont(None, 20)
                level_text = font.render(str(level), True, WHITE)
                text_rect = level_text.get_rect(center=(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE - 10))
                game_surface.blit(level_text, text_rect)

    # Draw pirates, player, etc.
    for p in pirates:
        for s in p["ship"]:
            sx = s["x"] - top_left_x
            sy = s["y"] - top_left_y
            if 0 <= sx < VIEW_WIDTH and 0 <= sy < VIEW_HEIGHT:
                boat_tile_image = tile_images.get(BOAT_TILE)
                if boat_tile_image:
                    game_surface.blit(pygame.transform.scale(boat_tile_image, (TILE_SIZE, TILE_SIZE)), (sx * TILE_SIZE, sy * TILE_SIZE))

    px = player_pos[0] - top_left_x
    py = player_pos[1] - top_left_y
    game_surface.blit(pygame.transform.scale(player_image, (TILE_SIZE, TILE_SIZE)), (px * TILE_SIZE, py * TILE_SIZE))

    draw_interaction_ui()

    for p in pirates:
        for pirate in p.get("pirates", []):
            px = pirate["x"] - top_left_x
            py = pirate["y"] - top_left_y
            if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
                level = pirate["level"]
                if pirate["health"] > 1:
                    pirate_image = pirate_sprites[f"level_{level}"]  # Hatted sprite
                else:
                    pirate_image = pirate_sprites["base"]  # Hatless at 1 health
                game_surface.blit(pygame.transform.scale(pirate_image, (TILE_SIZE, TILE_SIZE)), (px * TILE_SIZE, py * TILE_SIZE))

        if p["state"] == "landed":
            px = p["x"] - top_left_x
            py = p["y"] - top_left_y
            if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
                font = pygame.font.SysFont(None, 24)
                text = font.render("Land Ahoy!", True, WHITE)
                text_rect = text.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE - 10))
                game_surface.blit(text, text_rect)
    
    # Draw selected tile overlay
    if selected_tile:
        sel_x, sel_y = selected_tile
        sel_px = sel_x - top_left_x
        sel_py = sel_y - top_left_y
        if 0 <= sel_px < VIEW_WIDTH and 0 <= sel_py < VIEW_HEIGHT:
            overlay_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 128))  # Black with 50% transparency (128/255)
            game_surface.blit(overlay_surface, (sel_px * TILE_SIZE, sel_py * TILE_SIZE))

    # Draw floating wood gain texts
    for text in wood_texts:
        px = text["x"] - top_left_x
        py = text["y"] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            font = pygame.font.SysFont(None, 14)
            text_surface = font.render(text["text"], True, WHITE)
            text_surface.set_alpha(text["alpha"])
            text_rect = text_surface.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE - 10))
            game_surface.blit(text_surface, text_rect)

    # Draw floating XP gain texts
    for text in xp_texts:
        px = text["x"] - top_left_x
        py = text["y"] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            font = pygame.font.SysFont(None, 14)
            text_surface = font.render(text["text"], True, YELLOW)  # Yellow to distinguish from wood
            text_surface.set_alpha(text["alpha"])
            text_rect = text_surface.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE - 20))  # Slightly higher to avoid overlap
            game_surface.blit(text_surface, text_rect)

    for hat in hat_particles:
        px = hat["x"] - top_left_x
        py = hat["y"] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            hat_level = hat["level"]
            hat_image = pirate_hat_images[hat_level]
            rotated_hat = pygame.transform.rotate(hat_image, hat["rotation"])
            scaled_hat = pygame.transform.scale(rotated_hat, (TILE_SIZE, TILE_SIZE))
            alpha = int((hat["timer"] / hat["initial_timer"]) * 255)
            alpha = max(0, min(255, alpha))
            hat_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            hat_surface.blit(scaled_hat, (0, 0))
            hat_surface.set_alpha(alpha)
            hat_rect = hat_surface.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE + TILE_SIZE // 2))
            game_surface.blit(hat_surface, hat_rect.topleft)

    for explosion in explosions[:]:
        explosion["timer"] -= clock.get_time()
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

    for proj in projectiles:
        px = proj["x"] - top_left_x
        py = proj["y"] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            pygame.draw.circle(game_surface, DARK_GRAY, (int(px * TILE_SIZE + TILE_SIZE // 2), int(py * TILE_SIZE + TILE_SIZE // 2)), 4)

def draw_ui():
    font = pygame.font.SysFont(None, 28)
    score = turrets_placed + pirates_killed + tiles_placed
    wood_text = font.render(f"Wood: {wood}", True, WHITE)
    score_text = font.render(f"Score: {score}", True, WHITE)
    quit_text = font.render("Press ESC to quit", True, WHITE)
    help_color = WHITE if not interaction_ui_enabled else (150, 150, 150)
    help_text = font.render("Press I for Help", True, help_color)

    screen.blit(wood_text, (10, 10))
    screen.blit(score_text, (10, 40))
    screen.blit(quit_text, (10, 70))
    screen.blit(help_text, (10, 100))

def draw_minimap():
    """Simplified minimap showing nearby chunks."""
    minimap_scale = 3
    minimap_size = VIEW_CHUNKS * CHUNK_SIZE * minimap_scale
    minimap_surface = pygame.Surface((minimap_size, minimap_size))
    cx, cy = player_chunk
    for dy in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1):
        for dx in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1):
            chunk_key = (cx + dx, cy + dy)
            if chunk_key in chunks:
                chunk = chunks[chunk_key]
                for my in range(CHUNK_SIZE):
                    for mx in range(CHUNK_SIZE):
                        tile = chunk[my][mx]
                        color = {
                            WATER: BLUE,
                            LAND: GREEN,
                            TREE: BROWN,
                            SAPLING: (150, 255, 150),
                            WALL: DARK_GRAY,
                            TURRET: YELLOW,
                            BOAT_TILE: TAN,
                            USED_LAND: LIGHT_GRAY,
                            LOOT: ORANGE
                        }.get(tile, BLACK)
                        world_x, world_y = chunk_to_world(cx + dx, cy + dy, mx, my)
                        if (world_x, world_y) == tuple(player_pos):
                            color = WHITE
                        mx_map = (dx + VIEW_CHUNKS // 2) * CHUNK_SIZE + mx
                        my_map = (dy + VIEW_CHUNKS // 2) * CHUNK_SIZE + my
                        pygame.draw.rect(minimap_surface, color, (mx_map * minimap_scale, my_map * minimap_scale, minimap_scale, minimap_scale))

    cam_x = (player_pos[0] % CHUNK_SIZE + (VIEW_CHUNKS // 2) * CHUNK_SIZE - VIEW_WIDTH // 2) * minimap_scale
    cam_y = (player_pos[1] % CHUNK_SIZE + (VIEW_CHUNKS // 2) * CHUNK_SIZE - VIEW_HEIGHT // 2) * minimap_scale
    cam_rect = pygame.Rect(cam_x, cam_y, VIEW_WIDTH * minimap_scale, VIEW_HEIGHT * minimap_scale)
    pygame.draw.rect(minimap_surface, WHITE, cam_rect, 1)

    for p in pirates:
        mx = (p["x"] - (cx - VIEW_CHUNKS // 2) * CHUNK_SIZE) * minimap_scale
        my = (p["y"] - (cy - VIEW_CHUNKS // 2) * CHUNK_SIZE) * minimap_scale
        pygame.draw.rect(minimap_surface, RED, (int(mx), int(my), minimap_scale, minimap_scale))

    screen_width, _ = screen.get_size()
    minimap_x = screen_width - minimap_surface.get_width() - 10
    screen.blit(minimap_surface, (minimap_x, 10))

def show_game_over():
    global high_score, fade_done
    score = turrets_placed + pirates_killed + tiles_placed
    if score > high_score:
        high_score = score
        with open("score.txt", "w") as f:
            f.write(str(high_score))

    base_surface = pygame.Surface((WIDTH, HEIGHT))
    base_surface.fill(BLACK)

    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 32)

    lines = [
        "Game Over!",
        "A pirate caught you!",
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

def save_chunk(cx, cy, chunk_data):
    filename = f"{CHUNK_DIR}/chunk_{cx}_{cy}.pkl"
    with open(filename, "wb") as f:
        pickle.dump(chunk_data, f)

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
    top_left_x = player_pos[0] - VIEW_WIDTH // 2
    top_left_y = player_pos[1] - VIEW_HEIGHT // 2

    tile_x = int(world_x // TILE_SIZE)
    tile_y = int(world_y // TILE_SIZE)

    # Convert to world coordinates
    world_tile_x = tile_x + top_left_x
    world_tile_y = tile_y + top_left_y

    return world_tile_x, world_tile_y

def spawn_pirate():
    global pirates
    score = turrets_placed + pirates_killed + tiles_placed
    min_blocks = max(3, 1 + score // 10)
    max_blocks = max(min_blocks, 1 + score // 5)
    equivalent_level_1_pirates = random.randint(min_blocks, max_blocks)

    # Convert equivalent_level_1_pirates to a list of pirate levels
    pirate_levels = []
    remaining = equivalent_level_1_pirates
    while remaining > 0:
        # Find the highest level where 2^(level-1) <= remaining
        level = min(10, int(math.log2(max(1, remaining))) + 1)
        pirate_levels.append(level)
        remaining -= 2 ** (level - 1)  # Subtract the equivalent level 1 pirates

    # Get loaded chunks, excluding the player's chunk
    cx, cy = player_chunk
    loaded_chunks = [(cx + dx, cy + dy) for dx in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1)
                     for dy in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1) if (dx, dy) != (0, 0)]

    # Collect water tiles in loaded chunks
    water_tiles = []
    for chunk_key in loaded_chunks:
        if chunk_key in chunks:
            chunk = chunks[chunk_key]
            for ty in range(CHUNK_SIZE):
                for tx in range(CHUNK_SIZE):
                    if chunk[ty][tx] == WATER:
                        world_x, world_y = chunk_to_world(chunk_key[0], chunk_key[1], tx, ty)
                        water_tiles.append((world_x, world_y))

    if not water_tiles:
        print("No water tiles available for spawning!")
        return

    # Pick a random water tile as the starting point
    x, y = random.choice(water_tiles)

    # Build the ship with flood-fill
    block_count = max(3, len(pirate_levels))  # Ensure enough tiles for pirates
    ship_tiles = set()
    frontier = [(x, y)]
    while len(ship_tiles) < block_count and frontier:
        cx, cy = frontier.pop(0)
        if (cx, cy) not in ship_tiles and get_tile(cx, cy) == WATER:
            ship_tiles.add((cx, cy))
            neighbors = [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]
            random.shuffle(neighbors)
            frontier.extend(neighbors)
    ship_tiles = list(ship_tiles)

    if not ship_tiles:
        print("No connected water tiles for ship!")
        return

    # Assign pirates to ship tiles
    pirate_positions = random.sample(ship_tiles, min(len(pirate_levels), len(ship_tiles)))
    pirates_data = []
    for i, (px, py) in enumerate(pirate_positions):
        level = pirate_levels[i]
        max_health = 2 ** level  # 2^1 = 2 for level 1, 2^2 = 4 for level 2, etc.
        xp_value = 2 ** (level - 1)  # 2^0 = 1 for level 1, 2^1 = 2 for level 2, etc.
        pirates_data.append({
            "x": float(px),
            "y": float(py),
            "start_x": float(px),
            "start_y": float(py),
            "target_x": float(px),
            "target_y": float(py),
            "move_progress": 1.0,
            "move_duration": 300,
            "health": max_health,
            "max_health": max_health,
            "xp_value": xp_value,
            "level": level
        })

    # Calculate direction toward the player
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

def update_pirates():
    global game_over
    now = pygame.time.get_ticks()
    for p in pirates[:]:
        if p["state"] == "boat":
            if not p["ship"]:
                pirates.remove(p)
                continue
            for s in p["ship"]:
                s["x"] += p["dir"][0] * 0.05
                s["y"] += p["dir"][1] * 0.05
            for pirate in p["pirates"]:
                pirate["x"] += p["dir"][0] * 0.05
                pirate["y"] += p["dir"][1] * 0.05
                pirate["start_x"] = pirate["x"]
                pirate["start_y"] = pirate["y"]
                pirate["target_x"] = pirate["x"]
                pirate["target_y"] = pirate["y"]
                pirate["move_progress"] = 1.0
            nx = p["x"] + p["dir"][0] * 0.05
            ny = p["y"] + p["dir"][1] * 0.05

            landed = False
            landing_tile = None
            for s in p["ship"]:
                sx, sy = int(s["x"]), int(s["y"])
                if get_tile(sx, sy) != WATER:
                    landed = True
                    landing_tile = (sx, sy)
                    break

            if landed:
                for s in p["ship"]:
                    sx, sy = int(round(s["x"])), int(round(s["y"]))
                    if get_tile(sx, sy) == WATER:
                        set_tile(sx, sy, BOAT_TILE)
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
                    elapsed = clock.get_time()
                    pirate["move_progress"] = min(1.0, pirate["move_progress"] + elapsed / pirate["move_duration"])
                    pirate["x"] = pirate["start_x"] + (pirate["target_x"] - pirate["start_x"]) * pirate["move_progress"]
                    pirate["y"] = pirate["start_y"] + (pirate["target_y"] - pirate["start_y"]) * pirate["move_progress"]

            if now - p["walk_timer"] < pirate_walk_delay:
                continue

            for pirate in p["pirates"]:
                # Check if the pirate touches the player
                dist = math.hypot(pirate["x"] - player_pos[0], pirate["y"] - player_pos[1])
                if dist < 0.5:  # Reduced distance threshold for "touching"
                    game_over = True
                    return

                if pirate["move_progress"] >= 1.0:
                    # Move toward the player instead of the loot
                    dx = player_pos[0] - pirate["x"]
                    dy = player_pos[1] - pirate["y"]
                    primary = (1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1)
                    alt = (0, 1 if dy > 0 else -1) if primary[0] != 0 else (1 if dx > 0 else -1, 0)

                    def can_walk(x, y):
                        if get_tile(x, y) in [TREE, WATER]:
                            return False
                        for other_p in pirates:
                            for other_pirate in other_p["pirates"]:
                                if other_pirate is not pirate and int(other_pirate["x"]) == x and int(other_pirate["y"]) == y:
                                    return False
                        return True

                    moved = False
                    tx, ty = int(pirate["x"] + primary[0]), int(pirate["y"] + primary[1])
                    if can_walk(tx, ty):
                        pirate["start_x"] = pirate["x"]
                        pirate["start_y"] = pirate["y"]
                        pirate["target_x"] = tx
                        pirate["target_y"] = ty
                        pirate["move_progress"] = 0.0
                        moved = True
                    else:
                        ax, ay = int(pirate["x"] + alt[0]), int(pirate["y"] + alt[1])
                        if can_walk(ax, ay):
                            pirate["start_x"] = pirate["x"]
                            pirate["start_y"] = pirate["y"]
                            pirate["target_x"] = ax
                            pirate["target_y"] = ay
                            pirate["move_progress"] = 0.0
                            moved = True

                    if not moved:
                        for dx_try, dy_try in [primary, alt]:
                            cx, cy = int(pirate["x"] + dx_try), int(pirate["y"] + dy_try)
                            if get_tile(cx, cy) == TREE:
                                set_tile(cx, cy, LAND)
                                break

            if p["pirates"]:
                avg_x = sum(pirate["x"] for pirate in p["pirates"]) / len(p["pirates"])
                avg_y = sum(pirate["y"] for pirate in p["pirates"]) / len(p["pirates"])
                p["x"], p["y"] = avg_x, avg_y

            p["walk_timer"] = now

def update_turrets():
    now = pygame.time.get_ticks()
    top_left_x = player_pos[0] - VIEW_WIDTH // 2
    top_left_y = player_pos[1] - VIEW_HEIGHT // 2
    for y in range(VIEW_HEIGHT + 2):
        for x in range(VIEW_WIDTH + 2):
            gx, gy = top_left_x + x, top_left_y + y
            if get_tile(gx, gy) == TURRET:
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
                                "dir": (dx/length, dy/length),
                                "turret_id": turret_pos
                            })
                            turret_cooldowns[turret_pos] = now
                            break
                    else:
                        continue
                    break

def update_sparks():
    for spark in sparks[:]:
        spark["timer"] -= clock.get_time()
        if spark["timer"] <= 0:
            sparks.remove(spark)
            continue
        spark["x"] += spark["vel"][0]
        spark["y"] += spark["vel"][1]

def update_projectiles():
    global pirates_killed, wood
    import math
    for proj in projectiles[:]:
        next_x = proj["x"] + proj["dir"][0] * projectile_speed
        next_y = proj["y"] + proj["dir"][1] * projectile_speed
        tile_x, tile_y = int(next_x), int(next_y)

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

        if get_tile(tile_x, tile_y) == TREE:
            projectiles.remove(proj)
            continue

        proj["x"] = next_x
        proj["y"] = next_y

        hit = False
        for p in pirates[:]:
            for pirate in p["pirates"][:]:
                if abs(proj["x"] - pirate["x"]) < 0.5 and abs(proj["y"] - pirate["y"]) < 0.5:
                    pirate["health"] -= 1
                    if pirate["health"] == 1:
                        hat_particles.append({
                            "x": pirate["x"],
                            "y": pirate["y"] - 0.5,
                            "vel_x": random.uniform(-0.05, 0.05),
                            "vel_y": -0.1,
                            "rotation": 0,
                            "rotation_speed": random.uniform(-10, 10),
                            "timer": 1000,
                            "initial_timer": 1000,
                            "level": pirate["level"]  # Store pirate level for hat sprite
                        })
                    if pirate["health"] <= 0:
                        p["pirates"].remove(pirate)
                        pirates_killed += 1
                        explosions.append({"x": pirate["x"], "y": pirate["y"], "timer": 500})
                        for _ in range(5):
                            spark_color = random.choice([(255, 255, 0), (255, 165, 0), (255, 0, 0)])
                            spark_vel = [random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05)]
                            sparks.append({
                                "x": pirate["x"],
                                "y": pirate["y"],
                                "vel": spark_vel,
                                "timer": 150,
                                "color": spark_color
                            })
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
                    wood_gained = random.randint(5, 10)
                    wood += wood_gained
                    wood_texts.append({
                        "x": s["x"],
                        "y": s["y"],
                        "text": f"+{wood_gained} Wood",
                        "timer": 1000,
                        "alpha": 255
                    })
                    hit = True
                    break
                if hit:
                    break

        if hit and proj in projectiles:
            projectiles.remove(proj)

        if not p["pirates"] and not p["ship"]:
            pirates.remove(p)

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
        hat["timer"] -= clock.get_time()
        if hat["timer"] <= 0:
            hat_particles.remove(hat)
            continue
        hat["x"] += hat["vel_x"]
        hat["y"] += hat["vel_y"]
        hat["vel_y"] += 0.002
        hat["rotation"] = (hat["rotation"] + hat["rotation_speed"]) % 360

def update_wood_texts():
    for text in wood_texts[:]:
        text["timer"] -= clock.get_time()
        if text["timer"] <= 0:
            wood_texts.remove(text)
            continue
        # Move text upward
        text["y"] -= 0.02  # Adjust speed as needed
        # Fade out
        text["alpha"] = int((text["timer"] / 1000) * 255)  # Fade over 1 second
        text["alpha"] = max(0, min(255, text["alpha"]))

def update_xp_texts():
    for text in xp_texts[:]:
        text["timer"] -= clock.get_time()
        if text["timer"] <= 0:
            xp_texts.remove(text)
            continue
        text["y"] -= 0.02  # Move upward
        text["alpha"] = int((text["timer"] / 1000) * 255)
        text["alpha"] = max(0, min(255, text["alpha"]))

def interact(button):
    global wood, tiles_placed, turrets_placed
    if not selected_tile:
        return
    x, y = selected_tile
    tile = get_tile(x, y)
    
    if button == 3:  # Right-click
        turret_pos = (x, y)
        if tile == TURRET:
            level = turret_levels.get(turret_pos, 1)
            refund = 3  # Flat refund since no upgrades
            set_tile(x, y, LAND)
            wood += refund
            turrets_placed = max(0, turrets_placed - 1)
            if turret_pos in turret_cooldowns:
                del turret_cooldowns[turret_pos]
            if turret_pos in turret_levels:
                del turret_levels[turret_pos]
            if turret_pos in turret_xp:
                del turret_xp[turret_pos]
        elif tile == LAND and wood >= 3:
            set_tile(x, y, TURRET)
            wood -= 3
            turrets_placed += 1
            turret_levels[turret_pos] = 1
            turret_xp[turret_pos] = 0
            sound_place_turret.play()
        return

    if tile == WATER and wood >= 1:
        set_tile(x, y, BOAT_TILE)
        wood -= 3
        tiles_placed += 1
        sound_place_land.play()
    elif tile == LOOT:
        wood_gained = random.randint(5, 10)
        wood += wood_gained
        set_tile(x, y, LAND)
        wood_texts.append({
            "x": x,
            "y": y,
            "text": f"+{wood_gained} Wood",
            "timer": 1000,
            "alpha": 255
        })
    elif tile == TREE:
        set_tile(x, y, LAND)
        wood_gained = 3
        wood += wood_gained
        wood_texts.append({
            "x": x,
            "y": y,
            "text": f"+{wood_gained} Wood",
            "timer": 1000,
            "alpha": 255
        })
    elif tile == SAPLING:
        set_tile(x, y, LAND)
        wood += 1
        if (x, y) in tree_growth:
            del tree_growth[(x, y)]
    elif tile == BOAT_TILE:
        if player_pos[0] == x and player_pos[1] == y:
            return
        set_tile(x, y, WATER)
        wood_gained = 1
        wood += wood_gained
        wood_texts.append({
            "x": x,
            "y": y,
            "text": f"+{wood_gained} Wood",
            "timer": 1000,
            "alpha": 255
        })
    else:
        plant_sapling()

def update_interaction_ui():
    global interaction_ui, stationary_timer, last_player_pos
    if not interaction_ui_enabled:
        interaction_ui["alpha"] = 0
        interaction_ui["offset"] = 20
        interaction_ui["fade_timer"] = 0
        return

    # Check if the player has moved (optional, can remove if not needed)
    current_pos = list(player_pos)
    if current_pos != last_player_pos:
        interaction_ui["alpha"] = 0
        interaction_ui["offset"] = 20
        interaction_ui["fade_timer"] = 0
        stationary_timer = 0
        last_player_pos = current_pos
        return
    else:
        stationary_timer += clock.get_time()
        if stationary_timer < STATIONARY_DELAY:
            interaction_ui["alpha"] = 0
            interaction_ui["offset"] = 20
            interaction_ui["fade_timer"] = 0
            return

    # Use the selected tile instead of player position
    if not selected_tile:
        interaction_ui["left_message"] = ""
        interaction_ui["right_message"] = ""
        interaction_ui["alpha"] = 0
        interaction_ui["offset"] = 20
        interaction_ui["fade_timer"] = 0
        return

    x, y = selected_tile
    tile = get_tile(x, y)

    interaction_ui["left_message"] = ""
    interaction_ui["right_message"] = ""

    if tile == WATER and wood >= 1:
        interaction_ui["left_message"] = "Place Boat Tile\n-3 Wood"
    elif tile == LOOT:
        interaction_ui["left_message"] = "Collect\n+5-10 Wood"
    elif tile == TREE:
        interaction_ui["left_message"] = "Chop\n+2-4 Wood"
    elif tile == SAPLING:
        interaction_ui["left_message"] = "Uproot\n+1 Wood"
    elif tile == BOAT_TILE:
        # Check if the player is on the tile to show the message
        if player_pos[0] == x and player_pos[1] == y:
            interaction_ui["left_message"] = "Cannot remove\nwhile standing on tile"
        else:
            interaction_ui["left_message"] = "Remove Boat Tile\n+1 Wood"
    elif tile == TURRET:
        turret_pos = (x, y)
        level = turret_levels.get(turret_pos, 1)
        interaction_ui["right_message"] = "Pickup\n+3 Wood"
    elif tile == LAND:
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
            interaction_ui["fade_timer"] += clock.get_time()
            progress = min(1.0, interaction_ui["fade_timer"] / interaction_ui["fade_duration"])
            interaction_ui["alpha"] = int(progress * 255)
            interaction_ui["offset"] = 20 * (1 - progress)

def plant_sapling():
    global wood
    if not selected_tile:
        return
    x, y = selected_tile
    if get_tile(x, y) == LAND and wood >= 1:
        set_tile(x, y, SAPLING)
        tree_growth[(x, y)] = pygame.time.get_ticks()
        wood -= 1
        sound_plant_sapling.play()

def update_trees():
    now = pygame.time.get_ticks()
    to_grow = [pos for pos, t in tree_growth.items() if now - t >= sapling_growth_time]
    for pos in to_grow:
        set_tile(pos[0], pos[1], TREE)
        del tree_growth[pos]

def try_move(dx, dy):
    global player_move_timer, facing
    now = pygame.time.get_ticks()
    x, y = player_pos[0] + dx, player_pos[1] + dy
    facing = [dx, dy]
    if now - player_move_timer > player_move_delay:
        if get_tile(x, y) not in [WATER, TREE]:
            player_pos[0], player_pos[1] = x, y
            update_player_chunk()
            manage_chunks()
        player_move_timer = now

# --- Game Loop ---
running = True
while running:
    if game_over:
        if not fade_done:
            show_game_over()
            fade_done = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                delete_chunks()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    delete_chunks()
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_SPACE:
                    subprocess.Popen([sys.executable, os.path.abspath(__file__)])
                    delete_chunks()
                    pygame.quit()
                    sys.exit()
        continue

    game_surface.fill(BLACK)
    update_sparks()
    update_wood_texts()
    update_xp_texts()
    update_hat_particles()
    water_frame_timer += clock.get_time()
    if water_frame_timer >= water_frame_delay:
        water_frame = (water_frame + 1) % len(water_frames)
        water_frame_timer = 0
        tile_images[WATER] = water_frames[water_frame]
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
    update_interaction_ui()
    update_pirates()
    update_turrets()
    update_projectiles()

    pirate_spawn_timer += clock.get_time()
    if pirate_spawn_timer >= spawn_delay:
        spawn_pirate()
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

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: try_move(0, -1)
    elif keys[pygame.K_s]: try_move(0, 1)
    elif keys[pygame.K_a]: try_move(-1, 0)
    elif keys[pygame.K_d]: try_move(1, 0)

    clock.tick(60)

pygame.quit()