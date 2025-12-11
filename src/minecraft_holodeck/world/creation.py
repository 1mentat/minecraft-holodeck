"""World creation utilities for creating new Minecraft worlds.

This module provides functions to create new Minecraft Java Edition worlds
programmatically using amulet-core. Supports flat worlds and void worlds.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from amulet.api.block import Block  # type: ignore[import-untyped]
from amulet.level.formats.anvil_world import AnvilFormat  # type: ignore[import-untyped]
from amulet_nbt import TAG_Byte, TAG_Int, TAG_Long, TAG_String  # type: ignore[import-untyped]

from minecraft_holodeck.constants import MINECRAFT_PLATFORM, MINECRAFT_VERSION
from minecraft_holodeck.exceptions import WorldOperationError


@contextmanager
def _create_base_world(
    world_path: Path,
    name: str,
    spawn_x: int,
    spawn_y: int,
    spawn_z: int,
) -> Generator[AnvilFormat, None, None]:
    """Create and configure a base Minecraft world.

    This helper sets up the common world configuration shared by all world types:
    - Creates the world directory
    - Initializes AnvilFormat for Java Edition 1.20.1
    - Sets common NBT tags (name, game mode, difficulty, etc.)
    - Configures spawn point

    Args:
        world_path: Path where the world will be created
        name: World name for level.dat
        spawn_x: X coordinate of spawn point
        spawn_y: Y coordinate of spawn point
        spawn_z: Z coordinate of spawn point

    Yields:
        Configured AnvilFormat wrapper (saved and closed on exit)

    Raises:
        WorldOperationError: If world creation fails
    """
    # Create the world directory
    world_path.mkdir(parents=True, exist_ok=True)

    # Create a new Minecraft Java Edition world using AnvilFormat
    world_wrapper = AnvilFormat(str(world_path))
    world_wrapper.create_and_open(
        platform=MINECRAFT_PLATFORM,
        version=MINECRAFT_VERSION,
        overwrite=True
    )

    try:
        # Set world name in level.dat
        world_wrapper.root_tag["Data"]["LevelName"] = TAG_String(name)

        # Set game rules and world settings
        world_wrapper.root_tag["Data"]["GameType"] = TAG_Int(1)  # Creative mode
        world_wrapper.root_tag["Data"]["Difficulty"] = TAG_Byte(2)  # Normal difficulty
        world_wrapper.root_tag["Data"]["hardcore"] = TAG_Byte(0)
        world_wrapper.root_tag["Data"]["MapFeatures"] = TAG_Byte(0)  # No structures
        world_wrapper.root_tag["Data"]["raining"] = TAG_Byte(0)
        world_wrapper.root_tag["Data"]["thundering"] = TAG_Byte(0)
        world_wrapper.root_tag["Data"]["Time"] = TAG_Long(6000)  # Noon

        # Set spawn point
        world_wrapper.root_tag["Data"]["SpawnX"] = TAG_Int(spawn_x)
        world_wrapper.root_tag["Data"]["SpawnY"] = TAG_Int(spawn_y)
        world_wrapper.root_tag["Data"]["SpawnZ"] = TAG_Int(spawn_z)

        yield world_wrapper
    finally:
        # Save and close the world
        world_wrapper.save()
        world_wrapper.close()


def create_flat_world(
    world_path: str | Path,
    *,
    size_chunks: tuple[int, int] = (8, 8),
    layers: list[tuple[str, int]] | None = None,
    name: str | None = None,
) -> None:
    """Create a new flat Minecraft world.

    Creates a superflat world with customizable layers and size. The world is
    generated with the specified chunk dimensions and layer configuration.

    Args:
        world_path: Path where the world will be created
        size_chunks: Size in chunks (x, z). Each chunk is 16x16 blocks.
                    Default (8, 8) = 128x128 blocks
        layers: List of (block_id, thickness) tuples from bottom to top.
                Default creates classic flat world:
                - bedrock (1 block)
                - stone (2 blocks)
                - dirt (1 block)
                - grass_block (1 block)
        name: World name (defaults to folder name)

    Raises:
        WorldOperationError: If world creation fails

    Example:
        >>> create_flat_world("./my_world", size_chunks=(16, 16))
        >>> create_flat_world(
        ...     "./custom_world",
        ...     layers=[("bedrock", 1), ("stone", 10), ("grass_block", 1)],
        ...     name="Custom Flat World"
        ... )
    """
    world_path = Path(world_path)

    # Default layers: classic flat world
    if layers is None:
        layers = [
            ("bedrock", 1),
            ("stone", 2),
            ("dirt", 1),
            ("grass_block", 1),
        ]

    # Default name: folder name
    if name is None:
        name = world_path.name

    # Calculate spawn point at center of world
    spawn_x = (size_chunks[0] // 2) * 16
    spawn_z = (size_chunks[1] // 2) * 16
    spawn_y = sum(thickness for _, thickness in layers)

    try:
        # Create base world with common settings
        with _create_base_world(world_path, name, spawn_x, spawn_y, spawn_z):
            pass  # World is saved and closed by context manager

        # Now use WorldModifier to fill the world with layers
        from minecraft_holodeck.world.modifier import WorldModifier
        with WorldModifier(str(world_path)) as world:
            # Calculate bounds
            min_x = 0
            min_z = 0
            max_x = size_chunks[0] * 16 - 1
            max_z = size_chunks[1] * 16 - 1

            # Fill each layer
            current_y = 0
            for block_id, thickness in layers:
                # Add minecraft namespace if not present
                if ":" not in block_id:
                    block_id = f"minecraft:{block_id}"

                namespace, base_name = block_id.split(":")
                block = Block(namespace, base_name)

                # Fill this layer
                layer_top = current_y + thickness - 1
                world.fill_region(
                    min_x, current_y, min_z,
                    max_x, layer_top, max_z,
                    block,
                    mode="replace"
                )

                current_y += thickness

            world.save()

    except Exception as e:
        raise WorldOperationError(
            f"Failed to create flat world: {e}"
        ) from e


def create_void_world(
    world_path: str | Path,
    *,
    size_chunks: tuple[int, int] = (4, 4),
    spawn_platform: bool = True,
    name: str | None = None,
) -> None:
    """Create a void world (empty world with optional spawn platform).

    Creates an empty void world with no terrain. Optionally includes a small
    spawn platform to stand on.

    Args:
        world_path: Path where the world will be created
        size_chunks: Size in chunks (x, z) to generate
                    Default (4, 4) = 64x64 blocks
        spawn_platform: If True, creates a 3x3 stone platform at y=64
        name: World name (defaults to folder name)

    Raises:
        WorldOperationError: If world creation fails

    Example:
        >>> create_void_world("./void_world")
        >>> create_void_world("./creative_void", spawn_platform=False)
    """
    world_path = Path(world_path)

    # Default name: folder name
    if name is None:
        name = world_path.name

    # Calculate spawn point at center
    spawn_x = (size_chunks[0] // 2) * 16
    spawn_z = (size_chunks[1] // 2) * 16
    spawn_y = 64

    try:
        # Create base world with common settings
        with _create_base_world(world_path, name, spawn_x, spawn_y, spawn_z):
            pass  # World is saved and closed by context manager

        # Add spawn platform if requested using WorldModifier
        if spawn_platform:
            from minecraft_holodeck.world.modifier import WorldModifier
            with WorldModifier(str(world_path)) as world:
                platform = Block("minecraft", "stone")
                # 3x3 platform at spawn point
                for dx in range(-1, 2):
                    for dz in range(-1, 2):
                        world.set_block(
                            spawn_x + dx,
                            spawn_y - 1,  # One block below spawn
                            spawn_z + dz,
                            platform
                        )
                world.save()

    except Exception as e:
        raise WorldOperationError(
            f"Failed to create void world: {e}"
        ) from e
