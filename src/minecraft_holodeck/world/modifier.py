"""World modification interface using amulet-core."""

from typing import Any

import amulet  # type: ignore[import-untyped]
from amulet.api.block import Block  # type: ignore[import-untyped]
from amulet.api.level import World  # type: ignore[import-untyped]

from minecraft_holodeck.constants import MINECRAFT_PLATFORM, MINECRAFT_VERSION
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
            self.platform = MINECRAFT_PLATFORM
            self.version = MINECRAFT_VERSION
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

    def _place_block(self, x: int, y: int, z: int, block: Block) -> None:
        """Internal helper to place a block at the given coordinates.

        Args:
            x, y, z: Absolute coordinates
            block: Amulet Block object to place
        """
        self.world.set_version_block(
            x, y, z,
            self.dimension,
            (self.platform, self.version),
            block
        )

    def fill_region(
        self,
        x1: int, y1: int, z1: int,
        x2: int, y2: int, z2: int,
        block: Block,
        mode: str = "replace",
    ) -> int:
        """Fill a region with blocks.

        Phase 3: Added support for fill modes (hollow, destroy, keep, outline, replace).

        Args:
            x1, y1, z1: First corner
            x2, y2, z2: Second corner
            block: Block to fill with
            mode: Fill mode (replace, hollow, destroy, keep, outline)

        Returns:
            Number of blocks modified
        """
        # Normalize coordinates (ensure x1 <= x2, etc.)
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        min_z, max_z = min(z1, z2), max(z1, z2)

        # Dispatch to appropriate fill method based on mode
        try:
            if mode == "hollow":
                return self._fill_hollow(min_x, min_y, min_z, max_x, max_y, max_z, block)
            elif mode == "outline":
                return self._fill_outline(min_x, min_y, min_z, max_x, max_y, max_z, block)
            elif mode in ("replace", "destroy"):
                # Replace and destroy are the same for now (both replace all blocks)
                return self._fill_basic(min_x, min_y, min_z, max_x, max_y, max_z, block)
            elif mode == "keep":
                return self._fill_keep(min_x, min_y, min_z, max_x, max_y, max_z, block)
            else:
                raise WorldOperationError(f"Unknown fill mode: {mode}")
        except WorldOperationError:
            raise
        except Exception as e:
            raise WorldOperationError(
                f"Failed to fill region: {e}"
            ) from e

    def _fill_basic(
        self,
        min_x: int, min_y: int, min_z: int,
        max_x: int, max_y: int, max_z: int,
        block: Block,
    ) -> int:
        """Basic fill: replace all blocks in the region.

        Args:
            min_x, min_y, min_z: Minimum corner
            max_x, max_y, max_z: Maximum corner
            block: Block to fill with

        Returns:
            Number of blocks modified
        """
        count = 0
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                for z in range(min_z, max_z + 1):
                    self._place_block(x, y, z, block)
                    count += 1
        return count

    def _fill_hollow(
        self,
        min_x: int, min_y: int, min_z: int,
        max_x: int, max_y: int, max_z: int,
        block: Block,
    ) -> int:
        """Hollow fill: fill only the outer shell, air in the interior.

        Args:
            min_x, min_y, min_z: Minimum corner
            max_x, max_y, max_z: Maximum corner
            block: Block to fill with

        Returns:
            Number of blocks modified (not including air)
        """
        count = 0
        air = Block("minecraft", "air")

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                for z in range(min_z, max_z + 1):
                    # Check if on boundary
                    is_boundary = (
                        x == min_x or x == max_x or
                        y == min_y or y == max_y or
                        z == min_z or z == max_z
                    )

                    if is_boundary:
                        # Place block on boundary
                        self._place_block(x, y, z, block)
                        count += 1
                    else:
                        # Fill interior with air
                        self._place_block(x, y, z, air)

        return count

    def _fill_keep(
        self,
        min_x: int, min_y: int, min_z: int,
        max_x: int, max_y: int, max_z: int,
        block: Block,
    ) -> int:
        """Keep fill: only fill air blocks, don't replace existing blocks.

        Args:
            min_x, min_y, min_z: Minimum corner
            max_x, max_y, max_z: Maximum corner
            block: Block to fill with

        Returns:
            Number of blocks modified
        """
        count = 0
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                for z in range(min_z, max_z + 1):
                    # Check if current block is air
                    existing = self.world.get_block(x, y, z, self.dimension)
                    if existing.namespaced_name == "minecraft:air":
                        self._place_block(x, y, z, block)
                        count += 1
        return count

    def _fill_outline(
        self,
        min_x: int, min_y: int, min_z: int,
        max_x: int, max_y: int, max_z: int,
        block: Block,
    ) -> int:
        """Outline fill: fill only the edges (12 lines of the box).

        Args:
            min_x, min_y, min_z: Minimum corner
            max_x, max_y, max_z: Maximum corner
            block: Block to fill with

        Returns:
            Number of blocks modified
        """
        count = 0

        # Fill the 12 edges of the box
        # 4 edges parallel to X-axis
        for x in range(min_x, max_x + 1):
            for y, z in [(min_y, min_z), (min_y, max_z), (max_y, min_z), (max_y, max_z)]:
                self._place_block(x, y, z, block)
                count += 1

        # 4 edges parallel to Y-axis (excluding already placed corners)
        for y in range(min_y + 1, max_y):
            for x, z in [(min_x, min_z), (min_x, max_z), (max_x, min_z), (max_x, max_z)]:
                self._place_block(x, y, z, block)
                count += 1

        # 4 edges parallel to Z-axis (excluding already placed corners)
        for z in range(min_z + 1, max_z):
            for x, y in [(min_x, min_y), (min_x, max_y), (max_x, min_y), (max_x, max_y)]:
                self._place_block(x, y, z, block)
                count += 1

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
