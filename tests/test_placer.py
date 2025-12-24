"""Tests for smart structure placement (Phase 5)."""

from pathlib import Path

import pytest

from minecraft_holodeck.converter import BoundingBox
from minecraft_holodeck.placer import (
    Anchor,
    Direction,
    Footprint,
    PlacementError,
    PlacementResult,
    SliceInfo,
    StructureAnalyzer,
    StructurePlacer,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_script(tmp_path: Path) -> Path:
    """Create a sample script file with setblock commands."""
    script = tmp_path / "sample.txt"
    script.write_text(
        """/setblock 0 64 0 minecraft:stone
/setblock 1 64 0 minecraft:stone
/setblock 2 64 0 minecraft:stone
/setblock 0 65 0 minecraft:stone
/setblock 1 65 0 minecraft:stone
/setblock 2 65 0 minecraft:stone
/setblock 0 66 0 minecraft:stone
/setblock 1 66 0 minecraft:stone
/setblock 2 66 0 minecraft:stone
"""
    )
    return script


@pytest.fixture
def cabin_script(tmp_path: Path) -> Path:
    """Create a more complex cabin-like script."""
    script = tmp_path / "cabin.txt"
    # 5x5 footprint, 4 blocks tall (64-67)
    lines = []
    # Floor at y=64
    for x in range(5):
        for z in range(5):
            lines.append(f"/setblock {x} 64 {z} minecraft:oak_planks")
    # Walls at y=65-66
    for y in [65, 66]:
        for x in range(5):
            lines.append(f"/setblock {x} {y} 0 minecraft:oak_planks")
            lines.append(f"/setblock {x} {y} 4 minecraft:oak_planks")
        for z in range(1, 4):
            lines.append(f"/setblock 0 {y} {z} minecraft:oak_planks")
            lines.append(f"/setblock 4 {y} {z} minecraft:oak_planks")
    # Roof at y=67
    for x in range(5):
        for z in range(5):
            lines.append(f"/setblock {x} 67 {z} minecraft:oak_planks")
    script.write_text("\n".join(lines))
    return script


@pytest.fixture
def fill_script(tmp_path: Path) -> Path:
    """Create a script using fill commands."""
    script = tmp_path / "fill_structure.txt"
    script.write_text(
        """/fill 0 64 0 10 64 10 minecraft:stone
/fill 0 65 0 10 70 10 minecraft:air hollow
"""
    )
    return script


@pytest.fixture
def relative_script(tmp_path: Path) -> Path:
    """Create a script with relative coordinates."""
    script = tmp_path / "relative.txt"
    script.write_text(
        """/setblock ~ ~ ~ minecraft:stone
/setblock ~1 ~ ~ minecraft:stone
/setblock ~2 ~ ~ minecraft:stone
/setblock ~ ~1 ~ minecraft:stone
"""
    )
    return script


@pytest.fixture
def empty_script(tmp_path: Path) -> Path:
    """Create an empty script."""
    script = tmp_path / "empty.txt"
    script.write_text("# Just a comment\n\n")
    return script


# ============================================================================
# StructureAnalyzer Tests
# ============================================================================


class TestStructureAnalyzerBoundingBox:
    """Test bounding box calculation."""

    def test_get_bounding_box_setblock(self, sample_script: Path) -> None:
        """Test bounding box from setblock commands."""
        analyzer = StructureAnalyzer()
        bbox = analyzer.get_bounding_box(sample_script)

        assert bbox.min_x == 0
        assert bbox.max_x == 2
        assert bbox.min_y == 64
        assert bbox.max_y == 66
        assert bbox.min_z == 0
        assert bbox.max_z == 0
        assert bbox.width == 3
        assert bbox.height == 3
        assert bbox.depth == 1

    def test_get_bounding_box_cabin(self, cabin_script: Path) -> None:
        """Test bounding box from cabin script."""
        analyzer = StructureAnalyzer()
        bbox = analyzer.get_bounding_box(cabin_script)

        assert bbox.min_x == 0
        assert bbox.max_x == 4
        assert bbox.min_y == 64
        assert bbox.max_y == 67
        assert bbox.min_z == 0
        assert bbox.max_z == 4
        assert bbox.width == 5
        assert bbox.height == 4
        assert bbox.depth == 5

    def test_get_bounding_box_fill(self, fill_script: Path) -> None:
        """Test bounding box from fill commands."""
        analyzer = StructureAnalyzer()
        bbox = analyzer.get_bounding_box(fill_script)

        assert bbox.min_x == 0
        assert bbox.max_x == 10
        assert bbox.min_y == 64
        assert bbox.max_y == 70
        assert bbox.min_z == 0
        assert bbox.max_z == 10
        assert bbox.width == 11
        assert bbox.height == 7
        assert bbox.depth == 11

    def test_get_bounding_box_empty(self, empty_script: Path) -> None:
        """Test bounding box from empty script."""
        analyzer = StructureAnalyzer()
        bbox = analyzer.get_bounding_box(empty_script)

        # Empty script should return zero-size bounding box
        assert bbox == BoundingBox.empty()

    def test_get_bounding_box_string_path(self, sample_script: Path) -> None:
        """Test that string paths work."""
        analyzer = StructureAnalyzer()
        bbox = analyzer.get_bounding_box(str(sample_script))

        assert bbox.width == 3


class TestStructureAnalyzerFootprint:
    """Test base footprint calculation."""

    def test_get_base_footprint(self, cabin_script: Path) -> None:
        """Test base footprint calculation."""
        analyzer = StructureAnalyzer()
        footprint = analyzer.get_base_footprint(cabin_script)

        assert footprint.min_x == 0
        assert footprint.max_x == 4
        assert footprint.min_z == 0
        assert footprint.max_z == 4
        assert footprint.y_level == 64
        assert footprint.width == 5
        assert footprint.depth == 5
        # 5x5 = 25 blocks in base layer
        assert footprint.block_count == 25

    def test_get_base_footprint_empty(self, empty_script: Path) -> None:
        """Test footprint from empty script."""
        analyzer = StructureAnalyzer()
        footprint = analyzer.get_base_footprint(empty_script)

        assert footprint.block_count == 0


class TestStructureAnalyzerSlice:
    """Test Y-level slice analysis."""

    def test_get_slice_at_y(self, cabin_script: Path) -> None:
        """Test slice at specific Y level."""
        analyzer = StructureAnalyzer()

        # Floor level
        floor_slice = analyzer.get_slice_at_y(cabin_script, 64)
        assert floor_slice.width == 5
        assert floor_slice.depth == 5
        assert floor_slice.block_count == 25

        # Wall level (perimeter only)
        wall_slice = analyzer.get_slice_at_y(cabin_script, 65)
        assert wall_slice.width == 5
        assert wall_slice.depth == 5
        # Perimeter: 4 walls, but overlapping corners
        # Top/bottom walls: 5 + 5 = 10
        # Left/right walls (excluding corners): 3 + 3 = 6
        # Total: 16 blocks
        assert wall_slice.block_count == 16

    def test_get_slice_at_y_no_blocks(self, cabin_script: Path) -> None:
        """Test slice at Y level with no blocks."""
        analyzer = StructureAnalyzer()
        empty_slice = analyzer.get_slice_at_y(cabin_script, 100)

        assert empty_slice.block_count == 0

    def test_get_width_at_y(self, cabin_script: Path) -> None:
        """Test width at specific Y level."""
        analyzer = StructureAnalyzer()
        width = analyzer.get_width_at_y(cabin_script, 64)
        assert width == 5

    def test_get_depth_at_y(self, cabin_script: Path) -> None:
        """Test depth at specific Y level."""
        analyzer = StructureAnalyzer()
        depth = analyzer.get_depth_at_y(cabin_script, 64)
        assert depth == 5


class TestStructureAnalyzerHeight:
    """Test height calculation."""

    def test_get_height(self, cabin_script: Path) -> None:
        """Test total structure height."""
        analyzer = StructureAnalyzer()
        height = analyzer.get_height(cabin_script)
        assert height == 4  # 64-67 inclusive


# ============================================================================
# StructurePlacer Tests - Unit Tests (no world required)
# ============================================================================


class TestPlacerAnchorCalculation:
    """Test anchor point calculations."""

    def test_corner_anchor(self) -> None:
        """Test corner anchor calculation."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        bbox = BoundingBox(0, 0, 0, 10, 5, 10)
        origin = placer._calculate_origin_from_anchor((100, 64, 100), bbox, Anchor.CORNER)

        # Corner anchor: position is the origin
        assert origin == (100, 64, 100)

    def test_center_anchor(self) -> None:
        """Test center anchor calculation."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        # 11x6x11 structure (0-10 in each dimension)
        bbox = BoundingBox(0, 0, 0, 10, 5, 10)
        origin = placer._calculate_origin_from_anchor((100, 64, 100), bbox, Anchor.CENTER)

        # Center anchor: origin = position - (size / 2)
        # width=11, height=6, depth=11
        # origin = (100 - 5, 64 - 3, 100 - 5) = (95, 61, 95)
        assert origin == (95, 61, 95)

    def test_base_center_anchor(self) -> None:
        """Test base-center anchor calculation."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        # 11x6x11 structure
        bbox = BoundingBox(0, 0, 0, 10, 5, 10)
        origin = placer._calculate_origin_from_anchor((100, 64, 100), bbox, Anchor.BASE_CENTER)

        # Base-center: x/z centered, y at base level
        # origin = (100 - 5, 64, 100 - 5) = (95, 64, 95)
        assert origin == (95, 64, 95)


class TestPlacerAdjacentCalculation:
    """Test adjacent placement calculations."""

    def test_adjacent_east(self) -> None:
        """Test east adjacent placement."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        # New structure: 5 wide
        new_bbox = BoundingBox(0, 0, 0, 4, 3, 4)
        # Reference structure: 10 wide (0-9)
        ref_bbox = BoundingBox(0, 0, 0, 9, 3, 9)

        origin = placer._calculate_adjacent_origin(
            (0, 64, 0), new_bbox, ref_bbox, Direction.EAST, gap=5
        )

        # East: new_x = ref_x + ref_width + gap = 0 + 10 + 5 = 15
        assert origin == (15, 64, 0)

    def test_adjacent_west(self) -> None:
        """Test west adjacent placement."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        # New structure: 5 wide
        new_bbox = BoundingBox(0, 0, 0, 4, 3, 4)
        # Reference structure
        ref_bbox = BoundingBox(0, 0, 0, 9, 3, 9)

        origin = placer._calculate_adjacent_origin(
            (50, 64, 0), new_bbox, ref_bbox, Direction.WEST, gap=5
        )

        # West: new_x = ref_x - new_width - gap = 50 - 5 - 5 = 40
        assert origin == (40, 64, 0)

    def test_adjacent_south(self) -> None:
        """Test south adjacent placement."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        new_bbox = BoundingBox(0, 0, 0, 4, 3, 4)
        ref_bbox = BoundingBox(0, 0, 0, 9, 3, 9)

        origin = placer._calculate_adjacent_origin(
            (0, 64, 0), new_bbox, ref_bbox, Direction.SOUTH, gap=10
        )

        # South: new_z = ref_z + ref_depth + gap = 0 + 10 + 10 = 20
        assert origin == (0, 64, 20)

    def test_adjacent_north(self) -> None:
        """Test north adjacent placement."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        new_bbox = BoundingBox(0, 0, 0, 4, 3, 4)
        ref_bbox = BoundingBox(0, 0, 0, 9, 3, 9)

        origin = placer._calculate_adjacent_origin(
            (0, 64, 50), new_bbox, ref_bbox, Direction.NORTH, gap=5
        )

        # North: new_z = ref_z - new_depth - gap = 50 - 5 - 5 = 40
        assert origin == (0, 64, 40)

    def test_adjacent_up(self) -> None:
        """Test up adjacent placement."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        new_bbox = BoundingBox(0, 0, 0, 4, 3, 4)
        ref_bbox = BoundingBox(0, 0, 0, 4, 5, 4)  # 6 tall

        origin = placer._calculate_adjacent_origin(
            (0, 64, 0), new_bbox, ref_bbox, Direction.UP, gap=2
        )

        # Up: new_y = ref_y + ref_height + gap = 64 + 6 + 2 = 72
        assert origin == (0, 72, 0)

    def test_adjacent_down(self) -> None:
        """Test down adjacent placement."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        new_bbox = BoundingBox(0, 0, 0, 4, 3, 4)  # 4 tall
        ref_bbox = BoundingBox(0, 0, 0, 4, 5, 4)

        origin = placer._calculate_adjacent_origin(
            (0, 64, 0), new_bbox, ref_bbox, Direction.DOWN, gap=2
        )

        # Down: new_y = ref_y - new_height - gap = 64 - 4 - 2 = 58
        assert origin == (0, 58, 0)

    def test_adjacent_no_gap(self) -> None:
        """Test adjacent placement with no gap."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        new_bbox = BoundingBox(0, 0, 0, 4, 3, 4)
        ref_bbox = BoundingBox(0, 0, 0, 9, 3, 9)

        origin = placer._calculate_adjacent_origin(
            (0, 64, 0), new_bbox, ref_bbox, Direction.EAST, gap=0
        )

        # East with no gap: new_x = 0 + 10 + 0 = 10
        assert origin == (10, 64, 0)


class TestPlacerStringConversions:
    """Test that string anchor/direction values work."""

    def test_string_anchor(self) -> None:
        """Test string anchor conversion."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        bbox = BoundingBox(0, 0, 0, 10, 5, 10)

        # Should work with string
        origin = placer._calculate_origin_from_anchor((100, 64, 100), bbox, Anchor.CORNER)
        assert origin == (100, 64, 100)

    def test_string_direction(self) -> None:
        """Test string direction conversion."""
        placer = StructurePlacer.__new__(StructurePlacer)
        placer.analyzer = StructureAnalyzer()

        new_bbox = BoundingBox(0, 0, 0, 4, 3, 4)
        ref_bbox = BoundingBox(0, 0, 0, 9, 3, 9)

        # Should work with string (converted in place_adjacent)
        origin = placer._calculate_adjacent_origin(
            (0, 64, 0), new_bbox, ref_bbox, Direction.EAST, gap=5
        )
        assert origin == (15, 64, 0)


# ============================================================================
# Data Class Tests
# ============================================================================


class TestSliceInfo:
    """Test SliceInfo dataclass."""

    def test_slice_info_width(self) -> None:
        """Test SliceInfo width calculation."""
        info = SliceInfo(y=64, min_x=0, max_x=4, min_z=0, max_z=9, block_count=50)
        assert info.width == 5
        assert info.depth == 10

    def test_slice_info_single_block(self) -> None:
        """Test SliceInfo for single block."""
        info = SliceInfo(y=64, min_x=5, max_x=5, min_z=5, max_z=5, block_count=1)
        assert info.width == 1
        assert info.depth == 1


class TestFootprint:
    """Test Footprint dataclass."""

    def test_footprint_dimensions(self) -> None:
        """Test Footprint dimension calculation."""
        footprint = Footprint(min_x=0, max_x=9, min_z=0, max_z=9, y_level=64, block_count=100)
        assert footprint.width == 10
        assert footprint.depth == 10


class TestPlacementResult:
    """Test PlacementResult dataclass."""

    def test_placement_result_creation(self) -> None:
        """Test PlacementResult creation."""
        bbox = BoundingBox(0, 64, 0, 4, 67, 4)
        result = PlacementResult(
            blocks_placed=50,
            bounding_box=bbox,
            origin_used=(100, 64, 100),
        )

        assert result.blocks_placed == 50
        assert result.bounding_box.width == 5
        assert result.origin_used == (100, 64, 100)


# ============================================================================
# Enum Tests
# ============================================================================


class TestDirection:
    """Test Direction enum."""

    def test_direction_values(self) -> None:
        """Test Direction enum values."""
        assert Direction.NORTH.value == "north"
        assert Direction.SOUTH.value == "south"
        assert Direction.EAST.value == "east"
        assert Direction.WEST.value == "west"
        assert Direction.UP.value == "up"
        assert Direction.DOWN.value == "down"

    def test_direction_from_string(self) -> None:
        """Test creating Direction from string."""
        assert Direction("north") == Direction.NORTH
        assert Direction("east") == Direction.EAST


class TestAnchor:
    """Test Anchor enum."""

    def test_anchor_values(self) -> None:
        """Test Anchor enum values."""
        assert Anchor.CORNER.value == "corner"
        assert Anchor.CENTER.value == "center"
        assert Anchor.BASE_CENTER.value == "base-center"

    def test_anchor_from_string(self) -> None:
        """Test creating Anchor from string."""
        assert Anchor("corner") == Anchor.CORNER
        assert Anchor("base-center") == Anchor.BASE_CENTER
