# Minecraft Command Implementation Plan

## Project: minecraft-holodeck

A Python library for modifying Minecraft Java Edition world files through `/setblock` and `/fill` command interpretation.

---

## Architecture Overview

### Core Design Principles

- **Separation of Concerns**: Parser, validator, world modifier, and CLI are independent modules
- **Pipeline Architecture**: Command string → AST → Validated command → World modifications
- **Type Safety**: Full type hints with mypy strict mode
- **Testability**: Each layer independently testable

### Module Structure

```
┌─────────────────┐
│   CLI / API     │  Entry points (CLI tool, Python API)
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

---

## Implemented Features

### Core Commands
- ✅ `/setblock` with absolute and relative coordinates
- ✅ `/fill` with all modes (destroy, hollow, keep, outline, replace)
- ✅ Block states: `[facing=north,half=top]`
- ✅ Relative coordinates: `~5 ~-1 ~5`

### Tools
- ✅ CLI with `execute`, `batch`, `parse`, `analyze` commands
- ✅ World creation: `create-flat`, `create-void`
- ✅ Script converter for relative coordinate conversion
- ✅ Structure analysis with bounding box calculation

---

## Phase 5: Smart Placement (PLANNED)

**Goal**: Enable intelligent structure placement with automatic spacing calculation.

**Problem**: Current implementation places structures origin-to-origin. Need base-to-base placement for proper spacing.

### Planned Components

1. **StructurePlacer Class**
   ```python
   placer = StructurePlacer()
   placer.place_adjacent(world, "cabin.txt",
                         relative_to=(0, 64, 0),
                         direction="east",
                         gap=10)  # Accounts for structure width
   ```

2. **Grid Placement**
   ```python
   placer.place_grid(world, "cabin.txt",
                     grid_size=(3, 3),
                     spacing=(5, 5))
   ```

3. **Anchor Points**
   ```python
   placer.place_at(world, "tower.txt",
                   position=(0, 64, 0),
                   anchor="center")  # or "corner", "base-center"
   ```

4. **Extent Queries**
   ```python
   analyzer = StructureAnalyzer()
   width = analyzer.get_width_at_y(script, y=64)
   footprint = analyzer.get_base_footprint(script)
   ```

### Tasks
- ⏳ Implement StructurePlacer class
- ⏳ Add place_adjacent() method
- ⏳ Add place_grid() method
- ⏳ Support anchor points
- ⏳ Add extent query methods

---

## Future Considerations

### Additional Commands
- `/clone` - Copy regions
- `/summon` - Spawn entities
- `/execute` - Command execution context
- `/data` - Modify NBT data

### Web Interface
- FastAPI backend for world modification
- Monaco editor for command editing
- 3D preview using Three.js
- Command history and undo

### Performance Optimizations
- Parallelization for large fills
- Delta encoding for modified chunks
- Memory mapping for streaming

### Version Compatibility
- Support multiple Minecraft versions
- Block data files per version

### Plugin System
- Custom command plugins
- Command macros with variables/loops

### Undo/Redo
- Operation history with snapshots
- Rollback capability

---

## Dependencies

### Core
- **amulet-core** (>=1.9.0) - World file I/O
- **amulet-nbt** (>=2.0.0) - NBT parsing
- **lark** (>=1.1.0) - Parser generator
- **click** (>=8.1.0) - CLI framework

### Development
- **pytest** (>=7.0.0) - Testing
- **pytest-cov** (>=4.0.0) - Coverage
- **mypy** (>=1.0.0) - Type checking
- **ruff** (>=0.1.0) - Linting/formatting

---

## Success Criteria (Achieved)

- ✅ Both setblock and fill fully implemented
- ✅ All fill modes supported (hollow, outline, replace, etc.)
- ✅ Block states working
- ✅ Relative coordinates working
- ✅ 80%+ test coverage
- ✅ Type checking clean (mypy strict)
- ✅ Performance: >10k blocks/sec for fill operations
- ✅ Documentation complete
- ✅ Ready for pip install

---

*This plan is a living document. Core implementation is complete; future work focuses on smart placement helpers and additional features.*
