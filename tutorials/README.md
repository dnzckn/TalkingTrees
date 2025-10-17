# PyForest SDK Tutorials

Welcome to the PyForest SDK tutorials! These hands-on examples will teach you how to use PyForest's Python SDK to build, execute, profile, and version-control behavior trees.

## Why Use the SDK?

The PyForest SDK allows you to use behavior trees directly in Python without needing the API server. Perfect for:

- **Jupyter Notebooks** - Interactive experimentation and data analysis
- **Python Scripts** - Automated testing and batch processing
- **Embedded Systems** - Lightweight deployment without REST API overhead
- **Research & Learning** - Quick prototyping and exploration

## Prerequisites

```bash
# Install PyForest (adjust path as needed)
pip install -e /path/to/py_forest

# Or if using a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

## Tutorial Overview

### Tutorial 1: Getting Started
**File:** `01_getting_started.py`
**Duration:** 15 minutes
**Level:** Beginner

Learn the basics:
- Loading behavior trees from JSON files
- Creating executions
- Ticking trees with blackboard updates
- Reading execution results
- Creating trees programmatically
- Error handling

**Run it:**
```bash
cd tutorials
python 01_getting_started.py
```

**Key Concepts:**
- `PyForest()` - Main SDK entry point
- `load_tree()` - Load from visual editor exports
- `create_execution()` - Initialize tree execution
- `tick()` - Execute one step of the tree
- `load_and_run()` - Convenience one-liner

---

### Tutorial 2: Profiling & Performance
**File:** `02_profiling_performance.py`
**Duration:** 20 minutes
**Level:** Intermediate

Master performance analysis:
- Enable profiling at different levels
- Understand overhead vs detail tradeoffs
- Identify bottlenecks
- Production monitoring best practices
- Export profiling data

**Run it:**
```bash
python 02_profiling_performance.py
```

**Key Concepts:**
- `ProfilingLevel.BASIC` - 1-2% overhead, production-ready
- `ProfilingLevel.DETAILED` - 3-5% overhead, debugging
- `ProfilingLevel.FULL` - 8-10% overhead, deep analysis
- `get_profiling_report()` - Access performance metrics
- Bottleneck detection (>100ms nodes highlighted)

---

### Tutorial 3: Version Control & Diffing
**File:** `03_version_control.py`
**Duration:** 20 minutes
**Level:** Intermediate

Learn version control workflows:
- Compare tree versions
- Understand semantic vs UUID matching
- Merge trees with conflict detection
- Track evolution over time
- Git integration patterns
- Multiple diff output formats

**Run it:**
```bash
python 03_version_control.py
```

**Key Concepts:**
- `diff_trees()` - Compare two tree versions
- `diff_files()` - Quick file comparison
- `merge_trees()` - Three-way merge with conflict detection
- Semantic matching - Handle UUID changes gracefully
- JSON export for CI/CD integration

---

### Tutorial 4: Complete Robot Controller
**File:** `04_robot_controller.py`
**Duration:** 30 minutes
**Level:** Advanced

Build a complete system:
- Autonomous patrol robot with battery management
- Sensor integration and simulation
- Emergency handling
- Action logging and analysis
- Step-by-step debugging
- Real-world patterns and practices

**Run it:**
```bash
python 04_robot_controller.py
```

**What You'll Build:**
- Robot that patrols between waypoints
- Returns to charging station when battery is low
- Handles emergency conditions (critical battery)
- Obstacle detection and avoidance
- Complete simulation with logging

**Key Concepts:**
- Building complex trees programmatically
- Simulation loop integration
- Behavioral debugging techniques
- Action pattern analysis

---

### Tutorial 5: py_trees Integration
**File:** `05_py_trees_integration.py`
**Duration:** 25 minutes
**Level:** Intermediate

Bridge between py_trees and PyForest:
- Create trees using py_trees programmatic API
- Convert to PyForest format
- Visualize in PyForest editor
- Save/load JSON files
- Run via PyForest SDK or REST API
- Reverse conversion (PyForest → py_trees)

**Run it:**
```bash
python 05_py_trees_integration.py
```

**What You'll Learn:**
- Use py_trees mature Python API for tree creation
- Convert py_trees → PyForest for visualization
- Handle custom behaviors and node types
- Round-trip workflow (code → visualize → run)
- Integration with both ecosystems

**Key Concepts:**
- `pf.from_py_trees()` - Convert py_trees to PyForest
- `to_py_trees()` - Convert PyForest to py_trees
- `print_comparison()` - Debug conversions
- Automatic blackboard variable detection
- Custom behavior preservation

**Why This Matters:**
- py_trees is the standard Python behavior tree library
- Leverage existing py_trees knowledge and code
- Get PyForest's visualization and profiling tools
- Best of both worlds approach

---

## Quick Reference

### Basic Usage Pattern

```python
from py_forest.sdk import PyForest

# Initialize
pf = PyForest()

# Load tree (exported from visual editor)
tree = pf.load_tree("my_tree.json")

# Create execution
execution = pf.create_execution(tree, initial_blackboard={
    "sensor_value": 42.0
})

# Tick with sensor updates
result = execution.tick(blackboard_updates={
    "sensor_value": 45.0
})

# Read outputs
print(f"Status: {result.status}")
print(f"Output: {result.blackboard.get('/output_key')}")
```

### One-Liner for Quick Tests

```python
from py_forest.sdk import load_and_run

result = load_and_run(
    "tree.json",
    blackboard_updates={"input": 100},
    ticks=1
)
print(result.status)
```

### With Profiling

```python
from py_forest.sdk import PyForest
from py_forest.core.profiler import ProfilingLevel

pf = PyForest(profiling_level=ProfilingLevel.BASIC)
tree = pf.load_tree("tree.json")
execution = pf.create_execution(tree)

# Run workload
for i in range(100):
    execution.tick(blackboard_updates={"value": i})

# Get performance report
print(execution.get_profiling_report(verbose=True))
```

### Comparing Versions

```python
from py_forest.sdk import diff_files

# Quick diff
print(diff_files("tree_v1.json", "tree_v2.json"))

# Or with SDK
pf = PyForest()
tree_v1 = pf.load_tree("tree_v1.json")
tree_v2 = pf.load_tree("tree_v2.json")
diff = pf.diff_trees(tree_v1, tree_v2, verbose=True)
print(diff)
```

### py_trees Integration

```python
import py_trees
from py_forest.sdk import PyForest

# Create tree with py_trees
root = py_trees.composites.Sequence("MySequence")
root.add_child(py_trees.behaviours.Success("Step1"))
root.add_child(py_trees.behaviours.Success("Step2"))

# Convert to PyForest
pf = PyForest()
pf_tree = pf.from_py_trees(root, name="My Tree", version="1.0.0")

# Save for visualization
pf.save_tree(pf_tree, "my_tree.json")

# Load and run
loaded = pf.load_tree("my_tree.json")
execution = pf.create_execution(loaded)
result = execution.tick()
```

## Common Workflows

### Jupyter Notebook Exploration

```python
# In a Jupyter cell
from py_forest.sdk import PyForest

pf = PyForest()
tree = pf.load_tree("experiment.json")
execution = pf.create_execution(tree)

# Interactive testing
result = execution.tick(blackboard_updates={"param": 10})
result.blackboard.items()  # Inspect state
```

### Automated Testing

```python
# test_behavior.py
from py_forest.sdk import load_and_run

def test_low_battery_behavior():
    result = load_and_run(
        "robot_tree.json",
        {"battery_level": 5.0},
        ticks=1
    )
    assert result.blackboard.get("/action") == "return_to_base"

def test_normal_operation():
    result = load_and_run(
        "robot_tree.json",
        {"battery_level": 100.0},
        ticks=1
    )
    assert result.blackboard.get("/action") == "patrol"
```

### Production Monitoring

```python
import logging
from py_forest.sdk import PyForest
from py_forest.core.profiler import ProfilingLevel

# Setup
pf = PyForest(profiling_level=ProfilingLevel.BASIC)
tree = pf.load_tree("production_tree.json")
execution = pf.create_execution(tree)

# Run loop
while True:
    sensors = read_sensors()
    result = execution.tick(blackboard_updates=sensors)

    # Log performance every 1000 ticks
    if result.tick_count % 1000 == 0:
        report = execution.get_profiling_report()
        logging.info(f"Performance: {report}")

    # Execute outputs
    execute_action(result.blackboard.get("/action"))
```

## Tips & Best Practices

### Performance

- Use `ProfilingLevel.BASIC` in production (minimal overhead)
- Use `ProfilingLevel.DETAILED` for debugging (more metrics)
- Only use `ProfilingLevel.FULL` for deep analysis (highest overhead)
- Profile with realistic workloads, not toy examples

### Version Control

- Track `.json` tree files in Git
- Use semantic matching for diffs (handles UUID changes)
- Run `diff_files()` before committing changes
- Include diff output in PR descriptions
- Tag releases with tree version numbers

### Development

- Start with the visual editor for tree design
- Export to JSON for SDK integration
- Use SDK for automated testing
- Profile regularly to catch performance regressions
- Log tick counts and status to detect infinite loops

### Debugging

- Use `verbose=True` in profiling reports for details
- Check `result.tip_node` to see which node is active
- Log blackboard state at each tick
- Create minimal test cases that reproduce issues
- Use `ProfilingLevel.DETAILED` to track node execution patterns

## File Structure

After running all tutorials, you'll have:

```
tutorials/
├── README.md                      # This file
├── 01_getting_started.py          # Basic SDK usage
├── 02_profiling_performance.py    # Performance analysis
├── 03_version_control.py          # Version control & diffing
├── 04_robot_controller.py         # Complete example
├── 05_py_trees_integration.py     # py_trees integration
│
├── temp_control.json              # Created by tutorial 1
├── profile_export.json            # Created by tutorial 2
├── tree_diff.json                 # Created by tutorial 3
├── feature_v1.json                # Created by tutorial 3
├── feature_v1_1.json              # Created by tutorial 3
├── feature_v2.json                # Created by tutorial 3
├── merged_tree.json               # Created by tutorial 3
├── validate_trees.py              # Created by tutorial 3
├── robot_controller.json          # Created by tutorial 4
├── robot_simulation_log.json      # Created by tutorial 4
├── py_trees_simple.json           # Created by tutorial 5
├── py_trees_complex.json          # Created by tutorial 5
├── py_trees_task_manager.json     # Created by tutorial 5
├── py_trees_custom.json           # Created by tutorial 5
└── py_trees_api.json              # Created by tutorial 5
```

## Troubleshooting

### Import Errors

```python
# If you get: ModuleNotFoundError: No module named 'py_forest'
# Make sure you've installed the package:
cd /path/to/py_forest
pip install -e .
```

### File Not Found

```python
# Make sure you're running from the tutorials directory
cd tutorials
python 01_getting_started.py

# Or use absolute paths
pf.load_tree("/absolute/path/to/tree.json")
```

### Tree Validation Errors

```python
# Trees exported from the visual editor should work
# If you create trees programmatically, ensure:
# 1. All nodes have unique IDs
# 2. Parent IDs reference existing nodes
# 3. Root node has parent_id=None
# 4. Blackboard variables match tree requirements
```

## Next Steps

After completing these tutorials:

1. **Read the Documentation**
   - See `IMPROVEMENTS_SUMMARY.md` for feature details
   - Check `SESSION_CONTEXT.md` for architecture overview

2. **Explore the Visual Editor**
   - Open `visualization/tree_editor_pro.html`
   - Design trees visually
   - Export to JSON for SDK usage

3. **Try the Visual Diff Tool**
   - Open `visualization/tree_diff_viewer.html`
   - Load v1 and v2 of your trees
   - See changes highlighted visually

4. **Build Your Own Project**
   - Start with a simple behavior tree
   - Integrate with your system
   - Add profiling and monitoring
   - Version control your trees

## Getting Help

- **Documentation:** See `IMPROVEMENTS_SUMMARY.md` and `SESSION_CONTEXT.md`
- **Examples:** Check `examples/` directory for sample trees
- **Source Code:** Explore `src/py_forest/` for implementation details

## Contributing

Found an issue or have a tutorial idea? Please:
1. Document the problem/idea
2. Create a minimal reproducible example
3. Share with the team

---

Happy coding! 🎉

**Pro Tip:** Start with Tutorial 1, then pick tutorials based on your needs. Tutorial 4 shows everything working together in a realistic scenario. If you're already familiar with py_trees, start with Tutorial 5 to see how to integrate it with PyForest!
