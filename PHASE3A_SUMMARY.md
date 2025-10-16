# Phase 3A Summary: Real-time & History

## Overview
Phase 3A implements the foundation for advanced execution monitoring:
- **Event System** - Real-time event emission during execution
- **WebSocket Support** - Live updates via WebSocket connections
- **Execution History** - Automatic snapshot recording per tick
- **Hot-Reload** - Container-like tree replacement without losing context

## Components Implemented

### 1. Event System (`core/events.py`)

**EventEmitter** - Observer pattern for execution events
- Supports both sync and async listeners
- Wildcard listeners for all events
- Type-safe event handling
- Thread-safe concurrent access

**FilteredEventEmitter** - Event filtering support
- Filter by event type
- Filter by tick range
- Filter by node IDs
- Filter by blackboard keys

**Features:**
```python
emitter = EventEmitter()

# Register listeners
emitter.on(EventType.TICK_COMPLETE, handle_tick)
emitter.on_async(EventType.NODE_UPDATED, handle_node_async)
emitter.on_any(handle_all_events)

# Emit events
emitter.emit(TickCompleteEvent(...))
await emitter.emit_async(NodeUpdateEvent(...))
```

### 2. Event Models (`models/events.py`)

**Event Types:**
- `EXECUTION_STARTED`, `EXECUTION_STOPPED`, `EXECUTION_PAUSED`
- `EXECUTION_RESUMED`, `EXECUTION_COMPLETED`, `TREE_RELOADED`
- `TICK_START`, `TICK_COMPLETE`
- `NODE_INITIALISED`, `NODE_UPDATED`, `NODE_TERMINATED`
- `BLACKBOARD_UPDATE`, `BLACKBOARD_ACCESS`
- `BREAKPOINT_HIT`, `WATCH_TRIGGERED`
- `EXECUTION_ERROR`

**Event Classes:**
- `TickStartEvent` - Emitted before tick execution
- `TickCompleteEvent` - Emitted after tick with status/changes
- `NodeUpdateEvent` - Node status changed
- `BlackboardUpdateEvent` - Blackboard value changed
- `BreakpointHitEvent` - Breakpoint encountered
- `WatchTriggeredEvent` - Watch condition met
- `TreeReloadedEvent` - Tree hot-reloaded
- `ExecutionErrorEvent` - Error during execution

**EventFilter** - Subscription filtering
```python
filter = EventFilter(
    event_types=[EventType.TICK_COMPLETE, EventType.NODE_UPDATED],
    node_ids=[specific_uuid],
    min_tick=10,
    max_tick=100
)
```

### 3. Execution History (`core/history.py`)

**HistoryStore (ABC)** - Abstract storage interface
- `add_snapshot()` - Store snapshot
- `get_snapshot(tick)` - Retrieve by tick
- `get_range(start, end)` - Retrieve range
- `get_all()` - All snapshots
- `get_latest()` - Most recent
- `clear()` - Delete history
- `count()` - Count snapshots

**InMemoryHistoryStore** - Fast in-memory implementation
- Configurable max snapshots (default: 1000)
- LRU eviction when limit reached
- O(1) access by tick number
- Automatic cleanup of old executions

**ExecutionHistory** - High-level history manager
- `record_snapshot()` - Auto-record during tick
- `get_changes(from, to)` - Diff between ticks
- Delegates to storage backend

**Features:**
```python
history = ExecutionHistory(InMemoryHistoryStore(1000))

# Automatic recording (handled by ExecutionInstance)
history.record_snapshot(snapshot)

# Retrieve history
all_snaps = history.get_all(execution_id)
tick_5 = history.get_tick(execution_id, 5)
range_snaps = history.get_range(execution_id, 0, 10)

# Get changes
changes = history.get_changes(execution_id, 5, 10)
# Returns: {
#   "status_changes": [...],
#   "blackboard_changes": [...],
#   "node_changes": [...]
# }
```

### 4. WebSocket Manager (`core/websocket.py`)

**WebSocketConnection** - Single WebSocket client
- Event filtering per connection
- Subscription management
- Auto-disconnect on error
- Message validation

**WebSocketManager** - Global connection registry
- Per-execution connection pools
- Broadcast events to all clients
- Automatic cleanup of dead connections
- Connection statistics

**Features:**
```python
ws_manager = get_websocket_manager()

# Connect (handled by endpoint)
conn = await ws_manager.connect(websocket, execution_id)

# Broadcast to all clients
await ws_manager.broadcast_event(execution_id, event)

# Stats
count = ws_manager.get_connection_count(execution_id)
total = ws_manager.get_total_connections()
```

### 5. Enhanced ExecutionInstance

**New Features:**
- EventEmitter integration - emits events during tick
- History recording - stores snapshot after each tick
- Hot-reload support - `reload_tree()` method

**Event Emission:**
- `TICK_START` - Before tick execution
- `TICK_COMPLETE` - After tick with status
- `TREE_RELOADED` - After hot-reload

**Hot-Reload (`reload_tree`):**
```python
# Like docker restart but without docker
instance.reload_tree(
    new_tree_def=new_definition,
    preserve_blackboard=True  # Keep blackboard state
)
```

**Process:**
1. Preserve blackboard if requested
2. Shutdown current tree (`tree.shutdown()`)
3. Deserialize new tree
4. Restore blackboard values
5. Setup new tree (`tree.setup()`)
6. Emit `TREE_RELOADED` event

**Use Case:** Editor workflow
1. Edit tree in visual editor
2. PUT to `/executions/{id}/tree`
3. Tree hot-reloads instantly
4. Test immediately without recreating execution

### 6. Enhanced ExecutionService

**New Methods:**
- `reload_tree(id, tree_def, preserve_bb)` - Hot-reload
- `get_history(id)` - Get all history
- `get_history_snapshot(id, tick)` - Get specific tick
- `get_history_range(id, start, end)` - Get range

**Configuration:**
```python
service = ExecutionService(
    tree_library=library,
    enable_history=True,  # Enable history tracking
    max_history_snapshots=1000  # Max per execution
)
```

**Automatic History:**
- Every tick automatically recorded
- No manual calls needed
- Configurable retention limits

### 7. WebSocket API (`api/routers/websocket.py`)

**Endpoint:** `WS /ws/executions/{execution_id}`

**Client Commands:**
```json
// Subscribe to specific events
{"action": "subscribe", "events": ["tick_complete", "node_update"]}

// Unsubscribe
{"action": "unsubscribe", "events": ["tick_complete"]}

// Subscribe to all
{"action": "subscribe_all"}

// Update filter
{"action": "filter", "filter": {"min_tick": 10, "max_tick": 100}}

// Ping
{"action": "ping"}
```

**Server Messages:**
```json
// Connection confirmed
{"action": "connected", "data": {...}, "timestamp": "..."}

// Event
{"action": "event", "data": {event object}, "timestamp": "..."}

// Pong
{"action": "pong", "data": {}, "timestamp": "..."}

// Error
{"action": "error", "data": {"message": "..."}, "timestamp": "..."}
```

**Usage:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/executions/{id}');

ws.onmessage = (msg) => {
    const data = JSON.parse(msg.data);
    if (data.action === 'event') {
        console.log('Event:', data.data);
    }
};

// Subscribe to tick events
ws.send(JSON.stringify({
    action: 'subscribe',
    events: ['tick_complete']
}));
```

### 8. History API (`api/routers/history.py`)

**Endpoints:**
- `GET /history/executions/{id}` - Get all history
- `GET /history/executions/{id}/tick/{tick}` - Get specific tick
- `GET /history/executions/{id}/range?start=0&end=10` - Get range
- `GET /history/executions/{id}/changes?from=5&to=10` - Get changes

**Examples:**
```bash
# Get all history
curl http://localhost:8000/history/executions/{id}

# Get tick 5
curl http://localhost:8000/history/executions/{id}/tick/5

# Get range
curl "http://localhost:8000/history/executions/{id}/range?start_tick=0&end_tick=10"

# Get changes
curl "http://localhost:8000/history/executions/{id}/changes?from_tick=5&to_tick=10"
```

### 9. Execution Reload API

**Endpoint:** `PUT /executions/{id}/tree`

**Request Body:**
```json
{
    "tree_definition": {...},
    "preserve_blackboard": true
}
```

**Response:** Updated `ExecutionSummary`

**Example:**
```bash
curl -X PUT http://localhost:8000/executions/{id}/tree \
  -H "Content-Type: application/json" \
  -d @modified_tree.json
```

## Integration Points

### Event → WebSocket Flow
1. `ExecutionInstance.tick()` executes
2. Events emitted via `EventEmitter`
3. WebSocket listeners receive events
4. Events broadcast to all connected clients
5. Clients receive real-time updates

### Automatic History Flow
1. `ExecutionInstance.tick()` executes
2. After each tick, snapshot captured
3. Snapshot stored in `ExecutionHistory`
4. History queryable via API
5. Old snapshots evicted when limit reached

### Hot-Reload Flow
1. Client PUTs new tree definition
2. `ExecutionService.reload_tree()` called
3. Current tree shutdown, blackboard preserved
4. New tree deserialized and setup
5. Blackboard restored
6. `TREE_RELOADED` event emitted
7. Execution continues with new tree

## Technical Highlights

### Memory Management
- History stores limited to 1000 snapshots by default
- LRU eviction prevents unbounded growth
- Configurable limits per execution
- Cleanup on execution deletion

### Thread Safety
- EventEmitter uses asyncio.Lock
- WebSocketManager uses asyncio.Lock
- Safe concurrent access from multiple clients

### Error Handling
- WebSocket auto-cleanup on disconnect
- Best-effort tree shutdown on reload
- Graceful fallback if blackboard restore fails
- Error events for execution failures

### Performance
- O(1) history access by tick number
- Async event broadcasting
- No blocking during event emission
- Efficient snapshot storage

## API Endpoint Count

**Phase 2:** 18 endpoints
**Phase 3A:** 30 endpoints (+12)

**New Endpoints:**
- 1 WebSocket endpoint
- 4 History endpoints
- 1 Reload endpoint
- 6 Updated execution endpoints

## Testing

Phase 3A features can be tested via:

```python
# Test events
from py_forest.core.events import EventEmitter, EventType
from py_forest.models.events import TickCompleteEvent

emitter = EventEmitter()
emitter.on(EventType.TICK_COMPLETE, lambda e: print(f"Tick {e.tick}"))
emitter.emit(TickCompleteEvent(...))

# Test history
from py_forest.core.history import ExecutionHistory, InMemoryHistoryStore

history = ExecutionHistory(InMemoryHistoryStore(100))
history.record_snapshot(snapshot)
all_snaps = history.get_all(execution_id)

# Test WebSocket (requires running server)
# Use test_phase3a.py script

# Test hot-reload
PUT /executions/{id}/tree with new tree definition
```

## File Checklist

Phase 3A files created:
- ✅ `src/py_forest/models/events.py` - Event models
- ✅ `src/py_forest/core/events.py` - EventEmitter
- ✅ `src/py_forest/core/history.py` - Execution history
- ✅ `src/py_forest/core/websocket.py` - WebSocket manager
- ✅ `src/py_forest/core/execution.py` - Enhanced (events + history)
- ✅ `src/py_forest/api/routers/websocket.py` - WebSocket endpoint
- ✅ `src/py_forest/api/routers/history.py` - History endpoints
- ✅ `src/py_forest/api/routers/executions.py` - Updated (reload)
- ✅ `src/py_forest/api/main.py` - Updated (new routers)
- ✅ `PHASE3A_SUMMARY.md` - This document

## Status

✅ **Phase 3A Complete** - Real-time & History

All core features implemented:
- Event system working
- WebSocket support functional
- Execution history automatic
- Hot-reload operational
- API endpoints tested
- Code compiles successfully (30 routes)

**Next Steps:**
- Phase 3B: Auto/Interval Execution (Background scheduler)
- Phase 3C: Debugging (Breakpoints, step mode, watches)
- Phase 3D: Visualization & Stats

## Usage Example

```python
import asyncio
import websockets
import json

# Connect to execution WebSocket
async def monitor_execution(execution_id):
    uri = f"ws://localhost:8000/ws/executions/{execution_id}"

    async with websockets.connect(uri) as websocket:
        # Subscribe to tick events
        await websocket.send(json.dumps({
            "action": "subscribe",
            "events": ["tick_complete"]
        }))

        # Receive events
        async for message in websocket:
            data = json.loads(message)
            if data['action'] == 'event':
                event = data['data']
                print(f"Tick {event['tick']}: {event['root_status']}")

# Run monitor
asyncio.run(monitor_execution("execution-uuid-here"))
```

## Key Achievements

1. **Real-time Monitoring** - No more polling, push-based updates
2. **Time-Travel Debugging** - Access any historical tick
3. **Hot-Reload** - Instant tree updates without recreation
4. **Zero Config** - History and events work automatically
5. **Scalable** - Handles multiple clients per execution
6. **Memory Safe** - Bounded history with LRU eviction

Phase 3A provides the foundation for a production-ready behavior tree debugging and monitoring platform!
