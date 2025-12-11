"""Convert absolute coordinate scripts to relative coordinates."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TextIO

from minecraft_holodeck.parser import CommandParser, FillCommand, SetblockCommand
from minecraft_holodeck.parser.ast import Coordinate, Position


def _extract_positions_from_command(
    ast: SetblockCommand | FillCommand,
) -> Iterator[Position]:
    """Extract all positions from a parsed command.

    Args:
        ast: Parsed command (SetblockCommand or FillCommand)

    Yields:
        Position objects from the command
    """
    if isinstance(ast, SetblockCommand):
        yield ast.position
    elif isinstance(ast, FillCommand):
        yield ast.pos1
        yield ast.pos2


def _compute_coordinate_bounds(
    commands: Iterator[tuple[SetblockCommand | FillCommand | None, ...]],
) -> tuple[
    tuple[float, float, float],  # min_x, min_y, min_z
    tuple[float, float, float],  # max_x, max_y, max_z
]:
    """Compute coordinate bounds from a sequence of commands.

    Args:
        commands: Iterator of tuples containing command ASTs (can include None values)

    Returns:
        Tuple of (min_coords, max_coords) where each is (x, y, z)
        Uses float('inf') and float('-inf') if no coordinates found
    """
    min_x = float("inf")
    min_y = float("inf")
    min_z = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")
    max_z = float("-inf")

    for item in commands:
        # Handle both tuple format (from convert_file) and direct AST
        ast = item[-1] if isinstance(item, tuple) else item
        if ast is None:
            continue

        for pos in _extract_positions_from_command(ast):
            # Only consider absolute coordinates
            if not pos.x.relative:
                min_x = min(min_x, pos.x.value)
                max_x = max(max_x, pos.x.value)
            if not pos.y.relative:
                min_y = min(min_y, pos.y.value)
                max_y = max(max_y, pos.y.value)
            if not pos.z.relative:
                min_z = min(min_z, pos.z.value)
                max_z = max(max_z, pos.z.value)

    return (min_x, min_y, min_z), (max_x, max_y, max_z)


@dataclass
class BoundingBox:
    """Bounding box of a structure."""

    min_x: int
    min_y: int
    min_z: int
    max_x: int
    max_y: int
    max_z: int

    @property
    def width(self) -> int:
        """Width in X dimension (inclusive)."""
        return self.max_x - self.min_x + 1

    @property
    def height(self) -> int:
        """Height in Y dimension (inclusive)."""
        return self.max_y - self.min_y + 1

    @property
    def depth(self) -> int:
        """Depth in Z dimension (inclusive)."""
        return self.max_z - self.min_z + 1

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"Bounds: ({self.min_x},{self.min_y},{self.min_z}) to ({self.max_x},{self.max_y},{self.max_z})\n"
            f"Size: {self.width}×{self.height}×{self.depth} (width×height×depth)"
        )


class ScriptConverter:
    """Convert absolute coordinate build scripts to relative coordinates."""

    def __init__(self):
        self.parser = CommandParser()

    def analyze_script(self, script_path: Path | str) -> BoundingBox:
        """Analyze a script to determine its bounding box.

        Args:
            script_path: Path to script file

        Returns:
            BoundingBox containing structure extents
        """
        script_path = Path(script_path)

        # Parse all commands from file
        def _parse_commands():
            with open(script_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    try:
                        yield (self.parser.parse(line),)
                    except Exception:
                        # Skip unparseable lines
                        continue

        # Compute bounds using shared helper
        (min_x, min_y, min_z), (max_x, max_y, max_z) = _compute_coordinate_bounds(
            _parse_commands()
        )

        # If no coordinates found, return default
        if min_x == float("inf"):
            return BoundingBox(0, 0, 0, 0, 0, 0)

        return BoundingBox(
            int(min_x),
            int(min_y),
            int(min_z),
            int(max_x),
            int(max_y),
            int(max_z),
        )

    def convert_file(
        self,
        input_path: Path | str,
        output_path: Path | str,
        base_point: tuple[int, int, int] | None = None,
        auto_detect: bool = True,
    ) -> tuple[tuple[int, int, int], BoundingBox]:
        """Convert a script file from absolute to relative coordinates.

        Args:
            input_path: Path to input script file
            output_path: Path to output script file
            base_point: Base point for relative coordinates (x, y, z).
                       If None and auto_detect is True, uses minimum coordinates.
            auto_detect: If True, automatically detect base point from min coords

        Returns:
            Tuple of (base_point, bounding_box)
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        # Read and parse all commands
        commands = []
        with open(input_path) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    commands.append((line_num, line, None))  # Keep comments/blanks
                else:
                    try:
                        ast = self.parser.parse(line)
                        commands.append((line_num, line, ast))
                    except Exception as e:
                        print(f"Warning: Could not parse line {line_num}: {e}")
                        commands.append((line_num, line, None))

        # Determine base point
        if base_point is None and auto_detect:
            base_point = self._detect_base_point(commands)
        elif base_point is None:
            base_point = (0, 0, 0)

        # Compute bounding box from original script
        bbox = self.analyze_script(input_path)

        # Convert and write
        with open(output_path, "w") as f:
            f.write(f"# Converted to relative coordinates\n")
            f.write(f"# Base point: {base_point[0]}, {base_point[1]}, {base_point[2]}\n")
            f.write(f"#\n")
            f.write(f"# Structure extents:\n")
            f.write(f"#   {bbox}\n")
            f.write(f"#\n")
            f.write(f"# For base-to-base placement (e.g., 10 blocks east):\n")
            f.write(f"#   Cabin 1: --origin {base_point[0]},{base_point[1]},{base_point[2]}\n")
            f.write(
                f"#   Cabin 2: --origin {base_point[0] + bbox.width + 10},{base_point[1]},{base_point[2]} "
                f"(width={bbox.width}, gap=10)\n"
            )
            f.write(f"#\n")
            f.write(f"# Basic usage:\n")
            f.write(f"#   mccommand batch world {output_path.name} --origin {base_point[0]},{base_point[1]},{base_point[2]}\n")
            f.write("\n")

            for line_num, original_line, ast in commands:
                if ast is None:
                    # Keep comments and blank lines as-is
                    f.write(original_line + "\n")
                else:
                    # Convert to relative
                    converted = self._convert_command(ast, base_point)
                    f.write(converted + "\n")

        return base_point, bbox

    def _detect_base_point(
        self, commands: list[tuple[int, str, SetblockCommand | FillCommand | None]]
    ) -> tuple[int, int, int]:
        """Detect base point from minimum coordinates in commands.

        Args:
            commands: List of (line_num, line, ast) tuples

        Returns:
            Base point (min_x, min_y, min_z)
        """
        # Use shared helper to compute bounds (only need min values)
        (min_x, min_y, min_z), _ = _compute_coordinate_bounds(iter(commands))

        # If no coordinates found, use origin
        if min_x == float("inf"):
            return (0, 0, 0)

        return (int(min_x), int(min_y), int(min_z))

    def _convert_command(
        self, ast: SetblockCommand | FillCommand, base_point: tuple[int, int, int]
    ) -> str:
        """Convert a command AST to relative coordinates.

        Args:
            ast: Command AST
            base_point: Base point (x, y, z)

        Returns:
            Command string with relative coordinates
        """
        if isinstance(ast, SetblockCommand):
            pos_str = self._convert_position(ast.position, base_point)
            block_str = self._format_block(ast.block)
            return f"/setblock {pos_str} {block_str}"

        elif isinstance(ast, FillCommand):
            pos1_str = self._convert_position(ast.pos1, base_point)
            pos2_str = self._convert_position(ast.pos2, base_point)
            block_str = self._format_block(ast.block)
            if ast.mode == "replace":
                return f"/fill {pos1_str} {pos2_str} {block_str}"
            else:
                return f"/fill {pos1_str} {pos2_str} {block_str} {ast.mode}"

        return ""

    def _convert_position(
        self, pos: Position, base_point: tuple[int, int, int]
    ) -> str:
        """Convert a position to relative coordinate string.

        Args:
            pos: Position to convert
            base_point: Base point (x, y, z)

        Returns:
            Position string like "~0 ~5 ~-3"
        """
        x_str = self._convert_coord(pos.x, base_point[0])
        y_str = self._convert_coord(pos.y, base_point[1])
        z_str = self._convert_coord(pos.z, base_point[2])
        return f"{x_str} {y_str} {z_str}"

    def _convert_coord(self, coord: Coordinate, base: int) -> str:
        """Convert a coordinate to relative string.

        Args:
            coord: Coordinate to convert
            base: Base coordinate value

        Returns:
            Coordinate string like "~5" or "~0" or "~-3"
        """
        if coord.relative:
            # Already relative, keep as-is
            if coord.value == 0:
                return "~"
            else:
                return f"~{coord.value:+d}".replace("+-", "-")
        else:
            # Convert absolute to relative
            offset = coord.value - base
            if offset == 0:
                return "~"
            else:
                # Format with explicit sign
                return f"~{offset:+d}".replace("+-", "-")

    def _format_block(self, block) -> str:
        """Format a block spec to string.

        Args:
            block: BlockSpec

        Returns:
            Block string like "minecraft:stone" or "oak_stairs[facing=north]"
        """
        result = block.full_id

        if block.states:
            state_pairs = [f"{k}={v}" for k, v in block.states.items()]
            result += "[" + ",".join(state_pairs) + "]"

        return result
