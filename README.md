# minecraft-holodeck

A Python library for modifying Minecraft Java Edition world files through `/setblock` and `/fill` command interpretation.

## Status: Phase 5 Complete 🎉

Relative coordinates are now fully supported! Build anywhere without editing coordinates:
- `/setblock ~5 ~-1 ~5 minecraft:stone` - Place blocks relative to origin
- `/fill ~ ~ ~ ~9 ~5 ~7 spruce_planks hollow` - Build structures from current position
- `/setblock 10 ~5 -20 minecraft:glass` - Mix absolute and relative coordinates

**Previous features:**
- Fill modes: `/fill 0 65 0 9 69 7 spruce_planks hollow` - Build walls efficiently!
- Block states: `/setblock 0 64 0 minecraft:oak_stairs[facing=north,half=top]`
- World creation: Create flat and void worlds programmatically

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
    # Places block at (105, 63, 205)
    editor.execute("/setblock ~5 ~-1 ~5 minecraft:stone")
    # Builds a 10x6x8 structure starting from origin
    editor.execute("/fill ~ ~ ~ ~9 ~5 ~7 spruce_planks hollow")
    editor.save()
```

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
- Relative coordinates: `~5 ~-1 ~5` - Offset from origin
- Mixed coordinates: `10 ~5 -20` - Combine absolute and relative

✅ **Infrastructure**
- Full type checking with mypy (strict mode)
- Comprehensive test suite (56 tests, 100% passing)
- CLI with multiple commands
- Context manager support for safe resource handling

## Roadmap

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
- ✅ Support `~` notation for relative coordinates
- ✅ `~5` (offset from origin), `~` (same as origin)
- ✅ Mixed absolute and relative: `10 ~5 -20`
- ✅ `--origin` CLI parameter for setting origin point
- ✅ Reusable command templates

### Phase 6+
- NBT data for chests, signs, command blocks
- Full block validation with helpful error messages
- Replace mode with block filters
- Template-based world generation
- Advanced world manipulation (clone, copy regions)

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
