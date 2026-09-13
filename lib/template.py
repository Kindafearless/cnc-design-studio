"""
Parametric Part Template for build123d
Copy this file to start a new part design.

Usage:
    1. Copy to parts/your_part_name.py
    2. Fill in metadata and parameters
    3. Implement build_part() function
    4. Run: python parts/your_part_name.py
    5. Check exports/ for STEP file
    6. Import STEP into Fusion 360 for CAM
"""

import sys
from pathlib import Path

# Add lib to path so we can import shapeoko config
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from build123d import *
from shapeoko import (
    MachineConstraints,
    Tolerances,
    StockSizes,
    check_part_fits,
    get_tool,
)

# ============================================================================
# METADATA
# ============================================================================
PART_NAME = "example_part"
PART_VERSION = "v1"
DESCRIPTION = "Description of what this part does"
MATERIAL = "plywood"  # plywood, hardwood, softwood, aluminum
STOCK_THICKNESS = 12.0  # mm

# ============================================================================
# PARAMETERS (all dimensions in mm)
# ============================================================================
class PartParams:
    """Parametric dimensions - modify these to generate variants"""

    # Overall dimensions
    length = 100.0
    width = 50.0
    height = 20.0

    # Features
    hole_diameter = 6.0
    corner_radius = 3.0

    # Tolerances
    clearance = Tolerances.CLEARANCE_FIT


# ============================================================================
# BUILD FUNCTION
# ============================================================================
def build_part() -> Part:
    """
    Construct the parametric part.
    Returns a build123d Part object.
    """

    # Example: simple box with rounded corners and mounting holes
    with BuildPart() as part:
        with BuildSketch() as sk:
            Rectangle(
                PartParams.length,
                PartParams.width
            )
            fillet(sk.vertices(), radius=PartParams.corner_radius)

        extrude(amount=PartParams.height)

        # Add mounting holes at corners
        with BuildSketch(part.faces().sort_by(Axis.Z)[-1]) as hole_sk:
            inset = 10.0
            with Locations(
                (PartParams.length/2 - inset, PartParams.width/2 - inset),
                (PartParams.length/2 - inset, -PartParams.width/2 + inset),
                (-PartParams.length/2 + inset, PartParams.width/2 - inset),
                (-PartParams.length/2 + inset, -PartParams.width/2 + inset),
            ):
                Circle(PartParams.hole_diameter / 2)

        extrude(amount=-PartParams.height, mode=Mode.SUBTRACT)

    return part.part


# ============================================================================
# VALIDATION & EXPORT
# ============================================================================
def validate_part(part: Part) -> bool:
    """Check part meets machine constraints"""
    bbox = part.bounding_box()

    length_x = bbox.max.X - bbox.min.X
    length_y = bbox.max.Y - bbox.min.Y
    height_z = bbox.max.Z - bbox.min.Z

    print(f"\nPart bounding box: {length_x:.1f} x {length_y:.1f} x {height_z:.1f} mm")

    fits = check_part_fits(length_x, length_y, height_z)
    if not fits:
        print("WARNING: Part exceeds machine safe working envelope!")
        return False

    print("Part fits in machine envelope ✓")
    return True


def export_step(part: Part, output_dir: Path = None):
    """Export part to STEP file for Fusion 360 import"""
    from build123d import export_step as bd_export

    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "exports"

    output_dir.mkdir(exist_ok=True)

    filename = f"{PART_NAME}_{PART_VERSION}.step"
    filepath = output_dir / filename

    bd_export(part, str(filepath))
    print(f"\nExported: {filepath}")
    print(f"Import this STEP file into Fusion 360 for CAM.")


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    print(f"Building {PART_NAME} {PART_VERSION}")
    print(f"Material: {MATERIAL}, Stock: {STOCK_THICKNESS}mm")
    print(f"Description: {DESCRIPTION}")

    # Build the part
    part = build_part()

    # Validate it fits the machine
    if validate_part(part):
        # Export to STEP
        export_step(part)

        # Optional: show in ocp-vscode if running in VS Code
        try:
            show_object(part, name=PART_NAME)
            print("\nPart preview available in ocp-vscode panel")
        except Exception:
            print("\nRun in VS Code with ocp-vscode for live 3D preview")

    print("\n" + "="*60)
    print("Next steps:")
    print("  1. Import STEP file into Fusion 360")
    print("  2. Set up CAM toolpaths (use tools from lib/shapeoko.py)")
    print("  3. Post-process for Shapeoko")
    print("  4. Run in Carbide Motion")
    print("="*60)
