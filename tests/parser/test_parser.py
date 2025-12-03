"""Tests for command parser."""

import pytest

from minecraft_holodeck.parser import (
    BlockSpec,
    CommandParser,
    CommandSyntaxError,
    Coordinate,
    FillCommand,
    Position,
    SetblockCommand,
)


class TestBasicParsing:
    """Test basic command parsing."""

    def test_parse_basic_setblock(self) -> None:
        """Test parsing basic setblock command."""
        parser = CommandParser()
        result = parser.parse("/setblock 10 64 10 minecraft:stone")

        assert isinstance(result, SetblockCommand)
        assert result.position.x.value == 10
        assert result.position.y.value == 64
        assert result.position.z.value == 10
        assert result.block.namespace == "minecraft"
        assert result.block.block_id == "stone"
        assert result.block.full_id == "minecraft:stone"

    def test_parse_setblock_without_slash(self) -> None:
        """Test parsing without leading slash."""
        parser = CommandParser()
        result = parser.parse("setblock 0 0 0 minecraft:dirt")

        assert isinstance(result, SetblockCommand)
        assert result.position.x.value == 0
        assert result.block.block_id == "dirt"

    def test_parse_setblock_implicit_namespace(self) -> None:
        """Test parsing with implicit minecraft: namespace."""
        parser = CommandParser()
        result = parser.parse("/setblock 5 5 5 stone")

        assert isinstance(result, SetblockCommand)
        assert result.block.namespace == "minecraft"
        assert result.block.block_id == "stone"

    def test_parse_setblock_negative_coords(self) -> None:
        """Test parsing with negative coordinates."""
        parser = CommandParser()
        result = parser.parse("/setblock -10 64 -20 minecraft:glass")

        assert isinstance(result, SetblockCommand)
        assert result.position.x.value == -10
        assert result.position.z.value == -20

    def test_parse_basic_fill(self) -> None:
        """Test parsing basic fill command."""
        parser = CommandParser()
        result = parser.parse("/fill 0 64 0 10 70 10 minecraft:stone")

        assert isinstance(result, FillCommand)
        assert result.pos1.x.value == 0
        assert result.pos1.y.value == 64
        assert result.pos1.z.value == 0
        assert result.pos2.x.value == 10
        assert result.pos2.y.value == 70
        assert result.pos2.z.value == 10
        assert result.block.namespace == "minecraft"
        assert result.block.block_id == "stone"

    def test_parse_fill_negative_coords(self) -> None:
        """Test parsing fill with negative coordinates."""
        parser = CommandParser()
        result = parser.parse("/fill -5 0 -5 5 10 5 minecraft:air")

        assert isinstance(result, FillCommand)
        assert result.pos1.x.value == -5
        assert result.pos2.x.value == 5

    def test_parse_custom_namespace(self) -> None:
        """Test parsing block with custom namespace."""
        parser = CommandParser()
        result = parser.parse("/setblock 0 0 0 mymod:custom_block")

        assert isinstance(result, SetblockCommand)
        assert result.block.namespace == "mymod"
        assert result.block.block_id == "custom_block"


class TestParseErrors:
    """Test error handling."""

    def test_invalid_command(self) -> None:
        """Test parsing invalid command."""
        parser = CommandParser()
        with pytest.raises(CommandSyntaxError):
            parser.parse("/invalid 0 0 0")

    def test_missing_arguments(self) -> None:
        """Test parsing with missing arguments."""
        parser = CommandParser()
        with pytest.raises(CommandSyntaxError):
            parser.parse("/setblock 0 0")

    def test_invalid_coordinate(self) -> None:
        """Test parsing with invalid coordinate."""
        parser = CommandParser()
        with pytest.raises(CommandSyntaxError):
            parser.parse("/setblock abc 0 0 minecraft:stone")


class TestCoordinateResolution:
    """Test coordinate resolution."""

    def test_absolute_coordinate_resolve(self) -> None:
        """Test resolving absolute coordinates."""
        coord = Coordinate(10, relative=False)
        assert coord.resolve(100) == 10  # Absolute ignores origin

    def test_position_resolve(self) -> None:
        """Test resolving position."""
        pos = Position(
            Coordinate(10, relative=False),
            Coordinate(64, relative=False),
            Coordinate(20, relative=False),
        )
        result = pos.resolve((0, 0, 0))
        assert result == (10, 64, 20)


class TestBlockSpec:
    """Test BlockSpec functionality."""

    def test_full_id(self) -> None:
        """Test full_id property."""
        spec = BlockSpec("minecraft", "stone")
        assert spec.full_id == "minecraft:stone"

    def test_custom_namespace_full_id(self) -> None:
        """Test full_id with custom namespace."""
        spec = BlockSpec("mymod", "custom_block")
        assert spec.full_id == "mymod:custom_block"
