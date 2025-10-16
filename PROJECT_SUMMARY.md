# PyForest Project Summary

## Mission
Build a serializable behavior tree system with REST API and visual editor support on top of py_trees.

## Architecture Decision
**Two-tier system**: Tree Library (content management with versioning) + Execution Engine (runtime instances)

## Completed Phases

### Phase 1: Foundation ✅
**Files Created:** 15
- Pydantic models (tree.py, execution.py, schema.py)
- BehaviorRegistry with 13 behaviors (9 built-in py_trees + 3 custom)
- FileSystemTreeLibrary (versioning, search, CRUD)
- Custom behaviors: CheckBattery, Log, Wait
- Example tree: simple_tree.json

**Key Decisions:**
- Non-invasive approach (use py_trees as-is, no forking)
- Editor-first JSON format with UI metadata
- Semantic versioning for trees (MAJOR.MINOR.PATCH)
- Subtree references via $ref pattern

### Phase 2: Serialization & REST API ✅
**Files Created:** 13
- TreeSerializer (JSON ↔ py_trees with UUID mapping)
- SnapshotVisitor (state capture via visitor pattern)
- ExecutionService (instance lifecycle management)
- FastAPI app with 18 endpoints across 3 routers:
  - /trees (7 endpoints) - Library management
  - /behaviors (4 endpoints) - Schema for editors
  - /executions (7 endpoints) - Runtime control
- Integration tests (test_phase2.py)
- Server launcher (run_server.py)

**Technical Highlights:**
- Bottom-up building for decorators (need child in constructor)
- UUID mapping: TreeNodeDefinition ↔ py_trees nodes via `_pyforest_uuid` attribute
- Subtree resolution before deserialization
- Blackboard initialization from schema
- Singleton services via dependency injection

**API Verification:** All smoke tests passed ✅

## System Capabilities (Current)
1. **Store** trees as JSON with semantic versioning
2. **Search** trees by name/description/tags
3. **Serialize** JSON ↔ executable py_trees with UUID mapping
4. **Execute** multiple tree instances simultaneously
5. **Tick** trees (manual, auto, or interval modes)
6. **Capture** complete state snapshots with full history
7. **Monitor** via REST API + real-time WebSocket
8. **Hot-reload** trees without losing execution context
9. **Schedule** autonomous execution with pause/resume/stop
10. **Time-travel** through execution history

## Phase 3A: Real-time & History ✅
**Files Created:** 10

- EventEmitter system for real-time monitoring
- Event models (11 event types)
- ExecutionHistory with in-memory storage (1000 snapshots/execution)
- WebSocketManager for live client connections
- Enhanced ExecutionInstance with automatic event emission + history
- Hot-reload support (container-like tree replacement)
- WebSocket API endpoint (`WS /ws/executions/{id}`)
- History API (4 endpoints)
- Reload API (`PUT /executions/{id}/tree`)
- **Total API routes: 30** (up from 18)

**Key Features:**
- Real-time event streaming via WebSocket
- Automatic snapshot recording every tick
- Hot-reload trees without losing context
- Time-travel debugging (access any historical tick)
- Event filtering and subscription management
- Bounded memory with LRU eviction

## Phase 3B: Auto & Interval Execution ✅
**Files Created/Modified:** 5

- ExecutionScheduler with asyncio background tasks
- SchedulerContext for per-execution state management
- Scheduler models (SchedulerState, SchedulerStatus, StartSchedulerRequest)
- AUTO mode (tick as fast as possible)
- INTERVAL mode (tick every N milliseconds)
- Pause/Resume/Stop control
- Integrated with ExecutionService
- Scheduler control API (5 endpoints)
- **Total API routes: 35** (up from 30)

**Key Features:**
- Autonomous execution without manual control
- Background asyncio tasks (non-blocking)
- Start/pause/resume/stop at any time
- Stop conditions (terminal status, max ticks)
- Real-time WebSocket updates during autonomous execution
- Automatic history recording
- Error capture and graceful shutdown

## Next: Phase 3C/3D
Debugging (Breakpoints, Step modes, Watches) or Visualization (DOT graphs, Stats)
