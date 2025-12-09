"""AST data structures for Minecraft commands."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Coordinate:
    """Single coordinate (x, y, or z).

    Phase 5: Supports both absolute and relative coordinates.
    - Absolute: value directly represents the coordinate (relative=False)
    - Relative: value is offset from origin (relative=True)
    """
    value: int
    relative: bool = False

    def resolve(self, origin: int) -> int:
        """Resolve to absolute coordinate.

        Args:
            origin: The origin coordinate (used if relative=True)

        Returns:
            Absolute coordinate value
        """
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

    Phase 2: Added block states support.
    """
    namespace: str  # "minecraft"
    block_id: str   # "stone"
    states: dict[str, str | int | bool] | None = None  # {"facing": "north", "half": "top"}

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

    Phase 3: Added support for fill modes (hollow, destroy, keep, outline, replace).
    """
    pos1: Position
    pos2: Position
    block: BlockSpec
    mode: Literal["replace", "destroy", "hollow", "keep", "outline"] = "replace"


CommandAST = SetblockCommand | FillCommand
