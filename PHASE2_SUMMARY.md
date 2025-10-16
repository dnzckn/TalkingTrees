# Phase 2 Summary: Tree Serialization & REST API

## Overview

Phase 2 implements the core runtime functionality for PyForest:
- Tree serialization (JSON ↔ py_trees)
- Execution state capture and management
- Complete REST API with FastAPI

## Components Implemented

### 1. Tree Serialization (`core/serializer.py`)

**TreeSerializer** - Converts between JSON TreeDefinition and executable py_trees

**Key Features:**
- Bidirectional UUID mapping between TreeNodeDefinition and py_trees Behaviour instances
- Subtree reference resolution (`$ref` pattern)
- Bottom-up building strategy for decorators (which need children in constructor)
- Automatic blackboard initialization from schema

**Methods:**
- `deserialize(tree_def)` → `py_trees.BehaviourTree` - Main conversion method
- `_resolve_subtrees()` - Resolves $ref pointers before building
- `_build_node()` - Recursively builds nodes (handles composites, decorators, behaviors)
- `get_node_uuid()` / `get_node_by_uuid()` - UUID mapping lookups

**Technical Approach:**
```python
# Attaches UUID to py_trees nodes for reverse lookup
setattr(node, "_pyforest_uuid", uuid)

# Different building strategies per node category:
- Composites (Sequence, Selector): Build children first, pass to constructor
- Parallel: Build children + policy, pass to constructor
- Decorators (Inverter, Timeout, etc.): Build single child, pass to constructor
- Behaviors: Create via registry factory
```

### 2. State Snapshot (`core/snapshot.py`)

**SnapshotVisitor** - py_trees visitor that captures complete tree state

**Captures:**
- Node statuses and feedback messages
- Current child markers (for sequences/selectors)
- Tip node identification (deepest running node)
- Blackboard state (values + metadata)
- Tick counts and timestamps

**Function:**
- `capture_snapshot()` - Creates ExecutionSnapshot from running tree

**Integration:**
- Uses py_trees' built-in visitor pattern
- Leverages `_pyforest_uuid` attribute for node identification
- Captures blackboard metadata (readers, writers, exclusive access)

### 3. Execution Management (`core/execution.py`)

**ExecutionInstance** - Wrapper for a running tree instance

**Properties:**
- `execution_id` - Unique UUID for this execution
- `tree_def` - Original TreeDefinition
- `tree` - Live py_trees.BehaviourTree instance
- `serializer` - TreeSerializer with UUID mappings
- `config` - ExecutionConfig (mode, initial blackboard, etc.)
- `created_at`, `last_tick_at` - Timestamps

**Methods:**
- `tick(count)` → `TickResponse` - Execute N ticks
- `get_snapshot()` → `ExecutionSnapshot` - Capture current state
- `get_summary()` → `ExecutionSummary` - Quick status info

**ExecutionService** - Manages multiple execution instances

**Capabilities:**
- `create_execution(config)` - Load tree from library, deserialize, setup, create instance
- `get_execution(id)` - Retrieve instance
- `list_executions()` - List all instances
- `tick_execution(id, count, snapshot)` - Tick and optionally capture state
- `get_snapshot(id)` - Get current snapshot
- `delete_execution(id)` - Cleanup instance (calls tree.shutdown())
- `cleanup_stale_executions(hours)` - Remove old instances

### 4. REST API (`api/`)

**FastAPI Application** - Complete REST API with three router groups

#### Structure:
```
api/
├── main.py              # FastAPI app initialization
├── dependencies.py      # Dependency injection (singleton services)
└── routers/
    ├── trees.py         # Tree library management
    ├── behaviors.py     # Behavior schemas for editors
    └── executions.py    # Execution control
```

#### Tree Library Endpoints (`/trees`)
- `GET /trees/` - List all trees (catalog)
- `GET /trees/{tree_id}` - Get tree definition (optional version)
- `POST /trees/` - Create/save tree
- `PUT /trees/{tree_id}` - Update tree
- `DELETE /trees/{tree_id}` - Delete tree and all versions
- `GET /trees/{tree_id}/versions` - List all versions
- `GET /trees/search/?query={q}` - Search by name/description/tags

#### Behavior Schema Endpoints (`/behaviors`)
- `GET /behaviors/` - Get all behavior schemas (for editor palette)
- `GET /behaviors/types` - List all registered types
- `GET /behaviors/category/{category}` - Filter by category (composite/decorator/action/condition)
- `GET /behaviors/{node_type}` - Get specific behavior schema

#### Execution Control Endpoints (`/executions`)
- `POST /executions/` - Create new execution instance
  - Body: `ExecutionConfig` (tree_id, version, mode, initial_blackboard)
  - Returns: `ExecutionSummary`
- `GET /executions/` - List all executions
- `GET /executions/{id}` - Get execution summary
- `POST /executions/{id}/tick` - Tick the tree
  - Body: `TickRequest` (count, capture_snapshot)
  - Returns: `TickResponse` (with optional snapshot)
- `GET /executions/{id}/snapshot` - Get current snapshot
- `DELETE /executions/{id}` - Delete execution
- `POST /executions/cleanup` - Cleanup old executions

#### Dependencies:
- `tree_library_dependency()` - Provides TreeLibrary singleton
- `execution_service_dependency()` - Provides ExecutionService singleton
- `behavior_registry_dependency()` - Provides BehaviorRegistry singleton

#### CORS:
- Configured for web editor support (allowing all origins in dev)

## Testing

### Test Script (`test_phase2.py`)

Comprehensive integration test demonstrating:
1. Health check
2. Behavior schema retrieval (all, by category, specific)
3. Tree library management (create, list, get, search)
4. Execution lifecycle (create, tick, snapshot, delete)
5. Cleanup

**Usage:**
```bash
# Terminal 1: Start server
python run_server.py

# Terminal 2: Run tests
python test_phase2.py
```

### Server Script (`run_server.py`)

Convenience script to start the FastAPI server with uvicorn

**Features:**
- Default: localhost:8000
- Auto-reload enabled
- Shows API docs URLs
- Configurable host/port

## API Documentation

When server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Root**: http://localhost:8000/ (API info)
- **Health**: http://localhost:8000/health

## Example Workflow

### 1. Create Tree from Library
```bash
curl -X POST http://localhost:8000/trees/ \
  -H "Content-Type: application/json" \
  -d @examples/simple_tree.json
```

### 2. Create Execution
```bash
curl -X POST http://localhost:8000/executions/ \
  -H "Content-Type: application/json" \
  -d '{
    "tree_id": "550e8400-e29b-41d4-a716-446655440001",
    "mode": "manual",
    "initial_blackboard": {
      "/battery/level": 0.75
    }
  }'
```

### 3. Tick the Tree
```bash
curl -X POST http://localhost:8000/executions/{execution_id}/tick \
  -H "Content-Type: application/json" \
  -d '{
    "count": 1,
    "capture_snapshot": true
  }'
```

### 4. Get Snapshot
```bash
curl http://localhost:8000/executions/{execution_id}/snapshot
```

## Technical Highlights

### UUID Mapping Strategy
- Each TreeNodeDefinition has a UUID
- During deserialization, TreeSerializer attaches this UUID to the py_trees node as `_pyforest_uuid`
- SnapshotVisitor uses this attribute to map runtime state back to TreeNodeDefinition IDs
- Enables perfect round-tripping: JSON → py_trees → runtime state → JSON

### Subtree Resolution
- Trees can reference subtrees via `$ref: "#/subtrees/subtree_name"`
- `_resolve_subtrees()` recursively resolves these before building
- Enables tree composition and reusability

### Decorator Handling
- Decorators (Inverter, Timeout, etc.) require child in constructor
- Can't build parent before child
- TreeSerializer builds bottom-up recursively

### Blackboard Initialization
- TreeSerializer reads `blackboard_schema` from TreeDefinition
- Creates blackboard Client and registers keys with proper access rights
- Sets default values if specified in schema

### Execution Isolation
- Each execution is a separate py_trees.BehaviourTree instance
- Independent blackboard state
- Can run multiple executions of same tree definition simultaneously
- ExecutionService manages lifecycle

### State Capture
- Uses py_trees' visitor pattern (no intrusive modifications)
- Captures complete state: node statuses, blackboard, metadata
- Identifies tip node (deepest running node)
- Tracks current child for composites

## Integration Points

### With Phase 1:
- Uses TreeLibrary (filesystem storage) for tree definitions
- Uses BehaviorRegistry for node type → implementation mapping
- Uses all Pydantic models (TreeDefinition, ExecutionSnapshot, etc.)

### For Future Phases:
- WebSocket support for real-time updates (Phase 3?)
- Visual editor integration (Phase 4?)
- Debugging features: breakpoints, step-through (Phase 5?)
- History tracking and playback (Phase 5?)

## File Checklist

Phase 2 files created:
- ✅ `src/py_forest/core/serializer.py` - Tree serialization
- ✅ `src/py_forest/core/snapshot.py` - State capture
- ✅ `src/py_forest/core/execution.py` - Execution management
- ✅ `src/py_forest/core/__init__.py` - Updated exports
- ✅ `src/py_forest/api/__init__.py` - API package
- ✅ `src/py_forest/api/main.py` - FastAPI app
- ✅ `src/py_forest/api/dependencies.py` - DI singletons
- ✅ `src/py_forest/api/routers/__init__.py` - Routers package
- ✅ `src/py_forest/api/routers/trees.py` - Tree library endpoints
- ✅ `src/py_forest/api/routers/behaviors.py` - Schema endpoints
- ✅ `src/py_forest/api/routers/executions.py` - Execution endpoints
- ✅ `test_phase2.py` - Integration tests
- ✅ `run_server.py` - Server launcher
- ✅ `PHASE2_SUMMARY.md` - This document

## Status

✅ **Phase 2 Complete**

All core functionality implemented:
- TreeSerializer working (JSON ↔ py_trees)
- SnapshotVisitor capturing complete state
- ExecutionService managing instances
- REST API fully functional (18 endpoints)
- Integration tests passing
- Documentation complete

**Next Steps:**
- Phase 3: Advanced features (WebSockets, history, debugging)
- Phase 4: Visual editor integration
- Phase 5: Production hardening (auth, rate limiting, logging)
