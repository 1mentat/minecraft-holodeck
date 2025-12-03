"""Convert BlockSpec to Amulet Block objects."""

from amulet.api.block import Block  # type: ignore[import-untyped]

from minecraft_holodeck.parser.ast import BlockSpec


def blockspec_to_amulet(spec: BlockSpec) -> Block:
    """Convert our BlockSpec to Amulet Block object.

    Phase 1: Simple conversion without block states.

    Args:
        spec: Parsed block specification

    Returns:
        Amulet Block object ready for world placement
    """
    # Create basic block without properties
    # Phase 1: No block states yet
    return Block(spec.namespace, spec.block_id)
