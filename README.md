# **Last Stand**

Requires: **Python**, and the following libraries:  
`pygame`, `random`, `sys`, `math`, `os`, `subprocess`, `pickle`, `shutil`

---

A mini game where you **start on an island** and must **protect yourself from pirates**. Use your mouse to interact with the world, place wood tiles to expand your territory, grow trees for wood, and set up turrets to fend off pirate attacks.

### Controls:
- **WASD** to move  
- **I** to toggle the help menu (shows interaction hints above the selected tile)  
- **Mouse Scroll** to zoom in and out  
- **Left Click** on a tile to interact:
  - On **Water**: Place a boat tile *(uses 1 wood)*  
  - On **Land**: Plant a sapling *(uses 1 wood; grows into a tree over time)*  
  - On **Loot**: Collect 15-30 wood  
  - On **Tree**: Chop to harvest 3 wood  
  - On **Sapling**: Uproot for 1 wood  
  - On **Boat Tile**: Pick up for 1 wood  
  - On **Turret**: Upgrade its level/firing speed *(uses wood based on level)*  
- **Right Click** on a tile to manage turrets:
  - On **Land**: Place a turret *(uses 3 wood; protects against pirates)*  
  - On **Turret**: Pick up the turret *(refunds 3 wood + upgrade costs)*  
- **ESC** to quit the game  
- **SPACE** to restart (only on the game-over screen)