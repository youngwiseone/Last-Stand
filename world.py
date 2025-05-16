# World management for the Pygame-based island survival game.
# Handles chunk loading, saving, generation, and starting area initialization.
# Provides tile access and chunk management for the game world.

import pickle
import random
import os
from constants import *

class World:
    def __init__(self):
        # Initialize chunk system state.
        self.chunks = {}  # Dictionary: {(cx, cy): [[tile]]}
        self.tile_cache = {}  # Dictionary: {(x, y): tile_type}
        self.player_chunk = (0, 0)  # Player’s current chunk
        self.minimap_cache_valid = False  # Flag for minimap cache validity
        self.chunks_version = 0  # Version counter for tracking chunk changes

    def world_to_chunk(self, x, y):
        # Convert world coordinates to chunk coordinates.
        return int(x) // CHUNK_SIZE, int(y) // CHUNK_SIZE

    def chunk_to_world(self, cx, cy, tx, ty):
        # Convert chunk coordinates and tile offsets to world coordinates.
        return cx * CHUNK_SIZE + tx, cy * CHUNK_SIZE + ty

    def generate_chunk(self, cx, cy):
        # Generate a new chunk with rarer, larger land masses, occasional trees, loot, and boulders.
        chunk = [[Tile.WATER for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]
        total_tiles = CHUNK_SIZE * CHUNK_SIZE  # 256 tiles in a 16x16 chunk
        target_land_tiles = int(total_tiles * 0.05)  # 5% land = ~13 tiles per chunk
        min_mass_size = 8
        max_mass_size = 20
        land_tiles_placed = 0

        # Generate land masses until target is reached
        while land_tiles_placed < target_land_tiles:
            available_positions = [(tx, ty) for ty in range(CHUNK_SIZE) for tx in range(CHUNK_SIZE) if chunk[ty][tx] == Tile.WATER]
            if not available_positions:
                break
            start_x, start_y = random.choice(available_positions)
            remaining_tiles = target_land_tiles - land_tiles_placed
            mass_size = remaining_tiles if remaining_tiles < min_mass_size else random.randint(min_mass_size, min(max_mass_size, remaining_tiles))
            if mass_size <= 0:
                break

            # Flood-fill to create land mass
            land_mass = set()
            frontier = [(start_x, start_y)]
            chunk[start_y][start_x] = Tile.LAND
            land_mass.add((start_x, start_y))
            land_tiles_placed += 1

            while len(land_mass) < mass_size and frontier:
                cx, cy = frontier.pop(0)
                neighbors = [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]
                random.shuffle(neighbors)
                for nx, ny in neighbors:
                    if len(land_mass) >= mass_size:
                        break
                    if (0 <= nx < CHUNK_SIZE and 0 <= ny < CHUNK_SIZE and
                            chunk[ny][nx] == Tile.WATER and (nx, ny) not in land_mass):
                        chunk[ny][nx] = Tile.LAND
                        land_mass.add((nx, ny))
                        frontier.append((nx, ny))
                        land_tiles_placed += 1

        # Add trees to some land tiles
        tree_chance = 0.2
        for ty in range(CHUNK_SIZE):
            for tx in range(CHUNK_SIZE):
                if chunk[ty][tx] == Tile.LAND and random.random() < tree_chance:
                    chunk[ty][tx] = Tile.TREE

        # Add loot to some land tiles
        loot_chance = 0.05
        for ty in range(CHUNK_SIZE):
            for tx in range(CHUNK_SIZE):
                if chunk[ty][tx] == Tile.LAND and random.random() < loot_chance:
                    chunk[ty][tx] = Tile.LOOT

        # Add boulders to some land tiles
        boulder_chance = 0.03
        for ty in range(CHUNK_SIZE):
            for tx in range(CHUNK_SIZE):
                if chunk[ty][tx] == Tile.LAND and random.random() < boulder_chance:
                    chunk[ty][tx] = Tile.BOULDER

        return chunk

    def save_chunk(self, cx, cy, chunk_data):
        # Save chunk data to a file.
        filename = f"{CHUNK_DIR}/chunk_{cx}_{cy}.pkl"
        with open(filename, "wb") as f:
            pickle.dump(chunk_data, f)

    def load_chunk(self, cx, cy):
        # Load chunk data from a file, or return None if it doesn’t exist.
        filename = f"{CHUNK_DIR}/chunk_{cx}_{cy}.pkl"
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                return pickle.load(f)
        return None

    def get_tile(self, x, y):
        # Get the tile type at world coordinates (x, y), loading or generating chunks as needed.
        key = (x, y)
        if key in self.tile_cache:
            return self.tile_cache[key]
        cx, cy = self.world_to_chunk(x, y)
        tx = int(x % CHUNK_SIZE)
        ty = int(y % CHUNK_SIZE)
        if tx < 0:
            tx += CHUNK_SIZE
        if ty < 0:
            ty += CHUNK_SIZE
        if (cx, cy) not in self.chunks:
            loaded_data = self.load_chunk(cx, cy)
            if loaded_data is not None:
                self.chunks[(cx, cy)] = loaded_data
            else:
                self.chunks[(cx, cy)] = self.generate_chunk(cx, cy)
        tile = self.chunks[(cx, cy)][ty][tx]
        self.tile_cache[key] = tile
        return tile

    def set_tile(self, x, y, tile_type):
        # Set the tile type at world coordinates (x, y) and update cache and chunk data.
        cx, cy = self.world_to_chunk(x, y)
        tx = int(x % CHUNK_SIZE)
        ty = int(y % CHUNK_SIZE)
        if tx < 0:
            tx += CHUNK_SIZE
        if ty < 0:
            ty += CHUNK_SIZE
        if (cx, cy) not in self.chunks:
            loaded_data = self.load_chunk(cx, cy)
            if loaded_data is not None:
                self.chunks[(cx, cy)] = loaded_data
            else:
                self.chunks[(cx, cy)] = self.generate_chunk(cx, cy)
        self.chunks[(cx, cy)][ty][tx] = tile_type
        self.tile_cache[(x, y)] = tile_type
        self.save_chunk(cx, cy, self.chunks[(cx, cy)])
        self.minimap_cache_valid = False
        self.chunks_version += 1

    def initialize_starting_area(self):
        # Set up the initial 5x5 chunk area around (0, 0) with a varied, organic land patch.
        for cx in range(-2, 3):
            for cy in range(-2, 3):
                self.chunks[(cx, cy)] = self.generate_chunk(cx, cy)
        
        target_land_tiles = random.randint(10, 16)
        land_mass = set()
        frontier = [(0, 0)]
        land_mass.add((0, 0))
        self.set_tile(0, 0, Tile.LAND)
        
        while len(land_mass) < target_land_tiles and frontier:
            cx, cy = frontier.pop(0)
            neighbors = [
                (cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1),
                (cx+1, cy+1), (cx+1, cy-1), (cx-1, cy+1), (cx-1, cy-1)
            ]
            random.shuffle(neighbors)
            for nx, ny in neighbors:
                if len(land_mass) >= target_land_tiles:
                    break
                if (abs(nx) <= 2 and abs(ny) <= 2 and
                        (nx, ny) not in land_mass and
                        self.get_tile(nx, ny) == Tile.WATER):
                    if random.random() < 0.8:
                        self.set_tile(nx, ny, Tile.LAND)
                        land_mass.add((nx, ny))
                        frontier.append((nx, ny))
        
        land_tiles = list(land_mass)
        features_to_add = random.randint(1, 3)
        random.shuffle(land_tiles)
        for i in range(min(features_to_add, len(land_tiles))):
            tx, ty = land_tiles[i]
            feature = random.choices(
                [Tile.TREE, Tile.LOOT, Tile.BOULDER],
                weights=[0.6, 0.3, 0.1],
                k=1
            )[0]
            self.set_tile(tx, ty, feature)

    def update_player_chunk(self, player_pos):
        # Update the player’s current chunk based on their position.
        self.player_chunk = self.world_to_chunk(player_pos[0], player_pos[1])

    def manage_chunks(self, player_pos):
        # Load and unload chunks around the player based on their position.
        cx, cy = self.player_chunk
        loaded_chunks = set()
        chunks_changed = False
        for dx in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1):
            for dy in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1):
                chunk_key = (cx + dx, cy + dy)
                loaded_chunks.add(chunk_key)
                if chunk_key not in self.chunks:
                    loaded_data = self.load_chunk(cx + dx, cy + dy)
                    if loaded_data is not None:
                        self.chunks[chunk_key] = loaded_data
                    else:
                        self.chunks[chunk_key] = self.generate_chunk(cx + dx, cy + dy)
                    chunks_changed = True
        for key in list(self.chunks.keys()):
            if key not in loaded_chunks:
                self.save_chunk(key[0], key[1], self.chunks[key])
                cx, cy = key
                for ty in range(CHUNK_SIZE):
                    for tx in range(CHUNK_SIZE):
                        wx, wy = self.chunk_to_world(cx, cy, tx, ty)
                        self.tile_cache.pop((wx, wy), None)
                del self.chunks[key]
                chunks_changed = True
        if chunks_changed:
            self.minimap_cache_valid = False
            self.chunks_version += 1