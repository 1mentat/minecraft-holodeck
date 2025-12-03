"""World modification interface using amulet-core."""

from typing import Any

import amulet  # type: ignore[import-untyped]
from amulet.api.block import Block  # type: ignore[import-untyped]
from amulet.api.level import World  # type: ignore[import-untyped]
from amulet.api.selection import SelectionBox  # type: ignore[import-untyped]

from minecraft_holodeck.exceptions import WorldOperationError


class WorldModifier:
    """Interface to modify Minecraft worlds.

    Phase 1: Basic setblock and fill operations.
    """

    def __init__(self, world_path: str):
        """Open a Minecraft world.

        Args:
            world_path: Path to world folder (containing level.dat)
        """
        try:
            self.world: World = amulet.load_level(world_path)
            self.dimension = "minecraft:overworld"  # Default dimension
            self.platform = "java"  # Java Edition
            self.version = (1, 20, 1)  # Target version
        except Exception as e:
            raise WorldOperationError(f"Failed to load world: {e}") from e

    def set_block(
        self,
        x: int,
        y: int,
        z: int,
        block: Block,
    ) -> None:
        """Set a single block.

        Phase 1: Always replaces existing block (no mode parameter yet).

        Args:
            x, y, z: Absolute coordinates
            block: Amulet Block object
        """
        try:
            self.world.set_version_block(
                x, y, z,
                self.dimension,
                (self.platform, self.version),
                block
            )
        except Exception as e:
            raise WorldOperationError(
                f"Failed to set block at ({x}, {y}, {z}): {e}"
            ) from e

    def fill_region(
        self,
        x1: int, y1: int, z1: int,
        x2: int, y2: int, z2: int,
        block: Block,
    ) -> int:
        """Fill a region with blocks.

        Phase 1: Simple fill, always replaces (no modes yet).

        Args:
            x1, y1, z1: First corner
            x2, y2, z2: Second corner
            block: Block to fill with

        Returns:
            Number of blocks modified
        """
        # Normalize coordinates (ensure x1 <= x2, etc.)
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        min_z, max_z = min(z1, z2), max(z1, z2)

        count = 0
        try:
            # Iterate through all positions in the region
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    for z in range(min_z, max_z + 1):
                        self.world.set_version_block(
                            x, y, z,
                            self.dimension,
                            (self.platform, self.version),
                            block
                        )
                        count += 1
        except Exception as e:
            raise WorldOperationError(
                f"Failed to fill region: {e}"
            ) from e

        return count

    def save(self) -> None:
        """Save all changes to world files."""
        try:
            self.world.save()
        except Exception as e:
            raise WorldOperationError(f"Failed to save world: {e}") from e

    def close(self) -> None:
        """Close the world."""
        try:
            self.world.close()
        except Exception as e:
            raise WorldOperationError(f"Failed to close world: {e}") from e

    def __enter__(self) -> "WorldModifier":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
