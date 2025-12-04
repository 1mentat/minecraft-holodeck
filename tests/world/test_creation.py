"""Tests for world creation."""

from pathlib import Path

import pytest
import amulet  # type: ignore[import-untyped]

from minecraft_holodeck.exceptions import WorldOperationError
from minecraft_holodeck.world import create_flat_world, create_void_world


class TestFlatWorldCreation:
    """Test flat world creation."""

    def test_create_flat_world_creates_directory(self, tmp_path: Path) -> None:
        """Test that flat world creation creates the world directory."""
        world_path = tmp_path / "test_world"
        assert not world_path.exists()

        create_flat_world(world_path, size_chunks=(2, 2))

        assert world_path.exists()
        assert world_path.is_dir()

    def test_create_flat_world_creates_level_dat(self, tmp_path: Path) -> None:
        """Test that flat world creation creates level.dat file."""
        world_path = tmp_path / "test_world"

        create_flat_world(world_path, size_chunks=(2, 2))

        level_dat = world_path / "level.dat"
        assert level_dat.exists()

    def test_create_flat_world_is_loadable(self, tmp_path: Path) -> None:
        """Test that created world can be loaded by amulet."""
        world_path = tmp_path / "test_world"

        create_flat_world(world_path, size_chunks=(2, 2))

        # Should not raise an exception
        level = amulet.load_level(str(world_path))
        level.close()

    def test_create_flat_world_custom_name(self, tmp_path: Path) -> None:
        """Test that custom world name is set correctly."""
        world_path = tmp_path / "test_world"
        custom_name = "My Custom World"

        create_flat_world(world_path, size_chunks=(2, 2), name=custom_name)

        level = amulet.load_level(str(world_path))
        actual_name = level.level_wrapper.root_tag["Data"]["LevelName"].py_str
        level.close()

        assert actual_name == custom_name

    def test_create_flat_world_default_name_is_folder(self, tmp_path: Path) -> None:
        """Test that default world name is the folder name."""
        world_path = tmp_path / "my_folder_name"

        create_flat_world(world_path, size_chunks=(2, 2))

        level = amulet.load_level(str(world_path))
        actual_name = level.level_wrapper.root_tag["Data"]["LevelName"].py_str
        level.close()

        assert actual_name == "my_folder_name"

    def test_create_flat_world_custom_layers(self, tmp_path: Path) -> None:
        """Test creating flat world with custom layers."""
        world_path = tmp_path / "custom_world"

        # Just test that it doesn't crash with custom layers
        create_flat_world(
            world_path,
            size_chunks=(2, 2),
            layers=[
                ("bedrock", 1),
                ("stone", 5),
                ("grass_block", 1),
            ]
        )

        assert world_path.exists()
        level = amulet.load_level(str(world_path))
        level.close()

    def test_create_flat_world_spawn_point(self, tmp_path: Path) -> None:
        """Test that spawn point is set at center of world."""
        world_path = tmp_path / "test_world"
        size_chunks = (4, 4)

        create_flat_world(world_path, size_chunks=size_chunks)

        level = amulet.load_level(str(world_path))
        spawn_x = level.level_wrapper.root_tag["Data"]["SpawnX"].py_int
        spawn_z = level.level_wrapper.root_tag["Data"]["SpawnZ"].py_int
        level.close()

        # Spawn should be at center: (4 // 2) * 16 = 32
        expected_x = (size_chunks[0] // 2) * 16
        expected_z = (size_chunks[1] // 2) * 16

        assert spawn_x == expected_x
        assert spawn_z == expected_z

    def test_create_flat_world_with_string_path(self, tmp_path: Path) -> None:
        """Test that string paths work (not just Path objects)."""
        world_path = tmp_path / "string_path_world"

        # Pass as string instead of Path
        create_flat_world(str(world_path), size_chunks=(2, 2))

        assert world_path.exists()


class TestVoidWorldCreation:
    """Test void world creation."""

    def test_create_void_world_creates_directory(self, tmp_path: Path) -> None:
        """Test that void world creation creates the world directory."""
        world_path = tmp_path / "void_world"
        assert not world_path.exists()

        create_void_world(world_path, size_chunks=(2, 2))

        assert world_path.exists()
        assert world_path.is_dir()

    def test_create_void_world_creates_level_dat(self, tmp_path: Path) -> None:
        """Test that void world creation creates level.dat file."""
        world_path = tmp_path / "void_world"

        create_void_world(world_path, size_chunks=(2, 2))

        level_dat = world_path / "level.dat"
        assert level_dat.exists()

    def test_create_void_world_is_loadable(self, tmp_path: Path) -> None:
        """Test that created void world can be loaded by amulet."""
        world_path = tmp_path / "void_world"

        create_void_world(world_path, size_chunks=(2, 2))

        # Should not raise an exception
        level = amulet.load_level(str(world_path))
        level.close()

    def test_create_void_world_custom_name(self, tmp_path: Path) -> None:
        """Test that custom world name is set correctly."""
        world_path = tmp_path / "void_world"
        custom_name = "The Void"

        create_void_world(world_path, size_chunks=(2, 2), name=custom_name)

        level = amulet.load_level(str(world_path))
        actual_name = level.level_wrapper.root_tag["Data"]["LevelName"].py_str
        level.close()

        assert actual_name == custom_name

    def test_create_void_world_without_platform(self, tmp_path: Path) -> None:
        """Test creating void world without spawn platform."""
        world_path = tmp_path / "void_no_platform"

        # Should not crash
        create_void_world(world_path, size_chunks=(2, 2), spawn_platform=False)

        assert world_path.exists()
        level = amulet.load_level(str(world_path))
        level.close()

    def test_create_void_world_with_platform(self, tmp_path: Path) -> None:
        """Test creating void world with spawn platform."""
        world_path = tmp_path / "void_with_platform"

        create_void_world(world_path, size_chunks=(4, 4), spawn_platform=True)

        level = amulet.load_level(str(world_path))

        # Get spawn coordinates
        spawn_x = level.level_wrapper.root_tag["Data"]["SpawnX"].py_int
        spawn_y = level.level_wrapper.root_tag["Data"]["SpawnY"].py_int
        spawn_z = level.level_wrapper.root_tag["Data"]["SpawnZ"].py_int

        # Check that platform blocks exist (3x3 at y=spawn_y-1)
        dimension = "minecraft:overworld"
        platform_y = spawn_y - 1

        # Check center of platform
        center_block = level.get_block(spawn_x, platform_y, spawn_z, dimension)
        # amulet may return "minecraft:stone" or "universal_minecraft:stone"
        assert "stone" in center_block.namespaced_name

        level.close()

    def test_create_void_world_spawn_point(self, tmp_path: Path) -> None:
        """Test that spawn point is set at center of world."""
        world_path = tmp_path / "void_world"
        size_chunks = (4, 4)

        create_void_world(world_path, size_chunks=size_chunks)

        level = amulet.load_level(str(world_path))
        spawn_x = level.level_wrapper.root_tag["Data"]["SpawnX"].py_int
        spawn_y = level.level_wrapper.root_tag["Data"]["SpawnY"].py_int
        spawn_z = level.level_wrapper.root_tag["Data"]["SpawnZ"].py_int
        level.close()

        # Spawn should be at center and y=64
        expected_x = (size_chunks[0] // 2) * 16
        expected_z = (size_chunks[1] // 2) * 16

        assert spawn_x == expected_x
        assert spawn_y == 64
        assert spawn_z == expected_z
