#!/usr/bin/env python3
"""
Quick verification script to test CNC project setup.
Run this to verify lib/shapeoko.py is working correctly.

Usage:
    python verify_setup.py
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

try:
    from shapeoko import (
        MachineConstraints,
        Tolerances,
        StockSizes,
        TOOL_LIBRARY,
        CuttingParams,
        check_part_fits,
        get_tool,
        list_tools,
        ToolType,
    )

    print("="*60)
    print("CNC PROJECT SETUP VERIFICATION")
    print("="*60)

    # Test 1: Machine constraints
    print("\n✓ Machine Configuration:")
    print(f"  Work area: {MachineConstraints.X_TRAVEL} x {MachineConstraints.Y_TRAVEL} x {MachineConstraints.Z_TRAVEL} mm")
    print(f"  Spindle: {MachineConstraints.SPINDLE_MIN_RPM} - {MachineConstraints.SPINDLE_MAX_RPM} RPM")
    print(f"  Power: {MachineConstraints.SPINDLE_POWER_W}W")

    # Test 2: Tolerances
    print("\n✓ Tolerances:")
    print(f"  Clearance fit: {Tolerances.CLEARANCE_FIT}mm")
    print(f"  Press fit: {Tolerances.PRESS_FIT}mm")

    # Test 3: Stock sizes
    print("\n✓ Stock Sizes:")
    print(f"  Plywood sheet (half): {StockSizes.PLYWOOD_HALF}")
    print(f"  Plywood thicknesses: {StockSizes.PLY_THICKNESSES}")

    # Test 4: Tool library
    print("\n✓ Tool Library:")
    print(f"  Total tools: {len(TOOL_LIBRARY)}")
    for key, tool in list(TOOL_LIBRARY.items())[:3]:
        print(f"  - {key}: {tool.name} ({tool.diameter}mm)")

    # Test 5: Cutting params
    print("\n✓ Cutting Parameters:")
    rpm, feed, doc, stepover = CuttingParams.get_params("plywood", 6.35)
    print(f"  Plywood with 6.35mm tool: {rpm} RPM, {feed} mm/min, DOC {doc}mm")

    # Test 6: Part fit check
    print("\n✓ Part Fit Validation:")
    test_fits = check_part_fits(1000, 1000, 50)
    print(f"  1000x1000x50mm part fits: {test_fits}")

    # Test 7: Tool lookup
    print("\n✓ Tool Lookup:")
    tool = get_tool("em_6mm_2f")
    print(f"  em_6mm_2f: {tool.name}, {tool.flutes} flutes, {tool.material}")

    # Test 8: List endmills
    print("\n✓ Available Endmills:")
    endmills = list_tools(ToolType.ENDMILL)
    print(f"  Count: {len(endmills)}")

    print("\n" + "="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60)
    print("\nNext steps:")
    print("  1. Install dependencies: poetry install")
    print("  2. Run the hamper example: poetry run python parts/hamper.py")
    print("  3. Check exports/ for generated STEP file")
    print("="*60)

except ImportError as e:
    print(f"\n❌ ERROR: Failed to import shapeoko module")
    print(f"Details: {e}")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
