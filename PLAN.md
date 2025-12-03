# Minecraft Command Implementation Plan

## Project: minecraft-holodeck

A Python library for modifying Minecraft Java Edition world files through `/setblock` and `/fill` command interpretation.

---

## 🏡 Cabin-First Development Approach

**Goal**: Build the minimal feature set needed to construct a complete woodsy cabin, then expand from there.

### Target Build: Woodsy Cabin
- **Size**: 9×7 base, ~6 blocks tall with peaked roof
- **Features**: Stone foundation, spruce walls, glass windows, working door, stair roof, chimney
- **Commands needed**: ~40 commands using setblock, fill, block states, and hollow mode

### What This Unlocks (Phases 1-3, ~5 days):
✅ Basic `/setblock` and `/fill` with absolute coordinates
✅ Block states for stairs `[facing=east]`, doors `[half=lower]`, slabs `[type=top]`
✅ Hollow fill mode for efficient wall building
✅ Support for all cabin blocks: cobblestone, spruce planks/logs/stairs/slabs/doors, glass panes

### Why Cabin-First?
1. **Concrete milestone**: Can see real results quickly
2. **Validates architecture**: Tests parser, world modification, and block states
3. **User value**: Delivers a usable tool fast
4. **Motivating**: Building something cool beats abstract features

**After Phase 3 (Day 5), you can build the complete cabin!**

---

## 1. Architecture Overview

### Core Design Principles

- **Separation of Concerns**: Parser, validator, world modifier, and CLI are independent modules
- **Pipeline Architecture**: Command string → AST → Validated command → World modifications
- **Incremental Complexity**: Start simple, add features progressively
- **Type Safety**: Full type hints with mypy strict mode
- **Testability**: Each layer independently testable

### Module Responsibilities

```
┌─────────────────┐
│   CLI / API     │  Entry points (CLI tool, Python API, future web)
└────────┬────────┘
         │
┌────────▼────────┐
│  Command Parser │  Lark grammar → AST
└────────┬────────┘
         │
┌────────▼────────┐
│   Validator     │  Check block IDs, states, coordinates
└────────┬────────┘
         │
┌────────▼────────┐
│ World Modifier  │  amulet-core interface, batch operations
└────────┬────────┘
         │
┌────────▼────────┐
│  World Files    │  .mca region files (Anvil format)
└─────────────────┘
```

### Data Flow

1. **Input**: Command string (`/setblock 10 64 10 minecraft:stone`)
2. **Parse**: Lark parser → `CommandAST` object
3. **Resolve**: Convert relative coords, validate blocks → `ResolvedCommand`
4. **Execute**: Apply to world via amulet-core → Modified chunks
5. **Save**: Write back to world files

### Coordinate System Handling

Three coordinate types:
- **Absolute**: `10 64 10` - Direct world coordinates
- **Relative**: `~5 ~-1 ~5` - Offset from execution position
- **Local**: `^1 ^2 ^3` - Offset in rotated coordinate space (future)

Resolution strategy:
```python
@dataclass
class Position:
    x: int | RelativeCoord
    y: int | RelativeCoord
    z: int | RelativeCoord

@dataclass
class RelativeCoord:
    offset: int

def resolve(pos: Position, origin: tuple[int, int, int]) -> tuple[int, int, int]:
    # Convert Position to absolute coordinates
    pass
```

### Error Handling Strategy

**Three error categories:**

1. **Parse Errors** - Invalid syntax
   - Raise `CommandSyntaxError` with line/column info
   - Human-readable error messages

2. **Validation Errors** - Invalid blocks/states
   - Raise `BlockValidationError` with details
   - Suggest corrections (fuzzy matching)

3. **World Errors** - File I/O, corruption
   - Raise `WorldOperationError`
   - Always preserve backups

**Error hierarchy:**
```python
class MCCommandError(Exception): pass
class CommandSyntaxError(MCCommandError): pass
class BlockValidationError(MCCommandError): pass
class WorldOperationError(MCCommandError): pass
class ChunkNotFoundError(WorldOperationError): pass
```

---

## 2. Command Parser Design

### Parser Technology: Lark

Use Lark parser with LALR(1) for clean grammar definition and good error messages.

### Grammar Specification

```lark
// mccommand/parser/grammar.lark

?start: setblock_cmd | fill_cmd

// Setblock command
setblock_cmd: "setblock" position block_spec mode?
mode: "destroy" | "keep" | "replace"

// Fill command
fill_cmd: "fill" position position block_spec fill_mode?
fill_mode: "destroy"
         | "hollow"
         | "keep"
         | "outline"
         | ("replace" block_spec?)

// Position (absolute, relative, or mixed)
position: coord coord coord
coord: SIGNED_INT                    // absolute: 10
     | "~" SIGNED_INT?              // relative: ~5 or ~

SIGNED_INT: ["-"|"+"] INT

// Block specification
block_spec: namespaced_id block_states? nbt_data?

namespaced_id: NAMESPACE ":" ID
             | ID                    // implicit minecraft:

NAMESPACE: /[a-z0-9_-]+/
ID: /[a-z0-9_\/]+/

// Block states: [facing=north,half=top]
block_states: "[" state_pair ("," state_pair)* "]"
state_pair: ID "=" state_value
state_value: ID | SIGNED_INT | "true" | "false"

// NBT data: {Items:[...]}
nbt_data: "{" nbt_content "}"
nbt_content: /.+/                    // Parse separately with NBT parser

%import common.INT
%import common.WS
%ignore WS
```

### Parser Module Structure

```python
# mccommand/parser/__init__.py
from .parser import CommandParser, ParseResult
from .ast import *

# mccommand/parser/parser.py
from lark import Lark, Tree
from pathlib import Path

class CommandParser:
    """Parse Minecraft commands into AST."""

    def __init__(self):
        grammar_path = Path(__file__).parent / "grammar.lark"
        self.parser = Lark(
            grammar_path.read_text(),
            parser='lalr',
            start='start'
        )
        self.transformer = ASTTransformer()

    def parse(self, command: str) -> CommandAST:
        """Parse command string into AST.

        Args:
            command: Command string (with or without leading /)

        Returns:
            CommandAST object (SetblockCommand or FillCommand)

        Raises:
            CommandSyntaxError: Invalid syntax
        """
        try:
            # Strip leading / if present
            cmd = command.lstrip('/')
            tree = self.parser.parse(cmd)
            return self.transformer.transform(tree)
        except Exception as e:
            raise CommandSyntaxError(str(e)) from e
```

### AST Data Structures

```python
# mccommand/parser/ast.py
from dataclasses import dataclass
from typing import Literal

@dataclass
class Coordinate:
    """Single coordinate (x, y, or z)."""
    value: int
    relative: bool  # True if ~ notation

    def resolve(self, origin: int) -> int:
        return origin + self.value if self.relative else self.value

@dataclass
class Position:
    """3D position."""
    x: Coordinate
    y: Coordinate
    z: Coordinate

    def resolve(self, origin: tuple[int, int, int]) -> tuple[int, int, int]:
        return (
            self.x.resolve(origin[0]),
            self.y.resolve(origin[1]),
            self.z.resolve(origin[2]),
        )

@dataclass
class BlockState:
    """Block state property: facing=north."""
    key: str
    value: str | int | bool

@dataclass
class BlockSpec:
    """Full block specification."""
    namespace: str  # "minecraft"
    block_id: str   # "oak_stairs"
    states: dict[str, str | int | bool]  # {facing: "north", half: "top"}
    nbt: dict | None  # Parsed NBT data

    @property
    def full_id(self) -> str:
        return f"{self.namespace}:{self.block_id}"

@dataclass
class SetblockCommand:
    """Parsed /setblock command."""
    position: Position
    block: BlockSpec
    mode: Literal["destroy", "keep", "replace"]

@dataclass
class FillCommand:
    """Parsed /fill command."""
    pos1: Position
    pos2: Position
    block: BlockSpec
    mode: Literal["destroy", "hollow", "keep", "outline", "replace"]
    filter_block: BlockSpec | None  # For replace mode

CommandAST = SetblockCommand | FillCommand
```

### Lark Transformer

```python
# mccommand/parser/transformer.py
from lark import Transformer, Token

class ASTTransformer(Transformer):
    """Transform Lark parse tree to AST."""

    def coord(self, items) -> Coordinate:
        if len(items) == 1 and items[0] == "~":
            return Coordinate(0, relative=True)
        elif items[0] == "~":
            return Coordinate(int(items[1]), relative=True)
        else:
            return Coordinate(int(items[0]), relative=False)

    def position(self, items) -> Position:
        return Position(x=items[0], y=items[1], z=items[2])

    def block_spec(self, items) -> BlockSpec:
        namespaced_id = items[0]
        # Handle namespace:id or just id
        if ":" in namespaced_id:
            namespace, block_id = namespaced_id.split(":", 1)
        else:
            namespace, block_id = "minecraft", namespaced_id

        states = {}
        nbt = None

        for item in items[1:]:
            if isinstance(item, dict) and "states" in item:
                states = item["states"]
            elif isinstance(item, dict):
                nbt = item

        return BlockSpec(namespace, block_id, states, nbt)

    def setblock_cmd(self, items) -> SetblockCommand:
        position = items[0]
        block = items[1]
        mode = items[2] if len(items) > 2 else "replace"
        return SetblockCommand(position, block, mode)

    def fill_cmd(self, items) -> FillCommand:
        pos1 = items[0]
        pos2 = items[1]
        block = items[2]
        mode = "replace"
        filter_block = None

        if len(items) > 3:
            mode_data = items[3]
            # Parse mode and optional filter
            # ...

        return FillCommand(pos1, pos2, block, mode, filter_block)
```

### NBT Parsing

NBT data is complex - use dedicated library:

```python
# mccommand/parser/nbt_parser.py
from nbt import nbt  # Use existing NBT library

def parse_nbt_string(nbt_str: str) -> dict:
    """Parse NBT string notation to Python dict.

    Example: '{Items:[{Slot:0b,id:"diamond"}]}' → dict

    Uses snbt (stringified NBT) format parser.
    """
    # Use library like 'nbtlib' or implement SNBT parser
    import nbtlib
    return nbtlib.parse_nbt(nbt_str)
```

---

## 3. World Modification Layer

### Amulet-Core Integration

Amulet-core handles all low-level Anvil format details.

```python
# mccommand/world/modifier.py
from amulet.api.level import World
from amulet.api.block import Block
from amulet.api.selection import SelectionBox
import amulet

class WorldModifier:
    """Interface to modify Minecraft worlds."""

    def __init__(self, world_path: str):
        """Open a Minecraft world.

        Args:
            world_path: Path to world folder (containing level.dat)
        """
        self.world: World = amulet.load_level(world_path)
        self.dimension = "minecraft:overworld"  # Default dimension

    def set_block(
        self,
        x: int,
        y: int,
        z: int,
        block: Block,
        mode: str = "replace"
    ) -> None:
        """Set a single block.

        Args:
            x, y, z: Absolute coordinates
            block: Amulet Block object
            mode: "destroy", "keep", or "replace"
        """
        if mode == "keep":
            existing = self.world.get_block(x, y, z, self.dimension)
            if not existing.namespaced_name == "minecraft:air":
                return  # Don't replace non-air blocks

        self.world.set_version_block(
            x, y, z,
            self.dimension,
            ("java", (1, 20, 1)),  # Target version
            block
        )

    def fill_region(
        self,
        x1: int, y1: int, z1: int,
        x2: int, y2: int, z2: int,
        block: Block,
        mode: str = "replace",
        filter_block: Block | None = None
    ) -> int:
        """Fill a region with blocks.

        Returns:
            Number of blocks modified
        """
        # Normalize coordinates (ensure x1 <= x2, etc.)
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        min_z, max_z = min(z1, z2), max(z1, z2)

        selection = SelectionBox((min_x, min_y, min_z), (max_x + 1, max_y + 1, max_z + 1))

        if mode == "hollow":
            return self._fill_hollow(selection, block)
        elif mode == "outline":
            return self._fill_outline(selection, block)
        elif mode == "replace":
            return self._fill_replace(selection, block, filter_block)
        else:  # destroy, keep
            return self._fill_basic(selection, block, mode)

    def _fill_basic(self, selection: SelectionBox, block: Block, mode: str) -> int:
        """Basic fill operation."""
        count = 0
        for x, y, z in selection:
            if mode == "keep":
                existing = self.world.get_block(x, y, z, self.dimension)
                if not existing.namespaced_name == "minecraft:air":
                    continue

            self.world.set_version_block(
                x, y, z, self.dimension,
                ("java", (1, 20, 1)),
                block
            )
            count += 1
        return count

    def _fill_hollow(self, selection: SelectionBox, block: Block) -> int:
        """Fill only the outer shell."""
        count = 0
        min_x, min_y, min_z = selection.min
        max_x, max_y, max_z = selection.max

        for x, y, z in selection:
            # Check if on boundary
            is_boundary = (
                x == min_x or x == max_x - 1 or
                y == min_y or y == max_y - 1 or
                z == min_z or z == max_z - 1
            )

            if is_boundary:
                self.world.set_version_block(
                    x, y, z, self.dimension,
                    ("java", (1, 20, 1)),
                    block
                )
                count += 1
            else:
                # Fill interior with air
                air = Block("minecraft", "air")
                self.world.set_version_block(
                    x, y, z, self.dimension,
                    ("java", (1, 20, 1)),
                    air
                )

        return count

    def _fill_outline(self, selection: SelectionBox, block: Block) -> int:
        """Fill only the edges (12 lines of the box)."""
        # Only corners and edges, not faces
        # Implementation similar to hollow but only edges
        pass

    def _fill_replace(
        self,
        selection: SelectionBox,
        block: Block,
        filter_block: Block | None
    ) -> int:
        """Replace blocks matching filter."""
        count = 0
        for x, y, z in selection:
            existing = self.world.get_block(x, y, z, self.dimension)

            if filter_block is None:
                # Replace all non-air
                if existing.namespaced_name == "minecraft:air":
                    continue
            else:
                # Replace only matching blocks
                if existing.namespaced_name != filter_block.namespaced_name:
                    continue

            self.world.set_version_block(
                x, y, z, self.dimension,
                ("java", (1, 20, 1)),
                block
            )
            count += 1

        return count

    def save(self) -> None:
        """Save all changes to world files."""
        self.world.save()

    def close(self) -> None:
        """Close the world."""
        self.world.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
```

### Block Conversion

Convert our BlockSpec to Amulet Block:

```python
# mccommand/world/block_converter.py
from amulet.api.block import Block, BlockState
from mccommand.parser.ast import BlockSpec

def blockspec_to_amulet(spec: BlockSpec) -> Block:
    """Convert our BlockSpec to Amulet Block object.

    Args:
        spec: Parsed block specification

    Returns:
        Amulet Block object ready for world placement
    """
    # Create base block
    block = Block(spec.namespace, spec.block_id)

    # Add block states if present
    if spec.states:
        properties = {}
        for key, value in spec.states.items():
            # Convert to string (Amulet uses string properties)
            properties[key] = str(value).lower()

        block = Block(spec.namespace, spec.block_id, properties)

    # NBT data handled separately for tile entities
    return block
```

### Tile Entity Handling

Some blocks need tile entity data (chests, signs, etc.):

```python
# mccommand/world/tile_entities.py
from amulet.api.block_entity import BlockEntity

TILE_ENTITY_BLOCKS = {
    "chest", "trapped_chest", "barrel",
    "furnace", "blast_furnace", "smoker",
    "sign", "wall_sign",
    "command_block", "repeating_command_block", "chain_command_block",
    # ... more
}

def needs_tile_entity(block_id: str) -> bool:
    """Check if block requires tile entity data."""
    return block_id in TILE_ENTITY_BLOCKS

def create_tile_entity(
    x: int, y: int, z: int,
    block_spec: BlockSpec
) -> BlockEntity:
    """Create tile entity from NBT data in BlockSpec."""
    if block_spec.nbt is None:
        # Return default/empty tile entity
        return BlockEntity(block_spec.namespace, block_spec.block_id, x, y, z, {})

    # Merge NBT data with position
    nbt_data = block_spec.nbt.copy()
    nbt_data.update({"x": x, "y": y, "z": z})

    return BlockEntity(
        block_spec.namespace,
        block_spec.block_id,
        x, y, z,
        nbt_data
    )
```

### Batch Operations & Performance

For large `/fill` operations:

```python
# mccommand/world/batch.py

class BatchModifier:
    """Optimized batch block modifications."""

    def __init__(self, world: World):
        self.world = world
        self.pending_blocks = []
        self.chunk_cache = {}

    def queue_block(self, x: int, y: int, z: int, block: Block):
        """Queue a block change."""
        self.pending_blocks.append((x, y, z, block))

    def flush(self, batch_size: int = 1000):
        """Apply all queued changes in batches."""
        # Group by chunk for efficiency
        by_chunk = {}
        for x, y, z, block in self.pending_blocks:
            chunk_pos = (x >> 4, z >> 4)  # Chunk coordinates
            if chunk_pos not in by_chunk:
                by_chunk[chunk_pos] = []
            by_chunk[chunk_pos].append((x, y, z, block))

        # Process chunk by chunk
        for chunk_pos, blocks in by_chunk.items():
            for x, y, z, block in blocks:
                self.world.set_version_block(
                    x, y, z, "minecraft:overworld",
                    ("java", (1, 20, 1)),
                    block
                )

        self.pending_blocks.clear()
```

---

## 4. Block State & NBT Handling

### Block Registry

Validate blocks against known block list:

```python
# mccommand/blocks/registry.py
from pathlib import Path
import json

class BlockRegistry:
    """Registry of valid Minecraft blocks and their properties."""

    def __init__(self, version: str = "1.20.1"):
        self.version = version
        self.blocks = self._load_blocks()

    def _load_blocks(self) -> dict:
        """Load block definitions from data files.

        Uses extracted data from Minecraft JAR or Burger/PrismarineJS data.
        """
        # Load from mccommand/blocks/data/1.20.1/blocks.json
        data_path = Path(__file__).parent / "data" / self.version / "blocks.json"
        with open(data_path) as f:
            return json.load(f)

    def is_valid_block(self, namespace: str, block_id: str) -> bool:
        """Check if block exists."""
        full_id = f"{namespace}:{block_id}"
        return full_id in self.blocks

    def get_valid_states(self, namespace: str, block_id: str) -> dict[str, list]:
        """Get valid states for a block.

        Returns:
            Dict like {"facing": ["north", "south", "east", "west"],
                      "half": ["top", "bottom"]}
        """
        full_id = f"{namespace}:{block_id}"
        if full_id not in self.blocks:
            raise BlockValidationError(f"Unknown block: {full_id}")

        return self.blocks[full_id].get("states", {})

    def validate_block_spec(self, spec: BlockSpec) -> list[str]:
        """Validate a BlockSpec, return list of errors."""
        errors = []

        # Check block exists
        if not self.is_valid_block(spec.namespace, spec.block_id):
            errors.append(f"Unknown block: {spec.full_id}")
            # Try fuzzy matching for suggestions
            suggestion = self._find_similar_block(spec.block_id)
            if suggestion:
                errors.append(f"Did you mean: {suggestion}?")
            return errors

        # Check block states
        valid_states = self.get_valid_states(spec.namespace, spec.block_id)
        for key, value in spec.states.items():
            if key not in valid_states:
                errors.append(f"Unknown state '{key}' for {spec.full_id}")
                continue

            if value not in valid_states[key]:
                errors.append(
                    f"Invalid value '{value}' for state '{key}'. "
                    f"Valid values: {valid_states[key]}"
                )

        return errors

    def _find_similar_block(self, block_id: str) -> str | None:
        """Find similar block name using fuzzy matching."""
        from difflib import get_close_matches
        all_blocks = [b.split(":")[1] for b in self.blocks.keys()]
        matches = get_close_matches(block_id, all_blocks, n=1, cutoff=0.6)
        return f"minecraft:{matches[0]}" if matches else None
```

### Block Data Files

Extract from Minecraft JAR or use PrismarineJS data:

```json
// mccommand/blocks/data/1.20.1/blocks.json
{
  "minecraft:stone": {
    "states": {}
  },
  "minecraft:oak_stairs": {
    "states": {
      "facing": ["north", "south", "east", "west"],
      "half": ["top", "bottom"],
      "shape": ["straight", "inner_left", "inner_right", "outer_left", "outer_right"],
      "waterlogged": ["true", "false"]
    },
    "default_state": {
      "facing": "north",
      "half": "bottom",
      "shape": "straight",
      "waterlogged": "false"
    }
  },
  "minecraft:chest": {
    "states": {
      "facing": ["north", "south", "east", "west"],
      "type": ["single", "left", "right"],
      "waterlogged": ["true", "false"]
    },
    "tile_entity": true
  }
}
```

### NBT Validation

```python
# mccommand/blocks/nbt_validator.py

def validate_nbt_for_block(block_id: str, nbt_data: dict) -> list[str]:
    """Validate NBT data makes sense for the block type.

    For example, chest needs Items array, sign needs Text1-Text4, etc.
    """
    errors = []

    if block_id == "chest":
        if "Items" in nbt_data:
            # Validate Items structure
            if not isinstance(nbt_data["Items"], list):
                errors.append("chest Items must be a list")

    # More validation rules...

    return errors
```

---

## 5. File Structure

```
minecraft-holodeck/
├── pyproject.toml           # Project metadata, dependencies (uv)
├── uv.lock                  # Lockfile
├── README.md
├── PLAN.md                  # This file
├── .gitignore
│
├── mccommand/               # Main package
│   ├── __init__.py         # Public API exports
│   ├── cli.py              # Click-based CLI
│   ├── api.py              # High-level Python API
│   │
│   ├── parser/             # Command parsing
│   │   ├── __init__.py
│   │   ├── grammar.lark    # Lark grammar definition
│   │   ├── parser.py       # Parser class
│   │   ├── transformer.py  # Lark transformer
│   │   ├── ast.py          # AST data structures
│   │   └── nbt_parser.py   # NBT string parsing
│   │
│   ├── blocks/             # Block validation & data
│   │   ├── __init__.py
│   │   ├── registry.py     # BlockRegistry class
│   │   ├── nbt_validator.py
│   │   └── data/           # Block data per version
│   │       └── 1.20.1/
│   │           ├── blocks.json
│   │           └── entities.json
│   │
│   ├── world/              # World modification
│   │   ├── __init__.py
│   │   ├── modifier.py     # WorldModifier class
│   │   ├── block_converter.py
│   │   ├── tile_entities.py
│   │   └── batch.py        # Batch operations
│   │
│   └── exceptions.py       # Exception classes
│
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   │
│   ├── parser/
│   │   ├── test_parser.py
│   │   ├── test_coordinates.py
│   │   └── test_block_spec.py
│   │
│   ├── blocks/
│   │   └── test_registry.py
│   │
│   ├── world/
│   │   ├── test_modifier.py
│   │   └── test_integration.py
│   │
│   └── fixtures/           # Test worlds
│       ├── test_world_1/   # Minimal test world
│       └── commands.txt    # Test commands
│
├── scripts/                # Development scripts
│   ├── extract_blocks.py   # Extract block data from MC jar
│   └── benchmark.py        # Performance testing
│
└── docs/                   # Documentation
    ├── api.md
    ├── cli.md
    └── extending.md
```

### Key Files Detail

**pyproject.toml**:
```toml
[project]
name = "minecraft-holodeck"
version = "0.1.0"
description = "Modify Minecraft worlds with /setblock and /fill commands"
requires-python = ">=3.10"
dependencies = [
    "amulet-core>=1.9.0",
    "amulet-nbt>=2.0.0",
    "lark>=1.1.0",
    "click>=8.1.0",
    "typing-extensions>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]

[project.scripts]
mccommand = "mccommand.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.mypy]
strict = true
warn_unreachable = true
warn_unused_ignores = true

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "UP"]
```

**mccommand/__init__.py**:
```python
"""Minecraft world modification through command interpretation."""

from mccommand.api import execute_command, WorldEditor
from mccommand.parser import CommandParser
from mccommand.exceptions import *

__version__ = "0.1.0"
__all__ = [
    "execute_command",
    "WorldEditor",
    "CommandParser",
]
```

**mccommand/api.py**:
```python
"""High-level Python API."""

from pathlib import Path
from mccommand.parser import CommandParser
from mccommand.world import WorldModifier
from mccommand.blocks import BlockRegistry

class WorldEditor:
    """High-level API for executing commands on a world.

    Example:
        with WorldEditor("/path/to/world") as editor:
            editor.execute("/setblock 0 64 0 minecraft:diamond_block")
            editor.execute("/fill 0 64 0 10 70 10 minecraft:stone")
    """

    def __init__(self, world_path: str | Path, origin: tuple[int, int, int] = (0, 0, 0)):
        self.world_path = Path(world_path)
        self.origin = origin
        self.parser = CommandParser()
        self.registry = BlockRegistry()
        self.modifier = WorldModifier(str(world_path))

    def execute(self, command: str) -> int:
        """Execute a command, return number of blocks changed."""
        # Parse
        ast = self.parser.parse(command)

        # Validate
        from mccommand.parser.ast import SetblockCommand, FillCommand

        if isinstance(ast, SetblockCommand):
            errors = self.registry.validate_block_spec(ast.block)
            if errors:
                raise BlockValidationError("\n".join(errors))

            # Resolve coordinates
            x, y, z = ast.position.resolve(self.origin)

            # Convert block
            from mccommand.world.block_converter import blockspec_to_amulet
            block = blockspec_to_amulet(ast.block)

            # Execute
            self.modifier.set_block(x, y, z, block, ast.mode)
            return 1

        elif isinstance(ast, FillCommand):
            # Similar for fill...
            pass

    def save(self):
        """Save changes to world."""
        self.modifier.save()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.modifier.close()

def execute_command(world_path: str, command: str, origin: tuple[int, int, int] = (0, 0, 0)) -> int:
    """Quick API: execute single command.

    Args:
        world_path: Path to Minecraft world folder
        command: Command string (e.g., "/setblock 0 64 0 minecraft:stone")
        origin: Origin point for relative coordinates

    Returns:
        Number of blocks modified
    """
    with WorldEditor(world_path, origin) as editor:
        count = editor.execute(command)
        editor.save()
    return count
```

**mccommand/cli.py**:
```python
"""Command-line interface."""

import click
from pathlib import Path
from mccommand.api import WorldEditor

@click.group()
@click.version_option()
def main():
    """Minecraft world modification tool."""
    pass

@main.command()
@click.argument("world_path", type=click.Path(exists=True))
@click.argument("command")
@click.option("--origin", default="0,0,0", help="Origin for relative coords (x,y,z)")
@click.option("--dry-run", is_flag=True, help="Parse but don't execute")
def execute(world_path: str, command: str, origin: str, dry_run: bool):
    """Execute a single command on a world.

    Examples:
        mccommand execute ./my_world "/setblock 0 64 0 minecraft:stone"
        mccommand execute ./my_world "/fill 0 0 0 10 10 10 minecraft:glass"
    """
    origin_tuple = tuple(map(int, origin.split(",")))

    if dry_run:
        from mccommand.parser import CommandParser
        parser = CommandParser()
        ast = parser.parse(command)
        click.echo(f"Parsed: {ast}")
        return

    try:
        with WorldEditor(world_path, origin_tuple) as editor:
            count = editor.execute(command)
            editor.save()
            click.echo(f"Modified {count} blocks")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@main.command()
@click.argument("world_path", type=click.Path(exists=True))
@click.argument("commands_file", type=click.File("r"))
@click.option("--origin", default="0,0,0")
def batch(world_path: str, commands_file, origin: str):
    """Execute multiple commands from a file.

    File format: one command per line
    """
    origin_tuple = tuple(map(int, origin.split(",")))
    total = 0

    with WorldEditor(world_path, origin_tuple) as editor:
        for i, line in enumerate(commands_file, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                count = editor.execute(line)
                total += count
                click.echo(f"Line {i}: {count} blocks")
            except Exception as e:
                click.echo(f"Line {i} error: {e}", err=True)

        editor.save()

    click.echo(f"Total: {total} blocks modified")

@main.command()
@click.argument("command")
def parse(command: str):
    """Parse a command and show the AST (for debugging)."""
    from mccommand.parser import CommandParser
    parser = CommandParser()
    ast = parser.parse(command)

    import json
    from dataclasses import asdict
    click.echo(json.dumps(asdict(ast), indent=2))

if __name__ == "__main__":
    main()
```

---

## 6. Implementation Phases

> **🏡 CABIN-FIRST PRIORITY**: Phases reordered to support building the woodsy cabin as quickly as possible!

### Phase 1: Foundation - Basic Commands (Day 1-2)

**Goal**: Get `/setblock` and `/fill` working with absolute coordinates (no block states yet)

**Cabin commands unlocked**:
- ✅ `/fill 0 64 0 9 64 7 cobblestone` (foundation)
- ✅ `/fill 1 65 1 8 65 6 spruce_planks` (floor)
- ✅ `/setblock 2 67 0 glass_pane` (basic windows)

**Tasks**:
1. Set up project structure with uv
   - `uv init`
   - Add dependencies: amulet-core, lark, click
   - Configure mypy, ruff

2. Implement minimal parser
   - Grammar for: `/setblock <x> <y> <z> <namespace:id>`
   - Grammar for: `/fill <x1> <y1> <z1> <x2> <y2> <z2> <namespace:id>`
   - No block states, no NBT, no relative coords yet
   - Just integers and block IDs

3. Basic WorldModifier
   - Open world with amulet
   - Set single block
   - Fill region (simple mode only)
   - Save world

4. CLI with `execute` command

5. Basic tests
   - Parser tests for setblock and fill
   - Integration test with test world

**Deliverables**:
- Can run: `mccommand execute ./world "/setblock 0 64 0 minecraft:stone"`
- Can run: `mccommand execute ./world "/fill 0 0 0 10 10 10 minecraft:stone"`
- Tests pass
- Type checking clean

**Why this matters**: Gets the basic engine running so we can place blocks!

---

### Phase 2: Block States - Make It Pretty (Day 3-4)

**Goal**: Support block states like `[facing=north,half=top]` for stairs, doors, slabs

**Cabin commands unlocked**:
- ✅ `/setblock 4 66 0 spruce_door[half=lower,hinge=left]` (front door!)
- ✅ `/fill -1 70 -1 -1 70 8 spruce_stairs[facing=east]` (roof!)
- ✅ `/fill 2 72 -1 7 72 8 spruce_slab[type=top]` (roof peak!)

**Tasks**:
1. Extend grammar for block states: `block_id[key=value,key2=value2]`
2. Add block state parsing to transformer
3. Basic BlockRegistry (can start with hardcoded common blocks)
4. Convert block states to Amulet properties
5. Tests for doors, stairs, slabs

**Deliverables**:
- Can use: `/setblock 0 64 0 minecraft:oak_stairs[facing=north,half=top]`
- Can use: `/setblock 0 64 0 minecraft:spruce_door[half=lower,hinge=left]`
- Stairs face the right direction
- Doors work properly

**Why this matters**: This unlocks the ENTIRE cabin build including the peaked roof!

---

### Phase 3: Hollow Mode - Smart Building (Day 5)

**Goal**: Implement `hollow` fill mode for efficient wall building

**Cabin commands unlocked**:
- ✅ `/fill 0 65 0 9 69 7 spruce_planks hollow` (walls in one command!)

**Tasks**:
1. Extend fill grammar to support mode parameter
2. Implement `_fill_hollow()` method
3. Optimize boundary detection
4. Tests for hollow mode

**Deliverables**:
- Can use: `/fill 0 0 0 15 15 15 minecraft:glass hollow`
- Interior is automatically air, only outer shell is filled
- Performance: hollow fill of 10x10x10 in <1 second

**Why this matters**: This single feature saves dozens of commands for building walls!

---

### 🎉 CABIN MILESTONE: At this point, you can build the complete woodsy cabin!

---

### Phase 4: Relative Coordinates (Day 6-7)

**Goal**: Support `~` relative coordinates for flexible positioning

**New capabilities**:
- ✅ `/setblock ~5 ~-1 ~5 minecraft:stone` (build relative to player)
- ✅ Reusable command templates

**Tasks**:
1. Extend grammar for `~` notation
2. Add `Coordinate.relative` flag
3. Implement `resolve()` methods
4. Add `--origin` CLI option
5. Tests for relative coordinate resolution

**Deliverables**:
- Can use: `/setblock ~5 ~-1 ~5 minecraft:stone`
- Origin configurable via CLI: `--origin 100,64,200`
- Mixed absolute and relative: `/fill ~-5 64 ~-5 ~5 70 ~5 minecraft:stone`

**Why this matters**: Makes commands portable - build anywhere without editing coordinates!

---

### Phase 5: Advanced Fill Modes (Day 8)

**Goal**: Outline, keep, replace modes for advanced building

**New capabilities**:
- ✅ `/fill 0 0 0 20 20 20 minecraft:air replace minecraft:dirt` (clear specific blocks)
- ✅ `/fill 0 0 0 10 10 10 minecraft:stone outline` (frame structures)
- ✅ `/fill 0 0 0 10 10 10 minecraft:grass_block keep` (don't overwrite existing)

**Tasks**:
1. Implement `_fill_outline()` method
2. Implement `_fill_replace()` with filter support
3. Implement `keep` mode
4. Tests for each mode

**Deliverables**:
- All fill modes working: destroy, hollow, keep, outline, replace
- Replace with filter: `/fill ... replace minecraft:dirt`
- Proper mode validation

**Why this matters**: Professional building tools for terrain editing and modifications!

---

### Phase 6: Advanced Block Registry (Day 9-10)

**Goal**: Full block validation with comprehensive block data

**New capabilities**:
- ✅ Validate all block IDs and states
- ✅ Helpful error messages with suggestions
- ✅ Support for 1.20.1 blocks

**Tasks**:
1. Extract/download PrismarineJS block data for 1.20.1
2. Full BlockRegistry implementation with validation
3. Fuzzy matching for typos ("Did you mean minecraft:oak_stairs?")
4. Validate state values against allowed values
5. Tests for validation

**Deliverables**:
- Validates all blocks: `minecraft:nonexistent` → error with suggestion
- Validates states: `[facing=invalid]` → "Valid values: north, south, east, west"
- Supports all 1.20.1 blocks

**Why this matters**: Catches errors before modifying worlds, prevents data corruption!

---

### Phase 7: NBT & Tile Entities (Day 11-12)

**Goal**: Support chests, signs, and other tile entities with data

**New capabilities**:
- ✅ `/setblock 0 64 0 minecraft:chest{Items:[{Slot:0b,id:"minecraft:diamond",Count:64b}]}`
- ✅ Signs with text, command blocks with commands

**Tasks**:
1. Integrate NBT parser (nbtlib or custom SNBT parser)
2. Parse NBT strings in block specs
3. Tile entity detection and creation
4. WorldModifier support for placing tile entities
5. Tests with chests, signs, command blocks

**Deliverables**:
- Can create chests with items
- Can create signs with text
- Can create command blocks with commands

**Why this matters**: Furnish interiors, add interactive elements!

---

### Phase 8: Polish & Documentation (Day 13-14)

**Goal**: Production-ready with great UX

**Tasks**:
1. Comprehensive error messages
2. CLI help text and examples
3. README with installation and usage
4. Cabin build tutorial in docs
5. Performance benchmarks
6. CI/CD setup (GitHub Actions)
7. `--dry-run` mode to preview changes
8. Progress bars for large fills

**Deliverables**:
- Professional README
- Tutorial: "Build your first cabin"
- GitHub Actions running tests
- Performance: >10k blocks/second

**Why this matters**: Makes the tool accessible and reliable for everyone!

---

## Updated Timeline (Cabin-First)

- **Days 1-2**: Phase 1 - Basic commands
- **Days 3-4**: Phase 2 - Block states
- **Day 5**: Phase 3 - Hollow mode
- **🎉 CABIN COMPLETE** (can build full cabin after day 5!)
- **Days 6-7**: Phase 4 - Relative coordinates
- **Day 8**: Phase 5 - Advanced fill modes
- **Days 9-10**: Phase 6 - Block validation
- **Days 11-12**: Phase 7 - NBT support
- **Days 13-14**: Phase 8 - Polish

**Total: ~2 weeks for full implementation, cabin buildable in 5 days!**

---

## 7. Testing Strategy

### Unit Tests

**Parser Tests** (`tests/parser/test_parser.py`):
```python
def test_parse_basic_setblock():
    parser = CommandParser()
    result = parser.parse("/setblock 10 64 10 minecraft:stone")
    assert isinstance(result, SetblockCommand)
    assert result.position.x.value == 10
    assert result.block.block_id == "stone"

def test_parse_relative_coords():
    result = parser.parse("/setblock ~5 ~-1 ~5 minecraft:stone")
    assert result.position.x.relative == True
    assert result.position.x.value == 5

def test_parse_block_states():
    result = parser.parse("/setblock 0 0 0 minecraft:oak_stairs[facing=north,half=top]")
    assert result.block.states["facing"] == "north"

def test_parse_error():
    with pytest.raises(CommandSyntaxError):
        parser.parse("/setblock invalid")
```

**Block Registry Tests** (`tests/blocks/test_registry.py`):
```python
def test_valid_block():
    registry = BlockRegistry()
    assert registry.is_valid_block("minecraft", "stone")
    assert not registry.is_valid_block("minecraft", "nonexistent")

def test_validate_states():
    errors = registry.validate_block_spec(
        BlockSpec("minecraft", "oak_stairs", {"facing": "north"}, None)
    )
    assert len(errors) == 0

    errors = registry.validate_block_spec(
        BlockSpec("minecraft", "oak_stairs", {"facing": "invalid"}, None)
    )
    assert len(errors) > 0
```

### Integration Tests

**World Modification Tests** (`tests/world/test_integration.py`):

Use fixtures with actual test worlds:

```python
@pytest.fixture
def test_world(tmp_path):
    """Create a minimal test world."""
    # Copy fixture world or create programmatically
    world_path = tmp_path / "test_world"
    # ... setup world ...
    return world_path

def test_setblock_integration(test_world):
    with WorldEditor(test_world) as editor:
        count = editor.execute("/setblock 0 64 0 minecraft:diamond_block")
        editor.save()

    # Verify block was placed
    with WorldModifier(test_world) as world:
        block = world.world.get_block(0, 64, 0, "minecraft:overworld")
        assert block.namespaced_name == "minecraft:diamond_block"

def test_fill_integration(test_world):
    with WorldEditor(test_world) as editor:
        count = editor.execute("/fill 0 64 0 5 64 5 minecraft:stone")
        assert count == 36  # 6x1x6
        editor.save()
```

### Test Fixtures

**Test World**:
- Minimal world with a few chunks
- Pre-generated spawn area
- Stored in `tests/fixtures/test_world/`

**Test Commands** (`tests/fixtures/commands.txt`):
```
# Basic setblock
/setblock 0 64 0 minecraft:stone
/setblock 10 64 10 minecraft:diamond_block

# With states
/setblock 0 64 5 minecraft:oak_stairs[facing=north,half=top]

# Relative
/setblock ~5 ~0 ~5 minecraft:glass

# Fill
/fill 0 64 0 10 64 10 minecraft:stone
/fill 20 64 20 30 70 30 minecraft:glass hollow
```

### Performance Tests

**Benchmark Script** (`scripts/benchmark.py`):
```python
import time
from mccommand.api import WorldEditor

def benchmark_fill():
    with WorldEditor("test_world") as editor:
        start = time.time()
        editor.execute("/fill 0 0 0 100 100 100 minecraft:stone")
        duration = time.time() - start

        blocks = 101 * 101 * 101  # 1,030,301 blocks
        rate = blocks / duration
        print(f"Filled {blocks:,} blocks in {duration:.2f}s ({rate:.0f} blocks/sec)")

# Target: >100k blocks/second
```

### CI/CD

**GitHub Actions** (`.github/workflows/test.yml`):
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --dev

      - name: Type checking
        run: uv run mypy mccommand

      - name: Linting
        run: uv run ruff check mccommand

      - name: Tests
        run: uv run pytest --cov=mccommand

      - name: Coverage
        run: uv run coverage report --fail-under=80
```

---

## 8. Future Considerations

### Additional Commands

Architecture supports adding more commands easily:

- `/clone` - Copy regions
- `/summon` - Spawn entities
- `/execute` - Command execution context
- `/data` - Modify NBT data

**Pattern**:
1. Add grammar rules for new command
2. Add new AST dataclass
3. Add execution method to WorldModifier
4. Tests

### Web Interface Integration

**Architecture supports web via FastAPI**:

```python
# future: mccommand/web/api.py
from fastapi import FastAPI, UploadFile
from mccommand.api import WorldEditor

app = FastAPI()

@app.post("/execute")
async def execute_command(world_id: str, command: str):
    # World uploaded previously, stored server-side
    world_path = get_world_path(world_id)
    with WorldEditor(world_path) as editor:
        count = editor.execute(command)
        editor.save()
    return {"blocks_modified": count}

@app.post("/upload-world")
async def upload_world(file: UploadFile):
    # Save uploaded world, return ID
    pass

@app.get("/download-world/{world_id}")
async def download_world(world_id: str):
    # Return modified world as zip
    pass
```

**Web UI ideas**:
- Monaco editor for command editing
- 3D preview using Three.js
- Command history and undo
- Template library (common patterns)

### Multi-World Editing

Support editing multiple worlds or dimensions:

```python
class MultiWorldEditor:
    def __init__(self):
        self.worlds = {}

    def load_world(self, name: str, path: str):
        self.worlds[name] = WorldEditor(path)

    def execute(self, world_name: str, command: str):
        return self.worlds[world_name].execute(command)
```

### Performance Optimizations

**For very large fills (millions of blocks)**:

1. **Parallelization**: Process chunks in parallel
2. **Delta encoding**: Only save modified chunks
3. **Memory mapping**: Stream chunks instead of loading all
4. **GPU acceleration**: Use compute shaders for large regions

```python
# future: mccommand/world/parallel.py
from multiprocessing import Pool

def fill_parallel(region, block, num_workers=4):
    chunks = split_into_chunks(region)
    with Pool(num_workers) as pool:
        results = pool.map(fill_chunk, [(chunk, block) for chunk in chunks])
    return sum(results)
```

### Version Compatibility

Support multiple Minecraft versions:

```python
class WorldModifier:
    def __init__(self, world_path: str, target_version: str | None = None):
        self.world = amulet.load_level(world_path)
        self.version = target_version or self._detect_version()
        self.registry = BlockRegistry(self.version)
```

Block data files for each version:
- `blocks/data/1.19.4/blocks.json`
- `blocks/data/1.20.1/blocks.json`
- `blocks/data/1.21.0/blocks.json`

### Plugin System

Allow custom commands:

```python
# future: mccommand/plugins/base.py
class CommandPlugin:
    command_name: str

    def parse(self, args: str) -> CommandAST:
        pass

    def execute(self, ast: CommandAST, world: WorldModifier) -> int:
        pass

# Register plugins
register_plugin(PyramidCommand())  # Custom /pyramid command
```

### Command Macros

Support variables and loops:

```
# macro.mcc
@var base_y = 64
@var size = 10

@for x in range(-size, size):
    @for z in range(-size, size):
        /setblock {x} {base_y} {z} minecraft:stone
```

### Undo/Redo

Store operation history:

```python
class UndoableWorldEditor(WorldEditor):
    def __init__(self, world_path):
        super().__init__(world_path)
        self.history = []

    def execute(self, command: str) -> int:
        # Store pre-state
        snapshot = self._snapshot_affected_region(command)
        count = super().execute(command)
        self.history.append((command, snapshot))
        return count

    def undo(self):
        command, snapshot = self.history.pop()
        self._restore_snapshot(snapshot)
```

---

## Dependencies Summary

### Core Dependencies
- **amulet-core** (>=1.9.0) - World file I/O
- **amulet-nbt** (>=2.0.0) - NBT parsing
- **lark** (>=1.1.0) - Parser generator
- **click** (>=8.1.0) - CLI framework

### Development Dependencies
- **pytest** (>=7.0.0) - Testing
- **pytest-cov** (>=4.0.0) - Coverage
- **mypy** (>=1.0.0) - Type checking
- **ruff** (>=0.1.0) - Linting/formatting

### Optional Dependencies (Future)
- **nbtlib** - Better NBT parsing
- **fastapi** - Web API
- **uvicorn** - ASGI server
- **numpy** - Large array operations

---

## Success Criteria

Phase 1 successful when:
- [x] Can execute basic setblock with absolute coords
- [x] Changes persist to world files
- [x] Tests pass
- [x] CLI works

Full project successful when:
- [x] Both setblock and fill fully implemented
- [x] All modes supported (hollow, outline, replace, etc.)
- [x] Block states and NBT working
- [x] Relative coordinates working
- [x] 80%+ test coverage
- [x] Type checking clean (mypy strict)
- [x] Performance: >10k blocks/sec for fill operations
- [x] Documentation complete
- [x] Ready for pip install

---

## Timeline Estimate

**Cabin-First Development:**

- **Days 1-2**: Phase 1 (basic setblock + fill)
- **Days 3-4**: Phase 2 (block states for stairs/doors)
- **Day 5**: Phase 3 (hollow mode)
- **🎉 CABIN MILESTONE** - Can build complete woodsy cabin!
- **Days 6-7**: Phase 4 (relative coordinates)
- **Day 8**: Phase 5 (advanced fill modes)
- **Days 9-10**: Phase 6 (full block validation)
- **Days 11-12**: Phase 7 (NBT & tile entities)
- **Days 13-14**: Phase 8 (polish & documentation)

**Total: ~2 weeks for full implementation, cabin buildable in 5 days!**

---

## Open Questions

1. **Block data source**: Extract from Minecraft JAR ourselves or use PrismarineJS data?
   - **Recommendation**: Use PrismarineJS minecraft-data initially (MIT license)

2. **NBT parsing**: Use existing library (nbtlib) or build custom SNBT parser?
   - **Recommendation**: Start with nbtlib, build custom if needed

3. **Version support**: Target single version (1.20.1) or multi-version from start?
   - **Recommendation**: Single version initially, add multi-version in Phase 7

4. **Backups**: Auto-backup worlds before modification?
   - **Recommendation**: Add `--backup` flag, warn users in docs

5. **Progress reporting**: For large fills, show progress bar?
   - **Recommendation**: Add progress callback, use click.progressbar for CLI

---

## Next Steps

1. **Review this plan** - Get feedback on approach
2. **Set up project** - Run `uv init`, create directory structure
3. **Start Phase 1** - Basic setblock implementation
4. **Iterate** - Test, refine, move to next phase

---

*This plan is a living document and will be updated as implementation progresses.*
