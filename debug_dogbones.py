#!/usr/bin/env python3
"""
Debug script to inspect dog-bone geometry in hamper parts
"""
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "parts"))
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from hamper import build_back_panel, build_front_panel, build_side_panel, HamperParams
from build123d import Axis

def inspect_part(part_name, part):
    """Inspect a part's geometry to find all holes"""
    print(f"\n{'='*60}")
    print(f"Inspecting {part_name}")
    print(f"{'='*60}")

    # Get the top face
    try:
        top_face = part.faces().sort_by(Axis.Z)[-1]
        print(f"Top face found: {top_face}")

        # Count inner wires (holes)
        inner_wires = list(top_face.inner_wires())
        print(f"\nTotal inner wires (holes): {len(inner_wires)}")

        # Inspect each wire
        for i, wire in enumerate(inner_wires, 1):
            edges = wire.edges()
            print(f"\nWire {i}:")
            print(f"  Number of edges: {len(edges)}")

            # If single edge, check if circular
            if len(edges) == 1:
                edge = edges[0]
                print(f"  Edge type: {type(edge)}")

                # Check for radius attribute
                if hasattr(edge, 'radius'):
                    radius = edge.radius  # Property, not method!
                    diameter = radius * 2
                    center = edge.center()
                    print(f"  ✓ Circular edge detected:")
                    print(f"    - Radius: {radius:.3f}mm")
                    print(f"    - Diameter: {diameter:.3f}mm")
                    print(f"    - Center: ({center.X:.2f}, {center.Y:.2f}, {center.Z:.2f})")
                else:
                    print(f"  ✗ Not a circular edge (no radius attribute)")
            else:
                print(f"  Multi-edge wire (likely rectangular hole)")
                # Try to identify what this is
                bbox = wire.bounding_box()
                width = bbox.max.X - bbox.min.X
                height = bbox.max.Y - bbox.min.Y
                print(f"  Bounding box: {width:.1f} x {height:.1f}mm")

    except Exception as e:
        print(f"Error inspecting {part_name}: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("Dog-Bone Geometry Debug Tool")
    print("="*60)
    print(f"Tool diameter: {HamperParams.tool_diameter}mm")
    print(f"Dog-bone diameter: {(HamperParams.tool_diameter/2 + 0.1) * 2:.3f}mm")
    print(f"Include bottom: {HamperParams.include_bottom}")

    # Build and inspect each panel type
    print("\n\nBuilding panels...")

    back = build_back_panel()
    inspect_part("BACK PANEL", back)

    front = build_front_panel()
    inspect_part("FRONT PANEL", front)

    side = build_side_panel()
    inspect_part("SIDE PANEL", side)

    print("\n\n" + "="*60)
    print("Debug complete!")
    print("="*60)

if __name__ == "__main__":
    main()
