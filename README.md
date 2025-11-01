<p align="center">
  <img src="images/PyForest_logo.png" alt="PyForest Logo" width="400"/>
</p>

# PyForest

**Complete py_trees serialization library with REST API support**

PyForest provides bidirectional JSON serialization for [py_trees](https://github.com/splintered-reality/py_trees) behavior trees with 100% reversibility. Serialize trees to JSON for version control, edit them programmatically or via REST API, and deserialize back to executable py_trees with zero data loss.

## Core Features

- **Complete Reversibility** - Perfect round-trip: `py_trees ↔ JSON ↔ py_trees`
- **40+ Node Types** - All composites, decorators, and behaviors from py_trees 2.3+
- **Type-Safe Architecture** - Constants-based configuration system prevents typos
- **Enhanced Error Messages** - Detailed context with tree paths and suggestions
- **FastAPI Integration** - Optional REST API with 47 endpoints for tree management
- **Visual Tree Editor** - Professional browser-based drag-and-drop editor
- **Zero Data Loss** - All parameters, configurations, and tree structure preserved

## Quick Start

### Installation

```bash
pip install -e .
```

### Python SDK

```python
from py_forest.sdk import PyForest
from py_forest.adapters import from_py_trees, to_py_trees, compare_py_trees
import py_trees

# Serialize py_trees to JSON
root = py_trees.composites.Sequence(name="Main", memory=True, children=[
    py_trees.behaviours.Success(name="Task1"),
    py_trees.behaviours.Success(name="Task2"),
])

pf_tree, context = from_py_trees(root, name="My Tree", version="1.0.0")

# Save to file
pf = PyForest()
pf.save_tree(pf_tree, "my_tree.json")

# Load from file
loaded = pf.load_tree("my_tree.json")

# Deserialize back to py_trees
py_trees_root = to_py_trees(loaded)

# Verify round-trip conversion preserves everything
assert compare_py_trees(root, py_trees_root)  # Returns True
```

### REST API (Optional)

```bash
# Start server
python scripts/run_server.py

# Access API docs at http://localhost:8000/docs
```

```python
import requests

# Create tree via API
tree = {
    "$schema": "1.0.0",
    "metadata": {"name": "API Tree", "version": "1.0.0"},
    "root": {
        "node_type": "Sequence",
        "name": "Main",
        "children": [
            {"node_type": "Success", "name": "Task"}
        ]
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

### Visual Editor

```bash
./scripts/run_editor.sh
```

<p align="center">
  <img src="images/visualizer_screenshot.png" alt="PyForest Tree Editor" width="800"/>
</p>

Opens the PyForest Tree Editor at `http://localhost:8000` - a professional drag-and-drop interface for creating and editing behavior trees with real-time visualization, node property editing, and automatic layout.

## Supported Node Types (40+)

### Composites (3)
- **Sequence** - Execute children in order (AND logic)
- **Selector** - Try children until success (OR logic)
- **Parallel** - Execute children concurrently with configurable policies

### Decorators (14)
- **Status Converters** - Inverter, SuccessIsFailure, FailureIsSuccess, FailureIsRunning, RunningIsFailure, RunningIsSuccess, SuccessIsRunning
- **Repetition** - Repeat, Retry, OneShot
- **Time-based** - Timeout
- **Advanced** - EternalGuard, Condition, Count, StatusToBlackboard, PassThrough

### Behaviors (13+)
- **Basic** - Success, Failure, Running, Dummy
- **Time-based** - TickCounter, SuccessEveryN, Periodic, StatusQueue
- **Blackboard** - CheckBlackboardVariableExists, CheckBlackboardVariableValue, SetBlackboardVariable, UnsetBlackboardVariable, WaitForBlackboardVariable, WaitForBlackboardVariableValue, CheckBlackboardVariableValues, BlackboardToStatus
- **Probabilistic** - ProbabilisticBehaviour
- **Custom** - Extensible behavior registration system

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  py_trees (Executable Runtime)                           │
└────────────┬─────────────────────────────────────────────┘
             │ from_py_trees() / to_py_trees()
┌────────────▼─────────────────────────────────────────────┐
│  PyForest Core                                           │
│  • Constants (type-safe config keys)                     │
│  • Utilities (comparison, parallel policy, UUID)         │
│  • Registry (extensible node type system)                │
│  • Enhanced errors (context + suggestions)               │
└────────────┬─────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────┐
│  Pydantic Models (TreeDefinition, validation)            │
└────────────┬─────────────────────────────────────────────┘
             │ save_tree() / load_tree()
┌────────────▼─────────────────────────────────────────────┐
│  JSON Files (Version Control, Storage)                   │
└──────────────────────────────────────────────────────────┘
             │ (Optional)
┌────────────▼─────────────────────────────────────────────┐
│  REST API (FastAPI) - 47 endpoints                       │
│  • Trees • Executions • Debug • Visualization            │
└──────────────────────────────────────────────────────────┘
```

### Key Components

**Type-Safe Constants** (`core/constants.py`)
- All configuration keys as typed constants
- Prevents typos and enables IDE autocomplete
- Single source of truth for defaults

**Enhanced Errors** (`core/exceptions.py`)
- TreeBuildError with full context (node, path, suggestions)
- Helpful debugging information
- Clear guidance for fixing issues

**Centralized Utilities** (`core/utils.py`)
- ParallelPolicyFactory for policy creation
- ComparisonExpressionUtil for py_trees quirks
- Deterministic UUID generation

**Registry Pattern** (`core/registry.py`)
- Extensible node type registration
- Schema-based validation
- Category-based queries

## CLI Tool

```bash
# Tree management
pyforest tree list
pyforest tree create my_tree.json
pyforest tree get <TREE_ID>

# Execution
pyforest exec run <TREE_ID> --ticks 10
pyforest exec stats <EXECUTION_ID>

# Import/Export
pyforest export import examples/trees/01_simple_sequence.json
pyforest export tree <TREE_ID> -o output.json
```

## Examples

See `examples/trees/` for complete examples:
- `01_simple_sequence.json` - Basic sequence pattern
- `02_simple_selector.json` - Selector with fallback
- `03_retry_pattern.json` - Error handling with retry
- `04_parallel_tasks.json` - Concurrent execution
- `05_patrol_robot.json` - Robot patrol behavior

```bash
# Import and run an example
pyforest export import examples/trees/01_simple_sequence.json
pyforest exec run <TREE_ID> --ticks 5
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Core functionality tests
pytest tests/test_round_trip.py -v          # Reversibility verification
pytest tests/test_py_trees_adapter.py -v    # Adapter conversion
pytest tests/test_compare_trees.py -v       # Tree comparison
pytest tests/test_deterministic_uuids.py -v # UUID generation
pytest tests/test_security_hardening.py -v  # Depth limits, cycle detection
```

**Test Results**: 66 tests, 100% pass rate

## Code Quality

- **Minimal Duplication**: Less than 2% code duplication
- **Type Safety**: Constants-based configuration system
- **Pydantic V2**: Fully compatible with latest Pydantic
- **Zero Magic Strings**: All config keys are typed constants
- **Enhanced Errors**: Context-rich error messages
- **Registry Pattern**: Extensible architecture

## Documentation

- **[API Reference](docs/API_REFERENCE.md)** - REST API endpoints and usage

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Code quality tools
black src/ tests/
ruff check src/ tests/
mypy src/

# Run tests with coverage
pytest tests/ --cov=py_forest --cov-report=html
```

## Project Structure

```
py_forest/
├── src/py_forest/
│   ├── adapters/         # py_trees ↔ PyForest conversion
│   ├── core/
│   │   ├── constants.py  # Type-safe configuration constants
│   │   ├── exceptions.py # Enhanced error classes
│   │   ├── utils.py      # Centralized utilities
│   │   ├── registry.py   # Node type registration
│   │   ├── serializer.py # JSON ↔ py_trees conversion
│   │   ├── builders.py   # Node construction
│   │   ├── extractors.py # Config extraction
│   │   ├── validation.py # Tree validation
│   │   └── execution.py  # Runtime execution
│   ├── models/           # Pydantic data models (V2)
│   ├── storage/          # File-based tree library
│   ├── api/              # FastAPI REST API (optional)
│   ├── cli/              # Command-line interface
│   ├── behaviors/        # Custom behavior implementations
│   └── sdk.py            # High-level Python SDK
├── tests/                # Test suite (66 tests)
├── examples/             # Example trees and templates
├── docs/                 # Documentation
└── scripts/              # Launch and utility scripts
```

## Performance

- Tree serialization: ~10ms for 100-node trees
- Deserialization: ~15ms for 100-node trees
- Single tick execution: 0.1-1ms depending on complexity
- Memory usage: ~1MB per execution instance
- Registry lookups: O(1) with caching

## Requirements

- Python 3.10+
- py_trees 2.3+
- Pydantic 2.x
- FastAPI 0.100+ (optional, for REST API)

## Links

- [py_trees Documentation](https://py-trees.readthedocs.io/)
- [py_trees GitHub](https://github.com/splintered-reality/py_trees)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Behavior Trees Guide](https://www.behaviortree.dev/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
