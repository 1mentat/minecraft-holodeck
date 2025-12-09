#!/usr/bin/env python3
"""Examples of creating Minecraft worlds programmatically.

This script demonstrates how to create different types of worlds using
the minecraft-holodeck library.
"""

from minecraft_holodeck import create_flat_world, create_void_world, WorldEditor
from amulet.api.block import Block  # type: ignore[import-untyped]


def example_1_basic_flat_world():
    """Create a basic flat world with default settings."""
    print("Example 1: Creating a basic flat world...")

    create_flat_world(
        "./example_flat_world",
        size_chunks=(8, 8),  # 128x128 blocks
        name="Basic Flat World"
    )

    print("✓ Created: ./example_flat_world")
    print("  - Size: 128x128 blocks (8x8 chunks)")
    print("  - Layers: bedrock, stone, dirt, grass_block (default)")


def example_2_custom_layers():
    """Create a flat world with custom layers."""
    print("\nExample 2: Creating a flat world with custom layers...")

    create_flat_world(
        "./example_custom_layers",
        size_chunks=(16, 16),  # 256x256 blocks
        layers=[
            ("bedrock", 1),
            ("stone", 10),
            ("sandstone", 3),
            ("sand", 2),
        ],
        name="Desert Flat World"
    )

    print("✓ Created: ./example_custom_layers")
    print("  - Size: 256x256 blocks (16x16 chunks)")
    print("  - Layers: bedrock(1), stone(10), sandstone(3), sand(2)")


def example_3_void_world():
    """Create a void world with spawn platform."""
    print("\nExample 3: Creating a void world with spawn platform...")

    create_void_world(
        "./example_void_world",
        size_chunks=(8, 8),
        spawn_platform=True,
        name="The Void"
    )

    print("✓ Created: ./example_void_world")
    print("  - Size: 128x128 blocks (8x8 chunks)")
    print("  - Spawn platform: 3x3 stone platform at spawn point")


def example_4_create_and_build():
    """Create a world and immediately build in it."""
    print("\nExample 4: Creating a world and building a structure...")

    # Create a flat world
    create_flat_world(
        "./example_build_world",
        size_chunks=(8, 8),
        name="Build Example"
    )

    # Build a simple structure
    with WorldEditor("./example_build_world") as editor:
        # Build a 5x5x5 glass cube
        editor.execute("/fill 0 65 0 4 69 4 minecraft:glass hollow")

        # Add a door
        editor.execute("/setblock 2 65 0 minecraft:oak_door[half=lower]")
        editor.execute("/setblock 2 66 0 minecraft:oak_door[half=upper]")

        # Add some interior lighting
        editor.execute("/setblock 2 67 2 minecraft:glowstone")

        editor.save()

    print("✓ Created: ./example_build_world")
    print("  - Built a 5x5x5 glass cube with a door and lighting")


def example_5_superflat_template():
    """Create a superflat world similar to Minecraft's classic superflat."""
    print("\nExample 5: Creating Minecraft-style superflat world...")

    create_flat_world(
        "./example_superflat",
        size_chunks=(16, 16),
        layers=[
            ("bedrock", 1),
            ("dirt", 2),
            ("grass_block", 1),
        ],
        name="Classic Superflat"
    )

    print("✓ Created: ./example_superflat")
    print("  - Matches Minecraft's classic superflat preset")


def example_6_building_plot():
    """Create a void world and add a building platform."""
    print("\nExample 6: Creating a creative building plot...")

    # Create void world without platform
    create_void_world(
        "./example_building_plot",
        size_chunks=(8, 8),
        spawn_platform=False,  # We'll create our own
        name="Building Plot"
    )

    # Add a large building platform
    with WorldEditor("./example_building_plot") as editor:
        # Create a 64x64 stone platform at y=64
        editor.execute("/fill -32 64 -32 31 64 31 minecraft:stone")

        # Add a border
        editor.execute("/fill -32 64 -32 31 64 31 minecraft:quartz_block outline")

        # Add some lighting posts
        for x in range(-24, 32, 16):
            for z in range(-24, 32, 16):
                editor.execute(f"/setblock {x} 65 {z} minecraft:oak_fence")
                editor.execute(f"/setblock {x} 66 {z} minecraft:lantern[hanging=false]")

        editor.save()

    print("✓ Created: ./example_building_plot")
    print("  - 64x64 building platform with decorative border")
    print("  - Corner lighting posts with lanterns")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Minecraft World Creation Examples")
    print("=" * 60)

    examples = [
        ("Basic Flat World", example_1_basic_flat_world),
        ("Custom Layers", example_2_custom_layers),
        ("Void World", example_3_void_world),
        ("Create and Build", example_4_create_and_build),
        ("Superflat Template", example_5_superflat_template),
        ("Building Plot", example_6_building_plot),
    ]

    print("\nSelect an example to run:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print(f"  {len(examples) + 1}. Run all examples")
    print("  0. Exit")

    try:
        choice = input("\nEnter your choice (0-7): ").strip()
        choice_num = int(choice)

        if choice_num == 0:
            print("Exiting...")
            return
        elif choice_num == len(examples) + 1:
            # Run all examples
            for name, example_func in examples:
                example_func()
                print()
        elif 1 <= choice_num <= len(examples):
            # Run selected example
            examples[choice_num - 1][1]()
        else:
            print("Invalid choice. Please enter a number between 0 and 7.")
            return

        print("\n" + "=" * 60)
        print("Done! You can now open these worlds in Minecraft.")
        print("\nTo open in Minecraft:")
        print("1. Copy the world folder to ~/.minecraft/saves/")
        print("2. Launch Minecraft and select the world")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure minecraft-holodeck is installed:")
        print("  cd /path/to/minecraft-holodeck")
        print("  uv sync --all-extras")


if __name__ == "__main__":
    main()
