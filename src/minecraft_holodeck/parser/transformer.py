"""Lark transformer to convert parse tree to AST."""

from typing import Any, Literal, cast

from lark import Token, Transformer

from minecraft_holodeck.parser.ast import (
    BlockSpec,
    Coordinate,
    FillCommand,
    Position,
    SetblockCommand,
)


class ASTTransformer(Transformer):  # type: ignore[type-arg]
    """Transform Lark parse tree to AST."""

    def abs_coord(self, items: list[Token]) -> Coordinate:
        """Transform absolute coordinate.

        Grammar: abs_coord -> SIGNED_INT
        Items: [number_token]
        """
        value = int(items[0])
        return Coordinate(value, relative=False)

    def rel_coord(self, items: list[Token]) -> Coordinate:
        """Transform relative coordinate.

        Grammar: rel_coord -> "~" SIGNED_INT?
        Items: [] (for ~) or [number_token] (for ~N)
        Note: Lark doesn't include literal "~" in items
        """
        if len(items) == 0:
            # Just ~, means offset 0
            return Coordinate(0, relative=True)
        else:
            # ~N, means offset N
            value = int(items[0])
            return Coordinate(value, relative=True)

    def coord(self, items: list[Coordinate]) -> Coordinate:
        """Pass through coordinate (abs_coord or rel_coord already transformed).

        Grammar: coord -> abs_coord | rel_coord
        Items: [Coordinate] (already transformed by abs_coord or rel_coord)
        """
        return items[0]

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

    def block_states(
        self, items: list[tuple[str, str | int | bool]]
    ) -> dict[str, str | int | bool]:
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
        """Transform fill command.

        Phase 3: Added support for optional fill mode parameter.
        """
        pos1 = items[0]
        pos2 = items[1]
        block = items[2]
        # Mode is a Token if present, need to convert to string and cast to Literal
        mode_str = str(items[3]) if len(items) > 3 else "replace"
        mode = cast(Literal["replace", "destroy", "hollow", "keep", "outline"], mode_str)
        return FillCommand(pos1, pos2, block, mode)
