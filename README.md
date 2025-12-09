# minecraft-holodeck

A Python library for modifying Minecraft Java Edition world files through `/setblock` and `/fill` command interpretation.

## Status: Relative Coordinates Implemented! 🎉

**NEW:** Relative coordinates are now supported! Build position-independent structures and reuse them anywhere:
- `/setblock ~5 ~-1 ~10 minecraft:stone` - Relative to origin point
- `/fill ~ ~ ~ ~10 ~10 ~10 minecraft:glass hollow` - Build from origin
- Convert existing scripts: `mccommand convert-to-relative cabin_build.txt`
- Place same structure at different locations using `--origin` flag
- Structure analysis: `mccommand analyze cabin_build.txt` - Get extents for base-to-base placement

**Previous features also complete:**
- Fill modes (`hollow`, `keep`, `outline`, etc.)
- Block states (`[facing=north,half=top]`)
- World creation (flat and void worlds)

## Installation

```bash
# Clone the repository
git clone https://github.com/1mentat/minecraft-holodeck.git
cd minecraft-holodeck

# Install with uv
uv sync --all-extras
```

## Creating Worlds

You can create new Minecraft worlds programmatically or use existing ones:

### Create New Worlds

```bash
# Create a flat world
mccommand create-flat ./my_world --size 16,16

# Create a void world with spawn platform
mccommand create-void ./void_world --spawn-platform

# Custom flat world with specific layers
mccommand create-flat ./custom --layers "bedrock:1,stone:10,dirt:3,grass_block:1"
```

### Or Use Existing Worlds

1. **Minecraft Java Edition**: Launch Minecraft → Create New World
2. **Amulet Editor**: [https://www.amuletmc.com/](https://www.amuletmc.com/)

## Quick Start

### CLI Usage

Execute a single command:
```bash
mccommand execute ./my_world "/setblock 0 64 0 minecraft:stone"
```

Fill a region:
```bash
mccommand execute ./my_world "/fill 0 64 0 10 70 10 minecraft:glass"
```

Use relative coordinates with custom origin:
```bash
mccommand execute ./my_world "/setblock ~5 ~-1 ~5 minecraft:stone" --origin 100,64,200
# Places stone at (105, 63, 205)
```

Execute multiple commands from a file:
```bash
mccommand batch ./my_world commands.txt --origin 100,64,200
```

Parse and debug a command:
```bash
mccommand parse "/setblock ~10 ~ ~-5 minecraft:diamond_block"
```

### Python API

```python
from minecraft_holodeck import WorldEditor, create_flat_world, create_void_world

# Create a new flat world
create_flat_world(
    "./my_world",
    size_chunks=(16, 16),
    layers=[("bedrock", 1), ("stone", 5), ("dirt", 3), ("grass_block", 1)],
    name="My Flat World"
)

# Create a void world with spawn platform
create_void_world(
    "./void_world",
    size_chunks=(8, 8),
    spawn_platform=True,
    name="The Void"
)

# Execute commands on a world
with WorldEditor("/path/to/world") as editor:
    editor.execute("/setblock 0 64 0 minecraft:diamond_block")
    editor.execute("/fill 0 64 0 10 70 10 minecraft:stone")
    editor.save()

# Use relative coordinates with custom origin
with WorldEditor("/path/to/world", origin=(100, 64, 200)) as editor:
    editor.execute("/setblock ~ ~ ~ minecraft:diamond_block")  # Places at (100, 64, 200)
    editor.execute("/setblock ~5 ~0 ~10 minecraft:gold_block")  # Places at (105, 64, 210)
    editor.save()
```

## Relative Coordinates - Build Reusable Structures!

Relative coordinates make your build scripts position-independent, so you can place the same structure at multiple locations.

### Using Relative Coordinates

Relative coordinates use the `~` symbol and are offset from an origin point:

```bash
# ~ alone means ~0 (exactly at origin)
mccommand execute ./world "/setblock ~ ~ ~ minecraft:stone" --origin 100,64,200

# ~5 means 5 blocks from origin
mccommand execute ./world "/setblock ~5 ~0 ~10 minecraft:stone" --origin 100,64,200
# Places block at (105, 64, 210)

# Negative offsets work too
mccommand execute ./world "/setblock ~-3 ~5 ~-2 minecraft:glass" --origin 50,64,50
# Places block at (47, 69, 48)

# Mix absolute and relative coordinates
mccommand execute ./world "/setblock 100 ~5 200 minecraft:torch"
```

### Converting Existing Scripts

Convert absolute coordinate scripts to relative coordinates:

```bash
# Auto-detect base point from minimum coordinates
mccommand convert-to-relative scripts/cabin_build.txt

# Specify custom base point
mccommand convert-to-relative scripts/castle.txt --base 0,64,0

# Custom output filename
mccommand convert-to-relative scripts/house.txt -o scripts/house_relative.txt
```

This creates a new script with relative coordinates that you can reuse anywhere!

### Building Multiple Structures

Once converted to relative coordinates, place the same structure at different locations:

```bash
# Place first cabin at origin
mccommand batch ./world cabin_relative.txt --origin 0,64,0

# Place second cabin 20 blocks east
mccommand batch ./world cabin_relative.txt --origin 20,64,0

# Place third cabin 40 blocks east
mccommand batch ./world cabin_relative.txt --origin 40,64,0

# Build an entire village from one script!
```

### Real-World Example

```bash
# 1. Convert the cabin script to relative coordinates
mccommand convert-to-relative scripts/cabin_build.txt
# Output: scripts/cabin_build_relative.txt

# 2. Build a village with 5 cabins
mccommand batch ./world scripts/cabin_build_relative.txt --origin -1,64,-3
mccommand batch ./world scripts/cabin_build_relative.txt --origin 19,64,-3
mccommand batch ./world scripts/cabin_build_relative.txt --origin 39,64,-3
mccommand batch ./world scripts/cabin_build_relative.txt --origin -1,64,12
mccommand batch ./world scripts/cabin_build_relative.txt --origin 19,64,12

# Same cabin, 5 different locations - that's the power of relative coordinates!
```

>>>>>>> f33b9f0 (Implement relative coordinate support and script converter)
## Implemented Features (Phase 1-5)

✅ **Basic Commands**
- `/setblock x y z block_id` - Place single blocks
- `/fill x1 y1 z1 x2 y2 z2 block_id [mode]` - Fill regions with advanced modes

✅ **Block IDs**
- Namespace support: `minecraft:stone` or just `stone`
- Custom namespaces: `mymod:custom_block`

✅ **Block States**
- Full block state syntax: `block_id[key=value,key2=value2]`
- String values: `[facing=north,half=top]`
- Boolean values: `[waterlogged=true]`
- Integer values: `[delay=3]`
- Works with stairs, doors, slabs, and all state-based blocks

✅ **Fill Modes**
- `hollow` - Fill only the outer shell, interior becomes air (perfect for building walls!)
- `destroy` - Replace all blocks (same as default)
- `keep` - Only fill air blocks, preserve existing blocks
- `outline` - Fill only the edges (wireframe)
- `replace` - Default mode, replaces all blocks

✅ **Coordinates**
- Absolute coordinates: `10 64 10`
- Negative coordinates: `-10 64 -20`
- **Relative coordinates:** `~5 ~-1 ~10` - Offset from origin point
- **Mixed coordinates:** `10 ~5 -20` - Mix absolute and relative

✅ **Relative Coordinate Tools** (NEW!)
- Script converter: `mccommand convert-to-relative` - Convert absolute to relative
- Structure analyzer: `mccommand analyze` - Get structure extents for base-to-base placement
- Auto-detect base points from existing scripts
- Origin parameter: `--origin x,y,z` - Set reference point for relative coords
- Build reusable, position-independent structures

✅ **World Creation**
- Create flat worlds with custom layers
- Create void worlds with optional spawn platforms
- Programmatic world generation via Python API

✅ **Infrastructure**
- Full type checking with mypy (strict mode)
- Comprehensive test suite (60+ tests, 100% passing)
- CLI with multiple commands
- Context manager support for safe resource handling

## Roadmap

### ✅ Phase 1: Basic Commands (COMPLETE)
- ✅ `/setblock` and `/fill` with absolute coordinates
- ✅ Command parser with Lark grammar
- ✅ World modification via amulet-core

### ✅ Phase 2: Block States (COMPLETE)
- ✅ Support `[facing=north,half=top]` syntax
- ✅ Enable stairs, doors, slabs with proper orientation
- ✅ Unlock cabin building with peaked roofs!

### ✅ Phase 3: Fill Modes (COMPLETE)
- ✅ `hollow` fill mode for efficient wall building
- ✅ `keep`, `outline`, `destroy`, `replace` modes
- ✅ Complete cabin construction in single commands

### ✅ Phase 4: World Creation (COMPLETE)
- ✅ Create flat worlds programmatically with custom layers
- ✅ Create void worlds with optional spawn platforms
- ✅ CLI commands for world creation
- ✅ Python API for world creation

### ✅ Phase 5: Relative Coordinates (COMPLETE)
- ✅ Parse `~` relative coordinate syntax (`~5`, `~-1`, `~`)
- ✅ Mixed absolute and relative coordinates
- ✅ Origin parameter support (`--origin x,y,z`)
- ✅ Script converter tool (`convert-to-relative`)
- ✅ Structure analyzer tool (`analyze`) for extent calculation
- ✅ Auto-detect base points from existing scripts
- ✅ Build reusable, position-independent structures

### Phase 6+: Future Enhancements
- NBT data for chests, signs, command blocks
- Full block validation with helpful error messages
- Replace mode with block filters (`/fill ... replace stone`)
- Multi-script composition with YAML manifests
- Template-based world generation
- Advanced world manipulation (clone, copy regions)
- Structure rotation (90°, 180°, 270°)

See [PLAN.md](PLAN.md) for the complete implementation plan.

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Type checking
uv run mypy src/minecraft_holodeck

# Linting
uv run ruff check src/minecraft_holodeck
```

## Architecture

```
minecraft-holodeck/
├── src/minecraft_holodeck/
│   ├── parser/              # Lark-based command parser
│   │   ├── grammar.lark     # Command grammar
│   │   ├── ast.py           # AST data structures
│   │   └── parser.py        # Parser implementation
│   ├── world/               # World modification via amulet-core
│   │   ├── modifier.py      # WorldModifier class
│   │   └── block_converter.py
│   ├── api.py               # High-level Python API
│   └── cli.py               # Command-line interface
└── tests/
    └── parser/
        └── test_parser.py
```

## Requirements

- Python 3.10+
- amulet-core for world file I/O
- Lark for command parsing
- Click for CLI

## License

See [LICENSE](LICENSE) file.

## Contributing

This project follows a phased development approach. See PLAN.md for current phase and upcoming features.
