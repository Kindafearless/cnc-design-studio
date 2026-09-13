"""
Test Vector attribute access to prevent regression.

The build123d library uses OCP's Vector class which has UPPERCASE attributes (X, Y, Z).
This test ensures we don't accidentally use lowercase attributes which caused bugs in:
- lib/cam.py lines 125, 138
- webapp/app.py lines 438-440
"""

import pytest
from build123d import Vector, Axis


def test_vector_has_uppercase_attributes():
    """build123d Vectors use uppercase X, Y, Z attributes"""
    v = Vector(1.0, 2.0, 3.0)

    # Should have uppercase attributes
    assert hasattr(v, 'X'), "Vector should have uppercase X attribute"
    assert hasattr(v, 'Y'), "Vector should have uppercase Y attribute"
    assert hasattr(v, 'Z'), "Vector should have uppercase Z attribute"

    # Verify values are correct
    assert v.X == 1.0, f"Expected X=1.0, got {v.X}"
    assert v.Y == 2.0, f"Expected Y=2.0, got {v.Y}"
    assert v.Z == 3.0, f"Expected Z=3.0, got {v.Z}"


def test_vector_no_lowercase_attributes():
    """Verify that lowercase x, y, z attributes do NOT exist"""
    v = Vector(1.0, 2.0, 3.0)

    # Should NOT have lowercase attributes
    assert not hasattr(v, 'x'), "Vector should NOT have lowercase x attribute"
    assert not hasattr(v, 'y'), "Vector should NOT have lowercase y attribute"
    assert not hasattr(v, 'z'), "Vector should NOT have lowercase z attribute"


def test_vector_attribute_access_pattern():
    """Test the correct pattern for accessing Vector coordinates"""
    v = Vector(10.5, 20.3, 30.7)

    # Correct pattern: uppercase attributes
    x_coord = v.X
    y_coord = v.Y
    z_coord = v.Z

    assert x_coord == 10.5
    assert y_coord == 20.3
    assert z_coord == 30.7


def test_vector_to_tuple_conversion():
    """Test converting Vector to tuple for safe coordinate access"""
    v = Vector(5.0, 10.0, 15.0)

    # Safe pattern: convert to tuple
    coords = (v.X, v.Y, v.Z)

    assert coords == (5.0, 10.0, 15.0)
    assert len(coords) == 3


def test_bounding_box_vector_access():
    """Test accessing BoundBox min/max vectors (pattern from webapp/app.py:438-440)"""
    from build123d import Box

    box = Box(100, 200, 12)
    bbox = box.bounding_box()

    # This is the pattern we use in webapp/app.py
    min_coords = [bbox.min.X, bbox.min.Y, bbox.min.Z]
    max_coords = [bbox.max.X, bbox.max.Y, bbox.max.Z]
    size_coords = [bbox.size.X, bbox.size.Y, bbox.size.Z]

    # Verify structure is correct
    assert len(min_coords) == 3
    assert len(max_coords) == 3
    assert len(size_coords) == 3

    # Verify size values are reasonable
    assert abs(size_coords[0] - 100) < 0.01  # X size
    assert abs(size_coords[1] - 200) < 0.01  # Y size
    assert abs(size_coords[2] - 12) < 0.01   # Z size


def test_edge_position_vector_access():
    """Test accessing Vector from edge.position_at() (pattern from lib/cam.py:125,138)"""
    from build123d import Box

    box = Box(50, 50, 10)

    # Get top face
    top_face = box.faces().sort_by(Axis.Z)[-1]
    outer_wire = top_face.outer_wire()

    # Get first edge
    edges = outer_wire.edges()
    if len(edges) > 0:
        edge = edges[0]

        # This is the pattern we use in lib/cam.py
        pos = edge.position_at(0.5)  # Midpoint of edge

        # CORRECT: Uppercase attributes
        x_coord = pos.X
        y_coord = pos.Y

        # Verify we can access them
        assert isinstance(x_coord, (int, float))
        assert isinstance(y_coord, (int, float))


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
