"""
Test CAM toolpath generation functions.

Validates that:
- extract_contours correctly extracts 2D contours from parts
- Contour points use UPPERCASE Vector attributes (X, Y)
- generate_gcode_for_part produces valid G-code
- Multi-part toolpath generation works correctly
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from build123d import Box, Compound, BuildPart, BuildSketch, Rectangle, Circle, extrude, Locations, Mode
from lib.cam import (
    extract_contours,
    generate_gcode_for_part,
    ToolpathConfig,
    generate_contour_toolpath,
    GCodeGenerator,
)


def test_extract_contours_simple_box():
    """Test extracting contours from a simple box"""
    box = Box(100, 100, 12)
    contours = extract_contours(box)

    # Should extract at least one contour (outer edge of top face)
    assert len(contours) > 0, "Should extract at least one contour"

    # Each contour should be a list of (x, y) tuples
    first_contour = contours[0]
    assert len(first_contour) > 0, "Contour should have points"

    # Check point structure
    first_point = first_contour[0]
    assert len(first_point) == 2, "Each point should be (x, y) tuple"
    assert isinstance(first_point[0], (int, float)), "X coordinate should be numeric"
    assert isinstance(first_point[1], (int, float)), "Y coordinate should be numeric"


def test_extract_contours_uses_uppercase_vector_attributes():
    """
    CRITICAL: Verify that extract_contours uses UPPERCASE Vector attributes.
    This test prevents regression of the bug fixed in lib/cam.py:125,138
    """
    # Create a part with a hole (inner contour)
    with BuildPart() as part_builder:
        with BuildSketch():
            Rectangle(100, 100)
            with Locations((0, 0)):
                Circle(20, mode=Mode.SUBTRACT)  # Hole in center
        extrude(amount=12)

    part = part_builder.part
    contours = extract_contours(part)

    # Should have outer contour and inner contour (hole)
    assert len(contours) >= 1, "Should have at least outer contour"

    # Verify all points are valid (would fail if using lowercase .x, .y)
    for contour in contours:
        for point in contour:
            # If this was using lowercase .x, .y, it would have raised AttributeError
            assert isinstance(point[0], (int, float)), f"Invalid X coordinate: {point[0]}"
            assert isinstance(point[1], (int, float)), f"Invalid Y coordinate: {point[1]}"


def test_extract_contours_from_hamper_panel():
    """Test extracting contours from a real hamper panel"""
    from parts.hamper import build_front_panel

    front = build_front_panel()
    contours = extract_contours(front)

    # Front panel has handle cutout, so should have outer + inner contour
    assert len(contours) >= 1, "Should extract contours from front panel"

    # Check that contours have reasonable number of points
    outer_contour = contours[0]
    assert len(outer_contour) > 50, \
        "Outer contour should have many points (rectangular panel with fingers)"


def test_generate_gcode_basic_structure():
    """Test that generated G-code has correct structure"""
    box = Box(50, 50, 12)
    gcode = generate_gcode_for_part(
        box,
        tool_diameter=6.35,
        material_thickness=12.0,
        spindle_rpm=18000,
        feed_rate=1500
    )

    # G-code should be non-empty string
    assert isinstance(gcode, str)
    assert len(gcode) > 0, "G-code should not be empty"

    # Should have start marker
    assert gcode.startswith("%"), "G-code should start with %"

    # Should have end marker
    assert gcode.endswith("%"), "G-code should end with %"

    # Should contain key commands
    assert "G21" in gcode, "Should set metric units (G21)"
    assert "G90" in gcode, "Should set absolute positioning (G90)"
    assert "M3" in gcode, "Should turn spindle on (M3)"
    assert "M5" in gcode, "Should turn spindle off (M5)"
    assert "M2" in gcode, "Should have program end (M2)"


def test_generate_gcode_spindle_speed():
    """Test that spindle speed is correctly set in G-code"""
    box = Box(50, 50, 12)
    spindle_rpm = 24000

    gcode = generate_gcode_for_part(
        box,
        tool_diameter=6.35,
        material_thickness=12.0,
        spindle_rpm=spindle_rpm,
        feed_rate=1500
    )

    # Should contain spindle command with specified RPM
    expected_cmd = f"M3 S{spindle_rpm}"
    assert expected_cmd in gcode, f"Should contain '{expected_cmd}'"


def test_generate_gcode_has_movement_commands():
    """Test that G-code contains movement commands"""
    box = Box(50, 50, 12)
    gcode = generate_gcode_for_part(box)

    # Should contain rapid moves (G0)
    assert "G0" in gcode, "Should have rapid moves (G0)"

    # Should contain feed moves (G1)
    assert "G1" in gcode, "Should have feed moves (G1)"

    # Should have Z-axis moves (plunge and retract)
    assert "Z" in gcode, "Should have Z-axis moves"


def test_toolpath_config_defaults():
    """Test ToolpathConfig dataclass with default values"""
    config = ToolpathConfig(
        tool_diameter=6.35,
        spindle_rpm=18000,
        feed_rate=1500,
        plunge_rate=750,
        depth_of_cut=3.0,
        total_depth=12.0
    )

    # Check defaults
    assert config.stepover == 0.4, "Default stepover should be 0.4"
    assert config.safe_height == 5.0, "Default safe height should be 5mm"
    assert config.retract_height == 2.0, "Default retract height should be 2mm"
    assert config.add_tabs == True, "Tabs should be enabled by default"
    assert config.num_tabs == 3, "Should have 3 tabs by default"


def test_gcode_generator_header_footer():
    """Test GCodeGenerator header and footer generation"""
    config = ToolpathConfig(
        tool_diameter=6.35,
        spindle_rpm=18000,
        feed_rate=1500,
        plunge_rate=750,
        depth_of_cut=3.0,
        total_depth=12.0
    )

    generator = GCodeGenerator(config)
    generator.header()
    generator.footer()

    gcode = generator.get_gcode()

    # Should have both header and footer
    assert "G21" in gcode, "Header should set metric"
    assert "M3" in gcode, "Header should start spindle"
    assert "M5" in gcode, "Footer should stop spindle"
    assert "M2" in gcode, "Footer should end program"


def test_gcode_generator_rapid_move():
    """Test rapid move command generation"""
    config = ToolpathConfig(
        tool_diameter=6.35,
        spindle_rpm=18000,
        feed_rate=1500,
        plunge_rate=750,
        depth_of_cut=3.0,
        total_depth=12.0
    )

    generator = GCodeGenerator(config)
    generator.rapid_move(100.5, 200.3, 5.0)

    gcode = generator.get_gcode()

    # Should contain rapid move with coordinates
    assert "G0" in gcode
    assert "X100.500" in gcode
    assert "Y200.300" in gcode
    assert "Z5.000" in gcode


def test_gcode_generator_feed_move():
    """Test feed move command generation"""
    config = ToolpathConfig(
        tool_diameter=6.35,
        spindle_rpm=18000,
        feed_rate=1500,
        plunge_rate=750,
        depth_of_cut=3.0,
        total_depth=12.0
    )

    generator = GCodeGenerator(config)
    generator.feed_move(50.0, 75.0)

    gcode = generator.get_gcode()

    # Should contain feed move with coordinates and feed rate
    assert "G1" in gcode
    assert "X50.000" in gcode
    assert "Y75.000" in gcode
    assert "F1500" in gcode  # Feed rate


def test_multi_part_toolpath_generation():
    """Test generating toolpaths for a Compound"""
    from parts.hamper import build_hamper

    # Build hamper which returns a Compound of multiple panels
    hamper = build_hamper()

    # Should be a Compound
    assert isinstance(hamper, Compound), "Hamper should be a Compound"

    # Generate G-code for the entire compound
    # (The function should handle either Part or Compound)
    gcode = generate_gcode_for_part(
        hamper,
        tool_diameter=6.35,
        material_thickness=12.0
    )

    # Should generate valid G-code
    assert len(gcode) > 0, "Should generate G-code for Compound"
    assert gcode.startswith("%"), "G-code should start with %"
    assert "G21" in gcode, "Should have metric setting"


def test_contour_toolpath_offset_directions():
    """Test different offset directions for contour toolpaths"""
    box = Box(100, 100, 12)

    config = ToolpathConfig(
        tool_diameter=6.35,
        spindle_rpm=18000,
        feed_rate=1500,
        plunge_rate=750,
        depth_of_cut=3.0,
        total_depth=12.0
    )

    # Test outside offset
    gcode_outside = generate_contour_toolpath(box, config, offset_direction="outside")
    assert "outside" in gcode_outside.lower(), "Should mention offset direction"

    # Test inside offset
    gcode_inside = generate_contour_toolpath(box, config, offset_direction="inside")
    assert "inside" in gcode_inside.lower(), "Should mention offset direction"

    # Test on-line (no offset)
    gcode_on = generate_contour_toolpath(box, config, offset_direction="on")
    assert len(gcode_on) > 0, "Should generate G-code for 'on' offset"


def test_depth_passes_calculation():
    """Test that multiple depth passes are generated correctly"""
    box = Box(50, 50, 12)

    config = ToolpathConfig(
        tool_diameter=6.35,
        spindle_rpm=18000,
        feed_rate=1500,
        plunge_rate=750,
        depth_of_cut=3.0,  # 3mm per pass
        total_depth=12.0    # Total depth 12mm
    )

    gcode = generate_contour_toolpath(box, config)

    # Should have 4 passes (12mm / 3mm per pass)
    # Count occurrences of pass comments
    import math
    expected_passes = math.ceil(12.0 / 3.0)

    # G-code should mention multiple passes
    assert f"{expected_passes} depth passes" in gcode, \
        f"Should mention {expected_passes} depth passes in G-code"


def test_gcode_has_comments():
    """Test that generated G-code includes helpful comments"""
    box = Box(50, 50, 12)
    gcode = generate_gcode_for_part(box)

    # Should have descriptive comments (lines starting with parentheses)
    assert "(" in gcode and ")" in gcode, "Should have comments"

    # Check for specific helpful comments
    lines = gcode.split('\n')
    comment_lines = [line for line in lines if line.strip().startswith('(')]

    assert len(comment_lines) > 0, "Should have at least some comment lines"


def test_extract_contours_handles_complex_shapes():
    """Test contour extraction from shapes with finger joints"""
    from parts.hamper import build_front_panel

    # Front panel has finger joints which create complex outer contour
    front = build_front_panel()
    contours = extract_contours(front)

    # Should successfully extract contours
    assert len(contours) > 0, "Should extract contours from complex shape"

    # Contour should have sufficient sampling points
    # With finger joints, outer contour will have many edges
    outer_contour = contours[0]

    # Each edge is sampled with 20 points (from cam.py line 121)
    # Front panel has many edges due to finger joints
    assert len(outer_contour) > 100, \
        "Complex shape with fingers should have many contour points"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
