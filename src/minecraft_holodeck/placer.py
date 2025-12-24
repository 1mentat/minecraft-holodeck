"""Smart structure placement with automatic spacing calculation.

Phase 5 implementation: Intelligent structure placement with automatic spacing,
grid layouts, and anchor point support.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Literal

from minecraft_holodeck.api import WorldEditor
from minecraft_holodeck.converter import BoundingBox, ScriptConverter
from minecraft_holodeck.exceptions import MCCommandError
from minecraft_holodeck.parser import CommandParser, FillCommand, SetblockCommand

if TYPE_CHECKING:
    from minecraft_holodeck.parser.ast import Position


class PlacementError(MCCommandError):
    """Raised when structure placement fails."""
    pass


class Direction(Enum):
    """Cardinal directions for adjacent placement."""
    NORTH = "north"  # -Z
    SOUTH = "south"  # +Z
    EAST = "east"    # +X
    WEST = "west"    # -X
    UP = "up"        # +Y
    DOWN = "down"    # -Y


class Anchor(Enum):
    """Anchor points for structure placement."""
    CORNER = "corner"          # Min corner (default origin)
    CENTER = "center"          # Center of bounding box
    BASE_CENTER = "base-center"  # Center of base (Y=min_y)


@dataclass
class PlacementResult:
    """Result of a structure placement operation."""
    blocks_placed: int
    bounding_box: BoundingBox
    origin_used: tuple[int, int, int]


@dataclass
class SliceInfo:
    """Information about a horizontal slice of a structure at a given Y level."""
    y: int
    min_x: int
    max_x: int
    min_z: int
    max_z: int
    block_count: int

    @property
    def width(self) -> int:
        """Width in X dimension at this Y level."""
        return self.max_x - self.min_x + 1

    @property
    def depth(self) -> int:
        """Depth in Z dimension at this Y level."""
        return self.max_z - self.min_z + 1


@dataclass
class Footprint:
    """Base footprint of a structure (at minimum Y level)."""
    min_x: int
    max_x: int
    min_z: int
    max_z: int
    y_level: int
    block_count: int

    @property
    def width(self) -> int:
        """Width in X dimension."""
        return self.max_x - self.min_x + 1

    @property
    def depth(self) -> int:
        """Depth in Z dimension."""
        return self.max_z - self.min_z + 1


class StructureAnalyzer:
    """Analyze structure scripts for extent information.

    Provides detailed queries about structure dimensions at specific Y levels,
    base footprint, and other spatial information needed for smart placement.

    Example:
        analyzer = StructureAnalyzer()
        bbox = analyzer.get_bounding_box("cabin.txt")
        footprint = analyzer.get_base_footprint("cabin.txt")
        width = analyzer.get_width_at_y("cabin.txt", y=64)
    """

    def __init__(self) -> None:
        self.parser = CommandParser()
        self._converter = ScriptConverter()

    def get_bounding_box(self, script_path: Path | str) -> BoundingBox:
        """Get the bounding box of a structure script.

        Args:
            script_path: Path to the script file

        Returns:
            BoundingBox with structure extents
        """
        return self._converter.analyze_script(script_path)

    def get_base_footprint(self, script_path: Path | str) -> Footprint:
        """Get the base footprint of a structure (blocks at minimum Y).

        Args:
            script_path: Path to the script file

        Returns:
            Footprint information for the base layer
        """
        script_path = Path(script_path)
        commands = list(self._parse_commands(script_path))

        if not commands:
            return Footprint(0, 0, 0, 0, 0, 0)

        # Find minimum Y level
        min_y = float("inf")
        for cmd in commands:
            for pos in self._extract_positions(cmd):
                if not pos.y.relative:
                    min_y = min(min_y, pos.y.value)

        if min_y == float("inf"):
            return Footprint(0, 0, 0, 0, 0, 0)

        min_y = int(min_y)

        # Find extent at that Y level
        return self._get_footprint_at_y(commands, min_y)

    def get_slice_at_y(self, script_path: Path | str, y: int) -> SliceInfo:
        """Get structure extent at a specific Y level.

        Args:
            script_path: Path to the script file
            y: Y coordinate to analyze

        Returns:
            SliceInfo with extent at that Y level
        """
        script_path = Path(script_path)
        commands = list(self._parse_commands(script_path))

        min_x = float("inf")
        max_x = float("-inf")
        min_z = float("inf")
        max_z = float("-inf")
        block_count = 0

        for cmd in commands:
            positions = list(self._extract_positions(cmd))

            if isinstance(cmd, SetblockCommand):
                pos = cmd.position
                if not pos.y.relative and pos.y.value == y:
                    if not pos.x.relative:
                        min_x = min(min_x, pos.x.value)
                        max_x = max(max_x, pos.x.value)
                    if not pos.z.relative:
                        min_z = min(min_z, pos.z.value)
                        max_z = max(max_z, pos.z.value)
                    block_count += 1

            elif isinstance(cmd, FillCommand):
                # Check if fill region intersects with Y level
                y1 = cmd.pos1.y.value if not cmd.pos1.y.relative else None
                y2 = cmd.pos2.y.value if not cmd.pos2.y.relative else None

                if y1 is not None and y2 is not None:
                    y_min_fill, y_max_fill = min(y1, y2), max(y1, y2)
                    if y_min_fill <= y <= y_max_fill:
                        # Fill includes this Y level
                        if not cmd.pos1.x.relative and not cmd.pos2.x.relative:
                            min_x = min(min_x, cmd.pos1.x.value, cmd.pos2.x.value)
                            max_x = max(max_x, cmd.pos1.x.value, cmd.pos2.x.value)
                        if not cmd.pos1.z.relative and not cmd.pos2.z.relative:
                            min_z = min(min_z, cmd.pos1.z.value, cmd.pos2.z.value)
                            max_z = max(max_z, cmd.pos1.z.value, cmd.pos2.z.value)

                        # Estimate block count at this Y level
                        x_range = abs(cmd.pos2.x.value - cmd.pos1.x.value) + 1
                        z_range = abs(cmd.pos2.z.value - cmd.pos1.z.value) + 1
                        block_count += x_range * z_range

        if min_x == float("inf"):
            return SliceInfo(y, 0, 0, 0, 0, 0)

        return SliceInfo(
            y=y,
            min_x=int(min_x),
            max_x=int(max_x),
            min_z=int(min_z),
            max_z=int(max_z),
            block_count=block_count,
        )

    def get_width_at_y(self, script_path: Path | str, y: int) -> int:
        """Get structure width (X extent) at a specific Y level.

        Args:
            script_path: Path to the script file
            y: Y coordinate to analyze

        Returns:
            Width in blocks at that Y level
        """
        slice_info = self.get_slice_at_y(script_path, y)
        return slice_info.width

    def get_depth_at_y(self, script_path: Path | str, y: int) -> int:
        """Get structure depth (Z extent) at a specific Y level.

        Args:
            script_path: Path to the script file
            y: Y coordinate to analyze

        Returns:
            Depth in blocks at that Y level
        """
        slice_info = self.get_slice_at_y(script_path, y)
        return slice_info.depth

    def get_height(self, script_path: Path | str) -> int:
        """Get total structure height.

        Args:
            script_path: Path to the script file

        Returns:
            Height in blocks
        """
        bbox = self.get_bounding_box(script_path)
        return bbox.height

    def _parse_commands(
        self, script_path: Path
    ) -> Iterator[SetblockCommand | FillCommand]:
        """Parse all commands from a script file.

        Args:
            script_path: Path to the script file

        Yields:
            Parsed command ASTs
        """
        with open(script_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    yield self.parser.parse(line)
                except Exception:
                    continue

    def _extract_positions(
        self, cmd: SetblockCommand | FillCommand
    ) -> Iterator["Position"]:
        """Extract positions from a command."""
        from minecraft_holodeck.parser.ast import Position

        if isinstance(cmd, SetblockCommand):
            yield cmd.position
        elif isinstance(cmd, FillCommand):
            yield cmd.pos1
            yield cmd.pos2

    def _get_footprint_at_y(
        self, commands: list[SetblockCommand | FillCommand], y: int
    ) -> Footprint:
        """Get footprint at a specific Y level."""
        min_x = float("inf")
        max_x = float("-inf")
        min_z = float("inf")
        max_z = float("-inf")
        block_count = 0

        for cmd in commands:
            if isinstance(cmd, SetblockCommand):
                pos = cmd.position
                if not pos.y.relative and pos.y.value == y:
                    if not pos.x.relative:
                        min_x = min(min_x, pos.x.value)
                        max_x = max(max_x, pos.x.value)
                    if not pos.z.relative:
                        min_z = min(min_z, pos.z.value)
                        max_z = max(max_z, pos.z.value)
                    block_count += 1

            elif isinstance(cmd, FillCommand):
                y1 = cmd.pos1.y.value if not cmd.pos1.y.relative else None
                y2 = cmd.pos2.y.value if not cmd.pos2.y.relative else None

                if y1 is not None and y2 is not None:
                    y_min_fill, y_max_fill = min(y1, y2), max(y1, y2)
                    if y_min_fill <= y <= y_max_fill:
                        if not cmd.pos1.x.relative and not cmd.pos2.x.relative:
                            min_x = min(min_x, cmd.pos1.x.value, cmd.pos2.x.value)
                            max_x = max(max_x, cmd.pos1.x.value, cmd.pos2.x.value)
                        if not cmd.pos1.z.relative and not cmd.pos2.z.relative:
                            min_z = min(min_z, cmd.pos1.z.value, cmd.pos2.z.value)
                            max_z = max(max_z, cmd.pos1.z.value, cmd.pos2.z.value)

                        x_range = abs(cmd.pos2.x.value - cmd.pos1.x.value) + 1
                        z_range = abs(cmd.pos2.z.value - cmd.pos1.z.value) + 1
                        block_count += x_range * z_range

        if min_x == float("inf"):
            return Footprint(0, 0, 0, 0, y, 0)

        return Footprint(
            min_x=int(min_x),
            max_x=int(max_x),
            min_z=int(min_z),
            max_z=int(max_z),
            y_level=y,
            block_count=block_count,
        )


class StructurePlacer:
    """Intelligent structure placement with automatic spacing calculation.

    Enables placing structures with proper spacing based on their actual
    dimensions, rather than origin-to-origin placement.

    Example:
        with StructurePlacer("/path/to/world") as placer:
            # Place first cabin
            placer.place_at("cabin.txt", position=(0, 64, 0))

            # Place second cabin 10 blocks east (base-to-base)
            placer.place_adjacent("cabin.txt",
                                  relative_to=(0, 64, 0),
                                  direction="east",
                                  gap=10)

            # Place cabins in a 3x3 grid
            placer.place_grid("cabin.txt",
                             start=(100, 64, 100),
                             grid_size=(3, 3),
                             spacing=(5, 5))
    """

    def __init__(self, world_path: str | Path) -> None:
        """Initialize structure placer.

        Args:
            world_path: Path to Minecraft world folder
        """
        self.world_path = Path(world_path)
        self.analyzer = StructureAnalyzer()
        self._editor: WorldEditor | None = None

    @property
    def editor(self) -> WorldEditor:
        """Get or create world editor."""
        if self._editor is None:
            self._editor = WorldEditor(self.world_path)
        return self._editor

    def place_at(
        self,
        script_path: Path | str,
        position: tuple[int, int, int],
        anchor: Anchor | str = Anchor.CORNER,
    ) -> PlacementResult:
        """Place a structure at a specific position with anchor point.

        Args:
            script_path: Path to the script file
            position: Target position (x, y, z)
            anchor: Anchor point for placement
                - CORNER: Position is the min corner (default)
                - CENTER: Position is the center of the bounding box
                - BASE_CENTER: Position is the center of the base

        Returns:
            PlacementResult with placement details
        """
        script_path = Path(script_path)
        bbox = self.analyzer.get_bounding_box(script_path)

        # Convert string anchor to enum
        if isinstance(anchor, str):
            anchor = Anchor(anchor.lower())

        # Calculate origin based on anchor
        origin = self._calculate_origin_from_anchor(position, bbox, anchor)

        # Execute script at calculated origin
        blocks_placed = self._execute_script(script_path, origin)

        return PlacementResult(
            blocks_placed=blocks_placed,
            bounding_box=bbox,
            origin_used=origin,
        )

    def place_adjacent(
        self,
        script_path: Path | str,
        relative_to: tuple[int, int, int],
        direction: Direction | str,
        gap: int = 0,
        reference_script: Path | str | None = None,
    ) -> PlacementResult:
        """Place a structure adjacent to a reference position.

        Calculates placement based on actual structure dimensions for
        proper base-to-base spacing.

        Args:
            script_path: Path to the script file to place
            relative_to: Reference position (typically origin of existing structure)
            direction: Direction to place (north, south, east, west, up, down)
            gap: Gap in blocks between structures (base-to-base)
            reference_script: Script of reference structure (for calculating offset)
                             If None, offset starts from relative_to position

        Returns:
            PlacementResult with placement details
        """
        script_path = Path(script_path)
        bbox = self.analyzer.get_bounding_box(script_path)

        # Convert string direction to enum
        if isinstance(direction, str):
            direction = Direction(direction.lower())

        # Get reference structure dimensions if provided
        if reference_script is not None:
            ref_bbox = self.analyzer.get_bounding_box(reference_script)
        else:
            # Create a zero-size reference (point placement)
            ref_bbox = BoundingBox(0, 0, 0, 0, 0, 0)

        # Calculate origin based on direction
        origin = self._calculate_adjacent_origin(
            relative_to, bbox, ref_bbox, direction, gap
        )

        # Execute script at calculated origin
        blocks_placed = self._execute_script(script_path, origin)

        return PlacementResult(
            blocks_placed=blocks_placed,
            bounding_box=bbox,
            origin_used=origin,
        )

    def place_grid(
        self,
        script_path: Path | str,
        start: tuple[int, int, int],
        grid_size: tuple[int, int],
        spacing: tuple[int, int],
        anchor: Anchor | str = Anchor.CORNER,
    ) -> list[PlacementResult]:
        """Place structures in a grid pattern.

        Args:
            script_path: Path to the script file
            start: Starting position (x, y, z) for first structure
            grid_size: Grid dimensions as (columns, rows) in (X, Z)
            spacing: Gap between structures as (x_spacing, z_spacing)
            anchor: Anchor point for the start position

        Returns:
            List of PlacementResult for each placed structure
        """
        script_path = Path(script_path)
        bbox = self.analyzer.get_bounding_box(script_path)

        # Convert string anchor to enum
        if isinstance(anchor, str):
            anchor = Anchor(anchor.lower())

        cols, rows = grid_size
        x_spacing, z_spacing = spacing

        results = []

        for row in range(rows):
            for col in range(cols):
                # Calculate position for this grid cell
                # Structure width + spacing for each column
                x_offset = col * (bbox.width + x_spacing)
                z_offset = row * (bbox.depth + z_spacing)

                position = (
                    start[0] + x_offset,
                    start[1],
                    start[2] + z_offset,
                )

                result = self.place_at(script_path, position, anchor)
                results.append(result)

        return results

    def save(self) -> None:
        """Save changes to world."""
        if self._editor is not None:
            self._editor.save()

    def close(self) -> None:
        """Close the world editor."""
        if self._editor is not None:
            self._editor.modifier.close()
            self._editor = None

    def __enter__(self) -> "StructurePlacer":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit - save and close."""
        self.save()
        self.close()

    def _calculate_origin_from_anchor(
        self,
        position: tuple[int, int, int],
        bbox: BoundingBox,
        anchor: Anchor,
    ) -> tuple[int, int, int]:
        """Calculate origin point from position and anchor.

        Args:
            position: Target position
            bbox: Structure bounding box
            anchor: Anchor point type

        Returns:
            Origin point to use for script execution
        """
        x, y, z = position

        if anchor == Anchor.CORNER:
            # Position is the origin (min corner)
            return (x, y, z)

        elif anchor == Anchor.CENTER:
            # Position is center, calculate origin
            # Origin = position - (size / 2)
            return (
                x - bbox.width // 2,
                y - bbox.height // 2,
                z - bbox.depth // 2,
            )

        elif anchor == Anchor.BASE_CENTER:
            # Position is center of base, origin.y = position.y
            return (
                x - bbox.width // 2,
                y,  # Y stays at base level
                z - bbox.depth // 2,
            )

        raise PlacementError(f"Unknown anchor type: {anchor}")

    def _calculate_adjacent_origin(
        self,
        relative_to: tuple[int, int, int],
        bbox: BoundingBox,
        ref_bbox: BoundingBox,
        direction: Direction,
        gap: int,
    ) -> tuple[int, int, int]:
        """Calculate origin for adjacent placement.

        Args:
            relative_to: Reference position (origin of existing structure)
            bbox: Bounding box of structure being placed
            ref_bbox: Bounding box of reference structure
            direction: Direction to place
            gap: Gap between structures

        Returns:
            Origin point for the new structure
        """
        x, y, z = relative_to

        if direction == Direction.EAST:  # +X
            # New structure starts after reference width + gap
            new_x = x + ref_bbox.width + gap
            return (new_x, y, z)

        elif direction == Direction.WEST:  # -X
            # New structure ends before reference, so start is further back
            new_x = x - bbox.width - gap
            return (new_x, y, z)

        elif direction == Direction.SOUTH:  # +Z
            new_z = z + ref_bbox.depth + gap
            return (x, y, new_z)

        elif direction == Direction.NORTH:  # -Z
            new_z = z - bbox.depth - gap
            return (x, y, new_z)

        elif direction == Direction.UP:  # +Y
            new_y = y + ref_bbox.height + gap
            return (x, new_y, z)

        elif direction == Direction.DOWN:  # -Y
            new_y = y - bbox.height - gap
            return (x, new_y, z)

        raise PlacementError(f"Unknown direction: {direction}")

    def _execute_script(
        self, script_path: Path, origin: tuple[int, int, int]
    ) -> int:
        """Execute a script file at the given origin.

        Args:
            script_path: Path to script file
            origin: Origin point for relative coordinates

        Returns:
            Number of blocks placed
        """
        # Update editor origin for relative coordinate resolution
        self.editor.origin = origin

        blocks_placed = 0
        with open(script_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    blocks_placed += self.editor.execute(line)
                except Exception:
                    # Skip unparseable commands
                    continue

        return blocks_placed
