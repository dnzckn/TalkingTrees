# PyForest SDK Tutorials

Welcome to PyForest SDK tutorials! These hands-on examples teach you how to use PyForest to design, export, and USE behavior trees to control real systems.

## Why Use PyForest?

PyForest provides the complete workflow for behavior trees:

- **Visual Design** - Tree Editor Pro for rapid prototyping
- **One-Click Export** - "Copy Python" button generates ready-to-use code
- **Python Integration** - Load trees and control your systems
- **py_trees Compatible** - Bridge between py_trees and PyForest

## Prerequisites

```bash
# Install PyForest
cd /path/to/py_forest
pip install -e .
```

---

## Tutorial Overview

**🎯 START HERE: Tutorial 6 - Complete Workflow!**

This shows you everything you need: design → export → control.

---

## Tutorials

### Tutorial 5: py_trees Integration
**File:** `05_py_trees_integration.py`
**Duration:** 25 minutes
**Level:** Intermediate

**For existing py_trees users:**

Bridge between py_trees and PyForest:
- Create trees using py_trees programmatic API
- Convert to PyForest format for visualization
- Save/load JSON files
- Run via PyForest SDK
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
- Automatic blackboard variable detection
- All decorator support (Inverter, Repeat, Retry, Timeout)
- ComparisonExpression for conditions

**Why This Matters:**
- py_trees is the standard Python behavior tree library
- Leverage existing py_trees knowledge and code
- Get PyForest's visualization and profiling tools
- Best of both worlds approach

---

### Tutorial 6: Complete Workflow ⭐ RECOMMENDED
**File:** `06_complete_workflow.py`
**Duration:** 20 minutes
**Level:** Beginner

**THIS IS THE TUTORIAL TO START WITH!**

Shows the complete recommended PyForest workflow:
- ✅ Design trees visually in Tree Editor Pro
- ✅ Use "🐍 Copy Python" button to get ready-to-use code
- ✅ Load tree in Python
- ✅ **USE the tree to actually CONTROL a robot simulator**

**Run it:**
```bash
python 06_complete_workflow.py
```

**What You'll Learn:**
- The complete visual → code → control workflow
- How to use the "Copy Python" button (new feature!)
- **The control loop pattern: sensors → tree → actions**
- How to integrate behavior trees into real systems
- Testing different scenarios

**What You'll Build:**
- A robot simulator controlled by a behavior tree
- Battery management logic (patrol when high, charge when low)
- Patrol behavior with automatic charging
- Complete control loop implementation

**Key Concepts:**
- Visual design for rapid prototyping
- One-click Python code generation ("Copy Python" button)
- **The control loop pattern (THE MOST IMPORTANT!)**
- Integration with real systems
- How behavior trees make decisions

**Why This Matters:**
- **This shows you how to ACTUALLY USE behavior trees!**
- Most efficient workflow (visual design + Python integration)
- Ready-to-use code from "Copy Python" button
- Real control system example, not just theory

**💡 Pro Tip:** This tutorial demonstrates the REAL VALUE of behavior trees - making decisions to control systems (robots, game AI, automation, etc.). Start here to understand the complete picture!

---

## Quick Reference

### Recommended Workflow

```
1. Design Tree Visually
   └─> ./run_editor.sh
       └─> Drag and drop nodes
       └─> Configure behaviors
       └─> Test visually

2. Export with "Copy Python" Button
   └─> Click "🐍 Copy Python"
       └─> Choose "Load from File" or "Save to API"
       └─> Get ready-to-use Python code
       └─> Paste into your project

3. Use Tree to Control Your System
   └─> Load tree: pf.load_tree("tree.json")
       └─> Create execution: execution = pf.create_execution(tree)
       └─> Control loop:
           sensors → execution.tick(sensors) → actions → execute
```

### Basic Usage Pattern

```python
from py_forest.sdk import PyForest

# Initialize
pf = PyForest()

# Load tree (exported from visual editor)
tree = pf.load_tree("my_tree.json")

# Create execution
execution = pf.create_execution(tree)

# THE CONTROL LOOP (repeat this)
while True:
    # 1. Get sensor readings from your system
    sensors = get_system_sensors()

    # 2. Tick behavior tree with sensor data
    result = execution.tick(blackboard_updates=sensors)

    # 3. Read action from tree output
    action = result.blackboard.get('/action_key')

    # 4. Execute action on your system
    execute_system_action(action)
```

### Copy Python Button Output

When you click "🐍 Copy Python" in Tree Editor Pro, you get:

```python
from py_forest.sdk import PyForest

pf = PyForest()

# Option 1: From File
tree = pf.load_tree("robot_controller.json")

# Option 2: From API
pf = PyForest(api_url="http://localhost:8000")
tree = pf.get_tree("tree-id-here")

# Create and run
execution = pf.create_execution(tree)
result = execution.tick(blackboard_updates={"sensor": value})
print(result.status)
```

### py_trees Integration

```python
import py_trees
import operator
from py_trees.common import ComparisonExpression
from py_forest.sdk import PyForest

# Create tree with py_trees
root = py_trees.composites.Sequence("MySequence", memory=False)

# Add condition
check = ComparisonExpression('battery_level', operator.lt, 20)
root.add_child(
    py_trees.behaviours.CheckBlackboardVariableValue(
        name="Battery Low?",
        check=check
    )
)

# Convert to PyForest
pf = PyForest()
pf_tree = pf.from_py_trees(root, name="My Tree", version="1.0.0")

# Save for visualization
pf.save_tree(pf_tree, "my_tree.json")

# Load in visual editor: ./run_editor.sh
```

---

## Common Workflows

### 1. Visual First (Recommended)

```
./run_editor.sh
  → Design tree visually
  → Click "Export" to save JSON
  → Click "🐍 Copy Python"
  → Paste code into your project
  → Run!
```

### 2. py_trees First (For py_trees Users)

```python
# Write py_trees code
root = py_trees.composites.Selector("Root")
root.add_child(...)

# Convert and visualize
pf = PyForest()
tree = pf.from_py_trees(root, "Tree", "1.0")
pf.save_tree(tree, "tree.json")

# Open in editor: ./run_editor.sh
# Load tree.json to see visualization
```

### 3. Quick Testing

```bash
# Run tutorial to see example
python 06_complete_workflow.py

# Modify and test
# Edit the tutorial file
# Run again
```

---

## Tips & Best Practices

### Design

- ✅ Start with visual editor for rapid prototyping
- ✅ Use examples/robot_v1.json as reference
- ✅ Test tree visually before exporting
- ✅ Use meaningful node names

### Integration

- ✅ Use "Copy Python" button for quick code generation
- ✅ Save trees as JSON (version control friendly)
- ✅ Load trees at startup, not every tick
- ✅ Reuse executions (don't create new each tick)

### Control Loop

- ✅ Keep sensor updates separate from actions
- ✅ Read from `result.blackboard` for outputs
- ✅ Log tick count to detect infinite loops
- ✅ Handle tree status (SUCCESS, FAILURE, RUNNING)

### Debugging

- ✅ Use `result.tip_node` to see active node
- ✅ Print blackboard state each tick
- ✅ Test scenarios with different sensor values
- ✅ Use visual editor to verify tree structure

---

## File Structure

After running tutorials:

```
tutorials/
├── README.md                      # This file
├── 05_py_trees_integration.py     # py_trees integration
├── 06_complete_workflow.py        # Complete workflow (START HERE!)
│
├── py_trees_simple.json           # Created by tutorial 5
├── py_trees_complex.json          # Created by tutorial 5
├── py_trees_decorators.json       # Created by tutorial 5
└── py_trees_custom.json           # Created by tutorial 5
```

---

## Troubleshooting

### Import Errors

```python
# If you get: ModuleNotFoundError: No module named 'py_forest'
cd /path/to/py_forest
pip install -e .
```

### File Not Found

```python
# Make sure you're in the right directory
cd tutorials
python 06_complete_workflow.py

# Or use absolute paths
pf.load_tree("/absolute/path/to/tree.json")
```

### Tree Editor Not Opening

```bash
# Make sure you're in repo root
cd /path/to/py_forest
./run_editor.sh

# If API server won't start
python run_server.py
# Check: http://localhost:8000/health
```

---

## Next Steps

After completing these tutorials:

1. **Design Your Own Tree**
   - Open `./run_editor.sh`
   - Design tree for your use case
   - Export and integrate

2. **Explore Examples**
   - See `examples/robot_v1.json`
   - See `examples/robot_v2.json`
   - Load in editor to understand structure

3. **Read Documentation**
   - `COPY_PYTHON_FEATURE.md` - How "Copy Python" button works
   - `FINAL_REPORT.md` - System capabilities
   - `README.md` - Main documentation

4. **Build Your Project**
   - Start with Tutorial 6 pattern
   - Adapt control loop to your system
   - Use visual editor for iterations

---

## Getting Help

- **Documentation:** See `docs/` directory and root `.md` files
- **Examples:** Check `examples/` directory for sample trees
- **Source Code:** Explore `src/py_forest/` for implementation

---

## Summary

**PyForest provides two complete workflows:**

1. **Visual-First (Recommended):**
   ```
   Tree Editor Pro → Export JSON → "Copy Python" → Control System
   ```

2. **py_trees-First (For py_trees users):**
   ```
   py_trees Code → PyForest Adapter → Visualize → Control System
   ```

**Both workflows lead to the same goal:** Using behavior trees to control real systems!

---

**Start with Tutorial 6 to see the complete picture! 🎉**

**The key insight:** Behavior trees make decisions. Your code provides sensors and executes actions. The tree connects them.

```
Sensors → Behavior Tree → Actions
  ↑                           ↓
  └─────── Your System ────────┘
```

That's it! Now go build something awesome! 🚀
