"""Command-line interface for minecraft-holodeck."""

import sys

import click

from minecraft_holodeck.api import WorldEditor
from minecraft_holodeck.converter import ScriptConverter
from minecraft_holodeck.exceptions import MCCommandError
from minecraft_holodeck.world import create_flat_world, create_void_world


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """Minecraft world modification tool.

    Execute /setblock and /fill commands on Minecraft Java Edition worlds.
    """
    pass


@main.command()
@click.argument("world_path", type=click.Path(exists=True))
@click.argument("command")
@click.option("--origin", default="0,0,0", help="Origin for relative coords (x,y,z)")
@click.option("--dry-run", is_flag=True, help="Parse but don't execute")
def execute(world_path: str, command: str, origin: str, dry_run: bool) -> None:
    """Execute a single command on a world.

    Examples:

        mccommand execute ./my_world "/setblock 0 64 0 minecraft:stone"

        mccommand execute ./my_world "/fill 0 0 0 10 10 10 minecraft:glass"
    """
    # Parse origin
    try:
        origin_tuple = tuple(map(int, origin.split(",")))
        if len(origin_tuple) != 3:
            raise ValueError("Origin must be three integers")
    except ValueError as e:
        click.echo(f"Error: Invalid origin format: {e}", err=True)
        sys.exit(1)

    if dry_run:
        # Just parse and show AST
        from minecraft_holodeck.parser import CommandParser
        parser = CommandParser()
        try:
            ast = parser.parse(command)
            click.echo(f"Parsed successfully: {ast}")
        except MCCommandError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        return

    # Execute command
    try:
        with WorldEditor(world_path, origin_tuple) as editor:
            count = editor.execute(command)
            editor.save()
            click.echo(f"✓ Modified {count} blocks")
    except MCCommandError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("world_path", type=click.Path(exists=True))
@click.argument("commands_file", type=click.File("r"))
@click.option("--origin", default="0,0,0", help="Origin for relative coords (x,y,z)")
def batch(world_path: str, commands_file: click.File, origin: str) -> None:
    """Execute multiple commands from a file.

    File format: one command per line, # for comments

    Example:

        mccommand batch ./my_world commands.txt
    """
    # Parse origin
    try:
        origin_tuple = tuple(map(int, origin.split(",")))
        if len(origin_tuple) != 3:
            raise ValueError("Origin must be three integers")
    except ValueError as e:
        click.echo(f"Error: Invalid origin format: {e}", err=True)
        sys.exit(1)

    total = 0
    errors = 0

    try:
        with WorldEditor(world_path, origin_tuple) as editor:
            for i, line in enumerate(commands_file, 1):  # type: ignore[arg-type,var-annotated]
                line_str = str(line).strip()
                if not line_str or line_str.startswith("#"):
                    continue

                try:
                    count = editor.execute(line_str)
                    total += count
                    click.echo(f"Line {i}: {count} blocks")
                except MCCommandError as e:
                    click.echo(f"Line {i} error: {e}", err=True)
                    errors += 1

            editor.save()

        click.echo(f"\n✓ Total: {total} blocks modified")
        if errors:
            click.echo(f"⚠ {errors} commands failed", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("command")
def parse(command: str) -> None:
    """Parse a command and show the AST (for debugging).

    Example:

        mccommand parse "/setblock 0 64 0 minecraft:stone"
    """
    import json
    from dataclasses import asdict

    from minecraft_holodeck.parser import CommandParser

    parser = CommandParser()
    try:
        ast = parser.parse(command)
        click.echo(json.dumps(asdict(ast), indent=2))
    except MCCommandError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("world_path", type=click.Path())
@click.option(
    "--size",
    default="8,8",
    help="Size in chunks (x,z). Each chunk is 16x16 blocks. Default: 8,8 (128x128 blocks)",
)
@click.option(
    "--layers",
    help=(
        'Layers as "block:thickness,block:thickness". '
        'Example: "bedrock:1,stone:10,dirt:3,grass_block:1"'
    ),
)
@click.option("--name", help="World name (defaults to folder name)")
def create_flat(world_path: str, size: str, layers: str | None, name: str | None) -> None:
    """Create a new flat world.

    Creates a flat Minecraft world with customizable layers.

    Examples:

        # Create default flat world (8x8 chunks = 128x128 blocks)
        mccommand create-flat ./my_world

        # Create larger world
        mccommand create-flat ./my_world --size 16,16

        # Custom layers
        mccommand create-flat ./my_world --layers "bedrock:1,stone:10,dirt:3,grass_block:1"

        # With custom name
        mccommand create-flat ./my_world --name "My Test World"
    """
    # Parse size
    try:
        size_parts = size.split(",")
        if len(size_parts) != 2:
            raise ValueError("Size must be x,z")
        size_chunks = (int(size_parts[0]), int(size_parts[1]))
    except ValueError as e:
        click.echo(f"Error: Invalid size format: {e}", err=True)
        sys.exit(1)

    # Parse layers if provided
    layer_list = None
    if layers:
        try:
            layer_list = []
            for layer_spec in layers.split(","):
                block, thickness = layer_spec.split(":")
                layer_list.append((block.strip(), int(thickness)))
        except ValueError as e:
            click.echo(f"Error: Invalid layers format: {e}", err=True)
            sys.exit(1)

    # Create world
    try:
        click.echo(f"Creating flat world at {world_path}...")
        create_flat_world(
            world_path,
            size_chunks=size_chunks,
            layers=layer_list,
            name=name,
        )
        blocks_x = size_chunks[0] * 16
        blocks_z = size_chunks[1] * 16
        click.echo(f"✓ World created successfully ({blocks_x}x{blocks_z} blocks)")
    except MCCommandError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("world_path", type=click.Path())
@click.option(
    "--size",
    default="4,4",
    help="Size in chunks (x,z). Default: 4,4 (64x64 blocks)",
)
@click.option(
    "--spawn-platform/--no-spawn-platform",
    default=True,
    help="Create a 3x3 stone spawn platform at y=64",
)
@click.option("--name", help="World name (defaults to folder name)")
def create_void(
    world_path: str, size: str, spawn_platform: bool, name: str | None
) -> None:
    """Create a void world (empty world).

    Useful for testing or creative building in isolation.

    Examples:

        # Create void world with spawn platform
        mccommand create-void ./void_world

        # Create void world without spawn platform
        mccommand create-void ./void_world --no-spawn-platform

        # Larger void world
        mccommand create-void ./void_world --size 8,8
    """
    # Parse size
    try:
        size_parts = size.split(",")
        if len(size_parts) != 2:
            raise ValueError("Size must be x,z")
        size_chunks = (int(size_parts[0]), int(size_parts[1]))
    except ValueError as e:
        click.echo(f"Error: Invalid size format: {e}", err=True)
        sys.exit(1)

    # Create world
    try:
        click.echo(f"Creating void world at {world_path}...")
        create_void_world(
            world_path,
            size_chunks=size_chunks,
            spawn_platform=spawn_platform,
            name=name,
        )
        blocks_x = size_chunks[0] * 16
        blocks_z = size_chunks[1] * 16
        click.echo(f"✓ Void world created successfully ({blocks_x}x{blocks_z} blocks)")
    except MCCommandError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", help="Output file (default: adds _relative suffix)")
@click.option(
    "--base",
    help="Base point for relative coords (x,y,z). Default: auto-detect from min coords",
)
@click.option(
    "--no-auto-detect",
    is_flag=True,
    help="Don't auto-detect base point, use 0,0,0 instead",
)
def convert_to_relative(
    input_file: str, output: str | None, base: str | None, no_auto_detect: bool
) -> None:
    """Convert absolute coordinate script to relative coordinates.

    Takes a build script with absolute coordinates and converts it to use
    relative coordinates (~), making it position-independent.

    Examples:

        # Auto-detect base point from minimum coordinates
        mccommand convert-to-relative cabin_build.txt

        # Specify explicit base point
        mccommand convert-to-relative cabin_build.txt --base 0,64,0

        # Custom output filename
        mccommand convert-to-relative cabin_build.txt -o cabin_relative.txt
    """
    from pathlib import Path

    input_path = Path(input_file)

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        # Add _relative suffix before extension
        stem = input_path.stem
        suffix = input_path.suffix
        output_path = input_path.parent / f"{stem}_relative{suffix}"

    # Parse base point if provided
    base_point = None
    if base:
        try:
            parts = base.split(",")
            if len(parts) != 3:
                raise ValueError("Base must be x,y,z")
            base_point = (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError as e:
            click.echo(f"Error: Invalid base format: {e}", err=True)
            sys.exit(1)

    # Convert script
    try:
        converter = ScriptConverter()
        click.echo(f"Converting {input_path} to relative coordinates...")

        detected_base = converter.convert_file(
            input_path,
            output_path,
            base_point=base_point,
            auto_detect=not no_auto_detect,
        )

        click.echo(f"✓ Converted successfully")
        click.echo(f"  Base point: {detected_base[0]}, {detected_base[1]}, {detected_base[2]}")
        click.echo(f"  Output: {output_path}")
        click.echo(f"\nUsage:")
        click.echo(
            f"  mccommand batch world {output_path} --origin {detected_base[0]},{detected_base[1]},{detected_base[2]}"
        )

    except MCCommandError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
