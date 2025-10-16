# PyForest Architecture

This document provides a comprehensive overview of PyForest's architecture, design decisions, and implementation details.

## Table of Contents

1. [System Overview](#system-overview)
2. [Design Principles](#design-principles)
3. [Component Architecture](#component-architecture)
4. [Data Models](#data-models)
5. [Serialization System](#serialization-system)
6. [Execution Model](#execution-model)
7. [Event System](#event-system)
8. [Debugging Features](#debugging-features)
9. [Storage Layer](#storage-layer)
10. [API Layer](#api-layer)
11. [CLI Layer](#cli-layer)
12. [Extension Points](#extension-points)

## System Overview

PyForest is a serializable behavior tree management system built on top of py_trees. It provides:

- **Tree Library**: Content management for behavior tree definitions
- **Execution Engine**: Runtime instances with multiple concurrent executions
- **REST API**: HTTP/WebSocket interface for remote control
- **CLI**: Command-line tool for local management
- **Debugging Tools**: Breakpoints, watches, and step execution
- **Visualization**: DOT graphs and py_trees_js format export

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  (pyforest command - tree, template, exec, export, profile)  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP Client
┌────────────────────────────┴────────────────────────────────┐
│                        API Layer                             │
│  FastAPI + Uvicorn (REST + WebSocket)                       │
│  Routers: trees, behaviors, executions, debug, validation   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                      Core Services                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Tree Library │  │  Execution   │  │  Validation  │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Template   │  │  Statistics  │  │   Behavior   │      │
│  │   Engine     │  │   Tracker    │  │   Registry   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                      Core Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Tree      │  │   Execution  │  │    Event     │      │
│  │  Serializer  │  │   Instance   │  │   Emitter    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Snapshot   │  │    Debug     │  │   History    │      │
│  │   Visitor    │  │   Context    │  │    Store     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                     py_trees Layer                           │
│  Native py_trees behaviors, composites, decorators          │
└──────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Non-Invasive Integration

PyForest uses py_trees as-is without forking or modifying it. This ensures:
- Easy updates to latest py_trees versions
- Compatibility with py_trees ecosystem
- Clear separation of concerns

**Implementation**: UUID mapping via `_pyforest_uuid` attribute on py_trees nodes.

### 2. Two-Tier Architecture

Separation between tree definitions (library) and runtime instances (executions):

- **Tree Library**: Immutable tree definitions with versioning
- **Executions**: Stateful runtime instances with independent blackboards

**Benefits**:
- Multiple executions from one tree
- Tree updates don't affect running instances
- Clear lifecycle management

### 3. Editor-First Design

Trees stored as JSON with UI metadata support:

```json
{
  "node_type": "Sequence",
  "name": "Main Flow",
  "config": {},
  "ui_metadata": {
    "position": {"x": 100, "y": 200},
    "color": "#4CAF50",
    "notes": "Main execution flow"
  }
}
```

**Benefits**:
- Visual editor integration
- Human-readable format
- Version control friendly

### 4. API-First Development

All functionality exposed via REST API:
- CLI is a client of the API
- Easy integration with other tools
- Remote execution support

### 5. Event-Driven Monitoring

Observer pattern with event emitter:
- Real-time state updates via WebSocket
- Async event handlers
- Filtered subscriptions

## Component Architecture

### Core Components

#### 1. Behavior Registry

**Location**: `src/py_forest/core/registry.py`

Manages available behavior types:

```python
class BehaviorRegistry:
    def __init__(self):
        self._registry: Dict[str, BehaviorInfo] = {}

    def register(self, name: str, cls: Type[Behaviour], schema: BehaviorSchema):
        """Register a behavior type."""

    def get(self, name: str) -> BehaviorInfo:
        """Get behavior info by name."""

    def list_behaviors(self) -> List[Dict[str, Any]]:
        """List all registered behaviors."""
```

**Built-in Behaviors**: 9 standard py_trees behaviors
**Custom Behaviors**: CheckBattery, Log, Wait

#### 2. Tree Serializer

**Location**: `src/py_forest/core/serializer.py`

Handles bidirectional conversion between JSON and py_trees:

```python
class TreeSerializer:
    def serialize(self, tree_def: TreeDefinition) -> Behaviour:
        """Convert JSON to py_trees behavior tree."""
        # Bottom-up construction (decorators need child first)
        # UUID mapping via _pyforest_uuid
        # Subtree resolution via $ref pattern

    def deserialize(self, root: Behaviour) -> TreeDefinition:
        """Convert py_trees tree to JSON."""
        # Recursive tree traversal
        # UUID extraction from _pyforest_uuid
        # Config reconstruction
```

**Key Features**:
- UUID mapping for node identification
- Bottom-up tree construction
- Subtree reference resolution
- Config validation

#### 3. Execution Instance

**Location**: `src/py_forest/core/execution.py`

Manages runtime tree execution:

```python
class ExecutionInstance:
    def __init__(self, tree_id: str, root: Behaviour):
        self.execution_id = uuid4()
        self.root = root
        self.blackboard = Blackboard()
        self.event_emitter = EventEmitter()
        self.history = ExecutionHistory()
        self.debug_context = DebugContext()
        self.statistics = StatisticsTracker()

    def tick(self, count: int = 1) -> TickResult:
        """Execute tree ticks with debugging."""
        # Pre-tick: Check watches
        # Execute: Tick tree
        # Post-tick: Check breakpoints, emit events

    def setup(self):
        """Initialize tree."""

    def shutdown(self):
        """Clean up tree."""
```

**Lifecycle**:
1. Create from tree definition
2. Setup (py_trees setup)
3. Multiple ticks
4. Shutdown (py_trees shutdown)
5. Cleanup

#### 4. Event Emitter

**Location**: `src/py_forest/core/events.py`

Publishes execution events:

```python
class EventEmitter:
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}

    def on(self, event_type: EventType, handler: Callable):
        """Register event handler."""

    def emit(self, event: Event):
        """Emit event to all handlers."""

    async def emit_async(self, event: Event):
        """Async event emission."""
```

**Event Types**:
- TICK_STARTED, TICK_COMPLETED
- NODE_VISITED, NODE_STATUS_CHANGED
- BLACKBOARD_UPDATED
- EXECUTION_STARTED, EXECUTION_COMPLETED
- ERROR_OCCURRED
- BREAKPOINT_HIT, WATCH_TRIGGERED

#### 5. Debug Context

**Location**: `src/py_forest/core/debug.py`

Manages debugging state:

```python
class DebugContext:
    def __init__(self):
        self.is_paused = False
        self.breakpoints: List[Breakpoint] = []
        self.watches: Dict[str, WatchExpression] = {}
        self.step_mode: Optional[StepMode] = None

    def add_breakpoint(self, node_id: UUID, condition: Optional[str]):
        """Add breakpoint with optional condition."""

    def check_watches(self, blackboard: Blackboard) -> List[WatchEvent]:
        """Check watch expressions."""

    def check_breakpoint(self, node: Behaviour) -> bool:
        """Check if breakpoint should trigger."""
```

**Features**:
- Node-specific breakpoints
- Conditional breakpoints (Python expressions)
- Watch expressions (CHANGE, EQUALS, GREATER, etc.)
- Step modes (STEP_OVER, STEP_INTO, STEP_OUT, CONTINUE)

## Data Models

### Tree Definition

**Location**: `src/py_forest/models/tree.py`

```python
class TreeNodeDefinition(BaseModel):
    id: Optional[UUID] = None
    node_type: str
    name: str
    config: Dict[str, Any]
    children: List['TreeNodeDefinition'] = []
    ui_metadata: Optional[Dict[str, Any]] = None

class TreeMetadata(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    tags: List[str] = []
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TreeDefinition(BaseModel):
    tree_id: Optional[str] = None
    schema_version: str = Field(alias="$schema")
    metadata: TreeMetadata
    root: TreeNodeDefinition
    blackboard_schema: Optional[Dict[str, Any]] = None
```

### Execution Models

**Location**: `src/py_forest/models/execution.py`

```python
class ExecutionConfig(BaseModel):
    tree_id: str
    initial_blackboard: Optional[Dict[str, Any]] = None

class ExecutionInfo(BaseModel):
    execution_id: str
    tree_id: str
    root_status: str
    tick_count: int
    created_at: datetime

class TickResult(BaseModel):
    ticks_executed: int
    root_status: Status
    snapshot: Optional[TreeSnapshot] = None
```

## Serialization System

### UUID Mapping

Every node in the JSON tree has a UUID. During serialization, this UUID is stored on the py_trees node:

```python
def _serialize_node(self, node_def: TreeNodeDefinition) -> Behaviour:
    # Create py_trees node
    node = self._create_behavior(node_def)

    # Store UUID for future mapping
    node._pyforest_uuid = str(node_def.id)

    return node
```

This allows bidirectional mapping:
- **Serialize**: JSON UUID → py_trees node attribute
- **Deserialize**: py_trees node attribute → JSON UUID

### Bottom-Up Construction

Decorators in py_trees require their child in the constructor:

```python
# Correct order
child = Success(name="Child")
decorator = Retry(name="Retry", child=child, num_attempts=3)

# Wrong order (won't work)
decorator = Retry(name="Retry", num_attempts=3)
decorator.add_child(child)  # Decorators don't support this
```

PyForest handles this automatically by building trees bottom-up.

### Subtree References

Trees can reference other trees using `$ref`:

```python
{
  "node_type": "$ref",
  "name": "Reusable Subtree",
  "config": {
    "tree_id": "subtree-uuid-here"
  }
}
```

The serializer resolves references recursively.

## Execution Model

### Execution Modes

#### Manual Mode

Explicit tick control:

```python
result = execution.tick(count=1)
```

Use case: Step-by-step debugging, precise control

#### AUTO Mode

Continuous execution:

```python
scheduler.start_auto(execution_id)
# Ticks as fast as possible in background
```

Use case: Autonomous agents, simulations

#### INTERVAL Mode

Fixed-rate execution:

```python
scheduler.start_interval(execution_id, interval_ms=100)
# Ticks every 100ms
```

Use case: Real-time systems, game AI

### Scheduler Implementation

**Location**: `src/py_forest/core/scheduler.py`

```python
class ExecutionScheduler:
    def __init__(self, execution_service: ExecutionService):
        self.execution_service = execution_service
        self.contexts: Dict[str, SchedulerContext] = {}

    async def start_auto(self, execution_id: str):
        """Start continuous execution."""
        context = SchedulerContext(mode=ExecutionMode.AUTO)
        task = asyncio.create_task(self._auto_loop(execution_id, context))
        context.task = task
        self.contexts[execution_id] = context

    async def _auto_loop(self, execution_id: str, context: SchedulerContext):
        """AUTO mode loop."""
        while not context.is_stopped:
            if not context.is_paused:
                self.execution_service.tick(execution_id, count=1)
            await asyncio.sleep(0)  # Yield control
```

### Blackboard Management

Each execution has its own blackboard:

```python
# Execution 1
exec1_blackboard = exec1.blackboard
exec1_blackboard.set("position", [0, 0])

# Execution 2 (independent)
exec2_blackboard = exec2.blackboard
exec2_blackboard.set("position", [10, 10])
```

Blackboard is preserved during hot-reload:

```python
def hot_reload(self, new_tree_def: TreeDefinition):
    # Save blackboard state
    old_blackboard_data = self.blackboard.to_dict()

    # Shutdown old tree
    self.shutdown()

    # Create new tree
    new_root = serializer.serialize(new_tree_def)
    self.root = new_root
    self.setup()

    # Restore blackboard
    self.blackboard.from_dict(old_blackboard_data)
```

## Event System

### Event Flow

```
┌──────────────┐
│  Execution   │
│   Instance   │
└──────┬───────┘
       │ emit(event)
       ▼
┌──────────────┐
│    Event     │
│   Emitter    │
└──┬─────────┬─┘
   │         │
   ▼         ▼
┌─────┐   ┌─────────┐
│ WS  │   │ History │
│Client   │ Store   │
└─────┘   └─────────┘
```

### Event Handlers

**Synchronous**:
```python
def on_tick(event: Event):
    print(f"Tick {event.data['tick_count']}")

emitter.on(EventType.TICK_COMPLETED, on_tick)
```

**Asynchronous**:
```python
async def on_tick_async(event: Event):
    await save_to_database(event)

emitter.on(EventType.TICK_COMPLETED, on_tick_async)
await emitter.emit_async(event)
```

### WebSocket Integration

**Location**: `src/py_forest/core/websocket.py`

```python
class WebSocketManager:
    async def connect(self, execution_id: str, websocket: WebSocket):
        """Connect client to execution events."""
        await websocket.accept()

        def send_event(event: Event):
            asyncio.create_task(websocket.send_json(event.dict()))

        # Subscribe to events
        emitter = self.get_emitter(execution_id)
        emitter.on(EventType.ALL, send_event)
```

## Debugging Features

### Breakpoints

**Types**:
1. **Unconditional**: Always break at node
2. **Conditional**: Break if expression is true

**Example**:
```python
# Unconditional
debug_context.add_breakpoint(node_id)

# Conditional
debug_context.add_breakpoint(
    node_id,
    condition="blackboard.get('battery_level') < 20"
)
```

**Evaluation**:
```python
def _eval_condition(self, condition: str, node: Behaviour) -> bool:
    context = {
        'node': node,
        'blackboard': self.blackboard,
        'status': node.status,
    }
    try:
        return eval(condition, {"__builtins__": {}}, context)
    except Exception:
        return False
```

### Watch Expressions

**Conditions**:
- `CHANGE`: Value changed since last check
- `EQUALS`: Value equals target
- `NOT_EQUALS`: Value not equals target
- `GREATER`: Value > target
- `LESS`: Value < target
- `GREATER_OR_EQUAL`: Value >= target
- `LESS_OR_EQUAL`: Value <= target

**Implementation**:
```python
def check_watches(self, blackboard: Blackboard) -> List[WatchEvent]:
    events = []
    for key, watch in self.watches.items():
        current_value = blackboard.get(key)

        if watch.condition == WatchCondition.CHANGE:
            if current_value != watch.last_value:
                events.append(WatchEvent(key=key, old=watch.last_value, new=current_value))
                watch.last_value = current_value

        elif watch.condition == WatchCondition.EQUALS:
            if current_value == watch.target_value:
                events.append(WatchEvent(key=key, value=current_value))

    return events
```

### Step Execution

**Modes**:
- **STEP_OVER**: Execute until next node at same level
- **STEP_INTO**: Execute one node, enter children
- **STEP_OUT**: Execute until parent completes
- **CONTINUE**: Resume normal execution

**Implementation**:
```python
def should_pause_after_tick(self, node: Behaviour) -> bool:
    if self.step_mode == StepMode.STEP_OVER:
        return node == self.step_target_node

    elif self.step_mode == StepMode.STEP_INTO:
        return True  # Pause after every node

    elif self.step_mode == StepMode.STEP_OUT:
        return node == self.step_target_node.parent

    return False
```

## Storage Layer

### File System Tree Library

**Location**: `src/py_forest/storage/filesystem.py`

```python
class FileSystemTreeLibrary(TreeLibrary):
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.root_path.mkdir(parents=True, exist_ok=True)

    def save(self, tree: TreeDefinition) -> TreeDefinition:
        """Save tree to filesystem."""
        tree_id = tree.tree_id or str(uuid4())
        version = tree.metadata.version

        # Create versioned directory
        tree_dir = self.root_path / tree_id / version
        tree_dir.mkdir(parents=True, exist_ok=True)

        # Save tree.json
        tree_file = tree_dir / "tree.json"
        with open(tree_file, 'w') as f:
            json.dump(tree.dict(), f, indent=2)

        return tree

    def get(self, tree_id: str, version: Optional[str] = None) -> TreeDefinition:
        """Load tree from filesystem."""
        # Find latest version if not specified
        # Load and parse JSON
        # Return TreeDefinition
```

**Directory Structure**:
```
data/trees/
├── tree-uuid-1/
│   ├── 1.0.0/
│   │   └── tree.json
│   └── 1.1.0/
│       └── tree.json
└── tree-uuid-2/
    └── 1.0.0/
        └── tree.json
```

## API Layer

### Router Organization

**Routers** (7 total):
1. `trees` - Tree library management
2. `behaviors` - Behavior registry
3. `executions` - Execution lifecycle
4. `history` - Execution history
5. `debug` - Debugging features
6. `visualization` - Tree visualization
7. `validation` - Tree validation

### Dependency Injection

**Location**: `src/py_forest/api/dependencies.py`

```python
# Singletons
_behavior_registry: BehaviorRegistry | None = None
_tree_library: TreeLibrary | None = None
_execution_service: ExecutionService | None = None

# FastAPI dependencies
def behavior_registry_dependency() -> Generator[BehaviorRegistry, None, None]:
    yield get_behavior_registry()

def tree_library_dependency() -> Generator[TreeLibrary, None, None]:
    yield get_tree_library()

def execution_service_dependency() -> Generator[ExecutionService, None, None]:
    yield get_execution_service()
```

### WebSocket Endpoint

**Location**: `src/py_forest/api/routers/websocket.py`

```python
@router.websocket("/ws/executions/{execution_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    execution_id: str,
    ws_manager: WebSocketManager = Depends(websocket_manager_dependency),
):
    await ws_manager.connect(execution_id, websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(execution_id, websocket)
```

## CLI Layer

### Command Structure

```
pyforest
├── tree (commands/tree.py)
│   ├── list
│   ├── get
│   ├── create
│   ├── delete
│   └── validate
├── template (commands/template.py)
│   ├── list
│   ├── get
│   ├── create
│   └── instantiate
├── exec (commands/execution.py)
│   ├── list
│   ├── run
│   ├── tick
│   ├── stop
│   ├── delete
│   ├── snapshot
│   └── stats
├── export (commands/export.py)
│   ├── tree
│   ├── import
│   ├── dot
│   ├── batch
│   └── batch-import
├── config
├── profile
└── version
```

### API Client

**Location**: `src/py_forest/cli/client.py`

```python
class APIClient:
    def __init__(self, base_url: str, timeout: int):
        self.base_url = base_url
        self.timeout = timeout

    def _request(self, method: str, endpoint: str, **kwargs):
        """Make API request with error handling."""
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except ConnectionError:
            raise Exception(f"Could not connect to API at {self.base_url}")
        except RequestException as e:
            # Parse and re-raise error
```

## Extension Points

### Custom Behaviors

**Steps**:
1. Create behavior class inheriting from `py_trees.behaviour.Behaviour`
2. Define configuration schema
3. Register with BehaviorRegistry

**Example**:
```python
class CustomBehavior(Behaviour):
    def __init__(self, name: str, param1: str):
        super().__init__(name)
        self.param1 = param1

    def update(self) -> Status:
        # Implement behavior logic
        return Status.SUCCESS

# Schema
schema = BehaviorSchema(
    name="CustomBehavior",
    parameters=[
        ParameterSchema(name="param1", type="string", required=True)
    ]
)

# Register
registry.register("CustomBehavior", CustomBehavior, schema)
```

### Custom Storage Backend

Implement `TreeLibrary` interface:

```python
class DatabaseTreeLibrary(TreeLibrary):
    def save(self, tree: TreeDefinition) -> TreeDefinition:
        # Save to database

    def get(self, tree_id: str, version: Optional[str] = None) -> TreeDefinition:
        # Load from database

    def delete(self, tree_id: str) -> None:
        # Delete from database

    def list_trees(self) -> List[TreeDefinition]:
        # Query database
```

### Custom Event Handlers

Subscribe to execution events:

```python
def custom_handler(event: Event):
    if event.type == EventType.NODE_STATUS_CHANGED:
        # Custom logic
        pass

execution.event_emitter.on(EventType.NODE_STATUS_CHANGED, custom_handler)
```

### Custom Validators

Extend tree validation:

```python
class CustomValidator:
    def validate(self, tree_def: TreeDefinition) -> ValidationResult:
        issues = []

        # Custom validation logic
        if self._check_custom_rule(tree_def):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                code="CUSTOM_RULE",
                message="Custom rule violated"
            ))

        return ValidationResult(
            is_valid=len([i for i in issues if i.level == "error"]) == 0,
            issues=issues
        )
```

## Performance Considerations

### Execution Overhead

Each tick involves:
1. Pre-tick watch checks (O(watches))
2. Tree tick (O(nodes visited))
3. Post-tick breakpoint checks (O(breakpoints))
4. Event emission (O(handlers))
5. History storage (O(1) with LRU eviction)

**Optimization**: Disable features not in use.

### Memory Management

- **Execution instances**: Keep in memory while active
- **History**: LRU eviction after 1000 snapshots
- **Event handlers**: Weak references to avoid leaks

### Concurrent Executions

Each execution is independent:
- Separate blackboard
- Separate event emitter
- Thread-safe via asyncio

**Scaling**: Horizontal scaling via multiple API instances with shared storage.

## Security Considerations

### Conditional Breakpoints

Breakpoint conditions use `eval()` with restricted builtins:

```python
eval(condition, {"__builtins__": {}}, context)
```

This prevents:
- File system access
- Network access
- Module imports

**Limitation**: Still allows Python expressions. In production, consider:
- Sandboxed evaluation
- Expression parser with whitelisted operations
- Disabled conditional breakpoints

### API Authentication

Currently no authentication. For production:
- Add API key authentication
- Implement role-based access control
- Use HTTPS/WSS

## Testing Strategy

### Unit Tests

Test individual components in isolation:
- BehaviorRegistry
- TreeSerializer
- TreeValidator
- TemplateEngine

### Integration Tests

Test end-to-end workflows:
- Tree creation and execution
- Template instantiation
- Debugging features
- Visualization export

### Performance Tests

Benchmark critical paths:
- Tree serialization
- Tick execution
- Event emission
- History storage

## Future Enhancements

### Planned Features

1. **Distributed Execution**: Run executions across multiple machines
2. **Persistent Storage**: Database backend for trees and history
3. **Advanced Visualization**: Interactive web-based tree editor
4. **Behavior Marketplace**: Share and discover custom behaviors
5. **Execution Replay**: Load and replay execution from history
6. **Performance Metrics**: APM-style monitoring and tracing

### Extension Ideas

1. **ROS Integration**: Direct integration with Robot Operating System
2. **Unity Plugin**: Behavior trees for Unity game engine
3. **Jupyter Notebooks**: Interactive tree development
4. **CI/CD Integration**: Automated tree testing
5. **Cloud Deployment**: Managed PyForest service

## Summary

PyForest's architecture provides:
- Clear separation of concerns
- Extensibility at multiple levels
- Non-invasive py_trees integration
- Production-ready REST API
- Comprehensive debugging tools

The system is designed for:
- Robot behavior control
- Game AI development
- Automation workflows
- Educational purposes

For more information:
- **Getting Started**: `docs/GETTING_STARTED.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Behavior Reference**: `docs/BEHAVIOR_REFERENCE.md`
