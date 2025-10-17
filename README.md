<p align="center">
  <img src="images/PyForest_logo.png" alt="PyForest Logo" width="400"/>
</p>

# PyForest

**Behavior tree management system with JSON serialization, REST API, and visual editing**

Built on [py_trees](https://github.com/splintered-reality/py_trees), PyForest demonstrates how to serialize behavior trees to JSON, provide a REST API for tree management and execution, and edit trees visually in a browser. The system shows how to separate tree definitions from runtime execution, enable version control of trees, and provide debugging capabilities.

**What it demonstrates**: Serializing py_trees to/from JSON, REST API for tree execution, visual tree editor, debugging with breakpoints and watches, execution monitoring, tree diffing and versioning.

## Features

- **Tree Library** - Store and version tree definitions as JSON files
- **REST API** - HTTP/WebSocket API with 47 endpoints
- **CLI Tool** - Command-line interface for tree operations
- **Real-time Monitoring** - WebSocket streaming and execution history
- **Debugging** - Breakpoints, watches, and step execution
- **Templates** - Reusable tree patterns with parameter substitution
- **Validation** - Tree structure and behavior validation
- **Visualization** - DOT graph and py_trees_js format export
- **Statistics** - Execution profiling and per-node timing

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/py_forest.git
cd py_forest
pip install -e .
```

### Visual Tree Editor

Launch the visual tree editor with API server:

```bash
./run_editor.sh
```

This opens the **PyForest Tree Editor Pro** - a full-featured visual editor for creating and editing behavior trees.

For Python code generation:

```bash
./run_code_view.sh
```

This opens the **Code View** tool showing three synchronized views: Visual Tree, JSON Editor, and Python Code. Edit the JSON directly and see Python code generated automatically.

See [LAUNCHER_GUIDE.md](LAUNCHER_GUIDE.md) for all launcher options.

### Visual Tree Editor

<p align="center">
  <img src="images/visualizer_screenshot.png" alt="PyForest Visual Tree Editor" width="800"/>
</p>

The PyForest Tree Editor Pro provides a professional drag-and-drop interface for creating and editing behavior trees with real-time visualization, node property editing, and automatic layout.

### Start the API Server (Manual)

```bash
python run_server.py
```

Server runs at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Use the CLI

```bash
# List trees
pyforest tree list

# Import an example
pyforest export import examples/trees/01_simple_sequence.json

# Run a tree
pyforest exec run <TREE_ID> --ticks 10

# Profile performance
pyforest profile <TREE_ID> --ticks 1000
```

### Use the API

```python
import requests

# Create tree
tree = {
    "$schema": "1.0.0",
    "metadata": {"name": "Simple Tree", "version": "1.0.0"},
    "root": {
        "node_type": "Sequence",
        "name": "Main",
        "config": {},
        "children": [
            {"node_type": "Log", "name": "Start", "config": {"message": "Starting"}},
            {"node_type": "Success", "name": "Task"},
            {"node_type": "Log", "name": "End", "config": {"message": "Done"}}
        ]
    }
}

response = requests.post("http://localhost:8000/trees/", json=tree)
tree_id = response.json()["tree_id"]

# Create execution
config = {"tree_id": tree_id}
response = requests.post("http://localhost:8000/executions/", json=config)
execution_id = response.json()["execution_id"]

# Execute ticks
response = requests.post(
    f"http://localhost:8000/executions/{execution_id}/tick",
    json={"count": 5}
)
print(response.json())
```

## Documentation

- **[Launcher Guide](LAUNCHER_GUIDE.md)** - Launch scripts and visual editor
- **[Getting Started](docs/GETTING_STARTED.md)** - Installation and first steps
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Behavior Reference](docs/BEHAVIOR_REFERENCE.md)** - Available behaviors
- **[Deployment](docs/DEPLOYMENT.md)** - Production deployment guide
- **[Testing Report](TESTING_COMPLETE_FINAL.md)** - Comprehensive test coverage
- **SDK Tutorials** - See `tutorials/` directory for 5 complete examples

## Architecture

PyForest uses a two-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│              (pyforest command-line tool)                    │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP Client
┌────────────────────────────┴────────────────────────────────┐
│                        API Layer                             │
│  FastAPI + Uvicorn (REST + WebSocket)                       │
│  47 endpoints across 7 routers                              │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                      Core Services                           │
│  Tree Library │ Execution Engine │ Validation │ Templates   │
│  Event System │ Debug Context    │ Statistics │ Scheduler   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                     py_trees Layer                           │
│              Behaviors, Composites, Decorators               │
└──────────────────────────────────────────────────────────────┘
```

### Key Components

**Tree Library**: File-based storage with semantic versioning
**Execution Engine**: Multiple concurrent tree instances
**Event System**: Real-time monitoring via WebSocket
**Debug System**: Breakpoints, watches, step execution
**Statistics**: Performance profiling and metrics
**Validation**: Structural and type validation
**Templates**: Parameterized tree patterns

## CLI Commands

```bash
# Tree Management
pyforest tree list                      # List all trees
pyforest tree get <ID>                  # Get tree details
pyforest tree validate --file tree.json # Validate tree
pyforest tree create tree.json          # Create tree
pyforest tree delete <ID>               # Delete tree

# Templates
pyforest template list                  # List templates
pyforest template instantiate <ID>      # Create from template
  --name "My Tree"
  --interactive                         # Interactive parameters

# Execution
pyforest exec run <TREE_ID>            # Run tree
  --ticks 10                            # Manual mode
  --auto                                # Continuous mode
  --interval 100                        # Ticked every 100ms
  --monitor                             # Live monitoring
pyforest exec stats <EXEC_ID>          # Show statistics

# Import/Export
pyforest export import tree.json        # Import tree
pyforest export tree <ID> -o file.json # Export tree
pyforest export batch --output dir      # Export all trees
pyforest export dot <EXEC_ID> --render # Export visualization

# Profiling
pyforest profile <TREE_ID>             # Profile performance
  --ticks 1000                          # Number of ticks
  --warmup 50                           # Warmup ticks
```

## REST API

### Routers

1. **Trees** (`/trees`) - Tree library management (7 endpoints)
2. **Behaviors** (`/behaviors`) - Behavior registry (3 endpoints)
3. **Executions** (`/executions`) - Execution lifecycle (10 endpoints)
4. **History** (`/history`) - Execution history (4 endpoints)
5. **Debug** (`/debug`) - Debugging features (10 endpoints)
6. **Visualization** (`/visualizations`) - Graphs and stats (5 endpoints)
7. **Validation** (`/validation`) - Validation and templates (7 endpoints)
8. **WebSocket** (`/ws`) - Real-time events (1 endpoint)

### Example Endpoints

```bash
# Tree Library
GET    /trees/                   # List trees
POST   /trees/                   # Create tree
GET    /trees/{id}               # Get tree
DELETE /trees/{id}               # Delete tree

# Execution
POST   /executions/              # Create execution
POST   /executions/{id}/tick     # Tick execution
GET    /executions/{id}/snapshot # Get snapshot
POST   /executions/{id}/scheduler/auto  # Start AUTO mode

# Debugging
POST   /debug/executions/{id}/breakpoints    # Add breakpoint
POST   /debug/executions/{id}/watches        # Add watch
POST   /debug/executions/{id}/step           # Step execution

# Visualization
GET    /visualizations/executions/{id}/dot        # DOT graph
GET    /visualizations/executions/{id}/statistics # Stats
```

See [API Reference](docs/API_REFERENCE.md) for complete documentation.

## Behaviors

### Composites

- **Sequence** - Execute children in order (all must succeed)
- **Selector** - Try children until one succeeds (fallback)
- **Parallel** - Execute children concurrently

### Decorators

- **Inverter** - Flip SUCCESS/FAILURE
- **Retry** - Retry on failure N times
- **Timeout** - Fail if exceeds duration
- **RunningIsFailure/Success** - Convert RUNNING status

### Actions

- **Success/Failure/Running** - Return fixed status
- **Log** - Log message and return SUCCESS
- **Wait** - Wait for duration

### Conditions

- **CheckBlackboardVariableExists** - Check if key exists
- **CheckBattery** - Check battery level threshold

See [Behavior Reference](docs/BEHAVIOR_REFERENCE.md) for details.

## Examples

The `examples/` directory contains:

**Trees** (8 examples):
1. **01_simple_sequence.json** - Basic sequence pattern
2. **02_simple_selector.json** - Selector with fallback
3. **03_retry_pattern.json** - Error handling with retry
4. **04_parallel_tasks.json** - Concurrent execution
5. **05_patrol_robot.json** - Robot patrol behavior
6. **06_debug_showcase.json** - Debugging features demo
7. **07_game_ai.json** - Game NPC AI
8. **08_stress_test.json** - Performance testing

**Templates** (2 examples):
1. **simple_patrol.json** - Parameterized patrol pattern
2. **retry_task.json** - Configurable retry pattern

Import examples:
```bash
pyforest export import examples/trees/01_simple_sequence.json
```

## Project Structure

```
py_forest/
├── src/py_forest/
│   ├── models/           # Pydantic data models
│   ├── core/             # Core functionality
│   │   ├── registry.py   # Behavior registry
│   │   ├── serializer.py # JSON ↔ py_trees
│   │   ├── execution.py  # Execution instances
│   │   ├── validation.py # Tree validation
│   │   ├── templates.py  # Template engine
│   │   ├── statistics.py # Performance metrics
│   │   └── debug.py      # Debugging features
│   ├── storage/          # Tree library storage
│   ├── behaviors/        # Custom behaviors
│   ├── cli/              # Command-line interface
│   │   └── commands/     # CLI command modules
│   └── api/              # REST API
│       └── routers/      # API endpoint groups
├── examples/
│   ├── trees/            # Example trees
│   └── templates/        # Example templates
├── tests/                # Test suite
├── docs/                 # Documentation
├── run_server.py         # Server launcher
└── pyproject.toml        # Project configuration
```

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

Includes:
- pytest - Testing framework
- black - Code formatting
- ruff - Linting
- mypy - Type checking
- httpx - Async HTTP client for tests

### Run Tests

```bash
# Unit tests
pytest tests/test_phase1.py -v
pytest tests/test_debug_unit.py -v

# Integration tests (requires server running)
python run_server.py  # Terminal 1
pytest tests/test_integration.py -v  # Terminal 2
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Phase Status

- Phase 1: Foundation - Complete
- Phase 2: Serialization & REST API - Complete
- Phase 3A: Real-time & History - Complete
- Phase 3B: Autonomous Execution - Complete
- Phase 3C: Debugging Features - Complete
- Phase 3D: Visualization & Statistics - Complete
- Phase 4A: Validation & Templates - Complete
- Phase 4B: Examples & Testing - Complete
- Phase 4C: CLI & Developer Tools - Complete
- Phase 4D: Documentation - Complete

## What It Provides

PyForest includes:

**Tree Management**
- Store trees as JSON with semantic versioning
- Search and filter trees by name, description, and tags
- Bidirectional JSON to py_trees serialization with UUID mapping
- Template system with parameter substitution
- Tree validation (structural, type checking, config validation)
- Import/export in multiple formats (JSON, YAML, DOT)
- Batch operations for backup and restore

**Execution Engine**
- Execute multiple tree instances simultaneously
- Three execution modes: Manual, AUTO (continuous), and INTERVAL (fixed-rate)
- Autonomous execution with scheduler control
- Hot-reload trees without losing runtime context
- Per-execution isolated blackboard state

**Monitoring and Debugging**
- Real-time WebSocket event streaming
- Execution history with time-travel debugging capabilities
- Breakpoints (unconditional and conditional with Python expressions)
- Watch expressions with multiple conditions (CHANGE, EQUALS, GREATER, etc.)
- Step execution modes (over, into, out, continue)
- Per-node performance metrics and timing statistics

**Visualization and Analysis**
- Tree visualization in DOT, SVG, PNG, and py_trees_js formats
- Execution statistics including timing and success rates
- Performance profiling with per-node breakdown
- Graphviz export for documentation

**Developer Interface**
- Command-line tool (pyforest) for tree management
- REST API with 47 endpoints across 7 routers
- Interactive API documentation at /docs endpoint
- Python SDK for loading and executing trees

## Performance Notes

Observed performance on typical hardware:

- Tree serialization: ~10ms for 100-node trees
- Single tick: 0.1-1ms depending on tree complexity
- Memory: ~1MB per execution instance
- History: Limited to 1000 snapshots per execution (configurable)

Profiling available via CLI:
```bash
pyforest profile <TREE_ID> --ticks 1000
```

## Running the Server

Start the development server:

```bash
python run_server.py
```

See [Deployment Guide](docs/DEPLOYMENT.md) for information on:
- Running as a service
- Reverse proxy configuration
- Basic security considerations

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks
6. Submit a pull request

## License

BSD-3-Clause (same as py_trees)

## Acknowledgments

Built on [py_trees](https://github.com/splintered-reality/py_trees) by Daniel Stonier and contributors.

## Links

- [py_trees Documentation](https://py-trees.readthedocs.io/)
- [Behavior Trees Guide](https://www.behaviortree.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Typer Documentation](https://typer.tiangolo.com/)

## Support

- Documentation: See `docs/` directory
- Issues: GitHub Issues
- Examples: See `examples/` directory
- Interactive API Docs: `http://localhost:8000/docs`
