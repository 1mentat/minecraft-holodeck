"""Exception classes for minecraft-holodeck."""


class MCCommandError(Exception):
    """Base exception for all minecraft command errors."""
    pass


class CommandSyntaxError(MCCommandError):
    """Raised when command syntax is invalid."""
    pass


class BlockValidationError(MCCommandError):
    """Raised when block specification is invalid."""
    pass


class WorldOperationError(MCCommandError):
    """Raised when world file operation fails."""
    pass


class ChunkNotFoundError(WorldOperationError):
    """Raised when attempting to modify non-existent chunk."""
    pass
