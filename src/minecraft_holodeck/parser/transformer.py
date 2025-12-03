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

    def block_spec(self, items: list[Token]) -> BlockSpec:
        """Transform block specification.

        Phase 1: Just namespace:id
        """
        namespaced_id = str(items[0])

        # Check if it contains a colon
        if ":" in namespaced_id:
            namespace, block_id = namespaced_id.split(":", 1)
        else:
            # Implicit minecraft: namespace
            namespace = "minecraft"
            block_id = namespaced_id

        return BlockSpec(namespace, block_id)

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
