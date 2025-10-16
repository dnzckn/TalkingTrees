# PyForest 🌲

**Serializable behavior trees with REST API and visual editor support**

Built on top of the excellent [py_trees](https://github.com/splintered-reality/py_trees) library, PyForest adds:

- 📦 **Tree Library Management** - Store, version, and organize behavior tree definitions
- 🔄 **JSON Serialization** - Editor-friendly format with UI metadata
- 🚀 **REST API** - Create, execute, and monitor trees via FastAPI
- 🎨 **Editor Support** - Schema-driven system for drag-and-drop tree builders
- 📊 **State Snapshots** - Capture complete execution state at any point
- 🔌 **Plugin System** - Register custom behaviors dynamically

## Quick Start

### Installation

```bash
# Clone and install
git clone https://github.com/yourusername/py_forest.git
cd py_forest
pip install -e .
```

### Start the API Server

```bash
# Option 1: Using the convenience script
python run_server.py

# Option 2: Using uvicorn directly
uvicorn py_forest.api.main:app --reload

# Server will start at http://localhost:8000
# API docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Create and Execute a Tree

```python
import requests

# 1. Create a tree
tree_def = {
    "$schema": "1.0.0",
    "tree_id": "550e8400-e29b-41d4-a716-446655440001",
    "metadata": {
        "name": "Simple Example",
        "version": "1.0.0",
        "description": "A simple tree"
    },
    "root": {
        "node_type": "Sequence",
        "name": "Root",
        "children": [
            {"node_type": "Log", "name": "Log1", "config": {"message": "Hello"}},
            {"node_type": "Success", "name": "Done"}
        ]
    },
    "blackboard_schema": {}
}

response = requests.post("http://localhost:8000/trees/", json=tree_def)
tree = response.json()

# 2. Create an execution instance
config = {
    "tree_id": tree["tree_id"],
    "mode": "manual",
    "initial_blackboard": {}
}

response = requests.post("http://localhost:8000/executions/", json=config)
execution = response.json()
execution_id = execution["execution_id"]

# 3. Tick the tree
tick_request = {"count": 1, "capture_snapshot": True}
response = requests.post(
    f"http://localhost:8000/executions/{execution_id}/tick",
    json=tick_request
)
result = response.json()

print(f"Status: {result['root_status']}")
print(f"Tick count: {result['new_tick_count']}")
```

## Architecture

PyForest uses a two-tier architecture separating tree definitions from runtime instances:

```
┌─────────────────────────────────────────────────────────┐
│                      REST API (FastAPI)                  │
├─────────────────────────────────────────────────────────┤
│  Tree Library        │  Execution Engine  │  Registry    │
│  (Content Mgmt)      │  (Runtime)         │  (Schemas)   │
├─────────────────────────────────────────────────────────┤
│              Core Serialization Layer                    │
│         (TreeSerializer, SnapshotVisitor)               │
├─────────────────────────────────────────────────────────┤
│                   py_trees Core                          │
│         (Composites, Decorators, Behaviours)            │
└─────────────────────────────────────────────────────────┘
```

### Components

**Tree Library** (`storage/`)
- File-based storage with semantic versioning
- Catalog management and search
- Version history tracking

**Execution Engine** (`core/execution.py`)
- Manages multiple tree instances
- Tick control (manual, auto, interval)
- State snapshot capture
- Lifecycle management

**Behavior Registry** (`core/registry.py`)
- Maps node types to py_trees implementations
- Provides schemas for visual editors
- Factory for node instantiation

**Tree Serializer** (`core/serializer.py`)
- Converts JSON ↔ py_trees
- UUID mapping for state capture
- Subtree reference resolution

**State Snapshot** (`core/snapshot.py`)
- Captures complete execution state
- Node statuses and feedback
- Blackboard state and metadata
- Visitor pattern integration

## REST API

### Endpoints

#### Tree Library (`/trees`)
- `GET /trees/` - List all trees
- `GET /trees/{tree_id}` - Get tree definition
- `POST /trees/` - Create tree
- `PUT /trees/{tree_id}` - Update tree
- `DELETE /trees/{tree_id}` - Delete tree
- `GET /trees/{tree_id}/versions` - List versions
- `GET /trees/search/?query={q}` - Search trees

#### Behavior Schemas (`/behaviors`)
- `GET /behaviors/` - Get all schemas
- `GET /behaviors/types` - List behavior types
- `GET /behaviors/category/{cat}` - Filter by category
- `GET /behaviors/{type}` - Get specific schema

#### Execution Control (`/executions`)
- `POST /executions/` - Create execution
- `GET /executions/` - List executions
- `GET /executions/{id}` - Get summary
- `POST /executions/{id}/tick` - Tick tree
- `GET /executions/{id}/snapshot` - Get state
- `DELETE /executions/{id}` - Delete execution
- `POST /executions/cleanup` - Cleanup old executions

### Interactive Documentation

When the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Tree Definition Format

Trees are defined as JSON with the following structure:

```json
{
  "$schema": "1.0.0",
  "tree_id": "uuid",
  "metadata": {
    "name": "Tree Name",
    "version": "1.0.0",
    "description": "Tree description",
    "tags": ["tag1", "tag2"],
    "author": "Author Name"
  },
  "root": {
    "node_type": "Sequence",
    "node_id": "uuid",
    "name": "Root Node",
    "config": {},
    "ui_metadata": {
      "position": {"x": 0, "y": 0},
      "color": "#4A90E2",
      "notes": "Node notes",
      "breakpoint": false
    },
    "children": []
  },
  "blackboard_schema": {
    "/key/path": {
      "type": "number",
      "default": 0.0,
      "description": "Key description"
    }
  },
  "subtrees": {}
}
```

## Built-in Behaviors

### Composites
- **Sequence** - Execute children sequentially (SUCCESS if all succeed)
- **Selector** - Execute in priority order (SUCCESS if any succeeds)
- **Parallel** - Execute all children simultaneously

### Decorators
- **Inverter** - Flip SUCCESS ↔ FAILURE
- **Timeout** - Fail if child doesn't complete in time
- **Retry** - Retry child on failure N times
- **OneShot** - Execute child once, then return final status

### Actions
- **Success** - Always returns SUCCESS
- **Failure** - Always returns FAILURE
- **Running** - Always returns RUNNING
- **Log** - Log a message and return SUCCESS
- **Wait** - Wait for duration (RUNNING → SUCCESS)

### Conditions
- **CheckBattery** - Check if battery level is above threshold

## Custom Behaviors

Create custom behaviors by extending `py_trees.behaviour.Behaviour`:

```python
from py_trees import behaviour, common

class MyBehavior(behaviour.Behaviour):
    """My custom behavior."""

    def __init__(self, name: str, my_param: float = 1.0):
        super().__init__(name=name)
        self.my_param = my_param

    def setup(self):
        """Setup phase (called once)."""
        pass

    def initialise(self):
        """Initialize before first tick."""
        pass

    def update(self):
        """Execute one tick."""
        return common.Status.SUCCESS

    def terminate(self, new_status):
        """Cleanup when transitioning out."""
        pass
```

Register it with PyForest:

```python
from py_forest.core.registry import get_registry
from py_forest.models.schema import BehaviorSchema, NodeCategory

registry = get_registry()
registry.register(
    node_type="MyBehavior",
    implementation=MyBehavior,
    schema=BehaviorSchema(
        node_type="MyBehavior",
        category=NodeCategory.ACTION,
        display_name="My Behavior",
        description="Does something cool",
        # ... schema details
    )
)
```

## Testing

### Run Phase 1 Tests (Foundation)

```bash
python test_phase1.py
```

Tests:
- Pydantic models
- Behavior registry
- File-based storage
- Custom behaviors

### Run Phase 2 Tests (API)

```bash
# Terminal 1: Start server
python run_server.py

# Terminal 2: Run tests
python test_phase2.py
```

Tests:
- Health check
- Behavior schemas
- Tree library CRUD
- Execution lifecycle
- State snapshots

## Development

### Project Structure

```
py_forest/
├── src/py_forest/
│   ├── models/           # Pydantic data models
│   │   ├── tree.py       # Tree definitions
│   │   ├── execution.py  # Runtime state
│   │   └── schema.py     # Behavior schemas
│   ├── core/             # Core functionality
│   │   ├── registry.py   # Behavior registry
│   │   ├── serializer.py # JSON ↔ py_trees
│   │   ├── snapshot.py   # State capture
│   │   └── execution.py  # Instance management
│   ├── storage/          # Persistence layer
│   │   ├── base.py       # Abstract interface
│   │   └── filesystem.py # File storage
│   ├── behaviors/        # Custom behaviors
│   │   └── examples.py   # Example behaviors
│   └── api/              # REST API
│       ├── main.py       # FastAPI app
│       ├── dependencies.py
│       └── routers/      # Endpoint groups
├── examples/             # Example trees
├── tests/                # Test suite
├── test_phase1.py        # Phase 1 tests
├── test_phase2.py        # Phase 2 tests
├── run_server.py         # Server launcher
├── PHASE1_SUMMARY.md     # Phase 1 docs
├── PHASE2_SUMMARY.md     # Phase 2 docs
└── pyproject.toml        # Project config
```

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

Includes:
- pytest - Testing framework
- black - Code formatting
- ruff - Linting
- mypy - Type checking

## Project Status

✅ **Phase 1 Complete** - Foundation
- Pydantic models for trees and execution
- Behavior registry with schemas
- File-based tree library
- Custom behavior examples

✅ **Phase 2 Complete** - Serialization & API
- TreeSerializer (JSON ↔ py_trees)
- State snapshot capture
- Execution instance management
- Complete REST API (18 endpoints)
- Integration tests

🚧 **Future Phases**
- Phase 3: Advanced features (WebSockets, history, debugging)
- Phase 4: Visual editor integration
- Phase 5: Production hardening (auth, monitoring)

## Documentation

- [PHASE1_SUMMARY.md](PHASE1_SUMMARY.md) - Foundation details
- [PHASE2_SUMMARY.md](PHASE2_SUMMARY.md) - Serialization & API details
- API Docs: http://localhost:8000/docs (when server running)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

BSD-3-Clause (same as py_trees)

## Acknowledgments

Built on top of [py_trees](https://github.com/splintered-reality/py_trees) by Daniel Stonier and contributors.

## Links

- [py_trees Documentation](https://py-trees.readthedocs.io/)
- [Behavior Trees Guide](https://www.behaviortree.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
