"""Convert absolute coordinate scripts to relative coordinates."""

from pathlib import Path
from typing import TextIO

from minecraft_holodeck.parser import CommandParser, FillCommand, SetblockCommand
from minecraft_holodeck.parser.ast import Coordinate, Position


class ScriptConverter:
    """Convert absolute coordinate build scripts to relative coordinates."""

    def __init__(self):
        self.parser = CommandParser()

    def convert_file(
        self,
        input_path: Path | str,
        output_path: Path | str,
        base_point: tuple[int, int, int] | None = None,
        auto_detect: bool = True,
    ) -> tuple[int, int, int]:
        """Convert a script file from absolute to relative coordinates.

        Args:
            input_path: Path to input script file
            output_path: Path to output script file
            base_point: Base point for relative coordinates (x, y, z).
                       If None and auto_detect is True, uses minimum coordinates.
            auto_detect: If True, automatically detect base point from min coords

        Returns:
            The base point used (x, y, z)
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

        # Convert and write
        with open(output_path, "w") as f:
            f.write(f"# Converted to relative coordinates\n")
            f.write(f"# Base point: {base_point[0]}, {base_point[1]}, {base_point[2]}\n")
            f.write(f"# Use with: --origin {base_point[0]},{base_point[1]},{base_point[2]}\n")
            f.write("\n")

            for line_num, original_line, ast in commands:
                if ast is None:
                    # Keep comments and blank lines as-is
                    f.write(original_line + "\n")
                else:
                    # Convert to relative
                    converted = self._convert_command(ast, base_point)
                    f.write(converted + "\n")

        return base_point

    def _detect_base_point(
        self, commands: list[tuple[int, str, SetblockCommand | FillCommand | None]]
    ) -> tuple[int, int, int]:
        """Detect base point from minimum coordinates in commands.

        Args:
            commands: List of (line_num, line, ast) tuples

        Returns:
            Base point (min_x, min_y, min_z)
        """
        min_x = float("inf")
        min_y = float("inf")
        min_z = float("inf")

        for _, _, ast in commands:
            if ast is None:
                continue

            if isinstance(ast, SetblockCommand):
                positions = [ast.position]
            elif isinstance(ast, FillCommand):
                positions = [ast.pos1, ast.pos2]
            else:
                continue

            for pos in positions:
                # Only consider absolute coordinates
                if not pos.x.relative:
                    min_x = min(min_x, pos.x.value)
                if not pos.y.relative:
                    min_y = min(min_y, pos.y.value)
                if not pos.z.relative:
                    min_z = min(min_z, pos.z.value)

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
