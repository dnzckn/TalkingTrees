<p align="center">
  <img src="images/TalkingTrees_logo.png" alt="TalkingTrees Logo" width="800"/>
</p>

# TalkingTrees

**Complete py_trees serialization library with FastAPI-based REST API support**

## About

TalkingTrees provides bidirectional JSON serialization for [py_trees](https://github.com/splintered-reality/py_trees) behavior trees with 100% reversibility. Create trees visually in the GUI editor, edit them programmatically via Python SDK or REST API, version control as JSON, and execute with py_trees runtime—all with zero data loss.

Perfect round-trip conversion: `py_trees ↔ TalkingTrees (JSON) ↔ py_trees`

Multiple creation methods: `GUI Editor → TalkingTrees (JSON) → py_trees Runtime`

## Why TalkingTrees?

**py_trees has no JSON serialization.** While py_trees excels at runtime execution, it lacks the ability to save/load trees in a portable format. TalkingTrees adds JSON serialization, a visual editor, REST API, and tooling for version control and remote management. It doesn't replace py_trees—it extends it.

## Core Features

- **Complete Reversibility** - Perfect round-trip conversion with zero data loss
- **40+ Node Types** - All composites, decorators, and behaviors from py_trees 2.3+
- **Type-Safe Architecture** - Constants-based configuration system prevents typos
- **Enhanced Error Messages** - Detailed context with tree paths and suggestions
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
- **FastAPI-based REST API** - Optional HTTP API with 47 endpoints for tree management
- **Visual Tree Editor** - Browser-based drag-and-drop editor with 100% node coverage
- **Python SDK** - High-level API for tree creation and manipulation
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
- **FastAPI REST API** - Optional HTTP API with 47 endpoints for tree management
- **Professional GUI Editor** - Browser-based visual editor with:
  - Live execution simulation with timeline scrubber
  - Breakpoint debugging and blackboard inspector
  - Auto-discovery library (local folders or remote API)
  - Smart validation with unused variable detection
  - 12 interactive example trees
- **Python SDK** - High-level API for programmatic tree creation and manipulation
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

## Quick Start

### Installation

```bash
pip install -e .
```

### Basic Usage

```python
from talking_trees.sdk import TalkingTrees
from talking_trees.adapters import from_py_trees, to_py_trees
import py_trees

# Create a py_trees behavior tree
root = py_trees.composites.Sequence(name="Main", memory=True, children=[
    py_trees.behaviours.Success(name="Task1"),
    py_trees.behaviours.Success(name="Task2"),
])

# Convert to TalkingTrees format
tt_tree, context = from_py_trees(root, name="My Tree", version="1.0.0")

# Save to file
tt = TalkingTrees()
tt.save_tree(tt_tree, "my_tree.json")

# Load and convert back
loaded = tt.load_tree("my_tree.json")
py_trees_root = to_py_trees(loaded)
```

## Python SDK

The SDK provides high-level functions for working with behavior trees:

```python
from talking_trees.sdk import TalkingTrees
from talking_trees.adapters import from_py_trees, to_py_trees, compare_py_trees

# Serialize py_trees to JSON
tt_tree, context = from_py_trees(root, name="My Tree", version="1.0.0")

# Save/load trees
tt = TalkingTrees()
tt.save_tree(tt_tree, "output.json")
loaded = tt.load_tree("input.json")

# Deserialize back to py_trees
py_trees_root = to_py_trees(loaded)

# Verify round-trip conversion
assert compare_py_trees(original_root, py_trees_root)
```

## FastAPI-based REST API

Start the server for remote tree management:

```bash
python scripts/run_server.py
# Access API docs at http://localhost:8000/docs
```

### API Examples

```python
import requests

# Create tree via API
tree = {
    "$schema": "1.0.0",
    "metadata": {"name": "API Tree", "version": "1.0.0"},
    "root": {
        "node_type": "Sequence",
        "name": "Main",
        "children": [{"node_type": "Success", "name": "Task"}]
    }
}

response = requests.post("http://localhost:8000/trees/", json=tree)
tree_id = response.json()["tree_id"]

# Execute tree
exec_response = requests.post(
    "http://localhost:8000/executions/",
    json={"tree_id": tree_id}
)
execution_id = exec_response.json()["execution_id"]

# Tick the execution
requests.post(
    f"http://localhost:8000/executions/{execution_id}/tick",
    json={"count": 5}
)
```

47 endpoints available for tree management, execution, debugging, and visualization.

## Visual Editor

Launch the browser-based tree editor:

```bash
./scripts/run_editor.sh
```

<p align="center">
  <img src="images/visualizer_screenshot.png" alt="TalkingTrees Tree Editor" width="800"/>
</p>

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
Opens at `http://localhost:8000` - Drag-and-drop interface with all 40+ node types, enum dropdowns, array editors, and organized palette. Build any tree entirely in the GUI with full backend parity.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
**Professional drag-and-drop interface** with all 40+ node types, live execution simulation, and debugging tools:

**Core Features:**
- **Visual Tree Building**: Drag nodes from palette, Shift+Click to connect
- **Live Simulation**: Execute trees in real-time with visual feedback
- **Timeline Scrubber**: Rewind/replay execution history (last 100 ticks)
- **Breakpoint Debugging**: Pause execution at any node
- **Blackboard Inspector**: Watch variables change in real-time
- **Smart Validation**: Detects unreachable nodes, infinite loops, unused variables
- **Library Management**: Load/save trees locally or via remote API
- **12 Example Trees**: Interactive demos from basic tutorials to complex simulations

Opens at `http://localhost:8000` - zero-configuration, works offline, 100% node coverage.
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

## CLI Tools

```bash
# Tree management
talkingtrees tree list
talkingtrees tree create my_tree.json
talkingtrees tree get <TREE_ID>

# Execution
talkingtrees exec run <TREE_ID> --ticks 10
talkingtrees exec stats <EXECUTION_ID>

# Import/Export
talkingtrees export import examples/trees/01_simple_sequence.json
talkingtrees export tree <TREE_ID> -o output.json
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Creation Layer (Choose One or Both)                            │
├──────────────────────────────┬──────────────────────────────────┤
│  GUI Editor (Visual)         │  py_trees (Code)                 │
│  • Drag-and-drop interface   │  • Python behavior tree API      │
│  • Live simulation           │  • Programmatic creation         │
│  • Timeline scrubber         │  • Runtime execution             │
│  • Breakpoint debugging      │                                  │
└──────────────┬───────────────┴──────────────┬───────────────────┘
               │                              │
               │  export JSON    from_py_trees() / to_py_trees()
               │                              │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────────────────────────┐
               │  TalkingTrees Core (Central Format)             │
               │  • Constants (type-safe config keys)            │
               │  • Utilities (comparison, parallel policy, UUID) │
               │  • Registry (extensible node type system)       │
               │  • Enhanced errors (context + suggestions)      │
               └──────────────┬───────────────────────────────────┘
                              │
               ┌──────────────▼───────────────────────────────────┐
               │  Pydantic Models (TreeDefinition, validation)    │
               └──────────────┬───────────────────────────────────┘
                              │ save_tree() / load_tree()
               ┌──────────────▼───────────────────────────────────┐
               │  JSON Files (Version Control, Storage)           │
               │  • Git-friendly format                           │
               │  • Human-readable structure                      │
               │  • Portable across systems                       │
               └──────────────┬───────────────────────────────────┘
                              │ (Optional)
               ┌──────────────▼───────────────────────────────────┐
               │  FastAPI REST API - 47 endpoints                 │
               │  • Tree Management • Execution • Debug           │
               │  • Remote collaboration • Team workflows         │
               └──────────────────────────────────────────────────┘
```

**Key Insight**: TalkingTrees sits in the middle, providing a universal JSON format that can be:
- Created visually in the GUI editor
- Generated from existing py_trees code
- Edited via REST API or Python SDK
- Version controlled in Git
- Executed by converting back to py_trees

### Key Components

- **Type-Safe Constants** (`core/constants.py`) - All configuration keys as typed constants
- **Enhanced Errors** (`core/exceptions.py`) - TreeBuildError with full context and suggestions
- **Centralized Utilities** (`core/utils.py`) - ParallelPolicyFactory, ComparisonExpressionUtil, UUID generation
- **Registry Pattern** (`core/registry.py`) - Extensible node type registration with schema-based validation

## Project Structure

```
talking_trees/
├── src/talking_trees/
│   ├── adapters/         # py_trees ↔ TalkingTrees conversion
│   ├── core/             # Constants, exceptions, utils, registry
│   ├── models/           # Pydantic data models (V2)
│   ├── storage/          # File-based tree library
│   ├── api/              # FastAPI-based REST API (optional)
│   ├── cli/              # Command-line interface
│   ├── behaviors/        # Custom behavior implementations
│   └── sdk.py            # High-level Python SDK
├── tests/                # Test suite (66 tests, 100% pass)
├── examples/
│   ├── demos/            # Python demo scripts
│   ├── trees/            # Example tree JSON files
│   └── templates/        # Tree templates
├── tutorials/            # Tutorial scripts and code
│   └── assets/           # Tutorial JSON files
├── docs/                 # Documentation
└── scripts/              # Launch and utility scripts
```

## Links

- **Documentation**: [API Reference](docs/API_REFERENCE.md)
- **py_trees**: [Documentation](https://py-trees.readthedocs.io/) | [GitHub](https://github.com/splintered-reality/py_trees)
- **Dependencies**: [FastAPI](https://fastapi.tiangolo.com/) | [Pydantic](https://docs.pydantic.dev/)
- **Resources**: [Behavior Trees Guide](https://www.behaviortree.dev/)

---

**Requirements**: Python 3.10+ • py_trees 2.3+ • Pydantic 2.x • FastAPI 0.100+ (optional)

**License**: See [LICENSE](LICENSE)
