#!/usr/bin/env python3
"""Build a cozy woodland cabin in Minecraft.

This script creates a rustic spruce cabin with stone foundation at coordinates X=0, Y=64, Z=0.
Adjust the BASE_X, BASE_Y, BASE_Z constants to change the build location.

Usage:
    python cabin_build.py <path_to_world>

Example:
    python cabin_build.py ~/minecraft/saves/MyWorld

Requirements:
    - An existing Minecraft Java Edition world (create a flat world first)
    - minecraft-holodeck package installed
"""

import sys
from pathlib import Path

from minecraft_holodeck import WorldEditor

# Base coordinates for the cabin
BASE_X = 0
BASE_Y = 64
BASE_Z = 0


def build_cabin(world_path: str) -> None:
    """Build the cabin in the specified world.

    Args:
        world_path: Path to the Minecraft world directory
    """
    world = Path(world_path)
    if not world.exists():
        print(f"Error: World directory not found: {world_path}")
        sys.exit(1)

    print("🏡 Building Woodsy Cabin...")
    print(f"   Location: X={BASE_X}, Y={BASE_Y}, Z={BASE_Z}")
    print(f"   World: {world_path}")
    print()

    with WorldEditor(world_path) as editor:
        # Step 1: Clear the Build Area
        print("Step 1: Clearing build area...")
        editor.execute("/fill 0 64 0 10 72 8 air")

        # Step 2: Foundation (Cobblestone)
        print("Step 2: Building foundation...")
        editor.execute("/fill 0 64 0 9 64 7 cobblestone")

        # Step 3: Floor (Spruce Planks)
        print("Step 3: Adding floor...")
        editor.execute("/fill 1 65 1 8 65 6 spruce_planks")

        # Step 4: Walls — Build each wall separately
        print("Step 4: Building walls...")
        editor.execute("/fill 0 65 0 9 69 0 spruce_planks")  # Front wall
        editor.execute("/fill 0 65 7 9 69 7 spruce_planks")  # Back wall
        editor.execute("/fill 0 65 0 0 69 7 spruce_planks")  # Left wall
        editor.execute("/fill 9 65 0 9 69 7 spruce_planks")  # Right wall

        # Step 5: Corner Log Pillars
        print("Step 5: Adding corner pillars...")
        editor.execute("/fill 0 65 0 0 69 0 spruce_log")
        editor.execute("/fill 9 65 0 9 69 0 spruce_log")
        editor.execute("/fill 0 65 7 0 69 7 spruce_log")
        editor.execute("/fill 9 65 7 9 69 7 spruce_log")

        # Step 6: Clear Interior
        print("Step 6: Clearing interior...")
        editor.execute("/fill 1 66 1 8 68 6 air")

        # Step 7: Windows (Glass Panes)
        print("Step 7: Installing windows...")
        # Front windows
        editor.execute("/setblock 2 67 0 glass_pane")
        editor.execute("/setblock 7 67 0 glass_pane")
        # Side windows
        editor.execute("/fill 0 67 2 0 67 3 glass_pane")
        editor.execute("/fill 0 67 4 0 67 5 glass_pane")
        editor.execute("/fill 9 67 2 9 67 3 glass_pane")
        editor.execute("/fill 9 67 4 9 67 5 glass_pane")
        # Back window
        editor.execute("/fill 4 67 7 5 67 7 glass_pane")

        # Step 8: Front Door
        print("Step 8: Adding front door...")
        editor.execute("/setblock 4 66 0 air")
        editor.execute("/setblock 5 66 0 air")
        editor.execute("/setblock 4 67 0 air")
        editor.execute("/setblock 5 67 0 air")
        editor.execute("/setblock 4 66 0 spruce_door[half=lower,hinge=left]")
        editor.execute("/setblock 4 67 0 spruce_door[half=upper,hinge=left]")

        # Step 9: Peaked Roof (Spruce Stairs + Slabs)
        print("Step 9: Building peaked roof...")
        # First roof layer
        editor.execute("/fill -1 70 -1 -1 70 8 spruce_stairs[facing=east]")
        editor.execute("/fill 10 70 -1 10 70 8 spruce_stairs[facing=west]")
        # Second roof layer
        editor.execute("/fill 0 71 -1 0 71 8 spruce_stairs[facing=east]")
        editor.execute("/fill 9 71 -1 9 71 8 spruce_stairs[facing=west]")
        # Third roof layer
        editor.execute("/fill 1 72 -1 1 72 8 spruce_stairs[facing=east]")
        editor.execute("/fill 8 72 -1 8 72 8 spruce_stairs[facing=west]")
        # Roof peak
        editor.execute("/fill 2 72 -1 7 72 8 spruce_slab[type=top]")
        editor.execute("/fill 2 73 -1 7 73 8 spruce_slab[type=bottom]")

        # Step 10: Stone Chimney
        print("Step 10: Building chimney...")
        editor.execute("/fill 8 65 5 8 75 6 cobblestone")
        editor.execute("/fill 8 66 5 8 73 6 air")
        editor.execute("/setblock 8 66 5 campfire")

        # Step 11: Decorative Touches
        print("Step 11: Adding decorative touches...")
        editor.execute("/fill 1 65 0 8 65 0 stripped_spruce_log[axis=x]")
        editor.execute("/setblock 3 65 -1 potted_fern")
        editor.execute("/setblock 6 65 -1 potted_spruce_sapling")
        editor.execute("/setblock 4 68 -1 lantern[hanging=false]")

        # Optional Enhancements
        print("Step 12: Adding interior furnishings...")
        editor.execute("/fill 2 68 2 7 68 5 lantern[hanging=true]")
        editor.execute("/setblock -1 65 3 oak_leaves[persistent=true]")
        editor.execute("/fill 4 64 -3 5 64 -1 gravel")
        editor.execute("/setblock 2 66 5 crafting_table")
        editor.execute("/setblock 7 66 5 red_bed[facing=west,part=head]")

        # Save changes
        print("\nSaving changes...")
        editor.save()

    print("✅ Cabin build complete!")
    print(f"   Open your world in Minecraft and go to coordinates X={BASE_X}, Y={BASE_Y}, Z={BASE_Z}")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python cabin_build.py <path_to_world>")
        print()
        print("Example:")
        print("  python cabin_build.py ~/minecraft/saves/MyWorld")
        print()
        print("Note: You need to create a flat Minecraft world first.")
        print("      In Minecraft: File > New World > More World Options > World Type: Flat")
        sys.exit(1)

    world_path = sys.argv[1]
    build_cabin(world_path)


if __name__ == "__main__":
    main()
