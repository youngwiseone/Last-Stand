import pygame
import random
import sys
import math
import os
import subprocess

# --- Init ---
pygame.init()
pygame.mixer.init()
SCALE = 2
MIN_SCALE = 1
MAX_SCALE = 4

TILE_SIZE = 32
GRID_WIDTH, GRID_HEIGHT = 40, 40
VIEW_WIDTH, VIEW_HEIGHT = 20, 20
WIDTH, HEIGHT = VIEW_WIDTH * TILE_SIZE, VIEW_HEIGHT * TILE_SIZE
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()

explosions = []  # List to track explosion effects
explosions.clear() # Clear sparks to ensure no old sparks remain
sparks = []  # List to track spark particles
sparks.clear() # Clear sparks to ensure no old sparks remain

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
WATER, LAND, TREE, SAPLING, WALL, TURRET, BOAT_TILE, USED_LAND = range(8)

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
    "UNDER_WOOD": pygame.image.load("Assets/under_wood.png").convert_alpha()
}

water_frames = [
    pygame.image.load("Assets/water.png").convert(),
    pygame.image.load("Assets/water1.png").convert(),
    pygame.image.load("Assets/water2.png").convert()
]
water_frame = 0
water_frame_timer = 0
water_frame_delay = 1200  # Switch frames every 800ms

player_image = pygame.image.load("Assets/player.png").convert_alpha()
loot_image = pygame.image.load("Assets/loot.png").convert_alpha()
pirate_image = pygame.image.load("Assets/pirate.png").convert_alpha()

# Load high score
try:
    with open("score.txt", "r") as f:
        high_score = int(f.read())
except:
    high_score = 0

# --- Map Setup ---
grid = [[WATER for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
center = GRID_WIDTH // 2, GRID_HEIGHT // 2
for y in range(center[1] - 1, center[1] + 2):
    for x in range(center[0] - 1, center[0] + 2):
        grid[y][x] = LAND

# --- Game State ---
# Score variables
# These are used to calculate the score at the end of the game
turrets_placed = 0
pirates_killed = 0
tiles_placed = 0

game_over = False
fade_done = False
loot_pos = center
player_pos = list(center)
wood = 5
selected_block = LAND
player_move_timer = 0
player_move_delay = 150
facing = [0, -1]

# In the game state section
turret_cooldowns = {}  # Tracks last firing time for each turret
turret_levels = {}  # Tracks the level of each turret (key: (x, y), value: level)
BASE_TURRET_FIRE_RATE = 1000  # Base fire rate in milliseconds (1 second at level 1)
TURRET_UPGRADE_COSTS = {1: 1, 2: 2, 3: 4}  # Cost to upgrade to the next level (from level 1 to 2, 2 to 3, 3 to 4)
TURRET_MAX_LEVEL = 4  # Maximum turret level

tree_growth = {}
sapling_growth_time = 10000

pirates = []
pirate_spawn_timer = 0
spawn_delay = 5000
pirate_walk_delay = 300

projectiles = []
projectile_speed = 0.2
TURRET_RANGE = 4

game_surface = pygame.Surface((WIDTH, HEIGHT))

def draw_grid():
    minimap_scale = 3
    minimap_surface = pygame.Surface((GRID_WIDTH * minimap_scale, GRID_HEIGHT * minimap_scale))
    top_left_x = player_pos[0] - VIEW_WIDTH // 2
    top_left_y = player_pos[1] - VIEW_HEIGHT // 2

    # Step 1: Draw all tiles first (background layer)
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = top_left_x + x, top_left_y + y
            if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
                tile = grid[gy][gx]
                rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)

                # Draw the base tile (e.g., water, used_land)
                image = tile_images.get(tile)
                if image:
                    game_surface.blit(pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE)), rect)
                else:
                    pygame.draw.rect(game_surface, BLACK, rect)

    # Step 2: Draw under_land.png for LAND, TURRET, USED_LAND, SAPLING, and TREE tiles with water below
    # Also draw under_wood.png for BOAT_TILE tiles with water below
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = top_left_x + x, top_left_y + y
            if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
                tile = grid[gy][gx]
                # Check if the current tile is one that should have under_land or under_wood
                below_y = gy + 1
                if 0 <= below_y < GRID_HEIGHT:  # Ensure we’re within grid bounds
                    below_tile = grid[below_y][gx]
                    if below_tile == WATER:  # Only place under texture if the tile below is water
                        # Draw under_land for LAND, TURRET, USED_LAND, SAPLING, and TREE
                        if tile in [LAND, TURRET, USED_LAND, SAPLING, TREE]:
                            under_land_image = tile_images.get("UNDER_LAND")
                            if under_land_image:
                                under_rect = pygame.Rect(x*TILE_SIZE, (y+1)*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                                game_surface.blit(pygame.transform.scale(under_land_image, (TILE_SIZE, TILE_SIZE)), under_rect)
                        # Draw under_wood for BOAT_TILE
                        elif tile == BOAT_TILE:
                            under_wood_image = tile_images.get("UNDER_WOOD")
                            if under_wood_image:
                                under_rect = pygame.Rect(x*TILE_SIZE, (y+1)*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                                game_surface.blit(pygame.transform.scale(under_wood_image, (TILE_SIZE, TILE_SIZE)), under_rect)

    # Step 3: Draw overlay tiles (trees, saplings, turrets) and other game elements
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = top_left_x + x, top_left_y + y
            if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
                tile = grid[gy][gx]
                rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)

                # Draw overlay tiles (trees, saplings, turrets) on top of land
                if tile in [TURRET, TREE, SAPLING]:
                    land_image = tile_images.get(LAND)
                    if land_image:
                        game_surface.blit(pygame.transform.scale(land_image, (TILE_SIZE, TILE_SIZE)), rect)
                    overlay_image = tile_images.get(tile)
                    if overlay_image:
                        game_surface.blit(pygame.transform.scale(overlay_image, (TILE_SIZE, TILE_SIZE)), rect)

                # Draw turret level
                if tile == TURRET:
                    level = turret_levels.get((gx, gy), 1)
                    font = pygame.font.SysFont(None, 20)
                    level_text = font.render(str(level), True, WHITE)
                    text_rect = level_text.get_rect(center=(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE - 10))
                    game_surface.blit(level_text, text_rect)

    # Continue with the rest of the drawing (ships, player, etc.)
    for p in pirates:
        for s in p["ship"]:
            sx = s["x"] - top_left_x
            sy = s["y"] - top_left_y
            if 0 <= sx < VIEW_WIDTH and 0 <= sy < VIEW_HEIGHT:
                boat_tile_image = tile_images.get(BOAT_TILE)
                if boat_tile_image:
                    game_surface.blit(pygame.transform.scale(boat_tile_image, (TILE_SIZE, TILE_SIZE)), (sx*TILE_SIZE, sy*TILE_SIZE))

    px = player_pos[0] - top_left_x
    py = player_pos[1] - top_left_y
    game_surface.blit(pygame.transform.scale(player_image, (TILE_SIZE, TILE_SIZE)), (px*TILE_SIZE, py*TILE_SIZE))

    kx = loot_pos[0] - top_left_x
    ky = loot_pos[1] - top_left_y
    land_image = tile_images.get(LAND)
    if land_image:
        game_surface.blit(pygame.transform.scale(land_image, (TILE_SIZE, TILE_SIZE)), (kx*TILE_SIZE, ky*TILE_SIZE))
    game_surface.blit(pygame.transform.scale(loot_image, (TILE_SIZE, TILE_SIZE)), (kx*TILE_SIZE, ky*TILE_SIZE))

    for p in pirates:
        for pirate in p.get("pirates", []):
            px = pirate["x"] - top_left_x
            py = pirate["y"] - top_left_y
            if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
                game_surface.blit(pygame.transform.scale(pirate_image, (TILE_SIZE, TILE_SIZE)), (px * TILE_SIZE, py * TILE_SIZE))

        if p["state"] == "landed":
            px = p["x"] - top_left_x
            py = p["y"] - top_left_y
            if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
                font = pygame.font.SysFont(None, 24)
                text = font.render("Land Ahoy!", True, WHITE)
                text_rect = text.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE - 10))
                game_surface.blit(text, text_rect)

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
            pygame.draw.circle(game_surface, DARK_GRAY, (int(px*TILE_SIZE+TILE_SIZE//2), int(py*TILE_SIZE+TILE_SIZE//2)), 4)

    for my in range(GRID_HEIGHT):
        for mx in range(GRID_WIDTH):
            tile = grid[my][mx]
            color = {
                WATER: BLUE,
                LAND: GREEN,
                TREE: BROWN,
                SAPLING: (150, 255, 150),
                WALL: DARK_GRAY,
                TURRET: YELLOW,
                BOAT_TILE: TAN,
                USED_LAND: LIGHT_GRAY
            }.get(tile, BLACK)
            if (mx, my) == tuple(player_pos):
                color = WHITE
            pygame.draw.rect(minimap_surface, color, (mx*minimap_scale, my*minimap_scale, minimap_scale, minimap_scale))

    cam_x = player_pos[0] - VIEW_WIDTH // 2
    cam_y = player_pos[1] - VIEW_HEIGHT // 2
    cam_rect = pygame.Rect(cam_x * minimap_scale, cam_y * minimap_scale, VIEW_WIDTH * minimap_scale, VIEW_HEIGHT * minimap_scale)
    pygame.draw.rect(minimap_surface, WHITE, cam_rect, 1)
    for p in pirates:
        mx = int(p["x"]) * minimap_scale
        my = int(p["y"]) * minimap_scale
        pygame.draw.rect(minimap_surface, RED, (mx, my, minimap_scale, minimap_scale))

def draw_ui():
    font = pygame.font.SysFont(None, 28)
    score = turrets_placed + pirates_killed + tiles_placed
    wood_text = font.render(f"Wood: {wood}", True, WHITE)
    score_text = font.render(f"Score: {score}", True, WHITE)
    quit_text = font.render(f"Press ESC to quit", True, WHITE)

    screen.blit(wood_text, (10, 10))
    screen.blit(score_text, (10, 40))
    screen.blit(quit_text, (10, 70))

def draw_minimap():
    minimap_scale = 3
    minimap_surface = pygame.Surface((GRID_WIDTH * minimap_scale, GRID_HEIGHT * minimap_scale))
    
    for my in range(GRID_HEIGHT):
        for mx in range(GRID_WIDTH):
            tile = grid[my][mx]
            color = {
                WATER: BLUE,
                LAND: GREEN,
                TREE: BROWN,
                SAPLING: (150, 255, 150),
                WALL: DARK_GRAY,
                TURRET: YELLOW,
                BOAT_TILE: TAN,
                USED_LAND: LIGHT_GRAY
            }.get(tile, BLACK)
            if (mx, my) == tuple(player_pos):
                color = WHITE
            pygame.draw.rect(minimap_surface, color, (mx*minimap_scale, my*minimap_scale, minimap_scale, minimap_scale))

    # Draw camera view rectangle
    cam_x = player_pos[0] - VIEW_WIDTH // 2
    cam_y = player_pos[1] - VIEW_HEIGHT // 2
    cam_rect = pygame.Rect(cam_x * minimap_scale, cam_y * minimap_scale, VIEW_WIDTH * minimap_scale, VIEW_HEIGHT * minimap_scale)
    pygame.draw.rect(minimap_surface, WHITE, cam_rect, 1)

    # Draw pirates
    for p in pirates:
        mx = int(p["x"]) * minimap_scale
        my = int(p["y"]) * minimap_scale
        pygame.draw.rect(minimap_surface, RED, (mx, my, minimap_scale, minimap_scale))

    screen_width, _ = screen.get_size()
    minimap_x = screen_width - minimap_surface.get_width() - 10
    screen.blit(minimap_surface, (minimap_x, 10))

    
def show_game_over():
    global high_score
    global turrets_placed, pirates_killed, tiles_placed

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

    # Get screen and scaling info
    screen_w, screen_h = screen.get_size()
    max_scale_w = screen_w / WIDTH
    max_scale_h = screen_h / HEIGHT
    scale_factor = min(max_scale_w, max_scale_h)

    scaled_width = int(WIDTH * scale_factor)
    scaled_height = int(HEIGHT * scale_factor)

    offset_x = (screen_w - scaled_width) // 2
    offset_y = (screen_h - scaled_height) // 2

    # Fade-in loop
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
def get_turret_refund(level):
    if level == 1:
        return 0  # No upgrades at level 1
    total = 0
    for lvl in range(1, level):
        total += TURRET_UPGRADE_COSTS.get(lvl, 0)
    return total

def spawn_pirate():
    global pirates

    score = turrets_placed + pirates_killed + tiles_placed
    min_blocks = max(3, 1 + score // 10)
    max_blocks = max(min_blocks, 1 + score // 5)
    block_count = random.randint(min_blocks, max_blocks)

    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top":
        x, y = random.randint(5, GRID_WIDTH - 6), 0
    elif side == "bottom":
        x, y = random.randint(5, GRID_WIDTH - 6), GRID_HEIGHT - 1
    elif side == "left":
        x, y = 0, random.randint(5, GRID_HEIGHT - 6)
    else:
        x, y = GRID_WIDTH - 1, random.randint(5, GRID_HEIGHT - 6)

    ship_tiles = set()
    frontier = [(x, y)]
    while len(ship_tiles) < block_count and frontier:
        cx, cy = frontier.pop(0)
        if 0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT and (cx, cy) not in ship_tiles:
            ship_tiles.add((cx, cy))
            neighbors = [
                (cx+1, cy), (cx-1, cy),
                (cx, cy+1), (cx, cy-1)
            ]
            random.shuffle(neighbors)
            frontier.extend(neighbors)

    ship_tiles = list(ship_tiles)
    pirate_count = max(1, len(ship_tiles) // 3)
    pirate_positions = random.sample(ship_tiles, pirate_count)

    dx = loot_pos[0] - x
    dy = loot_pos[1] - y
    length = max(abs(dx), abs(dy)) or 1
    direction = (dx / length, dy / length)

    # Initialize each pirate with tweening state
    pirates.append({
        "x": x,
        "y": y,
        "dir": direction,
        "state": "boat",
        "ship": [{"x": sx, "y": sy} for sx, sy in ship_tiles],
        "pirates": [
            {
                "x": float(px),
                "y": float(py),
                "target_x": float(px),  # Initialize target position
                "target_y": float(py),
                "move_progress": 1.0,  # Start fully at the initial position
                "move_duration": 300  # 300ms to move one tile (same as pirate_walk_delay)
            } for px, py in pirate_positions
        ]
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
                if 0 <= sx < GRID_WIDTH and 0 <= sy < GRID_HEIGHT and grid[sy][sx] != WATER:
                    landed = True
                    landing_tile = (sx, sy)
                    break

            if landed:
                for s in p["ship"]:
                    sx, sy = int(round(s["x"])), int(round(s["y"]))
                    if 0 <= sx < GRID_WIDTH and 0 <= sy < GRID_HEIGHT and grid[sy][sx] == WATER:
                        grid[sy][sx] = BOAT_TILE
                p["ship"] = []
                p["state"] = "landed"
                p["land_time"] = now
                p["x"], p["y"] = landing_tile
            else:
                p["x"], p["y"] = nx, ny

        elif p["state"] == "landed":
            if now - p["land_time"] >= 1000:
                p["state"] = "walk"
                p["walk_timer"] = now  # Reset walk_timer to ensure a delay before moving
                # Ensure all pirates start from a stationary position
                for pirate in p["pirates"]:
                    pirate["start_x"] = pirate["x"]
                    pirate["start_y"] = pirate["y"]
                    pirate["target_x"] = pirate["x"]
                    pirate["target_y"] = pirate["y"]
                    pirate["move_progress"] = 1.0

        else:  # "walk" state
            if "walk_timer" not in p:
                p["walk_timer"] = 0

            # Update movement progress for all pirates in the group
            for pirate in p["pirates"]:
                if pirate["move_progress"] < 1.0:
                    elapsed = clock.get_time()
                    pirate["move_progress"] = min(1.0, pirate["move_progress"] + elapsed / pirate["move_duration"])
                    pirate["x"] = pirate["start_x"] + (pirate["target_x"] - pirate["start_x"]) * pirate["move_progress"]
                    pirate["y"] = pirate["start_y"] + (pirate["target_y"] - pirate["start_y"]) * pirate["move_progress"]

            # Only calculate a new target position if the previous movement is complete
            if now - p["walk_timer"] < pirate_walk_delay:
                continue

            for pirate in p["pirates"]:
                dist = math.hypot(pirate["x"] - loot_pos[0], pirate["y"] - loot_pos[1])
                if dist < 1.0:
                    print("The pirates stole your loot!")
                    game_over = True
                    return

                if pirate["move_progress"] >= 1.0:
                    dx = loot_pos[0] - pirate["x"]
                    dy = loot_pos[1] - pirate["y"]
                    primary = (1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1)
                    alt = (0, 1 if dy > 0 else -1) if primary[0] != 0 else (1 if dx > 0 else -1, 0)

                    def can_walk(x, y):
                        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
                            return False
                        if grid[y][x] in [TREE, WATER]:
                            return False
                        for other_p in pirates:
                            for other_pirate in other_p["pirates"]:
                                if other_pirate is not pirate:
                                    if int(other_pirate["x"]) == x and int(other_pirate["y"]) == y:
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
                            if 0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT and grid[cy][cx] == TREE:
                                grid[cy][cx] = LAND
                                break

            if p["pirates"]:
                avg_x = sum(pirate["x"] for pirate in p["pirates"]) / len(p["pirates"])
                avg_y = sum(pirate["y"] for pirate in p["pirates"]) / len(p["pirates"])
                p["x"], p["y"] = avg_x, avg_y

            p["walk_timer"] = now

def update_turrets():
    now = pygame.time.get_ticks()
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x] == TURRET:
                turret_pos = (x, y)
                # Get turret level and calculate fire rate
                level = turret_levels.get(turret_pos, 1)
                fire_rate = BASE_TURRET_FIRE_RATE / (2 ** (level - 1))  # Halve cooldown for each level
                # Check if turret can fire
                last_fire = turret_cooldowns.get(turret_pos, 0)
                if now - last_fire < fire_rate:
                    continue

                for p in pirates:
                    # Check each individual pirate in the group
                    for pirate in p.get("pirates", []):
                        dist = math.hypot(pirate["x"] - x, pirate["y"] - y)
                        if dist <= TURRET_RANGE:
                            dx, dy = pirate["x"] - x, pirate["y"] - y
                            length = math.hypot(dx, dy) or 1
                            projectiles.append({"x": x, "y": y, "dir": (dx/length, dy/length)})
                            turret_cooldowns[turret_pos] = now
                            break  # Only fire at one pirate per turret per frame
                    else:
                        continue  # If no pirate was in range, continue to the next pirate group
                    break  # Break out of the pirate group loop after firing

def update_sparks():
    for spark in sparks[:]:
        spark["timer"] -= clock.get_time()
        if spark["timer"] <= 0:
            sparks.remove(spark)
            continue
        spark["x"] += spark["vel"][0]
        spark["y"] += spark["vel"][1]

def update_projectiles():
    global pirates_killed
    for proj in projectiles[:]:
        next_x = proj["x"] + proj["dir"][0] * projectile_speed
        next_y = proj["y"] + proj["dir"][1] * projectile_speed
        tile_x, tile_y = int(next_x), int(next_y)

        # Spawn 1-3 sparks per frame
        for _ in range(random.randint(1, 3)):
            spark_color = random.choice([(255, 255, 0), (255, 165, 0), (255, 0, 0)])  # Yellow, Orange, Red
            if not (isinstance(spark_color, tuple) and len(spark_color) == 3 and all(0 <= c <= 255 for c in spark_color)):
                print(f"Invalid spark color: {spark_color}")
                spark_color = (255, 255, 0)  # Fallback to yellow
            spark_vel = [proj["dir"][0] * -0.05 + random.uniform(-0.02, 0.02),
                         proj["dir"][1] * -0.05 + random.uniform(-0.02, 0.02)]
            sparks.append({
                "x": proj["x"],
                "y": proj["y"],
                "vel": spark_vel,
                "timer": 100,  # 100ms lifetime
                "color": spark_color
            })

        if 0 <= tile_x < GRID_WIDTH and 0 <= tile_y < GRID_HEIGHT:
            if grid[tile_y][tile_x] == TREE:
                projectiles.remove(proj)
                continue

        proj["x"] = next_x
        proj["y"] = next_y

        for p in pirates[:]:
            for pirate in p["pirates"][:]:
                if abs(proj["x"] - pirate["x"]) < 0.3 and abs(proj["y"] - pirate["y"]) < 0.3:
                    p["pirates"].remove(pirate)
                    pirates_killed += 1
                    explosions.append({"x": pirate["x"], "y": pirate["y"], "timer": 500})
                    # Spawn extra sparks on impact
                    for _ in range(5):
                        spark_color = random.choice([(255, 255, 0), (255, 165, 0), (255, 0, 0)])
                        if not (isinstance(spark_color, tuple) and len(spark_color) == 3 and all(0 <= c <= 255 for c in spark_color)):
                            print(f"Invalid spark color on impact: {spark_color}")
                            spark_color = (255, 255, 0)  # Fallback to yellow
                        spark_vel = [random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05)]
                        sparks.append({
                            "x": pirate["x"],
                            "y": pirate["y"],
                            "vel": spark_vel,
                            "timer": 150,
                            "color": spark_color
                        })
                    if proj in projectiles:
                        projectiles.remove(proj)
                    break

            if not p["pirates"] and not p["ship"]:
                pirates.remove(p)

            for s in p["ship"][:]:
                if abs(proj["x"] - s["x"]) < 0.3 and abs(proj["y"] - s["y"]) < 0.3:
                    p["ship"].remove(s)
                    if proj in projectiles:
                        projectiles.remove(proj)
                    break

def interact():
    global wood
    x, y = player_pos
    tile = grid[y][x]
    if tile == TREE:
        grid[y][x] = LAND
        wood += 3
    elif tile == SAPLING:
        grid[y][x] = LAND
        del tree_growth[(x, y)]
    elif tile == BOAT_TILE:
        grid[y][x] = USED_LAND
        wood += 1
    elif tile == TURRET:
        # Upgrade the turret if possible
        turret_pos = (x, y)
        level = turret_levels.get(turret_pos, 1)
        if level < TURRET_MAX_LEVEL:
            next_level = level + 1
            cost = TURRET_UPGRADE_COSTS.get(level, 0)
            if wood >= cost:
                wood -= cost
                turret_levels[turret_pos] = next_level
    else:
        plant_sapling()

def place_land_ahead():
    global wood, tiles_placed
    x, y = player_pos[0] + facing[0], player_pos[1] + facing[1]
    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT and grid[y][x] == WATER and wood >= 1:
        grid[y][x] = LAND
        wood -= 1
        tiles_placed += 1
        sound_place_land.play()

def place_turret():
    global wood, turrets_placed
    x, y = player_pos
    turret_pos = (x, y)
    if grid[y][x] == TURRET:
        # Picking up the turret: refund base cost + upgrade costs
        level = turret_levels.get(turret_pos, 1)
        refund = 3 + get_turret_refund(level)  # Base cost (3) + upgrade costs
        grid[y][x] = LAND
        wood += refund
        turrets_placed = max(0, turrets_placed - 1)
        if turret_pos in turret_cooldowns:
            del turret_cooldowns[turret_pos]
        if turret_pos in turret_levels:
            del turret_levels[turret_pos]
    elif grid[y][x] == LAND and wood >= 3:
        # Placing a new turret
        grid[y][x] = TURRET
        wood -= 3
        turrets_placed += 1
        turret_levels[turret_pos] = 1  # Start at level 1
        sound_place_turret.play()

def plant_sapling():
    global wood
    x, y = player_pos
    if grid[y][x] == LAND and wood >= 1:
        grid[y][x] = SAPLING
        tree_growth[(x, y)] = pygame.time.get_ticks()
        wood -= 1
        sound_plant_sapling.play()

def update_trees():
    now = pygame.time.get_ticks()
    to_grow = [pos for pos, t in tree_growth.items() if now - t >= sapling_growth_time]
    for pos in to_grow:
        grid[pos[1]][pos[0]] = TREE
        del tree_growth[pos]

def try_move(dx, dy):
    global player_move_timer, facing
    now = pygame.time.get_ticks()
    x, y = player_pos[0] + dx, player_pos[1] + dy
    facing = [dx, dy]
    if now - player_move_timer > player_move_delay:
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT and grid[y][x] != WATER:
            player_pos[0], player_pos[1] = x, y
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
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_SPACE:
                    subprocess.Popen([sys.executable, os.path.abspath(__file__)])
                    pygame.quit()
                    sys.exit()

        continue
    game_surface.fill(BLACK)
    update_sparks()
    # Water animation
    water_frame_timer += clock.get_time()
    if water_frame_timer >= water_frame_delay:
        water_frame = (water_frame + 1) % len(water_frames)
        water_frame_timer = 0
        tile_images[WATER] = water_frames[water_frame]
    draw_grid()
    scaled_surface = pygame.transform.scale(game_surface, (WIDTH * SCALE, HEIGHT * SCALE))
    # Center the game on screen
    screen_width, screen_height = screen.get_size()
    blit_x = (screen_width - WIDTH * SCALE) // 2
    blit_y = (screen_height - HEIGHT * SCALE) // 2
    # Scale the game surface based on current zoom level
    scaled_surface = pygame.transform.scale(game_surface, (WIDTH * SCALE, HEIGHT * SCALE))

    # Center the game on screen
    screen_width, screen_height = screen.get_size()
    blit_x = (screen_width - WIDTH * SCALE) // 2
    blit_y = (screen_height - HEIGHT * SCALE) // 2

    # Draw the scaled game to the center of the screen
    screen.fill(BLACK)
    screen.blit(scaled_surface, (blit_x, blit_y))
    draw_ui()
    draw_minimap()
    pygame.display.flip()

    update_trees()
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
            if event.key == pygame.K_SPACE:
                place_land_ahead()
            elif event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                interact()
            elif event.button == 3:  # Right click
                place_turret()
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
