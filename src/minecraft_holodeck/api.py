"""High-level Python API for minecraft-holodeck."""

from pathlib import Path
from typing import Any

from minecraft_holodeck.parser import CommandParser, FillCommand, SetblockCommand
from minecraft_holodeck.world import WorldModifier, blockspec_to_amulet


class WorldEditor:
    """High-level API for executing commands on a world.

    Example:
        with WorldEditor("/path/to/world") as editor:
            editor.execute("/setblock 0 64 0 minecraft:diamond_block")
            editor.execute("/fill 0 64 0 10 70 10 minecraft:stone")
    """

    def __init__(
        self,
        world_path: str | Path,
        origin: tuple[int, int, int] = (0, 0, 0)
    ):
        """Initialize world editor.

        Args:
            world_path: Path to Minecraft world folder
            origin: Origin point for relative coordinates (Phase 5: now supported)
        """
        self.world_path = Path(world_path)
        self.origin = origin
        self.parser = CommandParser()
        self.modifier = WorldModifier(str(world_path))

    def execute(self, command: str) -> int:
        """Execute a command, return number of blocks changed.

        Args:
            command: Command string (e.g., "/setblock 0 64 0 minecraft:stone")

        Returns:
            Number of blocks modified

        Raises:
            CommandSyntaxError: Invalid command syntax
            WorldOperationError: World modification failed
        """
        # Parse command
        ast = self.parser.parse(command)

        # Execute based on command type
        if isinstance(ast, SetblockCommand):
            # Resolve coordinates
            x, y, z = ast.position.resolve(self.origin)

            # Convert block
            block = blockspec_to_amulet(ast.block)

            # Execute
            self.modifier.set_block(x, y, z, block)
            return 1

        elif isinstance(ast, FillCommand):
            # Resolve coordinates
            x1, y1, z1 = ast.pos1.resolve(self.origin)
            x2, y2, z2 = ast.pos2.resolve(self.origin)

            # Convert block
            block = blockspec_to_amulet(ast.block)

            # Execute with mode (Phase 3)
            count = self.modifier.fill_region(x1, y1, z1, x2, y2, z2, block, ast.mode)
            return count

        else:
            # This shouldn't happen with proper typing
            raise ValueError(f"Unknown command type: {type(ast)}")

    def save(self) -> None:
        """Save changes to world."""
        self.modifier.save()

    def __enter__(self) -> "WorldEditor":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.modifier.close()


def execute_command(
    world_path: str,
    command: str,
    origin: tuple[int, int, int] = (0, 0, 0)
) -> int:
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
