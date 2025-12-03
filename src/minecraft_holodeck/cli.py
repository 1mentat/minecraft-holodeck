"""Command-line interface for minecraft-holodeck."""

import sys

import click

from minecraft_holodeck.api import WorldEditor
from minecraft_holodeck.exceptions import MCCommandError


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
    from minecraft_holodeck.parser import CommandParser
    import json
    from dataclasses import asdict

    parser = CommandParser()
    try:
        ast = parser.parse(command)
        click.echo(json.dumps(asdict(ast), indent=2))
    except MCCommandError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
