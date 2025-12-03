"""Convert BlockSpec to Amulet Block objects."""

from amulet.api.block import Block  # type: ignore[import-untyped]

from minecraft_holodeck.parser.ast import BlockSpec


def blockspec_to_amulet(spec: BlockSpec) -> Block:
    """Convert our BlockSpec to Amulet Block object.

    Phase 2: Supports block states.

    Args:
        spec: Parsed block specification

    Returns:
        Amulet Block object ready for world placement
    """
    # If there are no block states, create simple block
    if not spec.states:
        return Block(spec.namespace, spec.block_id)

    # Convert block states to Amulet properties format
    # Amulet expects all property values as strings
    properties = {}
    for key, value in spec.states.items():
        # Convert booleans and integers to lowercase strings
        if isinstance(value, bool):
            properties[key] = str(value).lower()
        else:
            properties[key] = str(value)

    # Create block with properties
    return Block(spec.namespace, spec.block_id, properties)
