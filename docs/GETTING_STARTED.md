# Getting Started with PyForest

This guide will help you get started with PyForest, a behavior tree management system built on py_trees.

## Table of Contents

1. [Installation](#installation)
2. [Core Concepts](#core-concepts)
3. [Quick Start](#quick-start)
4. [Your First Tree](#your-first-tree)
5. [Using Templates](#using-templates)
6. [Executing Trees](#executing-trees)
7. [Next Steps](#next-steps)

## Installation

### Requirements

- Python 3.10 or higher
- pip package manager

### Basic Installation

Install PyForest from source:

```bash
git clone https://github.com/yourusername/py_forest.git
cd py_forest
pip install -e .
```

### Optional Dependencies

For visualization support (DOT graph rendering, YAML):

```bash
pip install -e ".[viz]"
```

For development tools:

```bash
pip install -e ".[dev]"
```

### Verify Installation

Check that PyForest is installed correctly:

```bash
pyforest --version
```

You should see: `PyForest version 0.1.0`

## Core Concepts

### What are Behavior Trees?

Behavior trees are a structured way to organize AI logic. They consist of:

- **Behaviors**: Individual actions or conditions
- **Composites**: Nodes that control child execution
- **Decorators**: Nodes that modify child behavior

### PyForest Architecture

PyForest uses a two-tier architecture:

1. **Tree Library**: Content management for tree definitions
2. **Execution Engine**: Runtime instances of trees

**Key Features:**
- Trees stored as JSON with semantic versioning
- Multiple execution instances from one tree
- Real-time monitoring via WebSocket
- Debugging with breakpoints and watches
- Template system for reusable patterns

### Tree Structure

A basic tree definition:

```json
{
  "$schema": "1.0.0",
  "metadata": {
    "name": "My First Tree",
    "version": "1.0.0",
    "description": "A simple behavior tree",
    "tags": ["tutorial", "demo"]
  },
  "root": {
    "node_type": "Sequence",
    "name": "Main Sequence",
    "config": {},
    "children": [
      {
        "node_type": "Log",
        "name": "Say Hello",
        "config": {
          "message": "Hello, World!"
        }
      }
    ]
  }
}
```

## Quick Start

### 1. Start the API Server

First, start the PyForest API server:

```bash
python run_server.py
```

The server will start on `http://localhost:8000`. You can view the interactive API documentation at `http://localhost:8000/docs`.

### 2. Import an Example Tree

Import one of the provided example trees:

```bash
pyforest export import examples/trees/01_simple_sequence.json
```

### 3. List Trees

View all trees in the library:

```bash
pyforest tree list
```

### 4. Run a Tree

Execute the tree:

```bash
# Get the tree ID from the list output
pyforest exec run <TREE_ID> --ticks 5
```

You should see the tree execute successfully with status output.

## Your First Tree

Let's create a simple tree from scratch.

### Step 1: Create the Tree Definition

Create a file named `my_first_tree.json`:

```json
{
  "$schema": "1.0.0",
  "metadata": {
    "name": "My First Tree",
    "version": "1.0.0",
    "description": "A simple tutorial tree",
    "tags": ["tutorial"],
    "author": "Your Name"
  },
  "root": {
    "node_type": "Sequence",
    "name": "Main Flow",
    "config": {},
    "children": [
      {
        "node_type": "Log",
        "name": "Start",
        "config": {
          "message": "Starting execution"
        }
      },
      {
        "node_type": "Success",
        "name": "Do Work",
        "config": {}
      },
      {
        "node_type": "Log",
        "name": "End",
        "config": {
          "message": "Execution complete"
        }
      }
    ]
  }
}
```

### Step 2: Validate the Tree

Before importing, validate your tree:

```bash
pyforest tree validate --file my_first_tree.json
```

If validation passes, you'll see: `Tree is valid`

### Step 3: Import the Tree

Add your tree to the library:

```bash
pyforest export import my_first_tree.json
```

### Step 4: Execute the Tree

Run your tree:

```bash
# List trees to get the ID
pyforest tree list --name "My First Tree"

# Run the tree
pyforest exec run <TREE_ID> --ticks 3
```

### Understanding the Output

The tree executes as follows:
1. The **Sequence** node executes children in order
2. The first **Log** prints "Starting execution"
3. The **Success** node returns SUCCESS
4. The second **Log** prints "Execution complete"
5. The **Sequence** returns SUCCESS (all children succeeded)

## Using Templates

Templates allow you to create reusable tree patterns with parameters.

### Step 1: List Available Templates

```bash
pyforest template list
```

You'll see templates like `simple_patrol` and `retry_task`.

### Step 2: View Template Details

```bash
pyforest template get simple_patrol
```

This shows the template's parameters and structure.

### Step 3: Instantiate a Template

Create a tree from the template:

```bash
pyforest template instantiate simple_patrol \
  --name "Office Patrol" \
  --interactive
```

The interactive mode will prompt you for parameter values:
- `num_waypoints`: Number of patrol points
- `scan_duration`: Time to scan at each point
- `battery_threshold`: Battery level to trigger charging

### Step 4: Run Your Templated Tree

```bash
pyforest tree list --name "Office Patrol"
pyforest exec run <TREE_ID> --ticks 10
```

## Executing Trees

PyForest supports three execution modes:

### Manual Mode

Execute a specific number of ticks:

```bash
pyforest exec run <TREE_ID> --ticks 10
```

### AUTO Mode

Execute continuously as fast as possible:

```bash
pyforest exec run <TREE_ID> --auto
```

Press Ctrl+C to stop.

### INTERVAL Mode

Execute with a fixed interval between ticks:

```bash
# Tick every 100ms
pyforest exec run <TREE_ID> --interval 100
```

### Monitoring Execution

Enable real-time monitoring:

```bash
pyforest exec run <TREE_ID> --auto --monitor
```

This displays live statistics:
- Total ticks executed
- Current tree status
- Average tick duration

### Viewing Statistics

After execution, view detailed statistics:

```bash
pyforest exec stats <EXECUTION_ID>
```

This shows:
- Total ticks and duration
- Average, min, max tick time
- Per-node statistics
- Top nodes by duration

## Next Steps

Now that you understand the basics, explore more advanced features:

### Debugging

Learn to use breakpoints and watches:

```bash
# Import the debug showcase tree
pyforest export import examples/trees/06_debug_showcase.json

# Run and explore debugging features via API
# See ARCHITECTURE.md for debugging details
```

### Performance Profiling

Profile tree performance:

```bash
pyforest profile <TREE_ID> --ticks 1000 --warmup 50
```

### Visualization

Export tree visualizations:

```bash
# Run tree to create execution
pyforest exec run <TREE_ID> --ticks 1

# Export as DOT graph
pyforest export dot <EXECUTION_ID> --output tree.dot --render
```

### Creating Custom Behaviors

See `ARCHITECTURE.md` for details on:
- Implementing custom behaviors
- Registering behaviors
- Behavior configuration schemas

### Using the REST API

While the CLI is convenient, you can also use the REST API directly:

```bash
# View API documentation
open http://localhost:8000/docs
```

The API provides:
- 47 endpoints across 7 routers
- WebSocket support for real-time updates
- Comprehensive tree management
- Execution control and monitoring

### Advanced Examples

Explore the example trees:

1. **01_simple_sequence.json** - Basic sequence pattern
2. **02_simple_selector.json** - Selector with fallback logic
3. **03_retry_pattern.json** - Retry decorator for error handling
4. **04_parallel_tasks.json** - Concurrent execution
5. **05_patrol_robot.json** - Realistic robot behavior
6. **06_debug_showcase.json** - Debugging features demonstration
7. **07_game_ai.json** - Game NPC AI example
8. **08_stress_test.json** - Performance testing

Each example demonstrates different patterns and capabilities.

## Common Patterns

### Sequence Pattern

Execute actions in order (all must succeed):

```json
{
  "node_type": "Sequence",
  "name": "Do Task",
  "children": [
    { "node_type": "CheckPrecondition", "name": "Check" },
    { "node_type": "ExecuteAction", "name": "Execute" },
    { "node_type": "VerifyResult", "name": "Verify" }
  ]
}
```

### Selector Pattern

Try actions until one succeeds (fallback logic):

```json
{
  "node_type": "Selector",
  "name": "Choose Action",
  "children": [
    { "node_type": "PreferredAction", "name": "Try First" },
    { "node_type": "AlternativeAction", "name": "Try Second" },
    { "node_type": "FallbackAction", "name": "Last Resort" }
  ]
}
```

### Retry Pattern

Retry an action multiple times:

```json
{
  "node_type": "Retry",
  "name": "Retry Task",
  "config": {
    "num_attempts": 3
  },
  "children": [
    { "node_type": "UnreliableAction", "name": "Task" }
  ]
}
```

### Parallel Pattern

Execute multiple actions concurrently:

```json
{
  "node_type": "Parallel",
  "name": "Do Multiple Things",
  "config": {
    "policy": "SuccessOnAll"
  },
  "children": [
    { "node_type": "Action1", "name": "Task 1" },
    { "node_type": "Action2", "name": "Task 2" },
    { "node_type": "Action3", "name": "Task 3" }
  ]
}
```

## Troubleshooting

### Server Not Starting

**Problem:** Server fails to start

**Solution:**
- Check if port 8000 is already in use: `lsof -i :8000`
- Use a different port: `uvicorn py_forest.api.main:app --port 8001`

### CLI Connection Errors

**Problem:** `Could not connect to API`

**Solution:**
- Verify server is running: `curl http://localhost:8000/behaviors/`
- Check CLI configuration: `pyforest config --show`
- Update API URL if needed: `pyforest config --api-url http://localhost:8000`

### Tree Validation Errors

**Problem:** Tree fails validation

**Solution:**
- Check for unknown behavior types: `pyforest tree validate --file tree.json`
- Verify all required config parameters are present
- Ensure JSON is valid: Use a JSON validator
- Check examples for reference: `examples/trees/`

### Execution Errors

**Problem:** Tree execution fails

**Solution:**
- Check tree is in library: `pyforest tree list`
- Verify tree ID is correct
- Check server logs for errors
- Use `--json` flag for detailed error messages

## Getting Help

### Documentation

- **Architecture Guide**: `docs/ARCHITECTURE.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Behavior Reference**: `docs/BEHAVIOR_REFERENCE.md`
- **CLI Guide**: `CLI_GUIDE.md`
- **Deployment Guide**: `docs/DEPLOYMENT.md`

### Interactive API Docs

Visit `http://localhost:8000/docs` for interactive API documentation with:
- All endpoints documented
- Request/response schemas
- Try-it-out functionality

### Examples

The `examples/trees/` directory contains 8 example trees with a README explaining each one.

### Community

- GitHub Issues: Report bugs or request features
- Discussions: Ask questions and share ideas

## Summary

You've learned:
- How to install and configure PyForest
- Core behavior tree concepts
- Creating and importing trees
- Using templates for reusable patterns
- Executing trees in different modes
- Monitoring and profiling execution
- Common tree patterns

Next, dive deeper into:
- **ARCHITECTURE.md**: Understand the system design
- **API_REFERENCE.md**: Explore all API endpoints
- **BEHAVIOR_REFERENCE.md**: Learn about available behaviors

Happy tree building!
