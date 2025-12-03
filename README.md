# minecraft-holodeck

A Python library for modifying Minecraft Java Edition world files through `/setblock` and `/fill` command interpretation.

## Status: Phase 3 Complete 🎉

Fill modes are now fully supported! You can now build efficiently with hollow mode and other advanced fill modes:
- `/fill 0 65 0 9 69 7 spruce_planks hollow` - Build walls in one command!
- `/fill 0 64 0 10 70 10 stone keep` - Only fill air blocks
- `/fill 0 64 0 10 70 10 glass outline` - Create wireframe boxes

**Phase 2** block states are also complete:
- `/setblock 0 64 0 minecraft:oak_stairs[facing=north,half=top]`
- `/setblock 4 66 0 spruce_door[half=lower,hinge=left]`

## Installation

```bash
# Clone the repository
git clone https://github.com/1mentat/minecraft-holodeck.git
cd minecraft-holodeck

# Install with uv
uv sync --all-extras
```

## Prerequisites

You'll need an existing Minecraft Java Edition world to modify. Create one using:

1. **Minecraft Java Edition**: Launch Minecraft → Create New World
   - For flat worlds: More World Options → World Type: Flat
   - For void worlds: Use the Void superflat preset
2. **Amulet Editor**: [https://www.amuletmc.com/](https://www.amuletmc.com/)

> **Note**: Programmatic world creation from scratch is planned for a future release. Currently, minecraft-holodeck modifies existing worlds.

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

Execute multiple commands from a file:
```bash
mccommand batch ./my_world commands.txt
```

Parse and debug a command:
```bash
mccommand parse "/setblock 10 64 10 minecraft:diamond_block"
```

### Python API

```python
from minecraft_holodeck import WorldEditor

# Execute commands on a world
with WorldEditor("/path/to/world") as editor:
    editor.execute("/setblock 0 64 0 minecraft:diamond_block")
    editor.execute("/fill 0 64 0 10 70 10 minecraft:stone")
    editor.save()
```

## Implemented Features (Phase 1-3)

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

✅ **Fill Modes** (NEW!)
- `hollow` - Fill only the outer shell, interior becomes air (perfect for building walls!)
- `destroy` - Replace all blocks (same as default)
- `keep` - Only fill air blocks, preserve existing blocks
- `outline` - Fill only the edges (wireframe)
- `replace` - Default mode, replaces all blocks

✅ **Coordinates**
- Absolute coordinates: `10 64 10`
- Negative coordinates: `-10 64 -20`

✅ **Infrastructure**
- Full type checking with mypy (strict mode)
- Comprehensive test suite (33 tests, 100% passing)
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

### Phase 4+
- Relative coordinates (`~5 ~-1 ~5`)
- NBT data for chests, signs, command blocks
- Full block validation with helpful error messages
- Replace mode with block filters

### Future Features
- **Programmatic world creation**: Create flat/void worlds from scratch without Minecraft
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
