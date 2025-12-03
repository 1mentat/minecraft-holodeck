"""World creation utilities for creating new Minecraft worlds.

NOTE: World creation from scratch is complex and requires generating proper NBT structures,
region files, and world metadata. Currently, this module provides a simplified approach.

For full world creation, consider:
1. Creating worlds in Minecraft Java Edition
2. Using external tools like Amulet Editor
3. Starting with an existing template world
"""

from pathlib import Path

from minecraft_holodeck.exceptions import WorldOperationError


def create_flat_world(
    world_path: str | Path,
    *,
    size_chunks: tuple[int, int] = (8, 8),
    layers: list[tuple[str, int]] | None = None,
    name: str | None = None,
) -> None:
    """Create a new flat Minecraft world.

    NOTE: This feature requires Minecraft Java Edition to be installed,
    or a template world to copy from. Full programmatic world creation
    is planned for a future release.

    For now, please create worlds using:
    1. Minecraft Java Edition (File > New World > More World Options > World Type: Flat)
    2. Or provide a template world directory

    Args:
        world_path: Path where the world will be created
        size_chunks: Size in chunks (x, z). Each chunk is 16x16 blocks.
                    Default (8, 8) = 128x128 blocks
        layers: List of (block_id, thickness) tuples from bottom to top.
                Default creates classic flat world
        name: World name (defaults to folder name)

    Raises:
        WorldOperationError: Always raised with instructions for now
    """
    raise WorldOperationError(
        "Programmatic world creation is not yet implemented.\n\n"
        "To create a flat world, please use one of these methods:\n"
        "1. Create in Minecraft: File > New World > More World Options > World Type: Flat\n"
        "2. Use Amulet Editor: https://www.amuletmc.com/\n"
        "3. Copy an existing template world\n\n"
        "Then use minecraft-holodeck to modify the world with setblock/fill commands.\n\n"
        "Full programmatic world creation will be added in a future release."
    )


def create_void_world(
    world_path: str | Path,
    *,
    size_chunks: tuple[int, int] = (4, 4),
    spawn_platform: bool = True,
    name: str | None = None,
) -> None:
    """Create a void world (empty world with optional spawn platform).

    NOTE: This feature requires Minecraft Java Edition to be installed.
    Full programmatic world creation is planned for a future release.

    For now, please create void worlds using:
    1. Minecraft Java Edition with the Void superflat preset
    2. Or use an existing void world template

    Args:
        world_path: Path where the world will be created
        size_chunks: Size in chunks (x, z) to generate
        spawn_platform: If True, creates a 3x3 stone platform at y=64
        name: World name (defaults to folder name)

    Raises:
        WorldOperationError: Always raised with instructions for now
    """
    raise WorldOperationError(
        "Programmatic world creation is not yet implemented.\n\n"
        "To create a void world, please use one of these methods:\n"
        "1. Create in Minecraft with the Void superflat preset\n"
        "2. Use Amulet Editor: https://www.amuletmc.com/\n"
        "3. Copy an existing void world template\n\n"
        "Then use minecraft-holodeck to modify the world with setblock/fill commands.\n\n"
        "Full programmatic world creation will be added in a future release."
    )
