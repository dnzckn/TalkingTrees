# Phase 3: Advanced Features & Debugging

## ULTRATHINK Analysis

### Current Limitations
1. **Manual execution only** - No auto/interval modes working yet
2. **No real-time updates** - Client must poll for state
3. **No execution history** - Can't see what happened between ticks
4. **No debugging tools** - Can't set breakpoints or step through
5. **No visualization** - Hard to see what the tree is doing
6. **Limited observability** - No metrics, no event subscriptions

### Goals for Phase 3
Transform PyForest from a basic API into a **production-ready debugging platform** for behavior trees.

## Design Philosophy

### Real-time First
- WebSocket connections for live execution monitoring
- Push-based updates (not polling)
- Multiple clients can observe same execution

### History-Aware
- Capture every tick as a snapshot
- Enable time-travel debugging
- Diff snapshots to see what changed

### Developer-Friendly
- Breakpoints on nodes
- Step-through execution
- Variable watching
- Performance metrics

## Feature Groups

### 1. WebSocket Real-time Updates 🔴 Critical

**Problem:** Client must poll `/snapshot` endpoint repeatedly. Inefficient and laggy.

**Solution:** WebSocket per execution that streams:
- Tick events (before/after)
- State changes
- Blackboard updates
- Status transitions
- Breakpoint hits

**Architecture:**
```
Client (Browser/Editor)
    ↓ WebSocket connect
WebSocketManager
    ↓ registers connection
ExecutionInstance
    ↓ emits events during tick
EventEmitter
    ↓ broadcasts to WebSocket
Client receives updates
```

**API Design:**
```python
# Connect
ws = WebSocket("/executions/{id}/ws")

# Receive messages
{
  "type": "tick_start",
  "tick": 42,
  "timestamp": "..."
}
{
  "type": "tick_complete",
  "tick": 42,
  "root_status": "RUNNING",
  "changes": {...}
}
{
  "type": "node_update",
  "node_id": "...",
  "status": "SUCCESS",
  "feedback": "..."
}
{
  "type": "blackboard_update",
  "key": "/battery/level",
  "value": 0.5,
  "old_value": 0.6
}
{
  "type": "breakpoint_hit",
  "node_id": "...",
  "node_name": "..."
}
```

**Implementation:**
- `WebSocketManager` - Connection registry per execution
- `EventEmitter` - Event generation during tick
- Modified `ExecutionInstance.tick()` to emit events
- New endpoint: `GET /executions/{id}/ws` (WebSocket)

### 2. Execution History 🔴 Critical

**Problem:** Can only see current state, not what happened before.

**Solution:** Store snapshot after each tick in chronological order.

**Features:**
- Get history: `GET /executions/{id}/history`
- Get specific tick: `GET /executions/{id}/history/{tick}`
- Get tick range: `GET /executions/{id}/history?from=10&to=20`
- Clear history: `DELETE /executions/{id}/history`
- History limits (max snapshots, auto-cleanup)

**Data Structure:**
```python
class ExecutionHistory:
    snapshots: List[ExecutionSnapshot]  # Ordered by tick
    max_snapshots: int = 1000

    def add_snapshot(snapshot)
    def get_tick(tick_number) -> ExecutionSnapshot
    def get_range(start, end) -> List[ExecutionSnapshot]
    def get_changes(from_tick, to_tick) -> Dict  # Delta
    def clear()
```

**Storage Strategy:**
- In-memory by default (fast, limited by RAM)
- Optional: Persist to SQLite for large histories
- Configurable retention: last N ticks or last M minutes

### 3. Auto & Interval Execution Modes 🔴 Critical

**Problem:** Only manual mode works. Can't run trees autonomously.

**Solution:** Background task scheduler for continuous/interval ticking.

**Modes:**
- `MANUAL` - Explicit tick commands (current)
- `AUTO` - Tick as fast as possible until terminal status
- `INTERVAL` - Tick every N milliseconds
- `PAUSED` - Temporarily stopped (can resume)

**Implementation:**
```python
class ExecutionScheduler:
    """Background scheduler for auto/interval execution."""

    def start_auto(execution_id: UUID, max_ticks: int = None)
    def start_interval(execution_id: UUID, interval_ms: int)
    def pause(execution_id: UUID)
    def resume(execution_id: UUID)
    def stop(execution_id: UUID)
```

**Technical Approach:**
- Use `asyncio` tasks for background execution
- Rate limiting with `asyncio.sleep()`
- Graceful cancellation via `task.cancel()`
- Stop conditions: terminal status, max_ticks, explicit stop

**New Endpoints:**
- `POST /executions/{id}/start` - Start auto/interval
- `POST /executions/{id}/pause` - Pause execution
- `POST /executions/{id}/resume` - Resume execution
- `POST /executions/{id}/stop` - Stop execution

### 4. Debugging Support 🟡 High Priority

**Hot-Reload (Container-like Isolation):**
- Replace running tree with new definition without losing execution context
- Cleanly shutdown current tree, deserialize and setup new one
- Preserve blackboard state (optional)
- Keep execution_id and history for comparison
- Like a container restart but without container software
- Critical for editor workflow: edit tree → hot-reload → test immediately

**Breakpoints:**
- Set on specific nodes
- Execution pauses when breakpoint hit
- Client notified via WebSocket
- Can inspect state, then continue or step

**Step Modes:**
- Step Over: Execute one tick, then pause
- Step Into: Execute until next node status change
- Step Out: Execute until parent node completes
- Continue: Run until next breakpoint or terminal

**Variable Watching:**
- Watch specific blackboard keys
- Break when value changes
- Break when value meets condition (e.g., `battery < 0.2`)

**Implementation:**
```python
class DebugContext:
    breakpoints: Set[UUID]  # Node IDs
    watches: Dict[str, WatchConfig]  # Blackboard key -> config
    step_mode: StepMode
    paused_at: Optional[UUID]  # Node where paused

    def should_break(node_id, blackboard) -> bool
    def evaluate_watches(blackboard) -> List[WatchHit]
```

**Integration:**
- Modify `ExecutionInstance.tick()` to check debug context
- Before ticking node, check if breakpoint
- After ticking, check watches
- Emit breakpoint_hit event via WebSocket

**New Endpoints:**
- `PUT /executions/{id}/tree` - Hot-reload with new tree definition
- `POST /executions/{id}/breakpoints` - Add breakpoint
- `DELETE /executions/{id}/breakpoints/{node_id}` - Remove
- `GET /executions/{id}/breakpoints` - List breakpoints
- `POST /executions/{id}/watches` - Add watch
- `POST /executions/{id}/step` - Step execution

### 5. Tree Visualization 🟡 High Priority

**Features:**
- Generate DOT graph from tree
- Highlight current state (tip node, running nodes)
- Annotate with status colors
- Export as SVG/PNG for docs

**Leverage py_trees:**
py_trees already has `display.render_dot_tree()` - we can enhance it.

**API:**
- `GET /trees/{id}/visualize?format=dot|svg|png`
- `GET /executions/{id}/visualize` - With current state overlay

**Enhancement:**
- Add UI metadata (positions, colors)
- Highlight execution path
- Show blackboard values inline

### 6. Execution Statistics 🟢 Medium Priority

**Metrics to Track:**
- Node visit counts
- Time spent in each node
- Success/failure rates per node
- Blackboard read/write counts
- Average tick duration
- Execution timeline

**Data Structure:**
```python
class ExecutionStats:
    node_visits: Dict[UUID, int]
    node_durations: Dict[UUID, List[float]]
    status_counts: Dict[UUID, Dict[Status, int]]
    tick_durations: List[float]
    blackboard_access: Dict[str, AccessStats]
```

**API:**
- `GET /executions/{id}/stats` - Get statistics
- `GET /executions/{id}/stats/nodes` - Per-node stats
- `GET /executions/{id}/stats/timeline` - Execution timeline

### 7. Event Subscription System 🟢 Medium Priority

**Built on WebSocket, provides filtered events:**

```javascript
// Subscribe to specific events
ws.send({
  "action": "subscribe",
  "events": ["tick_complete", "node_update"],
  "filters": {
    "node_ids": ["specific-uuid"],
    "statuses": ["FAILURE"]
  }
})
```

**Event Types:**
- `tick_start`, `tick_complete`
- `node_update` (status change)
- `blackboard_update` (value change)
- `breakpoint_hit`
- `execution_started`, `execution_stopped`
- `execution_completed` (terminal status)

## Implementation Plan

### Phase 3A: Real-time & History (Core)
1. Event emitter system in ExecutionInstance
2. WebSocket manager and endpoint
3. Execution history storage
4. History API endpoints
5. Integration tests

### Phase 3B: Advanced Execution (Modes)
1. Execution scheduler (asyncio tasks)
2. Auto/interval mode implementation
3. Pause/resume/stop control
4. Control endpoints
5. Integration tests

### Phase 3C: Debugging (Developer UX)
1. Debug context and breakpoint system
2. Watch expressions
3. Step execution modes
4. Debug API endpoints
5. Integration tests

### Phase 3D: Visualization & Stats (Observability)
1. Tree visualization with state overlay
2. DOT/SVG export
3. Statistics collector
4. Timeline generation
5. Visualization endpoints

## Technical Decisions

### WebSocket Framework
Use FastAPI's built-in WebSocket support (Starlette).

### Event Architecture
Observer pattern with `EventEmitter` class:
```python
class EventEmitter:
    def on(event_type, callback)
    def emit(event_type, data)
    def off(event_type, callback)
```

### History Storage
Start with in-memory, design for pluggable backends:
```python
class HistoryStore(ABC):
    @abstractmethod
    def add_snapshot(execution_id, snapshot)

    @abstractmethod
    def get_snapshot(execution_id, tick)

class InMemoryHistoryStore(HistoryStore): ...
class SQLiteHistoryStore(HistoryStore): ...
```

### Async Execution
Use FastAPI's `BackgroundTasks` or dedicated `asyncio` task pool for schedulers.

### Breaking Change: ExecutionService
Will need to become async-aware for auto/interval modes:
```python
class ExecutionService:
    scheduler: ExecutionScheduler
    history: HistoryStore
    ws_manager: WebSocketManager
```

## File Structure (New)

```
src/py_forest/
├── core/
│   ├── events.py          # EventEmitter
│   ├── history.py         # ExecutionHistory, HistoryStore
│   ├── scheduler.py       # ExecutionScheduler
│   ├── debug.py           # DebugContext, breakpoints
│   └── websocket.py       # WebSocketManager
├── api/
│   └── routers/
│       ├── websocket.py   # WebSocket endpoints
│       ├── history.py     # History endpoints
│       ├── debug.py       # Debug endpoints
│       └── visualization.py # Viz endpoints
└── utils/
    └── visualization.py   # Tree rendering helpers
```

## Success Criteria

✅ Real-time updates via WebSocket
✅ Execution history (last 1000 ticks)
✅ Auto/interval execution modes working
✅ Breakpoints pause execution
✅ Step-through debugging
✅ Tree visualization with state overlay
✅ Execution statistics available
✅ All features tested end-to-end

## Estimated Scope

**Files to Create:** ~12 new files
**API Endpoints:** +15 endpoints
**Models:** +8 new Pydantic models
**Lines of Code:** ~2000-2500 LOC

## Next Steps

Start with Phase 3A (Real-time & History) as foundation for everything else.
