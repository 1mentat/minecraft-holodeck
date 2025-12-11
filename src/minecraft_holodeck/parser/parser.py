"""Command parser using Lark."""

from pathlib import Path

from lark import Lark, LarkError

from minecraft_holodeck.exceptions import CommandSyntaxError
from minecraft_holodeck.parser.ast import CommandAST, FillCommand, SetblockCommand
from minecraft_holodeck.parser.transformer import ASTTransformer


class CommandParser:
    """Parse Minecraft commands into AST."""

    def __init__(self) -> None:
        """Initialize parser with grammar."""
        grammar_path = Path(__file__).parent / "grammar.lark"
        self.parser = Lark(
            grammar_path.read_text(),
            parser='lalr',
            start='start'
        )
        self.transformer = ASTTransformer()

    def parse(self, command: str) -> CommandAST:
        """Parse command string into AST.

        Args:
            command: Command string (with or without leading /)

        Returns:
            CommandAST object (SetblockCommand or FillCommand)

        Raises:
            CommandSyntaxError: Invalid syntax
        """
        try:
            # Strip leading / if present
            cmd = command.lstrip('/')
            tree = self.parser.parse(cmd)
            result = self.transformer.transform(tree)
            # The transformer returns our AST types
            assert isinstance(result, (SetblockCommand, FillCommand))
            return result
        except LarkError as e:
            raise CommandSyntaxError(f"Invalid syntax: {e}") from e
