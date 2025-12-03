"""Lark transformer to convert parse tree to AST."""

from typing import Any

from lark import Transformer, Token
from minecraft_holodeck.parser.ast import (
    BlockSpec,
    Coordinate,
    FillCommand,
    Position,
    SetblockCommand,
)


class ASTTransformer(Transformer):  # type: ignore[type-arg]
    """Transform Lark parse tree to AST."""

    def coord(self, items: list[Token]) -> Coordinate:
        """Transform coordinate.

        Phase 1: Only absolute coordinates.
        """
        value = int(items[0])
        return Coordinate(value, relative=False)

    def position(self, items: list[Coordinate]) -> Position:
        """Transform position (3 coordinates)."""
        return Position(x=items[0], y=items[1], z=items[2])

    def state_value(self, items: list[Token]) -> str | int | bool:
        """Transform block state value."""
        if not items:
            # Should not happen with correct grammar
            raise ValueError("Empty state value")

        value = str(items[0])

        # Convert to appropriate type
        if value == "true":
            return True
        elif value == "false":
            return False
        elif value.lstrip("-+").isdigit():
            return int(value)
        else:
            return value

    def state_pair(self, items: list[Any]) -> tuple[str, str | int | bool]:
        """Transform state key=value pair."""
        key = str(items[0])
        value = items[1]
        return (key, value)

    def block_states(self, items: list[tuple[str, str | int | bool]]) -> dict[str, str | int | bool]:
        """Transform block states into a dictionary."""
        return dict(items)

    def block_spec(self, items: list[Any]) -> BlockSpec:
        """Transform block specification.

        Phase 2: Supports block states.
        """
        namespaced_id = str(items[0])

        # Check if it contains a colon
        if ":" in namespaced_id:
            namespace, block_id = namespaced_id.split(":", 1)
        else:
            # Implicit minecraft: namespace
            namespace = "minecraft"
            block_id = namespaced_id

        # Check for block states (optional)
        states = None
        if len(items) > 1 and isinstance(items[1], dict):
            states = items[1]

        return BlockSpec(namespace, block_id, states)

    def setblock_cmd(self, items: list[Any]) -> SetblockCommand:
        """Transform setblock command."""
        position = items[0]
        block = items[1]
        return SetblockCommand(position, block)

    def fill_cmd(self, items: list[Any]) -> FillCommand:
        """Transform fill command."""
        pos1 = items[0]
        pos2 = items[1]
        block = items[2]
        return FillCommand(pos1, pos2, block)
