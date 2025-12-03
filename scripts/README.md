# 🏡 Cabin Build Script

This directory contains scripts to build a cozy woodland cabin in Minecraft using minecraft-holodeck.

## What's Included

- **cabin_build.txt** - Command file for batch execution
- **cabin_build.py** - Python script for programmatic building
- **README.md** - This file

## Build Specifications

- **Size:** 9×7 base, ~6 blocks tall (plus peaked roof)
- **Style:** Rustic spruce cabin with stone foundation
- **Location:** X=0, Y=64, Z=0 (customizable)
- **Features:**
  - Stone cobblestone foundation
  - Spruce wood walls with log corner pillars
  - Glass pane windows
  - Spruce door entrance
  - Peaked roof with stairs and slabs
  - Stone chimney with campfire
  - Interior furnishings (bed, crafting table, lanterns)
  - Exterior decorations (flower pots, path, bushes)

## Prerequisites

### 1. Create a Flat World

You need an existing Minecraft Java Edition world. Create one using:

**In Minecraft:**
1. Launch Minecraft Java Edition
2. Click "Singleplayer" → "Create New World"
3. Click "More World Options"
4. Set "World Type" to **Flat**
5. Create the world and close Minecraft

Your world will be saved in:
- **Windows:** `%APPDATA%\.minecraft\saves\<WorldName>`
- **macOS:** `~/Library/Application Support/minecraft/saves/<WorldName>`
- **Linux:** `~/.minecraft/saves/<WorldName>`

### 2. Install minecraft-holodeck

```bash
cd /path/to/minecraft-holodeck
uv sync --all-extras
```

## Usage

### Option 1: Batch Command File (Recommended)

Use the CLI batch command to execute all commands from the text file:

```bash
mccommand batch /path/to/your/world scripts/cabin_build.txt
```

**Example:**
```bash
# macOS/Linux
mccommand batch ~/.minecraft/saves/MyFlatWorld scripts/cabin_build.txt

# Windows
mccommand batch %APPDATA%\.minecraft\saves\MyFlatWorld scripts/cabin_build.txt
```

### Option 2: Python Script

Run the Python script directly:

```bash
python scripts/cabin_build.py /path/to/your/world
```

**Example:**
```bash
# macOS/Linux
python scripts/cabin_build.py ~/.minecraft/saves/MyFlatWorld

# Windows
python scripts/cabin_build.py %APPDATA%\.minecraft\saves\MyFlatWorld
```

## Customization

### Change Build Location

**For cabin_build.txt:**
- Edit the file and replace coordinates in each command
- For example, to build at X=100, Y=70, Z=200, adjust all coordinates accordingly

**For cabin_build.py:**
- Edit the script and change these constants at the top:
```python
BASE_X = 100  # Your desired X coordinate
BASE_Y = 70   # Your desired Y coordinate
BASE_Z = 200  # Your desired Z coordinate
```

### Modify the Design

Both files are well-commented with step-by-step instructions. You can:
- Change block types (e.g., `spruce_planks` → `dark_oak_planks`)
- Adjust dimensions in `/fill` commands
- Add or remove decorative elements
- Comment out optional enhancements

## Viewing Your Build

1. After running the script, open Minecraft
2. Load the world you modified
3. Teleport to the cabin location:
   ```
   /tp @s 0 64 0
   ```
   (Or use your custom coordinates)

## Troubleshooting

### "World directory not found"
- Make sure Minecraft is **closed** before running the script
- Verify the world path is correct
- Check that you created a world in Minecraft first

### "Permission denied"
- Close Minecraft completely
- Ensure you have write permissions to the world directory

### Blocks not appearing correctly
- Make sure you're using Minecraft Java Edition 1.13+
- Verify block names are correct (use F3+H in-game to see block IDs)

### Commands failing during batch execution
- Check the error message for the specific line number
- Verify block state syntax (e.g., `[facing=north]`)
- Ensure the world is large enough for the build area

## Examples

### Build Multiple Cabins

Edit cabin_build.py to change BASE_X, BASE_Y, BASE_Z and run multiple times:

```bash
# First cabin at origin
python scripts/cabin_build.py ~/.minecraft/saves/VillageWorld

# Edit BASE_X to 50, then run again
python scripts/cabin_build.py ~/.minecraft/saves/VillageWorld

# Edit BASE_X to 100, run again
python scripts/cabin_build.py ~/.minecraft/saves/VillageWorld
```

### Dark Oak Variant

Replace all instances of `spruce` with `dark_oak` in either file for a darker cabin:

```bash
sed 's/spruce/dark_oak/g' cabin_build.txt > dark_oak_cabin.txt
mccommand batch ~/.minecraft/saves/MyWorld dark_oak_cabin.txt
```

## Credits

Cabin design based on classic Minecraft building techniques for cozy woodland structures.
