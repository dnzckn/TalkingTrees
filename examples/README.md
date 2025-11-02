# TalkingTrees Examples

This directory contains example trees, demo scripts, and templates for learning and testing TalkingTrees.

## Directory Structure

```
examples/
├── demos/          # Python scripts demonstrating SDK usage
├── trees/          # 12 example behavior trees (JSON files)
└── templates/      # Tree templates for common patterns
```

## Quick Start

### Using the GUI Editor

The easiest way to explore examples:

```bash
# Launch the complete environment (API server + GUI editor)
./scripts/run_visualization.sh

# Or separately:
./scripts/run_server.sh    # Start API server
./scripts/run_editor.sh    # Open GUI editor
```

In the editor:
1. Click **"Load from Library"**
2. Browse the auto-discovered examples from `examples/trees/`
3. Click any tree to load and visualize it
4. Use **"Start Simulation"** to execute with live feedback

### Using the Python SDK

```python
from talking_trees.sdk import TalkingTrees
from talking_trees.adapters import to_py_trees

# Load an example tree
tt = TalkingTrees()
tree = tt.load_tree("examples/trees/01_simple_sequence.json")

# Convert to py_trees and execute
root = to_py_trees(tree)
root.tick_once()
```

### Using the REST API

```bash
# Start the API server
python scripts/run_server.py

# Load an example tree
curl -X POST http://localhost:8000/trees/ \
  -H "Content-Type: application/json" \
  -d @examples/trees/01_simple_sequence.json

# Execute a tree
curl -X POST http://localhost:8000/executions/ \
  -d '{"tree_id": "YOUR_TREE_ID"}' \
  -H "Content-Type: application/json"
```

## Example Trees (`trees/`)

**12 interactive examples** ranging from basic tutorials to complex simulations:

- **01-05**: Basic patterns (Sequence, Selector, Retry, Parallel, Patrol)
- **06**: Debug showcase with breakpoints and variable watching
- **07-08**: Game AI and stress testing
- **09**: Day-in-life simulation with complex state management
- **10**: Interactive 2D guard patrol game
- **11**: Ultra-complex demo showcasing ALL 40+ node types
- **12**: Smart home automation

See [`trees/README.md`](trees/README.md) for detailed descriptions.

## Demo Scripts (`demos/`)

Python scripts demonstrating SDK features:

- **`sdk_demo.py`** - Tree validation, search, statistics, batch operations
- **`round_trip_comparison.py`** - Verify py_trees ↔ TalkingTrees conversion
- **`py_trees_basic_example.py`** - Convert existing py_trees code to JSON
- **`programmatic_editing.py`** - Manipulate trees programmatically
- **`counter_memory_demo.py`** - Blackboard and state management
- **`ultra_complex_round_trip.py`** - Complex tree conversion testing

Run any demo:
```bash
python examples/demos/sdk_demo.py
```

## Templates (`templates/`)

Reusable tree patterns:

- **`simple_patrol.json`** - Basic patrol with battery management
- **`retry_task.json`** - Robust task execution with retry logic

Use as starting points for your own trees.

## Learning Path

**Beginners**:
1. Open `01_simple_sequence.json` in the GUI editor
2. Click "Start Simulation" to see it execute
3. Try `02_simple_selector.json` to understand fallback logic
4. Run `demos/py_trees_basic_example.py` to see SDK usage

**Intermediate**:
1. Load `05_patrol_robot.json` - realistic robot behavior
2. Experiment with `06_debug_showcase.json` - set breakpoints, watch variables
3. Run `demos/programmatic_editing.py` - modify trees with code

**Advanced**:
1. Study `11_ultra_complex.json` - ALL node types in one tree
2. Load `09_day_in_life_sim.json` - complex state machine simulation
3. Run `demos/ultra_complex_round_trip.py` - test conversion fidelity

## Creating Your Own Trees

**Three methods**:

1. **GUI Editor** (Recommended for beginners)
   - Drag-and-drop visual interface
   - Real-time validation
   - Export to JSON

2. **Python SDK** (Recommended for programmers)
   ```python
   from talking_trees.adapters import from_py_trees
   import py_trees

   root = py_trees.composites.Sequence(name="MyTree", memory=True)
   tt_tree, context = from_py_trees(root, name="My Tree", version="1.0.0")
   ```

3. **Direct JSON** (Advanced)
   - Copy a template from `examples/templates/`
   - Edit in your favorite editor
   - Validate via API: `POST /validation/trees`

---

**Next Steps**: See the main [README.md](../README.md) for full documentation.
