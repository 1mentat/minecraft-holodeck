"""AST data structures for Minecraft commands."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Coordinate:
    """Single coordinate (x, y, or z).

    Phase 1: Only absolute coordinates (no relative yet).
    """
    value: int
    relative: bool = False  # Always False in Phase 1

    def resolve(self, origin: int) -> int:
        """Resolve to absolute coordinate."""
        return origin + self.value if self.relative else self.value


@dataclass
class Position:
    """3D position."""
    x: Coordinate
    y: Coordinate
    z: Coordinate

    def resolve(self, origin: tuple[int, int, int]) -> tuple[int, int, int]:
        """Resolve to absolute coordinates."""
        return (
            self.x.resolve(origin[0]),
            self.y.resolve(origin[1]),
            self.z.resolve(origin[2]),
        )


@dataclass
class BlockSpec:
    """Block specification.

    Phase 1: Only namespace and block_id (no states or NBT yet).
    """
    namespace: str  # "minecraft"
    block_id: str   # "stone"

    @property
    def full_id(self) -> str:
        """Get full namespaced ID."""
        return f"{self.namespace}:{self.block_id}"


@dataclass
class SetblockCommand:
    """Parsed /setblock command.

    Phase 1: No mode parameter yet (always replace).
    """
    position: Position
    block: BlockSpec
    mode: Literal["replace"] = "replace"


@dataclass
class FillCommand:
    """Parsed /fill command.

    Phase 1: No mode parameter yet (always replace).
    """
    pos1: Position
    pos2: Position
    block: BlockSpec
    mode: Literal["replace"] = "replace"


CommandAST = SetblockCommand | FillCommand
