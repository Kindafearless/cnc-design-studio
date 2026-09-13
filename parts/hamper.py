"""
Clothes Hamper - Tall plywood box with finger joints
A parametric tall and thin clothes hamper with finger-jointed sides.

Design features:
- Four plywood panels (front, back, left, right) with finger joints
- Optional bottom panel with slots for assembly
- Decorative handle cutouts on sides
- Parametric sizing for material thickness and dimensions
- All parts designed for flat CNC cutting and assembly
"""

import sys
from pathlib import Path
from math import floor
from typing import Optional

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from build123d import Part, Compound, BuildPart, BuildSketch, Rectangle, RectangleRounded, Ellipse, Circle, Box, Locations, Location, Mode, extrude, fillet, Axis
from shapeoko import (
    MachineConstraints,
    Tolerances,
    StockSizes,
    check_part_fits,
    get_tool,
)

# Import CAM operation types
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from cam import Operation, OperationType, DrillPoint, extract_contours, extract_drill_points

# ============================================================================
# METADATA
# ============================================================================
PART_NAME = "clothes_hamper"
PART_VERSION = "v1"
DESCRIPTION = "Tall plywood clothes hamper with finger joints"
MATERIAL = "plywood"
STOCK_THICKNESS = 12.0  # mm (1/2" plywood)

# ============================================================================
# PARAMETERS (all dimensions in mm)
# ============================================================================
class HamperParams:
    """Parametric dimensions for the hamper"""

    # Overall dimensions (exterior)
    width = 400.0      # X dimension (front-to-back)
    depth = 300.0      # Y dimension (side-to-side)
    height = 600.0     # Z dimension (tall hamper)

    # Material
    thickness = 12.0   # Plywood thickness

    # Finger joint parameters
    finger_width = 25.0        # Width of each finger
    clearance = 0.15           # Joint clearance for assembly (mm)

    # Tool parameters for corner relief
    tool_diameter = 6.35       # 1/4" endmill diameter (mm)
    add_dogbone_fillets = True # Add dog-bone fillets to internal corners for tool clearance

    # Handle cutouts (decorative oval holes on front/back)
    handle_width = 120.0
    handle_height = 40.0
    handle_from_top = 100.0    # Distance from top edge

    # Bottom panel
    include_bottom = True
    bottom_slot_depth = 6.0    # How deep the bottom slots into side panels

    # Corner radius (soften sharp corners)
    corner_radius = 3.0


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


# ============================================================================
# PANEL BUILDER FUNCTIONS
# ============================================================================
def build_front_panel() -> Part:
    """
    Front panel with handle cutout and finger joints on sides.
    Dimensions: width (X) x height (Z)
    """
    p = HamperParams

    with BuildPart() as panel:
        # Base rectangle - no corner rounding for clean CNC cutting
        with BuildSketch() as sk:
            Rectangle(p.width, p.height)

            # Handle cutout (centered horizontally, offset from top) - straight edges
            with Locations((0, p.height/2 - p.handle_from_top)):
                Rectangle(p.handle_width, p.handle_height, mode=Mode.SUBTRACT)

        extrude(amount=p.thickness)

        # Add finger joints on left and right edges (5 fingers each side)
        # Panel is on XY plane: X = width, Y = height, Z = thickness
        # Left edge: fingers protruding in -X direction along Y (height)
        num_fingers = 5
        finger_length = p.height / num_fingers
        for i in range(num_fingers):
            if i % 2 == 0:  # Odd pattern - start and end with finger
                y_pos = -p.height/2 + i * finger_length + finger_length/2
                with Locations((-p.width/2 - p.thickness/2, y_pos, p.thickness/2)):
                    Box(p.thickness, finger_length, p.thickness, mode=Mode.ADD)

        # Right edge: fingers protruding in +X direction along Y (height)
        for i in range(num_fingers):
            if i % 2 == 0:  # Same pattern
                y_pos = -p.height/2 + i * finger_length + finger_length/2
                with Locations((p.width/2 + p.thickness/2, y_pos, p.thickness/2)):
                    Box(p.thickness, finger_length, p.thickness, mode=Mode.ADD)

        # Add slots on bottom edge for bottom panel fingers (3 slots)
        num_slots = 3
        slot_length = p.width / num_slots
        for i in range(num_slots):
            if i % 2 == 1:  # Gaps at odd indices
                x_pos = -p.width/2 + i * slot_length + slot_length/2
                with Locations((x_pos, -p.height/2, p.thickness/2)):
                    Box(slot_length, p.thickness + p.clearance, p.thickness, mode=Mode.SUBTRACT)

                # Dog-bone fillets are added during machining (not in CAD geometry)
                # The toolpath generation will calculate and drill them at the correct positions

    return panel.part


def build_back_panel() -> Part:
    """
    Back panel with handle cutout and finger joints on sides.
    Identical to front panel.
    """
    return build_front_panel()


def build_side_panel() -> Part:
    """
    Side panel with slots to accept finger joints from front/back/bottom panels.
    Dimensions: depth (Y) x height (Z)
    """
    p = HamperParams

    with BuildPart() as panel:
        # Base rectangle - no corner rounding for clean CNC cutting
        with BuildSketch() as sk:
            Rectangle(p.depth, p.height)

        extrude(amount=p.thickness)

        # Add slots on front and back edges to accept fingers (5 slots each)
        # Panel is on XY plane: X = depth, Y = height, Z = thickness
        num_slots = 5
        slot_length = p.height / num_slots

        # Front edge: slots to accept front panel fingers (along Y/height at front X edge)
        for i in range(num_slots):
            if i % 2 == 0:  # Slots at even indices (complementary to fingers)
                y_pos = -p.height/2 + i * slot_length + slot_length/2
                with Locations((-p.depth/2, y_pos, p.thickness/2)):
                    Box(p.thickness + p.clearance, slot_length, p.thickness, mode=Mode.SUBTRACT)

                # Dog-bone fillets are added during machining (not in CAD geometry)
                # The toolpath generation will calculate and drill them at the correct positions

        # Back edge: slots to accept back panel fingers (along Y/height at back X edge)
        for i in range(num_slots):
            if i % 2 == 0:  # Same pattern
                y_pos = -p.height/2 + i * slot_length + slot_length/2
                with Locations((p.depth/2, y_pos, p.thickness/2)):
                    Box(p.thickness + p.clearance, slot_length, p.thickness, mode=Mode.SUBTRACT)

                # Dog-bone fillets are added during machining (not in CAD geometry)
                # The toolpath generation will calculate and drill them at the correct positions

        # Bottom edge: slots to accept bottom panel fingers (3 slots along X/depth)
        if p.include_bottom:
            num_bottom_slots = 3
            bottom_slot_length = p.depth / num_bottom_slots
            for i in range(num_bottom_slots):
                if i % 2 == 1:  # Gaps at odd indices
                    x_pos = -p.depth/2 + i * bottom_slot_length + bottom_slot_length/2
                    with Locations((x_pos, -p.height/2, p.thickness/2)):
                        Box(bottom_slot_length, p.thickness + p.clearance, p.thickness, mode=Mode.SUBTRACT)

                    # Dog-bone fillets are added during machining (not in CAD geometry)
                    # The toolpath generation will calculate and drill them at the correct positions

    return panel.part


def build_bottom_panel() -> Optional[Part]:
    """
    Bottom panel with fingers on all edges to insert into slots.
    Dimensions: width (X) x depth (Y)
    """
    p = HamperParams

    if not p.include_bottom:
        return None

    # Bottom panel is sized to fit inside the assembled box
    # Account for thickness of front/back/side panels
    inner_width = p.width - 2 * p.thickness
    inner_depth = p.depth - 2 * p.thickness

    with BuildPart() as panel:
        # Base rectangle - no corner rounding for clean CNC cutting
        with BuildSketch() as sk:
            Rectangle(inner_width, inner_depth)

        extrude(amount=p.thickness)

        # Add fingers on all 4 edges to insert into slots (3 fingers per edge)
        # Bottom panel is on XY plane: X = width, Y = depth, Z = thickness
        num_fingers = 3

        # Front edge (along X/width): fingers protruding in -Y direction
        finger_length_x = inner_width / num_fingers
        for i in range(num_fingers):
            if i % 2 == 1:  # Fingers at odd indices (complementary to slots)
                x_pos = -inner_width/2 + i * finger_length_x + finger_length_x/2
                with Locations((x_pos, -inner_depth/2 - p.thickness/2, p.thickness/2)):
                    Box(finger_length_x, p.thickness, p.thickness, mode=Mode.ADD)

        # Back edge (along X/width): fingers protruding in +Y direction
        for i in range(num_fingers):
            if i % 2 == 1:  # Same pattern
                x_pos = -inner_width/2 + i * finger_length_x + finger_length_x/2
                with Locations((x_pos, inner_depth/2 + p.thickness/2, p.thickness/2)):
                    Box(finger_length_x, p.thickness, p.thickness, mode=Mode.ADD)

        # Left edge (along Y/depth): fingers protruding in -X direction
        finger_length_y = inner_depth / num_fingers
        for i in range(num_fingers):
            if i % 2 == 1:  # Same pattern
                y_pos = -inner_depth/2 + i * finger_length_y + finger_length_y/2
                with Locations((-inner_width/2 - p.thickness/2, y_pos, p.thickness/2)):
                    Box(p.thickness, finger_length_y, p.thickness, mode=Mode.ADD)

        # Right edge (along Y/depth): fingers protruding in +X direction
        for i in range(num_fingers):
            if i % 2 == 1:  # Same pattern
                y_pos = -inner_depth/2 + i * finger_length_y + finger_length_y/2
                with Locations((inner_width/2 + p.thickness/2, y_pos, p.thickness/2)):
                    Box(p.thickness, finger_length_y, p.thickness, mode=Mode.ADD)

    return panel.part


# ============================================================================
# MAIN BUILD FUNCTIONS
# ============================================================================
def build_hamper_assembled() -> Compound:
    """
    Build hamper in assembled 3D form using edge-based positioning.

    Strategy: Position panels based on their connection edges.
    All panels are built flat on XY plane, then positioned by:
    1. Rotating to correct orientation
    2. Translating so edges align at material boundaries
    """
    p = HamperParams

    # Build individual panels (all built flat on XY plane, centered at origin)
    front = build_front_panel()
    back = build_back_panel()
    left_side = build_side_panel()
    right_side = build_side_panel()
    bottom = build_bottom_panel() if p.include_bottom else None

    # Define the box dimensions for assembly
    # Outer box dimensions
    box_width = p.width    # X direction
    box_depth = p.depth    # Y direction
    box_height = p.height  # Z direction

    # Position panels in assembled configuration
    # Start with front panel as reference at Y=0
    # Front panel: width x height, stands vertical facing +Y
    # Original panel on XY plane needs to rotate 90° around X axis to stand up
    # Then position at Y = thickness/2 (half thickness from Y=0 plane)
    front_located = (
        front
        .rotate(Axis.X, -90)  # Rotate to stand vertical (XY -> XZ)
        .translate((0, p.thickness/2, box_height/2))  # Move to front position
    )

    # Back panel: width x height, stands vertical facing -Y at Y=depth
    # Rotate 180° around Z (flip), then rotate 90° around X to stand
    # Position at Y = depth - thickness/2
    back_located = (
        back
        .rotate(Axis.Z, 180)  # Flip panel
        .rotate(Axis.X, -90)  # Stand vertical
        .translate((0, box_depth - p.thickness/2, box_height/2))  # Move to back
    )

    # Left panel: depth x height, stands vertical facing +X at X=0
    # Rotate -90° around Y to stand (XY plane -> YZ plane)
    # Position at X = thickness/2
    left_located = (
        left_side
        .rotate(Axis.Y, -90)  # Rotate to stand vertical
        .translate((p.thickness/2, 0, box_height/2))  # Move to left position
    )

    # Right panel: depth x height, stands vertical facing -X at X=width
    # Rotate 180° around Z (flip), then -90° around Y to stand
    # Position at X = width - thickness/2
    right_located = (
        right_side
        .rotate(Axis.Z, 180)  # Flip panel
        .rotate(Axis.Y, -90)  # Stand vertical
        .translate((box_width - p.thickness/2, 0, box_height/2))  # Move to right
    )

    panels = [
        front_located,
        back_located,
        left_located,
        right_located,
    ]

    # Bottom panel: stays horizontal on XY plane
    # Just translate up to correct Z height (at bottom finger insertion point)
    if bottom is not None:
        # Bottom sits at the bottom of the box
        bottom_located = bottom.translate((0, 0, p.thickness/2))
        panels.append(bottom_located)

    return Compound(panels)


def build_hamper() -> Compound:
    """
    Build all hamper panels laid out flat for CNC cutting.
    Returns a Compound containing all panels positioned for efficient cutting.
    """
    p = HamperParams

    # Build individual panels
    front = build_front_panel()
    back = build_back_panel()
    left_side = build_side_panel()
    right_side = build_side_panel()
    bottom = build_bottom_panel() if p.include_bottom else None

    # Layout panels on XY plane for CNC cutting
    # Strategy: arrange in a grid to fit on stock material
    spacing = 20.0  # Gap between panels for tool clearance

    # Position front panel (top left)
    front_pos = Location((0, 0, 0))

    # Position back panel (to the right of front)
    back_pos = Location((p.width + 2*p.thickness + spacing, 0, 0))

    # Position left side (below front)
    left_pos = Location((0, -(p.height + spacing), 0))

    # Position right side (below back)
    right_pos = Location((p.width + 2*p.thickness + spacing, -(p.height + spacing), 0))

    # Position bottom (below left and right sides)
    if bottom:
        # Place bottom below the side panels with proper spacing
        inner_width = p.width - 2 * p.thickness
        bottom_pos = Location((0, -(p.height + p.depth + 2*spacing), 0))

    # Create compound with all positioned panels
    parts = [
        front.locate(front_pos),
        back.locate(back_pos),
        left_side.locate(left_pos),
        right_side.locate(right_pos),
    ]

    if bottom:
        parts.append(bottom.locate(bottom_pos))

    return Compound(parts)


def get_hamper_parts() -> dict:
    """
    Return individual hamper parts as a dictionary.
    Useful for loading parts separately in the UI.
    """
    p = HamperParams

    # Build individual panels
    front = build_front_panel()
    back = build_back_panel()
    left_side = build_side_panel()
    right_side = build_side_panel()
    bottom = build_bottom_panel() if p.include_bottom else None

    # Layout panels on XY plane for CNC cutting (same as build_hamper)
    spacing = 20.0

    parts = {
        'front': front.locate(Location((0, 0, 0))),
        'back': back.locate(Location((p.width + 2*p.thickness + spacing, 0, 0))),
        'left': left_side.locate(Location((0, -(p.height + spacing), 0))),
        'right': right_side.locate(Location((p.width + 2*p.thickness + spacing, -(p.height + spacing), 0))),
    }

    if bottom:
        parts['bottom'] = bottom.locate(Location((0, -(p.height + p.depth + 2*spacing), 0)))

    return parts


def calculate_dogbone_positions(part_name: str, part: Part) -> list:
    """
    Extract dog-bone fillet positions directly from the part geometry.
    Returns list of DrillPoint objects.
    """
    p = HamperParams
    drill_points = []
    dogbone_radius = p.tool_diameter / 2 + 0.1
    dogbone_diameter = dogbone_radius * 2

    # Extract all circular holes from the part
    # Dog-bones are small circles (diameter = tool_diameter) cut into the part
    try:
        top_face = part.faces().sort_by(Axis.Z)[-1]

        print(f"\n=== Extracting dog-bones for {part_name} ===")
        print(f"Looking for circles with diameter ~{dogbone_diameter:.2f}mm")

        # Iterate through all inner wires (holes) in the top face
        wire_count = 0
        for inner_wire in top_face.inner_wires():
            wire_count += 1
            edges = inner_wire.edges()
            print(f"  Wire {wire_count}: {len(edges)} edges")

            # Check if this is a single circular edge (a hole)
            if len(edges) == 1:
                edge = edges[0]
                if hasattr(edge, 'radius'):
                    radius = edge.radius  # radius is a property, not a method
                    diameter = radius * 2
                    center = edge.center()
                    print(f"    Found circular edge: d={diameter:.2f}mm at ({center.X:.1f}, {center.Y:.1f})")

                    # Check if this is a dog-bone sized hole (within tolerance)
                    # Filter out large holes like handle cutouts
                    if diameter < 15 and abs(diameter - dogbone_diameter) < 1.0:  # Ignore holes >15mm, 1mm tolerance
                        print(f"    ✓ MATCH - Adding as drill point")
                        drill_points.append(DrillPoint(
                            x=center.X,
                            y=center.Y,
                            depth=p.thickness,
                            diameter=diameter
                        ))
                    else:
                        print(f"    ✗ Filtered out (d={diameter:.2f}mm, expected ~{dogbone_diameter:.2f}mm)")

        print(f"Total drill points found: {len(drill_points)}")

    except Exception as e:
        print(f"Warning: Could not extract dog-bone positions from {part_name}: {e}")
        import traceback
        traceback.print_exc()

    return drill_points

def calculate_dogbone_positions_manual(part_name: str, part: Part) -> list:
    """
    DEPRECATED: Manual calculation of dog-bone positions (backup method).
    """
    p = HamperParams
    drill_points = []
    dogbone_radius = p.tool_diameter / 2 + 0.1

    # Get part's bounding box to determine its position
    bbox = part.bounding_box()
    # Calculate center position of the part
    part_center_x = (bbox.min.X + bbox.max.X) / 2
    part_center_y = (bbox.min.Y + bbox.max.Y) / 2

    if part_name == 'left' or part_name == 'right':
        # Side panels have slots on front, back, and bottom edges
        num_slots = 5
        slot_length = p.height / num_slots

        # Front edge slots (along Y/height at front X edge)
        for i in range(num_slots):
            if i % 2 == 0:  # Slots at even indices
                y_pos = -p.height/2 + i * slot_length + slot_length/2
                # 4 corners per slot
                drill_points.extend([
                    DrillPoint(x=part_center_x + (-p.depth/2 - (p.thickness + p.clearance)/2), y=part_center_y + (y_pos + slot_length/2), depth=p.thickness, diameter=dogbone_radius*2),
                    DrillPoint(x=part_center_x + (-p.depth/2 + (p.thickness + p.clearance)/2), y=part_center_y + (y_pos + slot_length/2), depth=p.thickness, diameter=dogbone_radius*2),
                    DrillPoint(x=part_center_x + (-p.depth/2 - (p.thickness + p.clearance)/2), y=part_center_y + (y_pos - slot_length/2), depth=p.thickness, diameter=dogbone_radius*2),
                    DrillPoint(x=part_center_x + (-p.depth/2 + (p.thickness + p.clearance)/2), y=part_center_y + (y_pos - slot_length/2), depth=p.thickness, diameter=dogbone_radius*2),
                ])

        # Back edge slots
        for i in range(num_slots):
            if i % 2 == 0:
                y_pos = -p.height/2 + i * slot_length + slot_length/2
                drill_points.extend([
                    DrillPoint(x=part_center_x + (p.depth/2 - (p.thickness + p.clearance)/2), y=part_center_y + (y_pos + slot_length/2), depth=p.thickness, diameter=dogbone_radius*2),
                    DrillPoint(x=part_center_x + (p.depth/2 + (p.thickness + p.clearance)/2), y=part_center_y + (y_pos + slot_length/2), depth=p.thickness, diameter=dogbone_radius*2),
                    DrillPoint(x=part_center_x + (p.depth/2 - (p.thickness + p.clearance)/2), y=part_center_y + (y_pos - slot_length/2), depth=p.thickness, diameter=dogbone_radius*2),
                    DrillPoint(x=part_center_x + (p.depth/2 + (p.thickness + p.clearance)/2), y=part_center_y + (y_pos - slot_length/2), depth=p.thickness, diameter=dogbone_radius*2),
                ])

        # Bottom edge slots
        if p.include_bottom:
            num_bottom_slots = 3
            bottom_slot_length = p.depth / num_bottom_slots
            for i in range(num_bottom_slots):
                if i % 2 == 1:  # Gaps at odd indices
                    x_pos = -p.depth/2 + i * bottom_slot_length + bottom_slot_length/2
                    drill_points.extend([
                        DrillPoint(x=part_center_x + (x_pos - bottom_slot_length/2), y=part_center_y + (-p.height/2 - (p.thickness + p.clearance)/2), depth=p.thickness, diameter=dogbone_radius*2),
                        DrillPoint(x=part_center_x + (x_pos - bottom_slot_length/2), y=part_center_y + (-p.height/2 + (p.thickness + p.clearance)/2), depth=p.thickness, diameter=dogbone_radius*2),
                        DrillPoint(x=part_center_x + (x_pos + bottom_slot_length/2), y=part_center_y + (-p.height/2 - (p.thickness + p.clearance)/2), depth=p.thickness, diameter=dogbone_radius*2),
                        DrillPoint(x=part_center_x + (x_pos + bottom_slot_length/2), y=part_center_y + (-p.height/2 + (p.thickness + p.clearance)/2), depth=p.thickness, diameter=dogbone_radius*2),
                    ])

    elif part_name == 'front' or part_name == 'back':
        # Front/back panels have slots on bottom edge only
        if p.include_bottom:
            num_bottom_slots = 3
            bottom_slot_length = p.width / num_bottom_slots
            for i in range(num_bottom_slots):
                if i % 2 == 1:  # Gaps at odd indices
                    x_pos = -p.width/2 + i * bottom_slot_length + bottom_slot_length/2
                    drill_points.extend([
                        DrillPoint(x=part_center_x + (x_pos - bottom_slot_length/2), y=part_center_y + (-p.height/2 - (p.thickness + p.clearance)/2), depth=p.thickness, diameter=dogbone_radius*2),
                        DrillPoint(x=part_center_x + (x_pos - bottom_slot_length/2), y=part_center_y + (-p.height/2 + (p.thickness + p.clearance)/2), depth=p.thickness, diameter=dogbone_radius*2),
                        DrillPoint(x=part_center_x + (x_pos + bottom_slot_length/2), y=part_center_y + (-p.height/2 - (p.thickness + p.clearance)/2), depth=p.thickness, diameter=dogbone_radius*2),
                        DrillPoint(x=part_center_x + (x_pos + bottom_slot_length/2), y=part_center_y + (-p.height/2 + (p.thickness + p.clearance)/2), depth=p.thickness, diameter=dogbone_radius*2),
                    ])

    # Bottom panel doesn't need dog-bones (it has fingers that insert into slots)

    return drill_points


def get_hamper_operations(part_name: str, part: Part) -> list:
    """
    Generate machining operations for a hamper part.
    Returns list of Operation objects in execution order.

    Args:
        part_name: Name of the part ('front', 'back', 'left', 'right', 'bottom')
        part: The Part object

    Returns:
        List of Operation objects
    """
    p = HamperParams
    operations = []

    # Operation 1: Drill dog-bone relief holes (if enabled)
    if p.add_dogbone_fillets:
        # Calculate drill points based on slot geometry for this part
        # Use manual calculation since geometry extraction is unreliable
        drill_points = calculate_dogbone_positions_manual(part_name, part)

        if drill_points:
            # Drilling operation with slower speeds for material protection
            drill_op = Operation(
                op_type=OperationType.DRILL,
                name=f"{part_name}_dogbone_drilling",
                tool_diameter=p.tool_diameter,
                spindle_rpm=12000,  # Slower RPM for drilling
                feed_rate=300,  # Slow feed for drilling
                plunge_rate=150,  # Very slow plunge for drilling
                drill_points=drill_points,
                depth_of_cut=p.thickness,
                total_depth=p.thickness,
                peck_depth=3.0,  # Peck 3mm at a time
                dwell_time=0.3,  # Brief dwell to clear chips
                safe_height=5.0,
                retract_height=2.0,
            )
            operations.append(drill_op)

    # Operation 2: Contour cutting (outside profile with tabs)
    # Extract contours from the part
    contours = extract_contours(part)

    if contours:
        # Contour operation with normal cutting speeds
        contour_op = Operation(
            op_type=OperationType.CONTOUR,
            name=f"{part_name}_contour",
            tool_diameter=p.tool_diameter,
            spindle_rpm=18000,  # Normal RPM for cutting
            feed_rate=1500,  # Normal feed rate
            plunge_rate=750,  # Normal plunge rate
            contours=contours,
            depth_of_cut=3.0,
            total_depth=p.thickness,
            stepover=0.4,
            offset_direction="outside",  # Cut outside the part
            add_tabs=True,  # Add tabs to hold part in place
            tab_width=5.0,
            tab_height=2.0,
            num_tabs=3,
            safe_height=5.0,
            retract_height=2.0,
        )
        operations.append(contour_op)

    return operations


# ============================================================================
# VALIDATION & EXPORT
# ============================================================================
def validate_hamper() -> bool:
    """Check design constraints"""
    p = HamperParams

    print(f"\nHamper Dimensions:")
    print(f"  Width: {p.width}mm")
    print(f"  Depth: {p.depth}mm")
    print(f"  Height: {p.height}mm")
    print(f"  Material: {p.thickness}mm plywood")

    # Check if panels fit on machine
    # Front/back panels: width x height
    if not check_part_fits(p.width, p.height, p.thickness):
        print("ERROR: Front/back panels exceed machine capacity!")
        return False

    # Side panels: depth x height
    if not check_part_fits(p.depth, p.height, p.thickness):
        print("ERROR: Side panels exceed machine capacity!")
        return False

    # Check if layout fits on standard 4x4 sheet
    layout_x = p.width + p.depth + 40  # front + back + spacing
    layout_y = p.height + 20  # sides below, plus spacing
    print(f"\nLayout size: {layout_x}mm x {layout_y}mm")

    sheet_x, sheet_y = StockSizes.PLYWOOD_HALF
    if layout_x > sheet_x or layout_y > sheet_y:
        print(f"WARNING: Layout ({layout_x} x {layout_y}) may not fit on 4x4 sheet!")
        print(f"  Consider reducing dimensions or splitting across multiple sheets")

    return True


def export_step(parts: Compound, output_dir: Optional[Path] = None) -> None:
    """Export all panels to STEP file"""
    from build123d import export_step as bd_export

    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "exports"

    output_dir.mkdir(exist_ok=True)

    filename = f"{PART_NAME}_{PART_VERSION}.step"
    filepath = output_dir / filename

    bd_export(parts, str(filepath))
    print(f"\n✓ Exported: {filepath}")
    print(f"\nImport this STEP file into Fusion 360 for CAM.")


# ============================================================================
# ASSEMBLY INSTRUCTIONS
# ============================================================================
def print_assembly_instructions() -> None:
    """Print assembly guide"""
    p = HamperParams

    print("\n" + "="*60)
    print("ASSEMBLY INSTRUCTIONS")
    print("="*60)
    print("\n1. Cut all panels from 12mm (1/2\") plywood")
    print("   - 2x front/back panels (with handle cutouts)")
    print("   - 2x side panels")
    if p.include_bottom:
        print("   - 1x bottom panel")

    print("\n2. Test fit finger joints (should slide together with light pressure)")
    print("   - If too tight, sand fingers slightly")
    print("   - If too loose, add tape/shims or use glue")

    print("\n3. Assembly sequence:")
    print("   a. Join one side panel to front panel")
    print("   b. Join back panel to the side panel")
    print("   c. Join second side panel to complete the box")
    if p.include_bottom:
        print("   d. Slide bottom panel into slots from the top")

    print("\n4. Finishing:")
    print("   - Sand all edges smooth")
    print("   - Apply finish (oil, stain, or polyurethane)")
    print("   - Optionally add rubber feet to protect floors")

    print("\n" + "="*60)


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    print(f"Building {PART_NAME} {PART_VERSION}")
    print(f"Description: {DESCRIPTION}")

    # Validate design
    if not validate_hamper():
        print("\nERROR: Design validation failed!")
        sys.exit(1)

    # Build all panels
    print("\nBuilding panels...")
    hamper = build_hamper()

    # Export to STEP
    export_step(hamper)

    # Print assembly guide
    print_assembly_instructions()

    # Optional: show in ocp-vscode if running in VS Code
    try:
        show_object(hamper, name=PART_NAME)
        print("\n✓ Part preview available in ocp-vscode panel")
    except Exception:
        print("\n  (Run in VS Code with ocp-vscode extension for live 3D preview)")

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("  1. Install dependencies: poetry install")
    print("  2. Import STEP file into Fusion 360")
    print("  3. Set up CAM toolpaths:")
    print(f"     - Tool: 6mm (1/4\") 2-flute endmill")
    print(f"     - Depth: {HamperParams.thickness}mm")
    print(f"     - Tabs: 2-3 per panel to hold parts during cutting")
    print("  4. Post-process for Shapeoko (carbide3d.cps)")
    print("  5. Run in Carbide Motion")
    print("="*60)
