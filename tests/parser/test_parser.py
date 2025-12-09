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

    def test_relative_coordinate_resolve(self) -> None:
        """Test resolving relative coordinates."""
        coord = Coordinate(5, relative=True)
        assert coord.resolve(100) == 105  # 100 + 5

    def test_relative_coordinate_negative_offset(self) -> None:
        """Test resolving relative coordinates with negative offset."""
        coord = Coordinate(-3, relative=True)
        assert coord.resolve(100) == 97  # 100 + (-3)

    def test_relative_coordinate_zero_offset(self) -> None:
        """Test resolving relative coordinates with zero offset."""
        coord = Coordinate(0, relative=True)
        assert coord.resolve(100) == 100  # 100 + 0

    def test_position_resolve(self) -> None:
        """Test resolving position."""
        pos = Position(
            Coordinate(10, relative=False),
            Coordinate(64, relative=False),
            Coordinate(20, relative=False),
        )
        result = pos.resolve((0, 0, 0))
        assert result == (10, 64, 20)

    def test_position_resolve_with_relative(self) -> None:
        """Test resolving position with relative coordinates."""
        pos = Position(
            Coordinate(5, relative=True),
            Coordinate(-1, relative=True),
            Coordinate(0, relative=True),
        )
        result = pos.resolve((100, 64, 200))
        assert result == (105, 63, 200)  # (100+5, 64-1, 200+0)

    def test_position_resolve_mixed(self) -> None:
        """Test resolving position with mixed absolute and relative."""
        pos = Position(
            Coordinate(10, relative=False),  # Absolute
            Coordinate(5, relative=True),    # Relative
            Coordinate(-20, relative=False), # Absolute
        )
        result = pos.resolve((100, 64, 200))
        assert result == (10, 69, -20)  # (10, 64+5, -20)


class TestRelativeCoordinates:
    """Test relative coordinate parsing (Phase 5)."""

    def test_parse_setblock_relative_all(self) -> None:
        """Test parsing setblock with all relative coordinates."""
        parser = CommandParser()
        result = parser.parse("/setblock ~5 ~-1 ~10 minecraft:stone")

        assert isinstance(result, SetblockCommand)
        assert result.position.x.value == 5
        assert result.position.x.relative is True
        assert result.position.y.value == -1
        assert result.position.y.relative is True
        assert result.position.z.value == 10
        assert result.position.z.relative is True

    def test_parse_setblock_relative_zero_offset(self) -> None:
        """Test parsing setblock with ~ (zero offset)."""
        parser = CommandParser()
        result = parser.parse("/setblock ~ ~ ~ minecraft:stone")

        assert isinstance(result, SetblockCommand)
        assert result.position.x.value == 0
        assert result.position.x.relative is True
        assert result.position.y.value == 0
        assert result.position.y.relative is True
        assert result.position.z.value == 0
        assert result.position.z.relative is True

    def test_parse_setblock_mixed_coordinates(self) -> None:
        """Test parsing setblock with mixed absolute and relative."""
        parser = CommandParser()
        result = parser.parse("/setblock 10 ~5 -20 minecraft:glass")

        assert isinstance(result, SetblockCommand)
        assert result.position.x.value == 10
        assert result.position.x.relative is False
        assert result.position.y.value == 5
        assert result.position.y.relative is True
        assert result.position.z.value == -20
        assert result.position.z.relative is False

    def test_parse_fill_relative_coordinates(self) -> None:
        """Test parsing fill with relative coordinates."""
        parser = CommandParser()
        result = parser.parse("/fill ~-5 ~ ~-5 ~5 ~10 ~5 minecraft:stone")

        assert isinstance(result, FillCommand)
        assert result.pos1.x.value == -5
        assert result.pos1.x.relative is True
        assert result.pos1.y.value == 0
        assert result.pos1.y.relative is True
        assert result.pos2.z.value == 5
        assert result.pos2.z.relative is True

    def test_parse_fill_mixed_coordinates(self) -> None:
        """Test parsing fill with mixed absolute and relative."""
        parser = CommandParser()
        result = parser.parse("/fill 0 64 0 ~10 ~6 ~10 minecraft:glass")

        assert isinstance(result, FillCommand)
        assert result.pos1.x.value == 0
        assert result.pos1.x.relative is False
        assert result.pos2.x.value == 10
        assert result.pos2.x.relative is True

    def test_parse_relative_with_block_states(self) -> None:
        """Test parsing relative coordinates with block states."""
        parser = CommandParser()
        result = parser.parse("/setblock ~1 ~2 ~3 oak_stairs[facing=north,half=top]")

        assert isinstance(result, SetblockCommand)
        assert result.position.x.value == 1
        assert result.position.x.relative is True
        assert result.block.states is not None
        assert result.block.states["facing"] == "north"

    def test_parse_relative_with_fill_mode(self) -> None:
        """Test parsing relative coordinates with fill mode."""
        parser = CommandParser()
        result = parser.parse("/fill ~ ~ ~ ~9 ~5 ~7 spruce_planks hollow")

        assert isinstance(result, FillCommand)
        assert result.pos1.x.relative is True
        assert result.pos2.x.relative is True
        assert result.mode == "hollow"


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
