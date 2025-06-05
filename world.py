# World management for the Pygame-based island survival game.
# Handles chunk loading, saving, generation, and starting area initialization.
# Provides tile access and chunk management for the game world.

import pickle
import random
import os
from abc import ABC, abstractmethod
from constants import *
from cachetools import LRUCache

class ChunkGenerator(ABC):
    """Base class for chunk generation strategies."""
    @abstractmethod
    def generate(self, cx, cy):
        """Generate a chunk at coordinates (cx, cy).

        Args:
            cx (int): Chunk x-coordinate.
            cy (int): Chunk y-coordinate.

        Returns:
            list: 2D list of tile types for the chunk.
        """
        pass

class DefaultIslandGenerator(ChunkGenerator):
    """Generates chunks with sparse land masses, trees, loot, and boulders."""
    def generate(self, cx, cy):
        chunk = [[Tile.WATER for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]
        total_tiles = CHUNK_SIZE * CHUNK_SIZE
        target_land_tiles = int(total_tiles * LAND_FRACTION)
        land_tiles = []
        land_tiles_placed = 0

        while land_tiles_placed < target_land_tiles:
            available_positions = [(tx, ty) for ty in range(CHUNK_SIZE) for tx in range(CHUNK_SIZE) if chunk[ty][tx] == Tile.WATER]
            if not available_positions:
                break
            start_x, start_y = random.choice(available_positions)
            mass_size = min(random.randint(MIN_LAND_MASS_SIZE, MAX_LAND_MASS_SIZE), target_land_tiles - land_tiles_placed)
            if mass_size <= 0:
                break

            x, y = start_x, start_y
            for _ in range(mass_size):
                if 0 <= x < CHUNK_SIZE and 0 <= y < CHUNK_SIZE and chunk[y][x] == Tile.WATER:
                    chunk[y][x] = Tile.LAND
                    land_tiles.append((x, y))
                    land_tiles_placed += 1
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(directions)
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < CHUNK_SIZE and 0 <= ny < CHUNK_SIZE and chunk[ny][nx] == Tile.WATER:
                        x, y = nx, ny
                        break
                else:
                    break

        random.shuffle(land_tiles)
        for i, (tx, ty) in enumerate(land_tiles):
            r = random.random()
            if r < TREE_CHANCE:
                chunk[ty][tx] = Tile.TREE
            elif r < TREE_CHANCE + LOOT_CHANCE:
                chunk[ty][tx] = Tile.LOOT
            elif r < TREE_CHANCE + LOOT_CHANCE + BOULDER_CHANCE:
                chunk[ty][tx] = Tile.BOULDER

        return chunk

class RockyIslandGenerator(ChunkGenerator):
    """Generates chunks with dense, rocky islands and minimal vegetation."""
    def generate(self, cx, cy):
        chunk = [[Tile.WATER for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]
        total_tiles = CHUNK_SIZE * CHUNK_SIZE
        # Slightly less overall land to create more water between large islands
        target_land_tiles = int(total_tiles * 0.08)
        land_tiles = []
        land_tiles_placed = 0

        while land_tiles_placed < target_land_tiles:
            available_positions = [(tx, ty) for ty in range(CHUNK_SIZE) for tx in range(CHUNK_SIZE) if chunk[ty][tx] == Tile.WATER]
            if not available_positions:
                break
            start_x, start_y = random.choice(available_positions)
            # Generate much larger island masses
            mass_size = min(random.randint(20, 50), target_land_tiles - land_tiles_placed)
            if mass_size <= 0:
                break

            x, y = start_x, start_y
            for _ in range(mass_size):
                if 0 <= x < CHUNK_SIZE and 0 <= y < CHUNK_SIZE and chunk[y][x] == Tile.WATER:
                    chunk[y][x] = Tile.LAND
                    land_tiles.append((x, y))
                    land_tiles_placed += 1
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(directions)
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < CHUNK_SIZE and 0 <= ny < CHUNK_SIZE and chunk[ny][nx] == Tile.WATER:
                        x, y = nx, ny
                        break
                else:
                    break

        random.shuffle(land_tiles)
        for i, (tx, ty) in enumerate(land_tiles):
            r = random.random()
            if r < 0.1:
                chunk[ty][tx] = Tile.TREE
            elif r < 0.3:
                chunk[ty][tx] = Tile.BOULDER

        return chunk
    
class ForestedIslandGenerator(ChunkGenerator):
    """Generates chunks with dense, tree-covered islands."""
    def generate(self, cx, cy):
        chunk = [[Tile.WATER for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]
        total_tiles = CHUNK_SIZE * CHUNK_SIZE
        # Less overall land for more water between bigger islands
        target_land_tiles = int(total_tiles * 0.07)  # 7% land
        land_tiles = []
        land_tiles_placed = 0

        while land_tiles_placed < target_land_tiles:
            available_positions = [(tx, ty) for ty in range(CHUNK_SIZE) for tx in range(CHUNK_SIZE) if chunk[ty][tx] == Tile.WATER]
            if not available_positions:
                break
            start_x, start_y = random.choice(available_positions)
            # Double the size of islands for dense forests
            mass_size = min(random.randint(24, 60), target_land_tiles - land_tiles_placed)
            if mass_size <= 0:
                break

            x, y = start_x, start_y
            for _ in range(mass_size):
                if 0 <= x < CHUNK_SIZE and 0 <= y < CHUNK_SIZE and chunk[y][x] == Tile.WATER:
                    chunk[y][x] = Tile.LAND
                    land_tiles.append((x, y))
                    land_tiles_placed += 1
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(directions)
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < CHUNK_SIZE and 0 <= ny < CHUNK_SIZE and chunk[ny][nx] == Tile.WATER:
                        x, y = nx, ny
                        break
                else:
                    break

        random.shuffle(land_tiles)
        for i, (tx, ty) in enumerate(land_tiles):
            r = random.random()
            if r < 0.5:  # 50% chance for trees
                chunk[ty][tx] = Tile.TREE
            elif r < 0.55:  # 5% chance for loot
                chunk[ty][tx] = Tile.LOOT

        return chunk

class World:
    def __init__(self):
        # Initialize the world with empty chunk storage and player state.
        self.chunks = {}  # Dictionary: {(cx, cy): [[tile]]}
        self.tile_cache = LRUCache(maxsize=10000)  # Cache up to 10,000 tiles
        self.player_chunk = (0, 0)  # Player’s current chunk
        self.dirty_chunks = set()  # Track chunks needing saving
        self.default_generator = DefaultIslandGenerator()
        self.rocky_generator = RockyIslandGenerator()
        self.forested_generator = ForestedIslandGenerator()
        self.starting_generator = DefaultIslandGenerator()
        # Track how many special resource tiles have been placed
        self.tile_counts = {Tile.WOOD: 0, Tile.METAL: 0}

    def _select_generator(self, cx, cy):
        value = (cx + cy) % 3
        if value == 0:
            return self.rocky_generator            
        elif value == 1:
            return self.forested_generator         
        return self.default_generator

    def clear_chunk_files(self):
        # Clear all chunk files in CHUNK_DIR, creating the directory if it doesn't exist.
        if not os.path.exists(CHUNK_DIR):
            try:
                os.makedirs(CHUNK_DIR)
            except OSError as e:
                print(f"Error: Could not create chunk directory: {e}")
                return
        for filename in os.listdir(CHUNK_DIR):
            file_path = os.path.join(CHUNK_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except PermissionError as e:
                print(f"Warning: Could not delete file {file_path} due to permission error: {e}")
            except OSError as e:
                print(f"Warning: Could not delete file {file_path}: {e}")

    def world_to_chunk(self, x, y):
        return int(x) // CHUNK_SIZE, int(y) // CHUNK_SIZE

    def chunk_to_world(self, cx, cy, tx, ty):
        return cx * CHUNK_SIZE + tx, cy * CHUNK_SIZE + ty

    def generate_chunk(self, cx, cy):
        generator = self._select_generator(cx, cy)
        return generator.generate(cx, cy)

    def save_chunk(self, cx, cy, chunk_data):
        filename = os.path.join(CHUNK_DIR, f"chunk_{cx}_{cy}.pkl")
        try:
            with open(filename, "wb") as f:
                pickle.dump(chunk_data, f)
        except (OSError, pickle.PicklingError) as e:
            print(f"Error saving chunk ({cx}, {cy}): {e}")

    def load_chunk(self, cx, cy):
        filename = os.path.join(CHUNK_DIR, f"chunk_{cx}_{cy}.pkl")
        try:
            if os.path.exists(filename):
                with open(filename, "rb") as f:
                    return pickle.load(f)
        except (OSError, pickle.UnpicklingError) as e:
            print(f"Error loading chunk ({cx}, {cy}): {e}")
        return None

    def get_tile(self, x, y):
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
            self.chunks[(cx, cy)] = loaded_data if loaded_data is not None else self.generate_chunk(cx, cy)
        tile = self.chunks[(cx, cy)][ty][tx]
        self.tile_cache[key] = tile
        return tile

    def set_tile(self, x, y, tile_type):
        cx, cy = self.world_to_chunk(x, y)
        tx = int(x % CHUNK_SIZE)
        ty = int(y % CHUNK_SIZE)
        if tx < 0:
            tx += CHUNK_SIZE
        if ty < 0:
            ty += CHUNK_SIZE
        if (cx, cy) not in self.chunks:
            loaded_data = self.load_chunk(cx, cy)
            self.chunks[(cx, cy)] = loaded_data if loaded_data is not None else self.generate_chunk(cx, cy)
        old_tile = self.chunks[(cx, cy)][ty][tx]
        self.chunks[(cx, cy)][ty][tx] = tile_type
        self.tile_cache[(x, y)] = tile_type
        if tile_type in self.tile_counts and old_tile != tile_type:
            self.tile_counts[tile_type] += 1
        self.dirty_chunks.add((cx, cy))

    def save_dirty_chunks(self):
        for cx, cy in self.dirty_chunks:
            if (cx, cy) in self.chunks:
                self.save_chunk(cx, cy, self.chunks[(cx, cy)])
        self.dirty_chunks.clear()

    def initialize_starting_area(self):
        for cx in range(-2, 3):
            for cy in range(-2, 3):
                self.chunks[(cx, cy)] = self.starting_generator.generate(cx, cy)
        
        target_land_tiles = random.randint(STARTING_AREA_LAND_MIN, STARTING_AREA_LAND_MAX)
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
        features_to_add = random.randint(STARTING_AREA_FEATURES_MIN, STARTING_AREA_FEATURES_MAX)
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
        self.player_chunk = self.world_to_chunk(player_pos[0], player_pos[1])

    def manage_chunks(self):
        cx, cy = self.player_chunk
        loaded_chunks = set()
        for dx in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1):
            for dy in range(-VIEW_CHUNKS // 2, VIEW_CHUNKS // 2 + 1):
                chunk_key = (cx + dx, cy + dy)
                loaded_chunks.add(chunk_key)
                if chunk_key not in self.chunks:
                    loaded_data = self.load_chunk(cx + dx, cy + dy)
                    self.chunks[chunk_key] = loaded_data if loaded_data is not None else self.generate_chunk(cx + dx, cy + dy)
        for key in list(self.chunks.keys()):
            if key not in loaded_chunks:
                if key in self.dirty_chunks:
                    self.save_chunk(key[0], key[1], self.chunks[key])
                self.dirty_chunks.discard(key)
                cx, cy = key
                for ty in range(CHUNK_SIZE):
                    for tx in range(CHUNK_SIZE):
                        wx, wy = self.chunk_to_world(cx, cy, tx, ty)
                        self.tile_cache.pop((wx, wy), None)
                del self.chunks[key]