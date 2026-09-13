# Development Methodology

This document outlines the development practices and strategies for the CNC Design Studio project.

## Core Principles

### 1. Triple Loop Learning Strategy

Always approach problems at the appropriate level:

**Single Loop (Symptomatic Fix)**
- "The toolpath is showing an error"
- Fix: Patch the immediate bug
- Risk: Doesn't address underlying issues

**Double Loop (Assumptions/Goals)**
- "Why is the toolpath failing?"
- Fix: Question the approach - maybe the data structure is wrong
- Better: Rethink how we generate and pass toolpath data

**Triple Loop (System/Context)**
- "Should we even be generating toolpaths this way?"
- Fix: Question the entire architecture
- Best: Consider if there's a better pattern/library/approach

**Application**: Start with triple loop questions, then work down to implementation.

### 2. Root Cause Over Symptoms

**Bad**: "The finger joints don't fit - add 0.5mm clearance"
**Good**: "The finger joints don't fit - why? Is it:"
- Material thickness variance?
- CNC accuracy issues?
- Design calculation error?
- Incorrect coordinate system?

**Process**:
1. Observe the symptom
2. Ask "why?" at least 5 times
3. Identify the root cause
4. Fix that, not the symptom
5. Verify the symptom is resolved

### 3. Use Git Worktrees

For parallel development or risky experiments:

```bash
# Create a worktree for feature development
git worktree add ../cnc-worktree-finger-joints feature/finger-joints

# Work in isolation
cd ../cnc-worktree-finger-joints

# When done
git worktree remove ../cnc-worktree-finger-joints
```

**When to use worktrees**:
- Major refactoring (like implementing edge-based assembly)
- Risky architectural changes
- Need to compare before/after side-by-side
- Long-running feature development

**When NOT to use**:
- Simple bug fixes
- Small incremental changes
- Quick experiments

### 4. Test-Driven Development (TDD)

**Process**:
1. Write the test first (it will fail)
2. Write minimal code to make it pass
3. Refactor
4. Repeat

**Example for finger joints**:

```python
# 1. Write test first
def test_finger_joint_spacing():
    """Fingers should be evenly spaced along edge"""
    panel = build_front_panel()
    bbox = panel.bounding_box()

    # Should have 5 fingers on left edge
    # Spacing should be height / 5
    expected_spacing = HamperParams.height / 5
    assert finger_spacing == expected_spacing

# 2. Run test (it fails)
# 3. Implement the feature
# 4. Run test (it passes)
# 5. Refactor if needed
```

**Benefits**:
- Prevents regression
- Documents expected behavior
- Forces thinking about edge cases
- Makes refactoring safer

### 5. Watch for Mission Drift

**Scenario**: "Let's add finger joints to the hamper"

**Mission Drift Examples**:
- ❌ "While I'm at it, let me redesign the entire assembly system"
- ❌ "I should also add dovetails and mortise-tenon joints"
- ❌ "Let me refactor the entire CAM library first"

**Stay Focused**:
- ✅ Add finger joints to hamper
- ✅ Make them adjustable via parameters
- ✅ Verify they integrate with toolpath generation
- ✅ Document the implementation

**Process**:
- Start each task with clear objective
- List what's in scope vs out of scope
- When tempted to add features, ask: "Is this needed for the original goal?"
- Keep a "future ideas" list for valid but out-of-scope improvements

### 6. Use Appropriate Sub-Agents

Leverage the Task tool with the right model for the job:

**Haiku (Fast, Simple)**
- File searches
- Simple code reading
- Basic refactoring
- Running tests
- Documentation updates

```python
Task(
    subagent_type="Explore",
    model="haiku",  # Fast and cheap
    prompt="Find all files that use the Vector class"
)
```

**Sonnet (Default, Balanced)**
- Feature implementation
- Bug investigation
- Code review
- Architecture decisions
- Most development work

```python
Task(
    subagent_type="general-purpose",
    # model defaults to sonnet
    prompt="Implement finger joint calculations with proper validation"
)
```

**Opus (Complex, Thorough)**
- Major refactoring
- Complex architectural changes
- Critical bug fixes
- Security-sensitive code

```python
Task(
    subagent_type="general-purpose",
    model="opus",  # Most capable
    prompt="Redesign the assembly system to use edge-based attachments"
)
```

**Guidelines**:
- Default to Sonnet for most work
- Use Haiku for quick searches and simple tasks
- Use Opus sparingly for complex/critical work
- Consider cost vs benefit

## Workflow Template

For each new feature or bug fix:

### 1. Discovery (Triple Loop)
```
Triple Loop Questions:
- Is this the right feature to build?
- Are we solving the right problem?
- Is there a simpler approach?

Double Loop:
- What assumptions are we making?
- What's the goal we're trying to achieve?

Single Loop:
- What's the immediate fix?
```

### 2. Root Cause Analysis
```
Symptom: [What we observe]
Why #1: [First level cause]
Why #2: [Deeper cause]
Why #3: [Even deeper]
Why #4: [Getting to root]
Why #5: [Root cause]

Root Cause: [The real issue]
Fix Strategy: [How to address the root]
```

### 3. Test-Driven Development
```bash
# 1. Create test file
touch tests/test_new_feature.py

# 2. Write failing test
# 3. Run test (verify it fails)
pytest tests/test_new_feature.py

# 4. Implement feature
# 5. Run test (verify it passes)
# 6. Refactor
```

### 4. Implementation
```
Scope:
- [ ] Feature A
- [ ] Feature B
- [ ] Documentation

Out of Scope (Future):
- [ ] Nice-to-have Feature X
- [ ] Optimization Y
```

### 5. Review
```
Mission Check:
- Did we solve the original problem?
- Did we drift from the goal?
- Are there unnecessary additions?

Quality Check:
- Tests passing?
- Documentation updated?
- No regressions?
```

## Git Worktree Examples

### Major Refactoring
```bash
# Current: Manual assembly positioning
# Goal: Edge-based assembly system

git worktree add ../cnc-edge-based-assembly feature/edge-based-assembly
cd ../cnc-edge-based-assembly

# Make changes, test extensively
# Compare old vs new approach
# Merge when stable
```

### A/B Testing
```bash
# Compare two CAM strategies
git worktree add ../cnc-cam-strategy-a feature/cam-offset-inside
git worktree add ../cnc-cam-strategy-b feature/cam-offset-outside

# Implement both, benchmark, choose best
```

## TDD Examples

### Example 1: Finger Joint Spacing
```python
def test_finger_joint_count():
    """Front panel should have 5 fingers on each vertical edge"""
    front = build_front_panel()

    # Count finger joints (Mode.ADD boxes on edges)
    # This test forces us to make joints countable/introspectable
    assert count_fingers(front, edge="left") == 5
    assert count_fingers(front, edge="right") == 5
```

### Example 2: Bounding Box Validation
```python
def test_finger_joints_extend_bounds():
    """Finger joints should extend the panel bounding box"""
    p = HamperParams
    front = build_front_panel()
    bbox = front.bounding_box()

    # With fingers on left/right, width should be:
    # base_width + 2 * thickness
    expected_width = p.width + 2 * p.thickness
    assert abs(bbox.size.X - expected_width) < 0.01
```

### Example 3: Vector Attribute Access
```python
def test_vector_attributes_are_uppercase():
    """build123d Vectors use uppercase X,Y,Z attributes"""
    from build123d import Vector

    v = Vector(1, 2, 3)

    # Should have uppercase attributes
    assert hasattr(v, 'X')
    assert hasattr(v, 'Y')
    assert hasattr(v, 'Z')

    # Should NOT have lowercase
    assert not hasattr(v, 'x')
```

## Mission Drift Examples

### Good: Focused Implementation

**Goal**: Add finger joints to hamper panels

**Scope**:
1. Design finger joint geometry
2. Integrate into existing panels
3. Add clearance parameter
4. Verify bounding boxes
5. Test in web UI

**Result**: Feature shipped, works well

### Bad: Mission Drift

**Goal**: Add finger joints to hamper panels

**Scope** (drifted):
1. Design finger joints ✓
2. Redesign entire assembly system ❌
3. Refactor all of lib/shapeoko.py ❌
4. Add dovetails and mortise-tenon ❌
5. Implement physics simulation ❌
6. Create new CAM library from scratch ❌

**Result**: Original goal lost, nothing shipped

### How to Avoid

**Before starting**:
- Write down the specific goal
- List what's in/out of scope
- Set time limit

**During work**:
- When tempted to add features, add to "Future Ideas" list
- Ask: "Is this needed for the original goal?"
- Review scope every 30 minutes

**After completing**:
- Did we achieve the goal?
- What got added that wasn't planned?
- Was it necessary?

## Model Selection Guidelines

### Use Haiku For
- File/code searches
- Reading existing code
- Simple refactoring (rename, move)
- Running tests
- Formatting code
- Quick documentation updates
- Grepping/finding patterns

**Cost**: ~$0.25 per million input tokens
**Speed**: Very fast (< 1s typically)

### Use Sonnet For (Default)
- Feature implementation
- Bug fixing
- Code review
- Writing tests
- Architecture decisions
- Most development work
- Complex debugging

**Cost**: ~$3 per million input tokens
**Speed**: Fast (1-3s typically)

### Use Opus For
- Major architectural changes
- Complex refactoring across many files
- Critical security issues
- Performance optimization requiring deep analysis
- When accuracy is more important than speed

**Cost**: ~$15 per million input tokens
**Speed**: Slower (3-10s typically)

**Rule of Thumb**: Start with Sonnet, drop to Haiku for simple tasks, escalate to Opus only when necessary.

---

## Quick Reference

**Before starting any task**:
1. ❓ Triple loop: Is this the right problem?
2. 🔍 Root cause: Why is this happening?
3. 🌿 Worktree: Need isolation?
4. ✅ TDD: Write test first
5. 🎯 Scope: What's in/out?
6. 🤖 Agent: Which model?

**During implementation**:
- ⚠️ Watch for mission drift
- 📝 Keep notes on decisions
- 🧪 Run tests frequently
- 💭 Update CLAUDE.md with findings

**After completion**:
- ✅ All tests passing?
- 📚 Documentation updated?
- 🎯 Original goal achieved?
- 📋 Future ideas captured?

---

*This methodology helps maintain code quality, prevents scope creep, and ensures we're solving the right problems the right way.*
