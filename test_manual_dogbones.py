#!/usr/bin/env python3
"""Test manual dog-bone position calculation"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "parts"))

from hamper import build_back_panel, build_side_panel, calculate_dogbone_positions_manual, HamperParams

print(f"Tool diameter: {HamperParams.tool_diameter}mm")
print(f"Dog-bone radius: {HamperParams.tool_diameter/2 + 0.1}mm")
print(f"Include bottom: {HamperParams.include_bottom}")

# Test back panel
print("\n" + "="*60)
print("BACK PANEL - Manual Calculation")
print("="*60)
back = build_back_panel()
drill_points = calculate_dogbone_positions_manual('back', back)
print(f"Total drill points: {len(drill_points)}")
for i, pt in enumerate(drill_points, 1):
    print(f"  {i}. X={pt.x:.2f}, Y={pt.y:.2f}, depth={pt.depth:.2f}mm, d={pt.diameter:.2f}mm")

# Test side panel (left)
print("\n" + "="*60)
print("SIDE PANEL - Manual Calculation")
print("="*60)
side = build_side_panel()
drill_points = calculate_dogbone_positions_manual('left', side)
print(f"Total drill points: {len(drill_points)}")
for i, pt in enumerate(drill_points, 1):
    print(f"  {i}. X={pt.x:.2f}, Y={pt.y:.2f}, depth={pt.depth:.2f}mm, d={pt.diameter:.2f}mm")
