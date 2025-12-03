"""Tests for world creation."""

from pathlib import Path

import pytest

from minecraft_holodeck.exceptions import WorldOperationError
from minecraft_holodeck.world import create_flat_world, create_void_world


class TestFlatWorldCreation:
    """Test flat world creation."""

    def test_create_flat_world_raises_not_implemented(self, tmp_path: Path) -> None:
        """Test that flat world creation raises informative error."""
        world_path = tmp_path / "test_world"

        with pytest.raises(WorldOperationError, match="not yet implemented"):
            create_flat_world(world_path)

    def test_create_flat_world_error_message_helpful(self, tmp_path: Path) -> None:
        """Test that error message provides helpful guidance."""
        world_path = tmp_path / "test_world"

        with pytest.raises(WorldOperationError) as exc_info:
            create_flat_world(world_path)

        error_msg = str(exc_info.value)
        assert "Minecraft" in error_msg
        assert "Amulet" in error_msg
        assert "future release" in error_msg


class TestVoidWorldCreation:
    """Test void world creation."""

    def test_create_void_world_raises_not_implemented(self, tmp_path: Path) -> None:
        """Test that void world creation raises informative error."""
        world_path = tmp_path / "void_world"

        with pytest.raises(WorldOperationError, match="not yet implemented"):
            create_void_world(world_path)

    def test_create_void_world_error_message_helpful(self, tmp_path: Path) -> None:
        """Test that error message provides helpful guidance."""
        world_path = tmp_path / "void_world"

        with pytest.raises(WorldOperationError) as exc_info:
            create_void_world(world_path)

        error_msg = str(exc_info.value)
        assert "Minecraft" in error_msg
        assert "Amulet" in error_msg or "void" in error_msg.lower()
        assert "future release" in error_msg
