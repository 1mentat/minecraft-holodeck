"""Minecraft world modification through command interpretation."""

from minecraft_holodeck.api import WorldEditor, execute_command
from minecraft_holodeck.exceptions import (
    BlockValidationError,
    ChunkNotFoundError,
    CommandSyntaxError,
    MCCommandError,
    WorldOperationError,
)
from minecraft_holodeck.parser import CommandParser
from minecraft_holodeck.placer import (
    Anchor,
    Direction,
    PlacementError,
    PlacementResult,
    StructureAnalyzer,
    StructurePlacer,
)
from minecraft_holodeck.world import create_flat_world, create_void_world

__version__ = "0.1.0"
__all__ = [
    # API
    "execute_command",
    "WorldEditor",
    "CommandParser",
    # World creation
    "create_flat_world",
    "create_void_world",
    # Smart placement (Phase 5)
    "StructurePlacer",
    "StructureAnalyzer",
    "Anchor",
    "Direction",
    "PlacementResult",
    "PlacementError",
    # Exceptions
    "MCCommandError",
    "CommandSyntaxError",
    "BlockValidationError",
    "WorldOperationError",
    "ChunkNotFoundError",
]
