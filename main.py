import pygame
import random
import sys
import math
import os
import subprocess

# --- Init ---
pygame.init()
SCALE = 2
MIN_SCALE = 1
MAX_SCALE = 4

TILE_SIZE = 32
GRID_WIDTH, GRID_HEIGHT = 40, 40
VIEW_WIDTH, VIEW_HEIGHT = 20, 20
WIDTH, HEIGHT = VIEW_WIDTH * TILE_SIZE, VIEW_HEIGHT * TILE_SIZE
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()

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
    USED_LAND: pygame.image.load("Assets/used_land.png").convert()
}

player_image = pygame.image.load("Assets/player.png").convert_alpha()
loot_image = pygame.image.load("Assets/loot.png").convert_alpha()

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


king_pos = center
player_pos = list(center)
wood = 5
selected_block = LAND
player_move_timer = 0
player_move_delay = 150
facing = [0, -1]

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

# --- Drawing ---
def draw_grid():
    minimap_scale = 3
    minimap_surface = pygame.Surface((GRID_WIDTH * minimap_scale, GRID_HEIGHT * minimap_scale))
    top_left_x = player_pos[0] - VIEW_WIDTH // 2
    top_left_y = player_pos[1] - VIEW_HEIGHT // 2

    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx, gy = top_left_x + x, top_left_y + y
            if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
                tile = grid[gy][gx]
                rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)

                if tile in [TURRET, TREE, SAPLING]:
                    land_image = tile_images.get(LAND)
                    if land_image:
                        game_surface.blit(pygame.transform.scale(land_image, (TILE_SIZE, TILE_SIZE)), rect)

                image = tile_images.get(tile)
                if image:
                    game_surface.blit(pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE)), rect)
                else:
                    pygame.draw.rect(game_surface, BLACK, rect)

    for p in pirates:
        for s in p["ship"]:
            sx = s["x"] - top_left_x
            sy = s["y"] - top_left_y
            if 0 <= sx < VIEW_WIDTH and 0 <= sy < VIEW_HEIGHT:
                pygame.draw.rect(game_surface, TAN, (sx*TILE_SIZE, sy*TILE_SIZE, TILE_SIZE, TILE_SIZE))

    px = player_pos[0] - top_left_x
    py = player_pos[1] - top_left_y
    game_surface.blit(pygame.transform.scale(player_image, (TILE_SIZE, TILE_SIZE)), (px*TILE_SIZE, py*TILE_SIZE))

    kx = king_pos[0] - top_left_x
    ky = king_pos[1] - top_left_y
    land_image = tile_images.get(LAND)
    if land_image:
        game_surface.blit(pygame.transform.scale(land_image, (TILE_SIZE, TILE_SIZE)), (kx*TILE_SIZE, ky*TILE_SIZE))
    game_surface.blit(pygame.transform.scale(loot_image, (TILE_SIZE, TILE_SIZE)), (kx*TILE_SIZE, ky*TILE_SIZE))

    for p in pirates:
        for pirate in p.get("pirates", []):
            px = pirate["x"] - top_left_x
            py = pirate["y"] - top_left_y
            if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
                screen_x = int(px * TILE_SIZE + 6)
                screen_y = int(py * TILE_SIZE + 6)
                pygame.draw.rect(game_surface, RED, (screen_x, screen_y, TILE_SIZE - 12, TILE_SIZE - 12))

        # Display "Land Ahoy!" above the pirates during the landed state
        if p["state"] == "landed":
            px = p["x"] - top_left_x
            py = p["y"] - top_left_y
            if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
                font = pygame.font.SysFont(None, 24)
                text = font.render("Land Ahoy!", True, WHITE)
                text_rect = text.get_rect(center=(px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE - 10))
                game_surface.blit(text, text_rect)

    for proj in projectiles:
        px = proj["x"] - top_left_x
        py = proj["y"] - top_left_y
        if 0 <= px < VIEW_WIDTH and 0 <= py < VIEW_HEIGHT:
            pygame.draw.circle(game_surface, ORANGE, (int(px*TILE_SIZE+TILE_SIZE//2), int(py*TILE_SIZE+TILE_SIZE//2)), 4)

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
    aspect_ratio = WIDTH / HEIGHT
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
def spawn_pirate():
    global pirates

    score = turrets_placed + pirates_killed + tiles_placed
    min_blocks = max(3, 1 + score // 10)
    max_blocks = max(min_blocks, 1 + score // 5)
    block_count = random.randint(min_blocks, max_blocks)

    # Entry edge and central point
    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top":
        x, y = random.randint(5, GRID_WIDTH - 6), 0
    elif side == "bottom":
        x, y = random.randint(5, GRID_WIDTH - 6), GRID_HEIGHT - 1
    elif side == "left":
        x, y = 0, random.randint(5, GRID_HEIGHT - 6)
    else:
        x, y = GRID_WIDTH - 1, random.randint(5, GRID_HEIGHT - 6)

    # Generate a blob around the center tile
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

    # Determine number of pirates (1 per 3 ship blocks, min 1)
    pirate_count = max(1, len(ship_tiles) // 3)

    # Choose pirate positions from the ship tiles
    pirate_positions = random.sample(ship_tiles, pirate_count)

    # Direction towards king
    dx = king_pos[0] - x
    dy = king_pos[1] - y
    length = max(abs(dx), abs(dy)) or 1
    direction = (dx / length, dy / length)

    # Append the pirate ship to the pirates list
    pirates.append({
        "x": x,
        "y": y,
        "dir": direction,
        "state": "boat",
        "ship": [{"x": sx, "y": sy} for sx, sy in ship_tiles],
        "pirates": [{"x": float(px), "y": float(py)} for px, py in pirate_positions]
    })

def update_pirates():
    global game_over
    now = pygame.time.get_ticks()
    for p in pirates[:]:
        if p["state"] == "boat":
            if not p["ship"]:
                pirates.remove(p)
                continue
            # Move the ship
            for s in p["ship"]:
                s["x"] += p["dir"][0] * 0.05
                s["y"] += p["dir"][1] * 0.05
            for pirate in p["pirates"]:
                pirate["x"] += p["dir"][0] * 0.05
                pirate["y"] += p["dir"][1] * 0.05
            nx = p["x"] + p["dir"][0] * 0.05
            ny = p["y"] + p["dir"][1] * 0.05

            # Check if any ship tile hits a non-water tile
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
            # Wait for 1 second (1000 ms)
            if now - p["land_time"] >= 1000:
                p["state"] = "walk"
            # The "Land Ahoy!" message is drawn in draw_grid

        else:  # "walk" state
            if "walk_timer" not in p:
                p["walk_timer"] = 0

            for pirate in p["pirates"]:
                dist = math.hypot(pirate["x"] - king_pos[0], pirate["y"] - king_pos[1])
                if dist < 2.0:
                    print(f"Pirate at ({pirate['x']}, {pirate['y']}), King at {king_pos}, Distance: {dist}")
                if dist < 1.0:
                    print("The pirates stole your loot!")
                    game_over = True
                    return

            if now - p["walk_timer"] < pirate_walk_delay:
                continue

            for pirate in p["pirates"]:
                dx = king_pos[0] - pirate["x"]
                dy = king_pos[1] - pirate["y"]
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
                    pirate["x"] += primary[0]
                    pirate["y"] += primary[1]
                    moved = True
                else:
                    ax, ay = int(pirate["x"] + alt[0]), int(pirate["y"] + alt[1])
                    if can_walk(ax, ay):
                        pirate["x"] += alt[0]
                        pirate["y"] += alt[1]
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
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x] == TURRET:
                for p in pirates:
                    dist = math.hypot(p["x"] - x, p["y"] - y)
                    if dist <= TURRET_RANGE:
                        dx, dy = p["x"] - x, p["y"] - y
                        length = math.hypot(dx, dy) or 1
                        projectiles.append({"x": x, "y": y, "dir": (dx/length, dy/length)})
                        break

def update_projectiles():
    global pirates_killed
    for proj in projectiles[:]:
        # Calculate next position
        next_x = proj["x"] + proj["dir"][0] * projectile_speed
        next_y = proj["y"] + proj["dir"][1] * projectile_speed
        tile_x, tile_y = int(next_x), int(next_y)

        # Block if hitting a tree
        if 0 <= tile_x < GRID_WIDTH and 0 <= tile_y < GRID_HEIGHT:
            if grid[tile_y][tile_x] == TREE:
                projectiles.remove(proj)
                continue

        proj["x"] = next_x
        proj["y"] = next_y

        # Check individual pirate hits
        for p in pirates[:]:
            for pirate in p["pirates"][:]:
                if abs(proj["x"] - pirate["x"]) < 0.3 and abs(proj["y"] - pirate["y"]) < 0.3:
                    p["pirates"].remove(pirate)
                    pirates_killed += 1
                    if proj in projectiles:
                        projectiles.remove(proj)
                    break

            # Remove pirate group if all pirates are dead and ship is also gone
            if not p["pirates"] and not p["ship"]:
                pirates.remove(p)

            # Check ship tile hits
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
    else:
        plant_sapling()

def place_land_ahead():
    global wood, tiles_placed
    x, y = player_pos[0] + facing[0], player_pos[1] + facing[1]
    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT and grid[y][x] == WATER and wood >= 1:
        grid[y][x] = LAND
        wood -= 1
        tiles_placed += 1

def place_turret():
    global wood, turrets_placed
    x, y = player_pos
    if grid[y][x] == TURRET:
        grid[y][x] = LAND
        wood += 3
        turrets_placed = max(0, turrets_placed - 1)
    elif grid[y][x] == LAND and wood >= 3:
        grid[y][x] = TURRET
        wood -= 3
        turrets_placed += 1

def plant_sapling():
    global wood
    x, y = player_pos
    if grid[y][x] == LAND and wood >= 1:
        grid[y][x] = SAPLING
        tree_growth[(x, y)] = pygame.time.get_ticks()
        wood -= 1

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
