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


class TestBlockStates:
    """Test block state parsing (Phase 2)."""

    def test_parse_single_block_state(self) -> None:
        """Test parsing block with single state."""
        parser = CommandParser()
        result = parser.parse("/setblock 0 64 0 minecraft:oak_stairs[facing=north]")

        assert isinstance(result, SetblockCommand)
        assert result.block.block_id == "oak_stairs"
        assert result.block.states is not None
        assert result.block.states["facing"] == "north"

    def test_parse_multiple_block_states(self) -> None:
        """Test parsing block with multiple states."""
        parser = CommandParser()
        result = parser.parse("/setblock 0 64 0 minecraft:oak_stairs[facing=north,half=top]")

        assert isinstance(result, SetblockCommand)
        assert result.block.states is not None
        assert result.block.states["facing"] == "north"
        assert result.block.states["half"] == "top"

    def test_parse_block_state_with_boolean(self) -> None:
        """Test parsing block state with boolean value."""
        parser = CommandParser()
        result = parser.parse("/setblock 0 64 0 minecraft:oak_stairs[waterlogged=true]")

        assert isinstance(result, SetblockCommand)
        assert result.block.states is not None
        assert result.block.states["waterlogged"] is True

    def test_parse_block_state_with_integer(self) -> None:
        """Test parsing block state with integer value."""
        parser = CommandParser()
        result = parser.parse("/setblock 0 64 0 minecraft:repeater[delay=3]")

        assert isinstance(result, SetblockCommand)
        assert result.block.states is not None
        assert result.block.states["delay"] == 3

    def test_parse_door_with_states(self) -> None:
        """Test parsing door with half and hinge states."""
        parser = CommandParser()
        result = parser.parse("/setblock 4 66 0 spruce_door[half=lower,hinge=left]")

        assert isinstance(result, SetblockCommand)
        assert result.block.namespace == "minecraft"
        assert result.block.block_id == "spruce_door"
        assert result.block.states is not None
        assert result.block.states["half"] == "lower"
        assert result.block.states["hinge"] == "left"

    def test_parse_stairs_complex_states(self) -> None:
        """Test parsing stairs with multiple states."""
        parser = CommandParser()
        result = parser.parse(
            "/setblock 0 64 0 minecraft:spruce_stairs[facing=east,half=top,shape=straight]"
        )

        assert isinstance(result, SetblockCommand)
        assert result.block.states is not None
        assert result.block.states["facing"] == "east"
        assert result.block.states["half"] == "top"
        assert result.block.states["shape"] == "straight"

    def test_parse_fill_with_block_states(self) -> None:
        """Test parsing fill command with block states."""
        parser = CommandParser()
        result = parser.parse("/fill 0 64 0 10 70 10 minecraft:oak_stairs[facing=north]")

        assert isinstance(result, FillCommand)
        assert result.block.block_id == "oak_stairs"
        assert result.block.states is not None
        assert result.block.states["facing"] == "north"

    def test_parse_block_without_states(self) -> None:
        """Test that blocks without states still work."""
        parser = CommandParser()
        result = parser.parse("/setblock 0 64 0 minecraft:stone")

        assert isinstance(result, SetblockCommand)
        assert result.block.block_id == "stone"
        assert result.block.states is None


class TestFillModes:
    """Test fill mode parsing (Phase 3)."""

    def test_parse_fill_default_mode(self) -> None:
        """Test parsing fill without mode (defaults to replace)."""
        parser = CommandParser()
        result = parser.parse("/fill 0 64 0 10 70 10 minecraft:stone")

        assert isinstance(result, FillCommand)
        assert result.mode == "replace"

    def test_parse_fill_hollow_mode(self) -> None:
        """Test parsing fill with hollow mode."""
        parser = CommandParser()
        result = parser.parse("/fill 0 64 0 10 70 10 minecraft:stone hollow")

        assert isinstance(result, FillCommand)
        assert result.block.block_id == "stone"
        assert result.mode == "hollow"

    def test_parse_fill_destroy_mode(self) -> None:
        """Test parsing fill with destroy mode."""
        parser = CommandParser()
        result = parser.parse("/fill 0 64 0 10 70 10 minecraft:glass destroy")

        assert isinstance(result, FillCommand)
        assert result.mode == "destroy"

    def test_parse_fill_keep_mode(self) -> None:
        """Test parsing fill with keep mode."""
        parser = CommandParser()
        result = parser.parse("/fill 0 64 0 10 70 10 minecraft:cobblestone keep")

        assert isinstance(result, FillCommand)
        assert result.mode == "keep"

    def test_parse_fill_outline_mode(self) -> None:
        """Test parsing fill with outline mode."""
        parser = CommandParser()
        result = parser.parse("/fill 0 64 0 10 70 10 minecraft:glass outline")

        assert isinstance(result, FillCommand)
        assert result.mode == "outline"

    def test_parse_fill_replace_mode(self) -> None:
        """Test parsing fill with explicit replace mode."""
        parser = CommandParser()
        result = parser.parse("/fill 0 64 0 10 70 10 minecraft:dirt replace")

        assert isinstance(result, FillCommand)
        assert result.mode == "replace"

    def test_parse_fill_hollow_with_block_states(self) -> None:
        """Test parsing hollow fill with block states."""
        parser = CommandParser()
        result = parser.parse(
            "/fill 0 65 0 9 69 7 spruce_planks[waterlogged=false] hollow"
        )

        assert isinstance(result, FillCommand)
        assert result.block.block_id == "spruce_planks"
        assert result.block.states is not None
        assert result.block.states["waterlogged"] is False
        assert result.mode == "hollow"
