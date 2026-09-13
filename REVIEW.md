# Code Review: Catching Up to Good

**Date**: April 25, 2026
**Scope**: Hamper finger joints, toolpath visualization, web UI enhancements

---

## Executive Summary

We've built working functionality, but skipped several best practices. Main issues:
- ❌ No tests written (TDD violated)
- ⚠️ Some symptoms fixed, not root causes
- ⚠️ Architecture has known brittleness
- ✅ Mission drift was moderate (stayed mostly focused)
- ❌ No git worktrees used for risky changes

**Priority**: Add tests first, then address architectural issues.

---

## Triple Loop Analysis

### Issue 1: Finger Joints Implementation

**What we did**: Added rectangular finger joints with fixed spacing

**Single Loop (Symptom Level)**:
- "Add finger joints to panels" ✓
- Works, joints interlock

**Double Loop (Assumptions/Goals)**:
- Are rectangular fingers optimal?
- Should clearance be constant across all joints?
- Is manual coordinate calculation the right approach?
- **Question**: Could we use a joinery library instead of hand-coding?

**Triple Loop (System/Context)**:
- Should we be designing joinery in CAD at all?
- Could the CNC post-processor handle this?
- Is there a parametric joinery system we could leverage?
- **Better approach**: Research existing solutions (like CadQuery's joinery helpers)

**Recommendation**:
- Current implementation is fine for learning
- Future: Investigate parametric joinery libraries
- Add parameter for finger taper (easier assembly)

---

### Issue 2: Toolpath Visualization

**What we did**: Fixed Vector bugs, added multi-part support

**Single Loop (Symptom Level)**:
- "Toolpath errored with Vector attribute issue"
- Fixed by changing `x` to `X` ✓

**Double Loop (Assumptions)**:
- Why did this happen TWICE?
- Are we accessing OCP objects correctly?
- Should we wrap these in our own types?

**Triple Loop (System)**:
- Should we generate toolpaths ourselves?
- Why not use existing CAM library (like OCCT's algorithms)?
- Is visualization the right tool for verification?

**Root Cause Analysis**:
```
Symptom: Vector attribute errors (happened twice!)
Why #1: Used lowercase instead of uppercase
Why #2: Didn't check build123d API docs
Why #3: No type hints (IDE couldn't help)
Why #4: No tests to catch before runtime
Why #5: No consistent pattern for Vector access
ROOT CAUSE: Missing type system + no tests
```

**Recommendation**:
- ✅ Add type hints to all Vector usage
- ✅ Create wrapper types with clear API
- ✅ Write tests for CAM functions
- 🔍 Research: Can we use existing CAM libraries?

---

### Issue 3: Assembly System

**What we did**: Manual rotation/translation for each panel

**Single Loop (Symptom)**:
- "Assembly view shows parts misaligned"
- Fixed by adjusting angles/positions

**Double Loop (Assumptions)**:
- Manual transforms are brittle
- No validation of correctness
- Hard to maintain/modify
- **We already noted**: Edge-based would be better

**Triple Loop (System)**:
- Should assembly be in CAD layer?
- Could we use constraints system?
- Is there an assembly library for build123d?

**Root Cause Analysis**:
```
Symptom: Brittle assembly positioning
Why #1: Manual math for each transform
Why #2: No relationship model between parts
Why #3: No automatic constraint solving
Why #4: Architecture doesn't capture design intent
Why #5: Treating symptoms (adjust angles) not cause
ROOT CAUSE: Missing constraint/relationship system
```

**Recommendation**:
- 📋 Future: Design proper assembly constraint system
- 📋 For now: Document the transform logic clearly
- ⚠️ This is a known architectural debt

---

## TDD Violations

**We implemented EVERYTHING without tests first!**

### What we should have tested:

#### Finger Joints
```python
# tests/test_finger_joints.py (MISSING!)

def test_finger_count():
    """Front panel should have 5 fingers per vertical edge"""
    # Forces us to make joints introspectable

def test_finger_spacing():
    """Fingers should be evenly spaced"""
    # Validates calculation logic

def test_finger_clearance():
    """Slots should be wider than fingers by clearance amount"""
    # Prevents fit issues

def test_bounding_box_with_fingers():
    """Fingers should extend panel bounds"""
    # We verified this manually - should be test!
```

#### Vector Usage
```python
# tests/test_vector_attributes.py (MISSING!)

def test_build123d_vector_has_uppercase_attrs():
    """Prevent future lowercase attribute bugs"""
    from build123d import Vector
    v = Vector(1, 2, 3)
    assert hasattr(v, 'X')
    assert hasattr(v, 'Y')
    assert hasattr(v, 'Z')
```

#### Toolpath Generation
```python
# tests/test_cam.py (MISSING!)

def test_extract_contours():
    """Should extract valid contours from part"""
    # Would have caught Vector bug before production!

def test_multi_part_toolpaths():
    """Should generate toolpath for each part in compound"""
    # Validates our API change
```

**Impact**: Bugs reached production that tests would have caught

**Recommendation**: **STOP** - Write tests before any new features

---

## Mission Drift Assessment

**Original Goal**: "Add finger joints to hamper for CNC cutting"

### In Scope ✅
- Finger joint geometry
- Integration with existing panels
- Toolpath generation for joints
- Clearance parameter

### Added Features (Scope Creep?)
- ⚠️ Multi-part toolpath visualization (useful but not core)
- ⚠️ Part visibility controls (nice-to-have)
- ⚠️ Toolpath legend (nice-to-have)
- ⚠️ Enhanced coordinate systems

### Avoided (Good!) ✅
- ✅ Didn't redesign entire CAM system
- ✅ Didn't add other joint types (dovetails, etc)
- ✅ Didn't refactor all of lib/shapeoko.py
- ✅ Stopped before physics simulation

**Assessment**: **Moderate drift** - Added useful features but lost some focus

**Learning**:
- Toolpath improvements were triggered by debugging, became feature work
- Should have documented as "future enhancement" and stayed focused
- Part visibility was legitimate UI improvement

---

## Git Worktree Missed Opportunities

**We made risky changes directly in main!**

### Should have used worktrees for:

1. **Finger Joint Implementation**
   ```bash
   # Should have done:
   git worktree add ../cnc-finger-joints feature/finger-joints

   # Why: Major geometry changes, risky
   # Benefit: Could keep working version while experimenting
   ```

2. **Toolpath API Changes**
   ```bash
   # Should have done:
   git worktree add ../cnc-multi-toolpath feature/multi-part-toolpath

   # Why: Breaking API change (toolpath → toolpaths array)
   # Benefit: Could A/B test old vs new approach
   ```

**Impact**: If changes had gone wrong, would have been harder to revert

**Recommendation**: Use worktrees for:
- Breaking API changes
- Major refactoring
- Experimental features

---

## Root Cause vs Symptom Fixes

### ✅ Good: Fixed Root Cause

**Vector Attribute Bug**:
- Could have: Added try/catch for AttributeError (symptom)
- Did instead: Fixed all Vector access to use uppercase (root cause)
- Result: Won't happen again

### ⚠️ Mixed: Symptom + Noted Root Cause

**Assembly Positioning**:
- Symptom: Adjusted rotation angles until it looked right
- Root cause noted: "Should use edge-based system"
- Status: Working but documented as technical debt

### ❌ Potential Symptom Fix

**Finger Joint Clearance**:
- If joints don't fit: "Add more clearance" (symptom)
- Root cause could be:
  - Material thickness variance
  - CNC accuracy
  - Thermal expansion
  - Calculation error
- **We need**: Real-world testing to validate

---

## Action Plan: Catching Up to Good

### Phase 1: Testing Foundation (DO FIRST)

**Priority: CRITICAL**

```bash
# 1. Create test structure
mkdir -p tests
touch tests/__init__.py
touch tests/test_finger_joints.py
touch tests/test_cam.py
touch tests/test_vectors.py
```

**Tests to write** (in order):
1. Vector attribute access (prevent regression)
2. Finger joint calculations (validate geometry)
3. Bounding box validation (ensure joints extend correctly)
4. Multi-part toolpath generation (validate API)

**Time estimate**: 2-3 hours
**Blocks**: All new feature work

---

### Phase 2: Type Safety

**Priority: HIGH**

Add type hints to prevent runtime errors:

```python
# Before
def extract_contours(part):
    # ...

# After
from build123d import Part, Vector
from typing import List, Tuple

def extract_contours(part: Part) -> List[List[Tuple[float, float]]]:
    # Now IDE can help us!
```

**Files to annotate**:
- `lib/cam.py` (most critical)
- `parts/hamper.py` (finger joint functions)
- `webapp/app.py` (API endpoints)

**Time estimate**: 1-2 hours

---

### Phase 3: Documentation Cleanup

**Priority: MEDIUM**

Document known issues and decisions:

1. Update `CLAUDE.md` with:
   - Known architectural debt (assembly system)
   - Tested vs untested code
   - Type coverage status

2. Add docstrings to key functions:
   ```python
   def build_front_panel() -> Part:
       """
       Build front hamper panel with finger joints.

       Finger joints:
       - 5 fingers on left/right edges (vertical)
       - 3 slots on bottom edge (horizontal)

       Coordinate system:
       - Panel built flat on XY plane
       - X = width, Y = height, Z = thickness
       - Fingers extend in -X (left) and +X (right)

       Returns:
           Part with integrated finger joints
       """
   ```

---

### Phase 4: Architectural Improvements (FUTURE)

**Priority: LOW (but document now)**

Issues to address later:

1. **Assembly System Refactor**
   - Research: build123d constraint solvers
   - Design: Edge-based attachment API
   - Implement: With tests first!

2. **CAM Library Research**
   - Evaluate: OCCT toolpath algorithms
   - Evaluate: FreeCAD Path workbench
   - Decision: Build vs buy

3. **Joinery Library**
   - Research: Existing parametric joinery
   - Evaluate: CadQuery joinery module
   - Consider: Extract our code into reusable library

---

## Immediate Next Steps

**Before writing ANY new features:**

1. **Write tests for existing code** (2-3 hours)
   ```bash
   # Test Vector access
   # Test finger joint math
   # Test toolpath generation
   ```

2. **Add type hints** (1-2 hours)
   ```bash
   # lib/cam.py first
   # Then other modules
   ```

3. **Document known issues** (30 min)
   ```bash
   # Update CLAUDE.md
   # Add TODO comments in code
   ```

4. **Git worktree practice** (15 min)
   ```bash
   # Create worktree for next feature
   # Get comfortable with workflow
   ```

**Total time to "catch up to good"**: ~4-6 hours

---

## Lessons Learned

### What Went Well ✅
- Working feature shipped quickly
- Identified issues (Vector bugs, assembly brittleness)
- Moderate scope control (didn't over-engineer)
- Good documentation (CLAUDE.md, DEVELOPMENT.md)

### What to Improve ❌
- **TDD**: Write tests BEFORE implementation
- **Worktrees**: Use for risky changes
- **Type hints**: Add as we write, not after
- **Root cause**: Dig deeper before fixing
- **Triple loop**: Ask system-level questions first

### New Habits to Build 🎯
1. Before coding: "What test should I write first?"
2. Before fixing: "What's the root cause?" (5 whys)
3. Before feature: "Triple loop - is this the right thing?"
4. Risky change? "Should this be a worktree?"
5. After commit: "Did we drift from the goal?"

---

## Conclusion

**Current State**: Working code with known issues and missing tests

**Path to Good**:
1. Add tests (retroactively)
2. Add type hints
3. Document known debt
4. Apply methodology going forward

**Estimated Effort**: 4-6 hours to catch up, then maintain discipline

**Key Insight**: We learned by doing, now we improve by testing and refactoring

---

*This review applies our DEVELOPMENT.md methodology to existing work. Future work will follow these practices from the start.*
