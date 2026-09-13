"""
CNC Design Studio - Web UI for parametric CAD and CAM
Flask application for viewing designs, editing parameters, and generating G-code
"""

import sys
from pathlib import Path
import json
import tempfile

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify, request, send_file
from build123d import *
import importlib.util

# Import our libraries
from lib.cam import (
    generate_gcode_for_part, ToolpathConfig, generate_contour_toolpath,
    generate_sequenced_operations, Operation, OperationType
)
from lib.shapeoko import MachineConstraints, TOOL_LIBRARY

# Compatibility patch for cadquery-ocp 7.9+ (HashCode was removed, ocp-tessellate still expects it)
try:
    from OCP.TopoDS import TopoDS_Shape
    if not hasattr(TopoDS_Shape, 'HashCode'):
        def _hash_code(self, upper):
            """Compatibility shim for removed HashCode method"""
            return hash(self) % upper
        TopoDS_Shape.HashCode = _hash_code
except Exception:
    pass  # Ignore if patch fails

app = Flask(__name__)


def load_part_module(part_name: str):
    """Dynamically load a part module"""
    parts_dir = Path(__file__).parent.parent / "parts"
    part_file = parts_dir / f"{part_name}.py"

    if not part_file.exists():
        raise FileNotFoundError(f"Part {part_name} not found")

    spec = importlib.util.spec_from_file_location(part_name, part_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def part_to_mesh(part):
    """Convert build123d Part/Compound to mesh data for Three.js"""
    try:
        from build123d import export_stl
        import struct

        # Export to binary STL and parse it
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            export_stl(part, tmp.name)
            tmp_path = tmp.name

        try:
            # Read the binary STL file
            with open(tmp_path, 'rb') as f:
                # Skip 80-byte header
                f.read(80)

                # Read number of triangles (4 bytes, little-endian)
                num_triangles = struct.unpack('<I', f.read(4))[0]

                # Parse triangle data
                vertices = []
                triangles = []
                vertex_map = {}
                vertex_count = 0

                for i in range(num_triangles):
                    # Normal vector (3 floats, 12 bytes) - skip for now
                    f.read(12)

                    # 3 vertices (9 floats, 36 bytes)
                    tri_verts = []
                    for j in range(3):
                        x, y, z = struct.unpack('<fff', f.read(12))

                        # Deduplicate vertices
                        key = (round(x, 6), round(y, 6), round(z, 6))
                        if key not in vertex_map:
                            vertex_map[key] = vertex_count
                            vertices.extend([x, y, z])
                            vertex_count += 1
                        tri_verts.append(vertex_map[key])

                    triangles.extend(tri_verts)

                    # Attribute byte count (2 bytes) - skip
                    f.read(2)

            return {
                "vertices": vertices,
                "triangles": triangles,
                "normals": [],
                "edges": [],
            }
        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(tmp_path)
            except:
                pass

    except Exception as e:
        import traceback
        print(f"Error tessellating part: {e}")
        print(traceback.format_exc())

        # Fallback to simple placeholder
        return {
            "vertices": [
                0, 0, 0,  100, 0, 0,  100, 100, 0,  0, 100, 0,
                0, 0, 12,  100, 0, 12,  100, 100, 12,  0, 100, 12,
            ],
            "triangles": [0, 1, 2, 0, 2, 3, 4, 6, 5, 4, 7, 6],
            "normals": [],
            "edges": [],
        }


@app.route('/')
def index():
    """Main UI page"""
    return render_template('index.html')


@app.route('/api/parts')
def list_parts():
    """List available part designs"""
    parts_dir = Path(__file__).parent.parent / "parts"
    parts = []

    for part_file in parts_dir.glob("*.py"):
        if part_file.stem != "__init__":
            parts.append(part_file.stem)

    return jsonify({"parts": parts})


@app.route('/api/part/<part_name>')
def get_part(part_name):
    """Get part info and parameters"""
    try:
        module = load_part_module(part_name)

        # Get parameters if they exist
        params = {}
        if hasattr(module, "HamperParams"):  # Hamper-specific
            params_class = module.HamperParams
            params = {
                k: v for k, v in vars(params_class).items()
                if not k.startswith('_')
            }
        elif hasattr(module, "PartParams"):  # Generic parts
            params_class = module.PartParams
            params = {
                k: v for k, v in vars(params_class).items()
                if not k.startswith('_')
            }

        # Get metadata
        metadata = {
            "name": getattr(module, "PART_NAME", part_name),
            "version": getattr(module, "PART_VERSION", "v1"),
            "description": getattr(module, "DESCRIPTION", ""),
            "material": getattr(module, "MATERIAL", "unknown"),
            "stock_thickness": getattr(module, "STOCK_THICKNESS", 12.0),
        }

        return jsonify({
            "success": True,
            "metadata": metadata,
            "parameters": params
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/part/<part_name>/preview')
def preview_part(part_name):
    """Generate 3D preview mesh for a part"""
    try:
        module = load_part_module(part_name)

        # Get updated parameters from query string
        params = request.args.to_dict()

        # Extract view mode (flat/assembled) and remove from params
        view_mode = params.pop('view_mode', 'flat')

        # Update module parameters if provided
        if params and hasattr(module, "HamperParams"):
            for key, value in params.items():
                if hasattr(module.HamperParams, key):
                    # Convert string to appropriate type
                    current_val = getattr(module.HamperParams, key)
                    if isinstance(current_val, float):
                        setattr(module.HamperParams, key, float(value))
                    elif isinstance(current_val, int):
                        setattr(module.HamperParams, key, int(value))
                    elif isinstance(current_val, bool):
                        setattr(module.HamperParams, key, value.lower() == 'true')

        # Build the part based on view mode
        if hasattr(module, "build_hamper"):
            if view_mode == 'assembled' and hasattr(module, "build_hamper_assembled"):
                part = module.build_hamper_assembled()
                # Convert to single mesh for assembled view
                mesh_data = part_to_mesh(part)
                if mesh_data is None:
                    return jsonify({"success": False, "error": "Failed to generate mesh"}), 500
                return jsonify({
                    "success": True,
                    "mesh": mesh_data
                })
            else:
                # For flat view, return individual parts
                if hasattr(module, "get_hamper_parts"):
                    parts_dict = module.get_hamper_parts()
                    meshes = {}
                    for name, part in parts_dict.items():
                        mesh_data = part_to_mesh(part)
                        if mesh_data:
                            meshes[name] = mesh_data

                    if not meshes:
                        return jsonify({"success": False, "error": "Failed to generate meshes"}), 500

                    return jsonify({
                        "success": True,
                        "parts": meshes  # Return multiple parts
                    })
                else:
                    # Fallback to single mesh
                    part = module.build_hamper()
                    mesh_data = part_to_mesh(part)
                    if mesh_data is None:
                        return jsonify({"success": False, "error": "Failed to generate mesh"}), 500
                    return jsonify({
                        "success": True,
                        "mesh": mesh_data
                    })
        elif hasattr(module, "build_part"):
            part = module.build_part()
            # Convert to mesh
            mesh_data = part_to_mesh(part)
            if mesh_data is None:
                return jsonify({"success": False, "error": "Failed to generate mesh"}), 500
            return jsonify({
                "success": True,
                "mesh": mesh_data
            })
        else:
            return jsonify({"success": False, "error": "No build function found"}), 500

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/part/<part_name>/gcode', methods=['POST'])
def generate_gcode(part_name):
    """Generate G-code for a part"""
    try:
        data = request.json
        module = load_part_module(part_name)

        # Update parameters if provided
        params = data.get('parameters', {})
        if params and hasattr(module, "HamperParams"):
            for key, value in params.items():
                if hasattr(module.HamperParams, key):
                    setattr(module.HamperParams, key, value)

        # Build the part
        if hasattr(module, "build_hamper"):
            compound = module.build_hamper()
            # For compound (multiple parts), process first part
            parts = compound.children if hasattr(compound, 'children') else [compound]
            part = parts[0] if parts else compound
        elif hasattr(module, "build_part"):
            part = module.build_part()
        else:
            return jsonify({"success": False, "error": "No build function found"}), 500

        # Get CAM config from request
        cam_config = data.get('cam_config', {})
        tool_diameter = cam_config.get('tool_diameter', 6.35)
        material_thickness = cam_config.get('material_thickness', 12.0)
        spindle_rpm = cam_config.get('spindle_rpm', 18000)
        feed_rate = cam_config.get('feed_rate', 1500)
        depth_of_cut = cam_config.get('depth_of_cut', 3.0)

        # Toolpath origin positioning (default: lower-left corner at machine origin)
        zero_to_lower_left = cam_config.get('zero_to_lower_left', True)
        origin_x = cam_config.get('origin_x', 0.0)
        origin_y = cam_config.get('origin_y', 0.0)

        # Generate G-code
        gcode = generate_gcode_for_part(
            part,
            tool_diameter=tool_diameter,
            material_thickness=material_thickness,
            spindle_rpm=spindle_rpm,
            feed_rate=feed_rate,
            depth_of_cut=depth_of_cut,
            zero_to_lower_left=zero_to_lower_left,
            origin_x=origin_x,
            origin_y=origin_y
        )

        return jsonify({
            "success": True,
            "gcode": gcode,
            "lines": len(gcode.split('\n'))
        })

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/part/<part_name>/export/step', methods=['POST'])
def export_step(part_name):
    """Export part as STEP file"""
    try:
        from build123d import export_step as bd_export

        data = request.json
        module = load_part_module(part_name)

        # Build the part
        if hasattr(module, "build_hamper"):
            part = module.build_hamper()
        elif hasattr(module, "build_part"):
            part = module.build_part()
        else:
            return jsonify({"success": False, "error": "No build function found"}), 500

        # Export to temp file
        with tempfile.NamedTemporaryFile(suffix='.step', delete=False) as tmp:
            bd_export(part, tmp.name)
            return send_file(
                tmp.name,
                as_attachment=True,
                download_name=f"{part_name}.step",
                mimetype='application/step'
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all saved projects"""
    try:
        projects_dir = Path(__file__).parent.parent / "projects"
        projects_dir.mkdir(exist_ok=True)

        projects = []
        for project_file in projects_dir.glob("*.json"):
            try:
                with open(project_file, 'r') as f:
                    data = json.load(f)
                    projects.append({
                        "name": project_file.stem,
                        "part_name": data.get("part_name", "unknown"),
                        "modified": project_file.stat().st_mtime
                    })
            except Exception:
                continue

        # Sort by modification time (most recent first)
        projects.sort(key=lambda x: x["modified"], reverse=True)

        return jsonify({"success": True, "projects": projects})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/projects/<project_name>', methods=['GET'])
def load_project(project_name):
    """Load a saved project"""
    try:
        projects_dir = Path(__file__).parent.parent / "projects"
        project_file = projects_dir / f"{project_name}.json"

        if not project_file.exists():
            return jsonify({"success": False, "error": "Project not found"}), 404

        with open(project_file, 'r') as f:
            project_data = json.load(f)

        return jsonify({"success": True, "project": project_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/projects/<project_name>', methods=['POST'])
def save_project(project_name):
    """Save project state"""
    try:
        projects_dir = Path(__file__).parent.parent / "projects"
        projects_dir.mkdir(exist_ok=True)

        project_data = request.json
        project_file = projects_dir / f"{project_name}.json"

        with open(project_file, 'w') as f:
            json.dump(project_data, f, indent=2)

        return jsonify({"success": True, "message": f"Project '{project_name}' saved"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/projects/<project_name>', methods=['DELETE'])
def delete_project(project_name):
    """Delete a saved project"""
    try:
        projects_dir = Path(__file__).parent.parent / "projects"
        project_file = projects_dir / f"{project_name}.json"

        if not project_file.exists():
            return jsonify({"success": False, "error": "Project not found"}), 404

        project_file.unlink()
        return jsonify({"success": True, "message": f"Project '{project_name}' deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tools')
def list_tools():
    """List available tools and materials from tool library"""
    try:
        tool_library_file = Path(__file__).parent.parent / "lib" / "tool_library.json"
        with open(tool_library_file, 'r') as f:
            tool_library = json.load(f)
        return jsonify(tool_library)
    except Exception as e:
        # Fallback to Python tool library if JSON not found
        tools = []
        for key, tool in TOOL_LIBRARY.items():
            tools.append({
                "id": key,
                "name": tool.name,
                "diameter_mm": tool.diameter,
                "flutes": tool.flutes,
                "type": tool.type.value,
                "material": tool.material,
                "notes": tool.notes
            })
        return jsonify({"tools": tools, "materials": [], "cutting_params": {}})


@app.route('/api/machine')
def machine_info():
    """Get machine constraints"""
    return jsonify({
        "x_travel": MachineConstraints.X_TRAVEL,
        "y_travel": MachineConstraints.Y_TRAVEL,
        "z_travel": MachineConstraints.Z_TRAVEL,
        "spindle_min_rpm": MachineConstraints.SPINDLE_MIN_RPM,
        "spindle_max_rpm": MachineConstraints.SPINDLE_MAX_RPM,
        "spindle_power_w": MachineConstraints.SPINDLE_POWER_W,
    })


@app.route('/api/part/<part_name>/toolpath', methods=['POST'])
def get_toolpath(part_name):
    """Get toolpath visualization data"""
    try:
        import re
        data = request.json
        module = load_part_module(part_name)

        # Update parameters if provided
        params = data.get('parameters', {})
        if params and hasattr(module, "HamperParams"):
            for key, value in params.items():
                if hasattr(module.HamperParams, key):
                    setattr(module.HamperParams, key, value)

        # Build the part
        if hasattr(module, "get_hamper_parts"):
            # Use get_hamper_parts() to get individual parts
            parts_dict = module.get_hamper_parts()
            part_names = list(parts_dict.keys())
            parts_list = list(parts_dict.values())

            # Get which parts to process from request (default: all)
            visible_parts = data.get('visible_parts', part_names)

        elif hasattr(module, "build_part"):
            parts_list = [module.build_part()]
            part_names = ['part']
            visible_parts = ['part']
        else:
            return jsonify({"success": False, "error": "No build function found"}), 500

        # Get CAM config from request
        cam_config = data.get('cam_config', {})
        tool_diameter = cam_config.get('tool_diameter', 6.35)
        material_thickness = cam_config.get('material_thickness', 12.0)
        spindle_rpm = cam_config.get('spindle_rpm', 18000)
        feed_rate = cam_config.get('feed_rate', 1500)
        depth_of_cut = cam_config.get('depth_of_cut', 3.0)

        # Generate toolpaths for each visible part
        all_toolpaths = []

        # Check if module supports multi-operation workflow
        # Look for get_<part_type>_operations function (e.g., get_hamper_operations)
        operations_func_name = None
        if hasattr(module, "get_hamper_operations"):
            operations_func_name = "get_hamper_operations"
        # Add more operation function names here as needed

        for idx, part in enumerate(parts_list):
            if idx >= len(part_names):
                break

            part_name = part_names[idx]

            # Skip if not visible
            if part_name not in visible_parts:
                continue

            # Get part bounding box to determine its position
            bbox = part.bounding_box()

            # Try to use multi-operation workflow if available
            if operations_func_name:
                operations_func = getattr(module, operations_func_name)
                operations = operations_func(part_name, part)

                if operations:
                    # Generate sequenced operations
                    result = generate_sequenced_operations(operations)
                    gcode = result['gcode']

                    print(f"\n=== TOOLPATH DEBUG for {part_name} ===")
                    print(f"Operations count: {len(operations)}")
                    print(f"G-code length: {len(gcode)} chars, {len(gcode.splitlines())} lines")
                    print(f"First 500 chars of G-code:\n{gcode[:500]}")

                    # Parse G-code to extract toolpath, categorized by operation
                    operation_toolpaths = []

                    # Split G-code by operation markers
                    gcode_sections = []
                    current_section = []
                    current_op_name = "initialization"

                    for line in gcode.split('\n'):
                        if '(--- Operation' in line:
                            if current_section:
                                gcode_sections.append((current_op_name, '\n'.join(current_section)))
                            current_section = []
                            # Extract operation name from comment
                            import re as re_module
                            match = re_module.search(r'Operation \d+: (.+) ---', line)
                            if match:
                                current_op_name = match.group(1)
                        else:
                            current_section.append(line)

                    if current_section:
                        gcode_sections.append((current_op_name, '\n'.join(current_section)))

                    print(f"Found {len(gcode_sections)} G-code sections:")
                    for i, (name, code) in enumerate(gcode_sections):
                        print(f"  Section {i}: {name} ({len(code)} chars, {len(code.splitlines())} lines)")

                    # Parse each operation's G-code
                    for op_idx, (op_name, op_gcode) in enumerate(gcode_sections):
                        rapid_moves = []
                        feed_moves = []
                        drill_points = []
                        current_pos = [0, 0, 0]

                        # Determine operation type from the operations list
                        op_type = "contour"  # default
                        if op_idx < len(operations):
                            op_type = operations[op_idx].op_type.value

                        for line in op_gcode.split('\n'):
                            line = line.strip()
                            if not line or line.startswith('(') or line.startswith('%'):
                                continue

                            # Extract coordinates
                            x_match = re.search(r'X([-\d.]+)', line)
                            y_match = re.search(r'Y([-\d.]+)', line)
                            z_match = re.search(r'Z([-\d.]+)', line)

                            new_pos = current_pos.copy()
                            if x_match:
                                new_pos[0] = float(x_match.group(1))
                            if y_match:
                                new_pos[1] = float(y_match.group(1))
                            if z_match:
                                new_pos[2] = float(z_match.group(1))

                            # Categorize move type
                            if line.startswith('G0'):  # Rapid move
                                rapid_moves.append([current_pos.copy(), new_pos.copy()])
                                current_pos = new_pos
                            elif line.startswith('G1'):  # Feed move
                                feed_moves.append([current_pos.copy(), new_pos.copy()])
                                current_pos = new_pos

                        operation_toolpaths.append({
                            "name": op_name,
                            "type": op_type,
                            "rapid_moves": rapid_moves,
                            "feed_moves": feed_moves
                        })

                    material_bounds = {
                        "min": [bbox.min.X, bbox.min.Y, bbox.min.Z],
                        "max": [bbox.max.X, bbox.max.Y, bbox.max.Z],
                        "size": [bbox.max.X - bbox.min.X, bbox.max.Y - bbox.min.Y, bbox.max.Z - bbox.min.Z]
                    }

                    all_toolpaths.append({
                        "name": part_name,
                        "operations": operation_toolpaths,
                        "material_bounds": material_bounds,
                        "multi_operation": True
                    })
                    continue

            # Fall back to single-operation workflow for parts without operations function
            # Generate G-code for this part
            # Don't use zero_to_lower_left since parts are already positioned
            gcode = generate_gcode_for_part(
                part,
                tool_diameter=tool_diameter,
                material_thickness=material_thickness,
                spindle_rpm=spindle_rpm,
                feed_rate=feed_rate,
                depth_of_cut=depth_of_cut,
                zero_to_lower_left=False,
                origin_x=0.0,
                origin_y=0.0
            )

            # Parse G-code to extract toolpath
            rapid_moves = []  # G0 moves (travel)
            feed_moves = []   # G1 moves (cutting)
            current_pos = [0, 0, 0]

            for line in gcode.split('\n'):
                line = line.strip()
                if not line or line.startswith('(') or line.startswith('%'):
                    continue

                # Extract coordinates
                x_match = re.search(r'X([-\d.]+)', line)
                y_match = re.search(r'Y([-\d.]+)', line)
                z_match = re.search(r'Z([-\d.]+)', line)

                new_pos = current_pos.copy()
                if x_match:
                    new_pos[0] = float(x_match.group(1))
                if y_match:
                    new_pos[1] = float(y_match.group(1))
                if z_match:
                    new_pos[2] = float(z_match.group(1))

                # Categorize move type
                if line.startswith('G0'):  # Rapid move
                    rapid_moves.append([current_pos.copy(), new_pos.copy()])
                    current_pos = new_pos
                elif line.startswith('G1'):  # Feed move
                    feed_moves.append([current_pos.copy(), new_pos.copy()])
                    current_pos = new_pos

            # Use bounding box calculated earlier
            material_bounds = {
                "min": [bbox.min.X, bbox.min.Y, bbox.min.Z],
                "max": [bbox.max.X, bbox.max.Y, bbox.max.Z],
                "size": [bbox.size.X, bbox.size.Y, bbox.size.Z]
            }

            all_toolpaths.append({
                "name": part_name,
                "rapid_moves": rapid_moves,
                "feed_moves": feed_moves,
                "material_bounds": material_bounds,
                "multi_operation": False
            })

        return jsonify({
            "success": True,
            "toolpaths": all_toolpaths
        })

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))  # Default to 5001 to avoid AirPlay conflict
    print("="*60)
    print("CNC Design Studio")
    print("="*60)
    print(f"Starting server on http://localhost:{port}")
    print("Open your browser to view designs and generate G-code")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=True)
