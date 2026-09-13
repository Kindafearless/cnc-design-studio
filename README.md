# CNC Projects - AI-Assisted Parametric CAD Workflow

Parametric CAD design for Shapeoko 5 Pro CNC using **build123d** (Python) with Claude Code as the modeling co-pilot.

**Machine**: Shapeoko 5 Pro (4' x 4')
**Spindle**: Carbide 3D 1.2kW VFD (8k-24k RPM, ER-16 collets)
**Materials**: Aluminum 6061, hardwoods, plywood, plastics

## Philosophy

Replace manual Fusion 360 sketch-extrude work with **parametric Python CAD**:
- Design parts in code using build123d
- Tweak parameters, regenerate instantly
- Git version control for your part library
- Claude Code helps you model complex geometry
- Export STEP files → Fusion 360 for CAM only → G-code → Shapeoko

## Repository Structure

```
CNC/
├── parts/          # Parametric part designs (.py)
├── fixtures/       # Workholding jigs and fixtures
├── jigs/           # Shop jigs and tooling aids
├── lib/            # Shared libraries and machine config
│   ├── shapeoko.py      # Machine constraints, tool library
│   └── template.py      # Parametric part template
├── exports/        # Generated STEP files
├── pyproject.toml  # Poetry dependencies
└── README.md
```

## Setup

### 1. Install Dependencies

The project uses Python 3.12 with a virtual environment:

```bash
cd ~/Projects/CNC/cnc-design-studio
source .venv/bin/activate  # Activate the environment
```

Already installed:
- `build123d` - Parametric CAD library (OpenCascade backend)
- `ocp-vscode` - Live 3D preview in VS Code
- `pytest`, `black` - Testing and formatting tools

### 2. Install VS Code Extension

Install the **OCP CAD Viewer** extension in VS Code for live 3D preview:
1. Open VS Code
2. Extensions → search "OCP CAD Viewer"
3. Install and reload

### 3. Activate Environment

Always activate the virtual environment before working:

```bash
source .venv/bin/activate
```

## NEW: Web UI - CNC Design Studio 🎨

**All-in-one web interface: Design → Preview → G-code**

Launch the studio:
```bash
./run-studio.sh local
```

Open http://localhost:5000

Features:
- 3D preview with orbit controls
- Live parameter editing
- Direct G-code generation (no Fusion 360 needed!)
- Automatic toolpath generation
- Download STEP files and G-code

See [webapp/README.md](webapp/README.md) for full documentation.

## Workflow

### Option 1: Web UI (Recommended)

1. `./run-studio.sh local`
2. Select part → Edit parameters → Generate G-code
3. Download .nc file → Load in Carbide Motion → Cut!

### Option 2: Command Line

Creating a New Part

1. **Copy the template**:
   ```bash
   cp lib/template.py parts/my_bracket.py
   ```

2. **Edit parameters** in `parts/my_bracket.py`:
   ```python
   class PartParams:
       length = 100.0
       width = 50.0
       # ... adjust dimensions
   ```

3. **Define the geometry** in `build_part()`:
   ```python
   def build_part() -> Part:
       with BuildPart() as part:
           # Your parametric logic here
           Box(PartParams.length, PartParams.width, PartParams.height)
       return part.part
   ```

4. **Run and preview**:
   ```bash
   python parts/my_bracket.py
   ```
   - STEP file appears in `exports/`
   - 3D preview shows in VS Code (if ocp-vscode is active)

5. **Import to Fusion 360**:
   - File → Upload → Select STEP file
   - Go straight to **Manufacture** workspace (skip modeling)
   - Set up toolpaths using `lib/shapeoko.py` tool library

6. **Post-process and run**:
   - Post: `~/Library/Mobile Documents/com~apple~CloudDocs/CNC/Shapeoko Profiles/carbide3d.cps` (iCloud Drive › CNC › Shapeoko Profiles)
   - Save G-code (.nc file)
   - Load in Carbide Motion and cut!

## Example: Clothes Hamper

Your first project is a tall plywood clothes hamper with finger joints:

```bash
source .venv/bin/activate
python parts/hamper.py
```

**Features**:
- Parametric finger joints (auto-calculated spacing)
- Handle cutouts on front/back
- Optional bottom panel with slots
- All panels laid out flat for CNC cutting
- Fits on 4x4 plywood sheet

**CAM Recommendations**:
- Tool: 6mm (1/4") 2-flute endmill (`lib/shapeoko.py`: `em_6mm_2f`)
- Material: 12mm plywood
- Add 2-3 tabs per panel
- Feeds: 1500 mm/min, DOC: 3mm (see `shapeoko.PARAMS`)

## Machine Configuration

All machine constraints and tooling are defined in `lib/shapeoko.py`:

```python
from lib.shapeoko import (
    MachineConstraints,      # Work envelope, spindle specs
    Tolerances,              # Clearance fit, press fit, etc.
    StockSizes,             # Standard plywood/aluminum sizes
    TOOL_LIBRARY,           # Your endmills, v-bits, etc.
    CuttingParams,          # Material-specific feeds/speeds
)
```

### Key Constants

**Machine Limits**:
- Work area: 1219 x 1219 x 114 mm (48" x 48" x 4.5")
- Spindle: 8,000 - 24,000 RPM
- Max tool diameter: 10mm (3/8" ER-16 limit)

**Tolerances** (for press-fits, clearances):
- `Tolerances.CLEARANCE_FIT` = 0.2mm
- `Tolerances.SLIP_FIT` = 0.1mm
- `Tolerances.PRESS_FIT` = -0.05mm

**Tool Library**:
```python
get_tool("em_6mm_2f")       # 1/4" 2-flute general purpose
get_tool("em_6mm_3f_al")    # 1/4" 3-flute for aluminum
get_tool("vbit_90")         # 90° chamfer/deburr
```

## Tips for Claude Code

When working with Claude to model parts:

1. **Be specific about features**:
   - "Add 6mm mounting holes in each corner, 10mm from edges"
   - "Create finger joints with 25mm spacing"

2. **Reference the machine config**:
   - "Use `MachineConstraints.SAFE_X` to validate part size"
   - "Apply `Tolerances.SLIP_FIT` to the shaft hole"

3. **Iterate parametrically**:
   - "Make the bracket thicker by changing `thickness` param"
   - "Add a parameter for hole count"

4. **Git-friendly workflow**:
   ```bash
   git add parts/my_bracket.py
   git commit -m "Add electronics mounting bracket (v1)"
   ```

## Common Operations

**Check if part fits machine**:
```python
from lib.shapeoko import check_part_fits

if check_part_fits(length, width, height):
    print("Part fits!")
```

**Get cutting params for material**:
```python
from lib.shapeoko import CuttingParams

rpm, feed, doc, stepover = CuttingParams.get_params("plywood", 6.35)
# Returns: (18000, 1500, 3.0, 0.4)
```

**List available tools**:
```python
from lib.shapeoko import list_tools, ToolType

endmills = list_tools(ToolType.ENDMILL)
for tool in endmills:
    print(f"{tool.name}: {tool.diameter}mm, {tool.flutes}FL")
```

## Project Ideas

**Fixtures & Jigs**:
- Drill press table with T-track slots
- Angle drilling jig
- Doweling jig
- Router template guides

**Shop Projects**:
- Tool wall organizer (parametric pockets)
- Dust collection fittings
- Clamp storage rack

**Functional Parts**:
- Electronics enclosures
- Cable management clips
- Desk organizers

**Joinery Experiments**:
- Box joints (various pitches)
- Dovetails (CNC-friendly angles)
- Mortise and tenon templates

## Troubleshooting

**build123d not found**:
```bash
source .venv/bin/activate  # Make sure venv is activated
```

**OCP viewer not showing preview**:
- Check VS Code extension is installed
- Ensure `show_object()` is called in script
- View → Output → select "OCP CAD Viewer"

**Part doesn't fit on machine**:
- Check `lib/shapeoko.py` constraints
- Use `check_part_fits()` to validate
- Consider splitting into multiple parts

**Finger joints too tight/loose**:
- Adjust `clearance` parameter in your part file
- Test fit: start with 0.15mm, increase if needed
- Account for plywood thickness variance

## Resources

**build123d**:
- Docs: https://build123d.readthedocs.io/
- Examples: https://github.com/gumyr/build123d/tree/dev/examples

**Shapeoko**:
- Carbide 3D Community: https://community.carbide3d.com/
- Fusion 360 CAM tutorials: Carbide 3D YouTube

**Claude Code**:
- Docs: https://docs.claude.com/claude-code

## Contributing

This is your personal CNC library! As you build parts:

1. Keep them parametric (easy to adjust)
2. Document assumptions in comments
3. Commit working versions to git
4. Reuse patterns from `lib/template.py`

## License

Personal project - all designs are yours!
