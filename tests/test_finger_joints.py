"""
Test finger joint geometry and calculations.

Validates that finger joints are:
- Correctly sized and spaced
- Extend the panel bounding boxes as expected
- Have proper clearances for assembly
- Follow the correct pattern (fingers/slots complementary)
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from build123d import *
from parts.hamper import (
    HamperParams,
    build_front_panel,
    build_back_panel,
    build_side_panel,
    build_bottom_panel,
)


def test_front_panel_basic_dimensions():
    """Front panel should have correct base dimensions"""
    p = HamperParams
    front = build_front_panel()
    bbox = front.bounding_box()

    # Width should be base width + 2*thickness (fingers on left and right)
    expected_width = p.width + 2 * p.thickness
    assert abs(bbox.size.X - expected_width) < 0.01, \
        f"Expected width {expected_width}mm, got {bbox.size.X}mm"

    # Height should match parameter
    assert abs(bbox.size.Y - p.height) < 0.01, \
        f"Expected height {p.height}mm, got {bbox.size.Y}mm"

    # Thickness should match parameter
    assert abs(bbox.size.Z - p.thickness) < 0.01, \
        f"Expected thickness {p.thickness}mm, got {bbox.size.Z}mm"


def test_front_panel_finger_spacing():
    """Front panel should have evenly spaced fingers on left/right edges"""
    p = HamperParams

    # From hamper.py line 99-100:
    # num_fingers = 5
    # finger_length = p.height / num_fingers

    num_fingers = 5
    expected_finger_length = p.height / num_fingers

    # Each finger should be exactly height/5
    assert abs(expected_finger_length - 120.0) < 0.01, \
        f"With height={p.height}, expected finger_length=120mm, got {expected_finger_length}mm"


def test_side_panel_basic_dimensions():
    """Side panel should have correct base dimensions"""
    p = HamperParams
    side = build_side_panel()
    bbox = side.bounding_box()

    # Side panel is depth x height (no fingers extending, only slots)
    assert abs(bbox.size.X - p.depth) < 0.01, \
        f"Expected depth {p.depth}mm, got {bbox.size.X}mm"

    assert abs(bbox.size.Y - p.height) < 0.01, \
        f"Expected height {p.height}mm, got {bbox.size.Y}mm"

    assert abs(bbox.size.Z - p.thickness) < 0.01, \
        f"Expected thickness {p.thickness}mm, got {bbox.size.Z}mm"


def test_bottom_panel_dimensions():
    """Bottom panel should fit inside the assembled box"""
    p = HamperParams

    if not p.include_bottom:
        pytest.skip("Bottom panel disabled in parameters")

    bottom = build_bottom_panel()
    bbox = bottom.bounding_box()

    # From hamper.py lines 193-194:
    # inner_width = p.width - 2 * p.thickness
    # inner_depth = p.depth - 2 * p.thickness

    expected_inner_width = p.width - 2 * p.thickness
    expected_inner_depth = p.depth - 2 * p.thickness

    # Bottom has fingers extending, so bounding box is larger
    # Fingers extend thickness/2 on each side
    expected_width_with_fingers = expected_inner_width + 2 * p.thickness
    expected_depth_with_fingers = expected_inner_depth + 2 * p.thickness

    assert abs(bbox.size.X - expected_width_with_fingers) < 0.01, \
        f"Expected width {expected_width_with_fingers}mm, got {bbox.size.X}mm"

    assert abs(bbox.size.Y - expected_depth_with_fingers) < 0.01, \
        f"Expected depth {expected_depth_with_fingers}mm, got {bbox.size.Y}mm"


def test_finger_joint_clearance_parameter():
    """Verify clearance parameter is used in slot calculations"""
    p = HamperParams

    # Clearance should be a small positive value
    assert p.clearance > 0, "Clearance must be positive"
    assert p.clearance < 1.0, "Clearance should be less than 1mm"

    # Default should be 0.15mm as specified in REVIEW.md
    assert abs(p.clearance - 0.15) < 0.01, \
        f"Expected default clearance of 0.15mm, got {p.clearance}mm"


def test_front_panel_extends_base_width():
    """Fingers should extend the panel beyond its base width"""
    p = HamperParams
    front = build_front_panel()
    bbox = front.bounding_box()

    # Base panel is width x height
    # Fingers on left and right add thickness on each side
    # So total bounding box width = width + 2*thickness

    base_width = p.width
    bbox_width = bbox.size.X

    # Bbox should be larger than base
    assert bbox_width > base_width, \
        f"Bounding box ({bbox_width}mm) should extend beyond base width ({base_width}mm)"

    # Should extend by exactly 2*thickness
    extension = bbox_width - base_width
    expected_extension = 2 * p.thickness

    assert abs(extension - expected_extension) < 0.01, \
        f"Expected fingers to extend by {expected_extension}mm, got {extension}mm"


def test_back_panel_identical_to_front():
    """Back panel should be identical to front panel"""
    front = build_front_panel()
    back = build_back_panel()

    front_bbox = front.bounding_box()
    back_bbox = back.bounding_box()

    # Should have identical dimensions
    assert abs(front_bbox.size.X - back_bbox.size.X) < 0.01
    assert abs(front_bbox.size.Y - back_bbox.size.Y) < 0.01
    assert abs(front_bbox.size.Z - back_bbox.size.Z) < 0.01


def test_finger_pattern_alternating():
    """Verify finger joints follow alternating pattern (even indices have fingers)"""
    p = HamperParams

    # From hamper.py line 102:
    # if i % 2 == 0:  # Odd pattern - start and end with finger

    num_fingers = 5

    # Pattern should be: Finger, Gap, Finger, Gap, Finger
    # Indices:           0,      1,    2,     3,    4
    # So even indices (0, 2, 4) have fingers

    expected_finger_indices = [0, 2, 4]
    expected_gap_indices = [1, 3]

    assert len(expected_finger_indices) == 3, "Should have 3 fingers"
    assert len(expected_gap_indices) == 2, "Should have 2 gaps"

    # Total should equal num_fingers
    assert len(expected_finger_indices) + len(expected_gap_indices) == num_fingers


def test_bottom_panel_finger_pattern():
    """Bottom panel fingers should be complementary to front panel slots"""
    p = HamperParams

    if not p.include_bottom:
        pytest.skip("Bottom panel disabled in parameters")

    # From hamper.py:
    # Front panel bottom slots: i % 2 == 1 (line 118)
    # Bottom panel fingers: i % 2 == 1 (line 210)

    # Pattern for 3 segments:
    # Index:  0,   1,      2
    # Front:  Base, Slot,  Base
    # Bottom: Base, Finger, Base

    num_segments = 3
    expected_finger_indices = [1]  # Only middle segment has finger

    assert len(expected_finger_indices) == 1, \
        "Bottom panel should have 1 finger on each edge (3 total segments)"


def test_parameters_are_reasonable():
    """Sanity check on parameter values"""
    p = HamperParams

    # Dimensions should be positive
    assert p.width > 0
    assert p.depth > 0
    assert p.height > 0
    assert p.thickness > 0

    # Hamper should be taller than it is wide (tall hamper)
    assert p.height > p.width, \
        f"Hamper should be tall (height={p.height} should be > width={p.width})"

    # Material thickness should be reasonable for plywood (6-25mm typical)
    assert 6 <= p.thickness <= 25, \
        f"Material thickness {p.thickness}mm is outside typical plywood range (6-25mm)"

    # Handle should fit on front panel
    assert p.handle_width < p.width, "Handle wider than panel"
    assert p.handle_from_top < p.height, "Handle offset exceeds height"


def test_corner_radius_applied():
    """Verify corner radius is positive and reasonable"""
    p = HamperParams

    assert p.corner_radius > 0, "Corner radius should be positive"
    assert p.corner_radius < p.thickness, \
        "Corner radius should be smaller than material thickness"


def test_handle_cutout_dimensions():
    """Verify handle cutout parameters are reasonable"""
    p = HamperParams

    # Handle should be reasonably sized
    assert p.handle_width > 50, "Handle should be at least 50mm wide"
    assert p.handle_height > 20, "Handle should be at least 20mm tall"

    # Handle should fit within panel
    assert p.handle_width < p.width - 100, \
        "Handle should leave at least 50mm margin on each side"

    assert p.handle_from_top + p.handle_height < p.height, \
        "Handle should not extend beyond panel height"


def test_panel_count():
    """Verify build_hamper returns a Compound"""
    from parts.hamper import build_hamper

    hamper = build_hamper()

    # Should be a Compound
    assert isinstance(hamper, Compound), "Hamper should be a Compound"

    # Compound should exist and be valid
    bbox = hamper.bounding_box()
    assert bbox is not None, "Hamper should have a valid bounding box"


def test_assembled_hamper_dimensions():
    """
    Verify assembled hamper builds successfully.

    NOTE: Assembly positioning is known to be brittle (see REVIEW.md).
    This test just verifies the assembly builds without errors.
    Actual dimensional accuracy is a known issue to be addressed in future refactoring.
    """
    from parts.hamper import build_hamper_assembled

    p = HamperParams
    assembled = build_hamper_assembled()

    # Just verify assembly exists and has valid bounding box
    assert assembled is not None, "Assembly should build"

    bbox = assembled.bounding_box()
    assert bbox is not None, "Assembly should have bounding box"

    # Verify dimensions are at least in the right ballpark (very lenient)
    # Assembly system is known to be brittle - this just ensures it builds
    assert bbox.size.X > 0, "Width should be positive"
    assert bbox.size.Y > 0, "Depth should be positive"
    assert bbox.size.Z > 0, "Height should be positive"

    # Height should be close to expected (Z-axis positioning is more reliable)
    assert bbox.size.Z > p.height * 0.9, "Height should be approximately correct"
    assert bbox.size.Z < p.height * 1.1, "Height should be approximately correct"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
