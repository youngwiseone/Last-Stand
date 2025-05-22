import pygame
import random
import math
from abc import ABC, abstractmethod
from constants import Tile, TILE_SIZE, MOVEMENT_TILES
from world import World

class DialogueNode:
    """Represents a single dialogue entry with text, choices, and conditions."""
    def __init__(self, text, choices=None, condition=None, action=None):
        self.text = text
        self.choices = choices or []
        self.condition = condition
        self.action = action
        self.node_id = None

class DialogueTree:
    """Manages a sequence of dialogue nodes with branching."""
    def __init__(self, nodes):
        self.nodes = {}
        for node in nodes:
            node.node_id = len(self.nodes)
            self.nodes[node.node_id] = node
        self.start_node = 0 if nodes else None
        if not nodes:
            print("Warning: DialogueTree initialized with no nodes")

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def evaluate_node(self, node_id, game_state):
        node = self.get_node(node_id)
        if not node:
            return None
        if node.condition is None or node.condition(game_state):
            return node
        return None

class DialogueManager:
    """Manages dialogue state, with rendering and input handled externally."""
    def __init__(self):
        self.active = False
        self.current_tree = None
        self.current_node_id = None
        self.game_state = None
        self.npc = None
        self.start_time = 0
        self.timeout = 30000  # 30 seconds timeout

    def start_dialogue(self, npc, tree, game_state):
        if not tree or tree.start_node is None:
            print(f"Error: Invalid dialogue tree for {npc.type}")
            return False
        self.active = True
        self.npc = npc
        self.current_tree = tree
        self.game_state = game_state
        self.current_node_id = tree.start_node
        self.start_time = pygame.time.get_ticks()
        if self.npc:
            self.npc.interaction_cooldown = pygame.time.get_ticks() + 999999
        print(f"Started dialogue with {npc.type} at node {self.current_node_id}")
        return True

    def end_dialogue(self):
        self.active = False
        self.current_tree = None
        self.current_node_id = None
        self.game_state = None
        if self.npc:
            self.npc.interaction_cooldown = pygame.time.get_ticks() + 3000
            self.npc = None
        print("Dialogue ended")

    def advance_dialogue(self, choice_index=None):
        current_node = self.current_tree.get_node(self.current_node_id)
        if not current_node:
            print("No current node, ending dialogue")
            self.end_dialogue()
            return

        if current_node.action:
            try:
                current_node.action(self.game_state)
            except Exception as e:
                print(f"Error in node action: {e}")

        if choice_index is not None and current_node.choices:
            if choice_index < len(current_node.choices):
                choice_text, next_node_id, choice_action = current_node.choices[choice_index]
                if choice_action:
                    try:
                        choice_action(self.game_state)
                    except Exception as e:
                        print(f"Error in choice action: {e}")
                self.current_node_id = next_node_id
            else:
                print(f"Invalid choice index {choice_index}")
                self.end_dialogue()
                return
        elif not current_node.choices:
            self.current_node_id += 1
            if self.current_node_id not in self.current_tree.nodes:
                self.end_dialogue()
                return

        next_node = self.current_tree.evaluate_node(self.current_node_id, self.game_state)
        if not next_node:
            print("Next node invalid, ending dialogue")
            self.end_dialogue()

    def check_timeout(self):
        if self.active and pygame.time.get_ticks() - self.start_time > self.timeout:
            print("Dialogue timed out, forcing end")
            self.end_dialogue()

class NPC(ABC):
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
    def get_dialogue_tree(self, game_state):
        pass

class WallerNPC(NPC):
    def __init__(self, x, y, state="boat", ship=None, direction=None):
        super().__init__(x, y, state, ship, direction)
        self.type = "waller"

    def get_dialogue_tree(self, game_state):
        nodes = []
        has_fishing_rod = game_state["has_fishing_rod"]
        wood = game_state["wood"]
        fish_caught = game_state["fish_caught"]

        if fish_caught >= 10:
            nodes.append(DialogueNode(
                text="Wow, already up to 10 fish! You're a natural!",
                condition=lambda gs: gs["fish_caught"] >= 10
            ))

        if not has_fishing_rod and wood >= 50:
            nodes.append(DialogueNode(
                text="Want a fishing rod? It'll cost 50 wood.",
                choices=[
                    ("Yes, I'll take it!", len(nodes) + 1, lambda gs: (
                        print(f"Executing purchase: wood={gs['wood']}, has_fishing_rod={gs['has_fishing_rod']}"),
                        gs.update({"wood": gs["wood"] - 50, "has_fishing_rod": True}),
                        gs["wood_texts"].extend([
                            {
                                "x": self.x, "y": self.y - 0.5, "text": "-50 Wood", "timer": 1000, "alpha": 255
                            },
                            {
                                "x": self.x, "y": self.y - 0.5, "text": "", "image_key": "FISHING_ROD", "timer": 1000, "alpha": 255
                            }
                        ]),
                        print(f"Purchased fishing rod: wood={gs['wood']}, has_fishing_rod={gs['has_fishing_rod']}, wood_texts={gs['wood_texts']}")
                    )),
                    ("No, thanks.", None, None)
                ]
            ))
            nodes.append(DialogueNode(
                text="Here's your fishing rod! Happy fishing!"
            ))
        elif not has_fishing_rod:
            nodes.append(DialogueNode(
                text="Come back with 50 wood, and I'll sell you a fishing rod!"
            ))
        else:
            nodes.append(DialogueNode(
                text=f"You've caught {fish_caught} fish so far. Keep it up!"
            ))

        return DialogueTree(nodes)

class TraderNPC(NPC):
    def __init__(self, x, y, state="boat", ship=None, direction=None):
        super().__init__(x, y, state, ship, direction)
        self.type = "trader"

    def get_dialogue_tree(self, game_state):
        nodes = []
        wood = game_state["wood"]
        world = game_state.get("world")

        nodes.append(DialogueNode(
            text="I can trade 10 wood for a loot tile on nearby land.",
            choices=[
                ("Trade 10 wood.", len(nodes) + 1, lambda gs: (
                    gs.update({"wood": gs["wood"] - 10}),
                    gs["wood_texts"].extend(self._place_loot(gs["world"], gs["wood_texts"]))
                )[0] if gs["wood"] >= 10 else None),
                ("Not now.", None, None)
            ],
            condition=lambda gs: gs["wood"] >= 10
        ))
        nodes.append(DialogueNode(
            text="Loot placed! Check nearby land tiles.",
            action=lambda gs: (
                gs.update({"wood": gs["wood"] - 10}),
                gs["wood_texts"].extend(self._place_loot(gs["world"], gs["wood_texts"]))
            )[0]
        ))
        nodes.append(DialogueNode(
            text="You need 10 wood to trade for loot.",
            condition=lambda gs: gs["wood"] < 10
        ))

        return DialogueTree(nodes)

    def _place_loot(self, world, wood_texts):
        neighbors = [(self.x + dx, self.y + dy) for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]]
        for nx, ny in neighbors:
            if world.get_tile(int(nx), int(ny)) == Tile.LAND:
                world.set_tile(int(nx), int(ny), Tile.LOOT)
                return [{
                    "x": nx,
                    "y": ny - 0.5,
                    "text": "+1 Loot",
                    "timer": 1000,
                    "alpha": 255
                }, {
                    "x": self.x,
                    "y": self.y - 0.5,
                    "text": "-10 Wood",
                    "timer": 1000,
                    "alpha": 255
                }]
        return [{
            "x": self.x,
            "y": self.y - 0.5,
            "text": "No Land Nearby",
            "timer": 1000,
            "alpha": 255
        }]

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
        self.npcs = []
        self.scaled_tile_images = scaled_tile_images
        self.npc_sprites = npc_sprites
        self.now = pygame.time.get_ticks()
        self.spawned_counts = {npc["type"]: 0 for npc in NPC_REGISTRY}
        self.dialogue_manager = DialogueManager()

    def interact(self, x, y, game_state, world):
        self.now = pygame.time.get_ticks()
        for npc in self.npcs:
            if any(s["x"] == x and s["y"] == y for s in npc.ship) and self.now >= npc.interaction_cooldown:
                game_state["world"] = world
                dialogue_tree = npc.get_dialogue_tree(game_state)
                if self.dialogue_manager.start_dialogue(npc, dialogue_tree, game_state):
                    return game_state
                else:
                    print("Failed to start dialogue")
                    return game_state
        return game_state

    def spawn_npcs(self, game_state, player_pos, view_width, view_height):
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

    def update(self, dt, world, player_pos):
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