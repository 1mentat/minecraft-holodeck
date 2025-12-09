#!/bin/bash
# Example: Building a Small Village with Multiple Cabins
# This demonstrates how relative coordinates make structures reusable

# First, convert the cabin to relative coordinates (if not already done)
# mccommand convert-to-relative scripts/cabin_build.txt

WORLD="./my_world"
CABIN_SCRIPT="scripts/cabin_build_relative.txt"

echo "Building a small village with 5 cabins..."

# Place cabin #1 at origin
echo "Placing cabin #1 at (0, 64, 0)..."
mccommand batch "$WORLD" "$CABIN_SCRIPT" --origin -1,64,-3

# Place cabin #2 - 20 blocks east
echo "Placing cabin #2 at (20, 64, 0) - 20 blocks east..."
mccommand batch "$WORLD" "$CABIN_SCRIPT" --origin 19,64,-3

# Place cabin #3 - 40 blocks east
echo "Placing cabin #3 at (40, 64, 0) - 40 blocks east..."
mccommand batch "$WORLD" "$CABIN_SCRIPT" --origin 39,64,-3

# Place cabin #4 - 15 blocks north of cabin #1
echo "Placing cabin #4 at (0, 64, 15) - 15 blocks north..."
mccommand batch "$WORLD" "$CABIN_SCRIPT" --origin -1,64,12

# Place cabin #5 - 20 blocks east, 15 blocks north
echo "Placing cabin #5 at (20, 64, 15) - diagonal position..."
mccommand batch "$WORLD" "$CABIN_SCRIPT" --origin 19,64,12

echo "✓ Village complete! 5 cabins placed."
echo ""
echo "The same cabin script was reused 5 times at different positions!"
echo "This is the power of relative coordinates."
