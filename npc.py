import pygame
import random
import math
from abc import ABC, abstractmethod
from constants import Tile, TILE_SIZE, MOVEMENT_TILES
from world import World

class NPC(ABC):
    """Base class for NPCs."""
    def __init__(self, x, y, state="boat", ship=None, direction=None):
        self.type = "base"
        self.state = state
        self.x = x
        self.y = y
        self.ship = ship or [{"x": x, "y": y}]
        self.dir = direction or [0, 0]
        self.roam_timer = 0
        self.move_progress = 1.0
        self.start_x = x
        self.start_y = y
        self.target_x = x
        self.target_y = y
        self.interaction_cooldown = 0

    @abstractmethod
    def interact(self, game_state, world):
        """Handle interaction with the NPC."""
        pass

class WallerNPC(NPC):
    """NPC that trades fishing rod or shows fish caught."""
    def __init__(self, x, y, state="boat", ship=None, direction=None):
        super().__init__(x, y, state, ship, direction)
        self.type = "waller"

    def interact(self, game_state, world):
        wood = game_state["wood"]
        has_fishing_rod = game_state["has_fishing_rod"]
        fish_caught = game_state["fish_caught"]
        wood_texts = []
        if not has_fishing_rod and wood >= 50:
            has_fishing_rod = True
            wood -= 50
            wood_texts.append({
                "x": self.x,
                "y": self.y - 0.5,
                "text": "-50 Wood",
                "timer": 1000,
                "alpha": 255
            })
            wood_texts.append({
                "x": self.x,
                "y": self.y - 0.5,
                "text": "",
                "image_key": "FISHING_ROD",
                "timer": 1000,
                "alpha": 255
            })
        else:
            wood_texts.append({
                "x": self.x,
                "y": self.y - 0.5,
                "text": f"Fish Caught: {fish_caught}",
                "timer": 1000,
                "alpha": 255
            })
        self.interaction_cooldown = pygame.time.get_ticks() + 3000
        return {
            "wood": wood,
            "has_fishing_rod": has_fishing_rod,
            "fish_caught": fish_caught,
            "wood_texts": wood_texts
        }

class TraderNPC(NPC):
    """NPC that trades wood for loot tiles."""
    def __init__(self, x, y, state="boat", ship=None, direction=None):
        super().__init__(x, y, state, ship, direction)
        self.type = "trader"

    def interact(self, game_state, world):
        wood = game_state["wood"]
        wood_texts = []
        if wood >= 10:
            wood -= 10
            neighbors = [(self.x + dx, self.y + dy) for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]]
            for nx, ny in neighbors:
                if world.get_tile(int(nx), int(ny)) == Tile.LAND:
                    world.set_tile(int(nx), int(ny), Tile.LOOT)
                    wood_texts.append({
                        "x": nx,
                        "y": ny - 0.5,
                        "text": "+1 Loot",
                        "timer": 1000,
                        "alpha": 255
                    })
                    break
            else:
                wood_texts.append({
                    "x": self.x,
                    "y": self.y - 0.5,
                    "text": "No Land Nearby",
                    "timer": 1000,
                    "alpha": 255
                })
            wood_texts.append({
                "x": self.x,
                "y": self.y - 0.5,
                "text": "-10 Wood",
                "timer": 1000,
                "alpha": 255
            })
        else:
            wood_texts.append({
                "x": self.x,
                "y": self.y - 0.5,
                "text": "Need 10 Wood",
                "timer": 1000,
                "alpha": 255
            })
        self.interaction_cooldown = pygame.time.get_ticks() + 3000
        return {
            "wood": wood,
            "has_fishing_rod": game_state["has_fishing_rod"],
            "fish_caught": game_state["fish_caught"],
            "wood_texts": wood_texts
        }

# NPC Registry with sprite keys
NPC_REGISTRY = [
    {
        "type": "waller",
        "class": WallerNPC,
        "sprite_key": "NPC_WALLER",
        "spawn_conditions": {
            "wood_threshold": 50,
            "max_instances": 1
        }
    },
    {
        "type": "trader",
        "class": TraderNPC,
        "sprite_key": "NPC_TRADER",
        "spawn_conditions": {
            "wood_threshold": 100,
            "max_instances": 1
        }
    }
]

class NPCManager:
    def __init__(self, scaled_tile_images, npc_sprites):
        """Initialize NPC manager with rendering assets."""
        self.npcs = []
        self.scaled_tile_images = scaled_tile_images
        self.npc_sprites = npc_sprites  # Dictionary of NPC type to sprite
        self.now = pygame.time.get_ticks()
        self.spawned_counts = {npc["type"]: 0 for npc in NPC_REGISTRY}

    def spawn_npcs(self, game_state, player_pos, view_width, view_height):
        """Spawn NPCs based on game state and registry conditions."""
        wood = game_state["wood"]
        for npc_config in NPC_REGISTRY:
            npc_type = npc_config["type"]
            npc_class = npc_config["class"]
            conditions = npc_config["spawn_conditions"]
            wood_threshold = conditions["wood_threshold"]
            max_instances = conditions["max_instances"]
            if (wood >= wood_threshold and
                self.spawned_counts[npc_type] < max_instances):
                buffer = 2
                spawn_dist = view_width / 2 + buffer
                angle = random.uniform(0, 2 * math.pi)
                spawn_x = player_pos[0] + math.cos(angle) * spawn_dist
                spawn_y = player_pos[1] + math.sin(angle) * spawn_dist
                dx = player_pos[0] - spawn_x
                dy = player_pos[1] - spawn_y
                length = math.hypot(dx, dy) or 1
                direction = [dx / length, dy / length]
                npc = npc_class(spawn_x, spawn_y, direction=direction)
                self.npcs.append(npc)
                self.spawned_counts[npc_type] += 1

    def interact(self, x, y, game_state, world):
        """Handle interaction with NPC at (x, y)."""
        self.now = pygame.time.get_ticks()
        for npc in self.npcs:
            if any(s["x"] == x and s["y"] == y for s in npc.ship) and self.now >= npc.interaction_cooldown:
                return npc.interact(game_state, world)
        return game_state | {"wood_texts": []}

    def update(self, dt, world, player_pos):
        """Update all NPCs and remove dead ones."""
        self.now = pygame.time.get_ticks()
        for npc in self.npcs[:]:
            if self.now < npc.interaction_cooldown:
                continue
            if npc.state == "boat":
                for s in npc.ship:
                    s["x"] += npc.dir[0] * 0.05
                    s["y"] += npc.dir[1] * 0.05
                nx = npc.x + npc.dir[0] * 0.05
                ny = npc.y + npc.dir[1] * 0.05
                landed = False
                landing_tile = None
                for s in npc.ship:
                    sx, sy = int(s["x"]), int(s["y"])
                    if world.get_tile(sx, sy) != Tile.WATER:
                        landed = True
                        landing_tile = (sx, sy)
                        break
                if landed:
                    for s in npc.ship:
                        sx, sy = int(round(s["x"])), int(round(s["y"]))
                        if world.get_tile(sx, sy) == Tile.WATER:
                            world.set_tile(sx, sy, Tile.BOAT)
                    npc.ship = [{"x": landing_tile[0], "y": landing_tile[1]}]
                    npc.state = "docked"
                    npc.x, npc.y = landing_tile
                    npc.roam_timer = self.now
                    npc.move_progress = 1.0
                    npc.start_x = float(landing_tile[0])
                    npc.start_y = float(landing_tile[1])
                    npc.target_x = float(landing_tile[0])
                    npc.target_y = float(landing_tile[1])
                else:
                    npc.x, npc.y = nx, ny
            elif npc.state == "docked":
                if npc.move_progress < 1.0:
                    elapsed = dt
                    npc.move_progress = min(1.0, npc.move_progress + elapsed / 300)
                    npc.x = npc.start_x + (npc.target_x - npc.start_x) * npc.move_progress
                    npc.y = npc.start_y + (npc.target_y - npc.start_y) * npc.move_progress
                    npc.ship[0]["x"] = npc.x
                    npc.ship[0]["y"] = npc.y
                if self.now - npc.roam_timer >= 1000 and npc.move_progress >= 1.0:
                    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                    random.shuffle(neighbors)
                    for dx, dy in neighbors:
                        tx, ty = int(npc.x + dx), int(npc.y + dy)
                        if world.get_tile(tx, ty) in MOVEMENT_TILES:
                            npc.start_x = npc.x
                            npc.start_y = npc.y
                            npc.target_x = tx
                            npc.target_y = ty
                            npc.move_progress = 0.0
                            npc.roam_timer = self.now
                            break
            if not npc.ship:
                self.npcs.remove(npc)
                self.spawned_counts[npc.type] -= 1

    def render(self, game_surface, top_left_x, top_left_y, darkness_factor, view_width, view_height):
        """Render NPCs on the game surface."""
        for npc in self.npcs:
            for s in npc.ship:
                sx = s["x"] - top_left_x
                sy = s["y"] - top_left_y
                if darkness_factor == 1.0 and (
                    sx <= 1 or sx >= view_width - 2 or sy <= 1 or sy >= view_height - 2
                ):
                    continue
                if 0 <= sx < view_width and 0 <= sy < view_height:
                    if npc.state == "boat":
                        boat_tile_image = self.scaled_tile_images.get(Tile.BOAT)
                        if boat_tile_image:
                            boat_tile_image = boat_tile_image.copy()
                            if darkness_factor == 1.0:
                                dist_to_edge = min(sx, view_width - sx, sy, view_height - sy)
                                alpha = 0 if dist_to_edge <= 2 else 255 if dist_to_edge >= 5 else int(255 * (dist_to_edge - 2) / (5 - 2))
                                boat_tile_image.set_alpha(alpha)
                            else:
                                boat_tile_image.set_alpha(255)
                            game_surface.blit(boat_tile_image, (sx * TILE_SIZE, sy * TILE_SIZE))
                        if s["x"] == npc.x and s["y"] == npc.y:
                            npc_image = self.npc_sprites.get(npc.type, self.npc_sprites["waller"]).copy()
                            if darkness_factor == 1.0:
                                npc_image.set_alpha(alpha)
                            else:
                                npc_image.set_alpha(255)
                            game_surface.blit(npc_image, (sx * TILE_SIZE, sy * TILE_SIZE))
                    elif npc.state == "docked":
                        npc_image = self.npc_sprites.get(npc.type, self.npc_sprites["waller"])
                        game_surface.blit(npc_image, (sx * TILE_SIZE, sy * TILE_SIZE))