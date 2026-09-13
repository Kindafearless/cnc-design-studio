"""
Shapeoko 5 Pro machine configuration and tooling library.
Machine: Shapeoko 5 Pro (4' x 4' custom bed)
Spindle: Carbide 3D 1.2kW VFD Spindle (65mm, ER-16 collets)
  - Power: 1200W (1.6 HP)
  - RPM range: 8,000-24,000
  - Collets: 1/8", 1/4", 3/8" (max tool diameter: 10mm)
  - Air-cooled
"""

from typing import Dict, List, NamedTuple
from enum import Enum


# Machine constraints (all dimensions in mm)
class MachineConstraints:
    """Shapeoko 5 Pro physical limits"""

    # Work envelope
    X_TRAVEL = 1219.0  # 48 inches
    Y_TRAVEL = 1219.0  # 48 inches
    Z_TRAVEL = 114.0   # ~4.5 inches (typical for Pro)

    # Safe working area (accounting for fixturing, tool clearance)
    SAFE_X = 1150.0
    SAFE_Y = 1150.0
    SAFE_Z = 100.0

    # Rapids and feeds
    MAX_RAPID = 5000.0  # mm/min (conservative)
    MAX_FEED = 3000.0   # mm/min (material dependent)

    # Spindle (Carbide 3D 1.2kW VFD)
    SPINDLE_MIN_RPM = 8000
    SPINDLE_MAX_RPM = 24000
    SPINDLE_POWER_W = 1200
    MAX_TOOL_DIA = 10.0  # mm (3/8" ER-16 collet limit)


# Default tolerances for different operations
class Tolerances:
    """CNC routing tolerances for fit types"""

    CLEARANCE_FIT = 0.2    # Loose fit, easy assembly (mm)
    SLIP_FIT = 0.1         # Parts slide together with minimal force
    PRESS_FIT = -0.05      # Slight interference, requires force
    TIGHT_FIT = -0.1       # Strong interference fit

    # General machining
    GENERAL = 0.1          # General dimensional tolerance
    FINE = 0.05            # Fine feature tolerance


# Common stock sizes (all in mm)
class StockSizes:
    """Standard material dimensions available"""

    # Plywood sheets
    PLYWOOD_FULL = (1219.0, 2438.0)      # 4x8 ft
    PLYWOOD_HALF = (1219.0, 1219.0)      # 4x4 ft

    # Common plywood thicknesses
    PLY_THICKNESSES = [6.0, 9.0, 12.0, 18.0, 25.0]  # mm (1/4", 3/8", 1/2", 3/4", 1")

    # Aluminum stock
    AL_6061_PLATE = [(3.175, "1/8\""), (6.35, "1/4\""), (12.7, "1/2\""), (25.4, "1\"")]
    AL_6061_BAR = [(25.4, 25.4), (50.8, 50.8)]  # Square bar sizes

    # Hardwood dimensional lumber (actual sizes, not nominal)
    HARDWOOD_ACTUAL = {
        "1x4": (19.0, 89.0),
        "1x6": (19.0, 140.0),
        "2x4": (38.0, 89.0),
        "2x6": (38.0, 140.0),
    }


class ToolType(Enum):
    """Tool categories"""
    ENDMILL = "endmill"
    BALLNOSE = "ballnose"
    VBIT = "vbit"
    SURFACING = "surfacing"
    DRILL = "drill"


class Tool(NamedTuple):
    """CNC tool definition"""
    name: str
    type: ToolType
    diameter: float      # mm
    flutes: int
    stick_out: float     # mm (length below collet)
    material: str        # carbide, HSS, etc.
    notes: str = ""


# Standard tool library
TOOL_LIBRARY: Dict[str, Tool] = {
    # Endmills for aluminum and wood
    "em_3mm_2f": Tool(
        name="3mm 2-flute endmill",
        type=ToolType.ENDMILL,
        diameter=3.0,
        flutes=2,
        stick_out=25.0,
        material="Carbide",
        notes="Detail work, small features"
    ),

    "em_6mm_2f": Tool(
        name="6mm 2-flute endmill",
        type=ToolType.ENDMILL,
        diameter=6.35,  # 1/4"
        flutes=2,
        stick_out=38.0,
        material="Carbide",
        notes="General purpose, plywood, hardwood"
    ),

    "em_6mm_3f_al": Tool(
        name="6mm 3-flute endmill (aluminum)",
        type=ToolType.ENDMILL,
        diameter=6.35,
        flutes=3,
        stick_out=38.0,
        material="Carbide",
        notes="Aluminum roughing and finishing"
    ),

    "em_12mm_2f": Tool(
        name="12mm 2-flute endmill",
        type=ToolType.ENDMILL,
        diameter=12.7,  # 1/2"
        flutes=2,
        stick_out=50.0,
        material="Carbide",
        notes="Heavy stock removal in wood"
    ),

    # V-bits for chamfers and engraving
    "vbit_60": Tool(
        name="60° V-bit",
        type=ToolType.VBIT,
        diameter=6.35,  # tip diameter
        flutes=2,
        stick_out=30.0,
        material="Carbide",
        notes="Chamfers, engraving, V-carve"
    ),

    "vbit_90": Tool(
        name="90° V-bit",
        type=ToolType.VBIT,
        diameter=6.35,
        flutes=2,
        stick_out=30.0,
        material="Carbide",
        notes="Chamfers, deburring"
    ),

    # Surfacing
    "surfacing_50mm": Tool(
        name="50mm surfacing bit",
        type=ToolType.SURFACING,
        diameter=50.8,  # 2"
        flutes=4,
        stick_out=15.0,
        material="Carbide",
        notes="Spoilboard flattening, slab surfacing"
    ),

    # Ball nose for 3D contours
    "ball_6mm": Tool(
        name="6mm ball nose",
        type=ToolType.BALLNOSE,
        diameter=6.35,
        flutes=2,
        stick_out=38.0,
        material="Carbide",
        notes="3D contours, organic shapes"
    ),
}


# Feed and speed recommendations (conservative starting points)
class CuttingParams:
    """Material-specific cutting parameters"""

    # Format: (RPM, feed_mm_min, depth_of_cut_mm, stepover_fraction)
    PARAMS = {
        # Plywood
        ("plywood", 6.35): (18000, 1500, 3.0, 0.4),
        ("plywood", 12.7): (18000, 2000, 4.0, 0.5),

        # Hardwood
        ("hardwood", 6.35): (18000, 1200, 2.5, 0.4),
        ("hardwood", 12.7): (18000, 1800, 3.5, 0.5),

        # Aluminum 6061
        ("aluminum", 3.0): (12000, 400, 0.5, 0.3),
        ("aluminum", 6.35): (12000, 600, 0.75, 0.4),

        # MDF / Softwood
        ("softwood", 6.35): (18000, 1800, 3.5, 0.5),
        ("softwood", 12.7): (18000, 2500, 5.0, 0.5),
    }

    @staticmethod
    def get_params(material: str, tool_dia: float):
        """Lookup cutting parameters for material and tool size"""
        key = (material.lower(), tool_dia)
        if key in CuttingParams.PARAMS:
            return CuttingParams.PARAMS[key]
        else:
            # Return conservative defaults
            return (12000, 1000, 2.0, 0.4)


# Helper functions for common operations
def check_part_fits(length_x: float, length_y: float, height_z: float) -> bool:
    """Verify part fits in machine envelope"""
    return (length_x <= MachineConstraints.SAFE_X and
            length_y <= MachineConstraints.SAFE_Y and
            height_z <= MachineConstraints.SAFE_Z)


def get_tool(tool_key: str) -> Tool:
    """Retrieve tool from library by key"""
    if tool_key in TOOL_LIBRARY:
        return TOOL_LIBRARY[tool_key]
    else:
        raise ValueError(f"Tool '{tool_key}' not found in library")


def list_tools(tool_type: ToolType = None) -> List[Tool]:
    """List all tools, optionally filtered by type"""
    if tool_type:
        return [t for t in TOOL_LIBRARY.values() if t.type == tool_type]
    return list(TOOL_LIBRARY.values())


if __name__ == "__main__":
    # Quick test/demo
    print("Shapeoko 5 Pro Configuration")
    print(f"Work envelope: {MachineConstraints.X_TRAVEL} x {MachineConstraints.Y_TRAVEL} x {MachineConstraints.Z_TRAVEL} mm")
    print(f"\nAvailable tools: {len(TOOL_LIBRARY)}")

    for key, tool in TOOL_LIBRARY.items():
        print(f"  {key}: {tool.name} ({tool.diameter}mm, {tool.flutes}FL)")

    print(f"\nTest fit: 1000x1000x50mm part fits? {check_part_fits(1000, 1000, 50)}")
