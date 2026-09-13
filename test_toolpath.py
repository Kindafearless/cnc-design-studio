#!/usr/bin/env python3
"""Test toolpath generation for hamper parts"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "parts"))
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from hamper import build_side_panel, get_hamper_operations, HamperParams
from cam import generate_sequenced_operations

print("=" * 60)
print("TESTING TOOLPATH GENERATION")
print("=" * 60)
print(f"Tool diameter: {HamperParams.tool_diameter}mm")
print(f"Include bottom: {HamperParams.include_bottom}")
print(f"Add dog-bones: {HamperParams.add_dogbone_fillets}")

# Build the side panel
print("\nBuilding right panel...")
side = build_side_panel()
bbox = side.bounding_box()
print(f"  Bounding box: X({bbox.min.X:.1f} to {bbox.max.X:.1f}), Y({bbox.min.Y:.1f} to {bbox.max.Y:.1f}), Z({bbox.min.Z:.1f} to {bbox.max.Z:.1f})")

# Get operations
print("\nGetting operations...")
operations = get_hamper_operations('right', side)
print(f"  Number of operations: {len(operations)}")
for i, op in enumerate(operations, 1):
    print(f"  {i}. {op.name} ({op.op_type.value})")
    if op.op_type.value == 'drill':
        print(f"     Drill points: {len(op.drill_points) if hasattr(op, 'drill_points') and op.drill_points else 0}")
        if hasattr(op, 'drill_points') and op.drill_points:
            print(f"     First point: X={op.drill_points[0].x:.2f}, Y={op.drill_points[0].y:.2f}, depth={op.drill_points[0].depth:.2f}mm")
    if op.op_type.value == 'contour':
        print(f"     Contours: {len(op.contours) if hasattr(op, 'contours') and op.contours else 0}")

# Generate G-code
print("\nGenerating G-code...")
try:
    result = generate_sequenced_operations(operations)
    gcode = result['gcode']
    print(f"  G-code length: {len(gcode)} characters")
    print(f"  G-code lines: {len(gcode.splitlines())} lines")
    print(f"  Operations in result: {result.get('total_operations', 0)}")

    # Show first few lines
    print("\nFirst 30 lines of G-code:")
    for i, line in enumerate(gcode.splitlines()[:30], 1):
        print(f"    {i:3d}: {line}")

except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete!")
