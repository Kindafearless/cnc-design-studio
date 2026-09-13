# Claude Development Notes

This file tracks development progress and technical details for the CNC Design Studio project.

**Last Updated**: April 25, 2026

## Test Coverage Status (Added Apr 25, 2026)

**All Tests Passing**: ✅ 35/35 tests

### Test Suites

1. **tests/test_vectors.py** (6 tests)
   - Prevents Vector attribute regression (uppercase X,Y,Z vs lowercase)
   - Tests bounding box access patterns
   - Tests edge position vector access
   - Critical for preventing the bug that occurred in lib/cam.py:125,138

2. **tests/test_finger_joints.py** (14 tests)
   - Validates finger joint geometry and spacing
   - Tests panel dimensions and bounding boxes
   - Tests clearance parameters
   - Tests finger/slot pattern alternation
   - Tests assembled hamper construction

3. **tests/test_cam.py** (15 tests)
   - Tests contour extraction from parts
   - Tests G-code generation and structure
   - Tests toolpath configuration
   - Tests multi-part toolpath generation
   - Validates Vector uppercase attribute usage in CAM functions

### Type Hints Coverage

- **lib/cam.py**: ✅ Full type hints on all functions and GCodeGenerator class
- **parts/hamper.py**: ✅ Type hints on main build functions and Optional types
- **webapp/app.py**: ⚠️ Partial (Flask routes less critical for type safety)

**Run tests**: `pytest tests/ -v`

---

## Recent Work (Apr 25, 2026)

### Hamper Project - Finger Joints Implementation

Added proper finger joint implementation to the clothes hamper design:

**Files Modified**:
- `parts/hamper.py` - Added finger joints to all panels
- `webapp/app.py` - Fixed toolpath generation for multiple parts
- `webapp/templates/index.html` - Enhanced toolpath visualization
- `lib/cam.py` - Fixed Vector attribute access

**Key Features**:
1. **Finger Joints**
   - Front/Back panels: 5 fingers on vertical edges, 3 slots on bottom
   - Side panels: 5 slots on front/back edges, 3 slots on bottom
   - Bottom panel: 3 fingers on all 4 edges
   - All joints integrated into panel bodies (not separate objects)
   - Coordinate system: panels built flat on XY plane (X=width, Y=height, Z=thickness)

2. **Toolpath Visualization Improvements**
   - Multi-part toolpath support (generates paths for all 5 panels)
   - Color-coded visualization:
     - **Red** (#ff3333): Cutting paths (feed moves)
     - **Yellow** (#ffff00): Rapid/travel moves
     - **Cyan** (#00ffff): Material bounds (wireframe boxes)
   - Added interactive legend
   - Part visibility controls (show/hide individual panels)

3. **Bug Fixes**
   - Fixed Vector attribute errors: build123d uses uppercase `X,Y,Z` not lowercase `x,y,z`
   - Updated both `lib/cam.py:125,138` and `webapp/app.py:438-440`
   - Fixed toolpath endpoint to return array of toolpaths instead of single object

## Technical Details

### Coordinate Systems

**Flat Panel Layout** (for CNC cutting):
- All panels built on XY plane at Z=0
- X = width, Y = height, Z = thickness
- Finger joints extend in their respective directions
- Example: Left edge fingers on front panel protrude in -X direction

**Assembly Positioning**:
- Front panel: rotate -90° around X, position at Y=thickness/2
- Back panel: rotate 180° around Z then -90° around X, position at Y=depth-thickness/2
- Side panels: rotate -90° around Y, position at respective X positions
- Bottom panel: just translate to Z=thickness/2

### API Changes

**Toolpath Endpoint** (`/api/part/<part_name>/toolpath`):
```python
# Request
{
    "parameters": {...},
    "cam_config": {...},
    "visible_parts": ["front", "back", "left", "right", "bottom"]  # NEW
}

# Response
{
    "success": true,
    "toolpaths": [  # Changed from single "toolpath" to array
        {
            "name": "front",
            "rapid_moves": [...],
            "feed_moves": [...],
            "material_bounds": {...}
        },
        ...
    ]
}
```

### Frontend Architecture

**Toolpath Rendering**:
- `renderToolpaths(toolpaths)` - Loops through all parts
- `togglePartVisibility(partName, isVisible)` - Controls which parts to show
- Legend and visibility controls auto-show/hide with toolpath toggle

**State Management**:
- `visibleParts` array tracks which parts should have toolpaths generated
- Toggling part visibility triggers toolpath reload
- Toolpath group cleared and rebuilt on each update

## Known Issues

1. **Assembly View** - Manual rotation/translation is brittle
   - Suggested improvement: Use edge-based attachment system
   - Would make assembly positioning more robust and maintainable

2. **Finger Joint Design**
   - Currently uses rectangular fingers
   - Could benefit from slight taper for easier assembly
   - Clearance currently hardcoded (0.15mm default)

## Future Improvements

1. **Edge-Based Assembly System**
   - Track attachment points between parts
   - Automatic positioning based on edge relationships
   - Would replace manual rotation/translation

2. **Toolpath Optimization**
   - Currently generates separate toolpaths per part
   - Could optimize cutting order across all parts
   - Consider tool changes and minimize rapids

3. **Material Simulation**
   - Show remaining material after each operation
   - Visual simulation of cutting process
   - Collision detection for tool/workpiece

4. **G-code Export**
   - Currently only generates toolpaths for visualization
   - Need to implement actual G-code export for multi-part projects
   - Include proper tool changes, safe moves, etc.

## Development Notes

### build123d Specifics

**Vector Attributes**:
- build123d uses OCP (OpenCascade) Vector class
- Attributes are UPPERCASE: `X`, `Y`, `Z` (not lowercase)
- This caught us twice: once in CAM library, once in webapp

**Compound vs Part**:
- `Compound` contains multiple parts (like our hamper panels)
- Access children via `.children` attribute
- Each child is a separate `Part` object

### Testing Workflow

1. Start server: `./run-studio.sh local`
2. Open http://localhost:5001
3. Select hamper part
4. Toggle between "Cutting View" and "Assembled View"
5. Click "Show Toolpath" to see multi-part toolpaths
6. Use part visibility controls to isolate specific panels

## Code Locations

**Key Functions**:
- `parts/hamper.py:build_front_panel()` - Lines 70-135
- `parts/hamper.py:build_side_panel()` - Lines 138-203
- `parts/hamper.py:build_bottom_panel()` - Lines 206-240
- `webapp/app.py:get_toolpath()` - Lines 362-460
- `webapp/templates/index.html:renderToolpaths()` - Lines 716-779
- `lib/cam.py:extract_contours()` - Lines 110-142

**Important Constants**:
- `HamperParams.thickness` = 12.0mm (plywood)
- `HamperParams.clearance` = 0.15mm (finger joint fit)
- `HamperParams.finger_width` = 25mm (finger spacing)
- Part names: ['front', 'back', 'left', 'right', 'bottom']

## Dependencies

**Python Packages**:
- build123d >= 0.7.0 (parametric CAD)
- Flask >= 3.0 (web framework)
- ocp-tessellate >= 3.2.2 (mesh generation)

**Frontend**:
- Three.js r128 (3D rendering)
- OrbitControls (camera controls)

## Deployment

**Local Development**:
```bash
./run-studio.sh local  # Uses host Python environment
```

**Container Mode**:
```bash
./run-studio.sh container  # Uses Podman container
```

Container includes:
- Python 3.12
- All dependencies pre-installed
- Mounts for live code editing
- Exposed on port 5001

---

*This document is maintained by Claude Code to track development progress and technical decisions.*
