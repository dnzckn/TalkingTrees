"""Execution service for managing tree instances."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import py_trees

from py_forest.core.debug import DebugContext
from py_forest.core.events import EventEmitter
from py_forest.core.history import ExecutionHistory, InMemoryHistoryStore
from py_forest.core.scheduler import ExecutionScheduler
from py_forest.core.serializer import TreeSerializer
from py_forest.core.snapshot import capture_snapshot
from py_forest.core.statistics import StatisticsTracker
from py_forest.models.debug import DebugState, StepMode
from py_forest.models.events import (
    BreakpointHitEvent,
    EventType,
    TickCompleteEvent,
    TickStartEvent,
    TreeReloadedEvent,
)
from py_forest.models.execution import (
    ExecutionConfig,
    ExecutionMode,
    ExecutionSnapshot,
    ExecutionSummary,
    SchedulerStatus,
    StartSchedulerRequest,
    Status,
    TickResponse,
)
from py_forest.models.tree import TreeDefinition
from py_forest.models.visualization import ExecutionStatistics
from py_forest.storage.base import TreeLibrary


class ExecutionInstance:
    """A single execution instance of a behavior tree.

    Represents a running (or runnable) instance of a tree definition.
    Enhanced with event emission and history tracking.
    """

    def __init__(
        self,
        execution_id: UUID,
        tree_def: TreeDefinition,
        tree: py_trees.trees.BehaviourTree,
        serializer: TreeSerializer,
        config: ExecutionConfig,
        event_emitter: Optional[EventEmitter] = None,
        history: Optional[ExecutionHistory] = None,
    ):
        """Initialize execution instance.

        Args:
            execution_id: Unique execution identifier
            tree_def: Tree definition
            tree: Instantiated py_trees tree
            serializer: Serializer with UUID mappings
            config: Execution configuration
            event_emitter: Optional event emitter for real-time updates
            history: Optional history manager for snapshot storage
        """
        self.execution_id = execution_id
        self.tree_def = tree_def
        self.tree = tree
        self.serializer = serializer
        self.config = config
        self.created_at = datetime.utcnow()
        self.last_tick_at: Optional[datetime] = None
        self.is_running = False

        # Event and history support
        self.event_emitter = event_emitter or EventEmitter()
        self.history = history

        # Debug support
        self.debug = DebugContext(execution_id)

        # Statistics tracking
        self.statistics = StatisticsTracker(execution_id)

    def tick(self, count: int = 1) -> TickResponse:
        """Tick the tree.

        Args:
            count: Number of ticks to execute

        Returns:
            Tick response with status and optional snapshot
        """
        initial_count = self.tree.count

        # Emit tick start event
        self.event_emitter.emit(
            TickStartEvent(
                execution_id=self.execution_id,
                tick=self.tree.count,
                count=count,
            )
        )

        # Execute ticks
        for _ in range(count):
            # Check if paused by debugger
            if self.debug.is_paused:
                break

            # Statistics: Start tick timing
            self.statistics.on_tick_start()

            # Pre-tick: Check watches
            blackboard = self._get_blackboard_dict()
            watch_event = self.debug.check_watches(blackboard)
            if watch_event:
                self.event_emitter.emit(watch_event)
                break

            # Execute tick
            self.tree.tick()
            self.last_tick_at = datetime.utcnow()

            # Statistics: End tick timing
            root_status = Status(self.tree.root.status.value)
            self.statistics.on_tick_end(root_status)

            # Post-tick: Check breakpoints at tip node
            tip = self.tree.tip()
            if tip:
                tip_uuid = self.serializer.get_node_uuid(tip)
                if tip_uuid and self.debug.should_break_at_node(
                    tip_uuid, tip, blackboard
                ):
                    # Hit breakpoint
                    self.debug.pause(tip_uuid)
                    self.event_emitter.emit(
                        BreakpointHitEvent(
                            execution_id=self.execution_id,
                            tick=self.tree.count,
                            node_id=tip_uuid,
                            node_name=tip.name,
                            node_status=Status(tip.status.value),
                        )
                    )
                    break

                # Update node status tracking
                if tip_uuid:
                    self.debug.update_node_status(
                        tip_uuid, Status(tip.status.value)
                    )

            # Record snapshot in history after each tick if history enabled
            if self.history:
                snapshot = self.get_snapshot()
                self.history.record_snapshot(snapshot)

        ticks_executed = self.tree.count - initial_count

        # Get tip node
        tip_node_id = None
        tip = self.tree.tip()
        if tip:
            tip_node_id = self.serializer.get_node_uuid(tip)

        # Emit tick complete event
        self.event_emitter.emit(
            TickCompleteEvent(
                execution_id=self.execution_id,
                tick=self.tree.count,
                root_status=Status(self.tree.root.status.value),
                ticks_executed=ticks_executed,
                tip_node_id=tip_node_id,
            )
        )

        return TickResponse(
            execution_id=self.execution_id,
            ticks_executed=ticks_executed,
            new_tick_count=self.tree.count,
            root_status=Status(self.tree.root.status.value),
            snapshot=None,  # Will be filled by caller if requested
        )

    def _get_blackboard_dict(self) -> Dict:
        """Get blackboard as dictionary.

        Returns:
            Dictionary of blackboard values
        """
        bb_dict = {}
        bb = py_trees.blackboard.Blackboard()
        for key in bb.keys():
            try:
                bb_dict[key] = bb.get(key)
            except KeyError:
                pass
        return bb_dict

    def get_snapshot(self) -> ExecutionSnapshot:
        """Capture current state snapshot.

        Returns:
            Complete execution snapshot
        """
        return capture_snapshot(
            execution_id=self.execution_id,
            tree_id=self.tree_def.tree_id,
            tree_version=self.tree_def.metadata.version,
            tree=self.tree,
            serializer=self.serializer,
            mode=self.config.mode.value,
            is_running=self.is_running,
        )

    def get_summary(self) -> ExecutionSummary:
        """Get execution summary.

        Returns:
            Execution summary
        """
        return ExecutionSummary(
            execution_id=self.execution_id,
            tree_id=self.tree_def.tree_id,
            tree_name=self.tree_def.metadata.name,
            tree_version=self.tree_def.metadata.version,
            status=Status(self.tree.root.status.value),
            mode=self.config.mode,
            tick_count=self.tree.count,
            started_at=self.created_at,
            last_tick_at=self.last_tick_at,
            is_running=self.is_running,
        )

    def reload_tree(
        self, new_tree_def: TreeDefinition, preserve_blackboard: bool = True
    ) -> None:
        """Hot-reload with a new tree definition.

        Like a container restart but without container software.
        Cleanly shuts down current tree and starts new one.

        Args:
            new_tree_def: New tree definition to load
            preserve_blackboard: Whether to preserve blackboard state

        Raises:
            ValueError: If tree cannot be deserialized
        """
        old_tree_id = self.tree_def.tree_id
        old_version = self.tree_def.metadata.version

        # Preserve blackboard if requested
        preserved_blackboard = {}
        if preserve_blackboard:
            bb = py_trees.blackboard.Blackboard()
            for key in bb.keys():
                try:
                    preserved_blackboard[key] = bb.get(key)
                except KeyError:
                    pass

        # Shutdown current tree
        try:
            self.tree.shutdown()
        except Exception as e:
            print(f"Warning: Error shutting down tree: {e}")

        # Deserialize new tree
        new_serializer = TreeSerializer()
        new_tree = new_serializer.deserialize(new_tree_def)

        # Restore blackboard if preserved
        if preserved_blackboard:
            bb = py_trees.blackboard.Client(name="Reloader")
            for key, value in preserved_blackboard.items():
                try:
                    bb.register_key(key=key, access=py_trees.common.Access.WRITE)
                    bb.set(key, value, overwrite=True)
                except Exception as e:
                    print(f"Warning: Could not restore blackboard key {key}: {e}")

        # Setup new tree
        new_tree.setup()

        # Update instance
        self.tree_def = new_tree_def
        self.tree = new_tree
        self.serializer = new_serializer

        # Emit tree reloaded event
        self.event_emitter.emit(
            TreeReloadedEvent(
                execution_id=self.execution_id,
                tick=self.tree.count,
                old_tree_id=old_tree_id,
                new_tree_id=new_tree_def.tree_id,
                old_version=old_version,
                new_version=new_tree_def.metadata.version,
                blackboard_preserved=preserve_blackboard,
            )
        )


class ExecutionService:
    """Service for managing tree execution instances.

    Provides:
    - Instance creation from tree library
    - Tick control (manual, auto, interval)
    - State snapshot capture
    - Instance lifecycle management
    - Event emission and history tracking
    """

    def __init__(
        self,
        tree_library: TreeLibrary,
        enable_history: bool = True,
        max_history_snapshots: int = 1000,
    ):
        """Initialize execution service.

        Args:
            tree_library: Tree library for loading definitions
            enable_history: Whether to enable execution history
            max_history_snapshots: Maximum snapshots per execution
        """
        self.library = tree_library
        self.instances: Dict[UUID, ExecutionInstance] = {}

        # History support
        self.enable_history = enable_history
        if enable_history:
            history_store = InMemoryHistoryStore(max_history_snapshots)
            self.history = ExecutionHistory(history_store)
        else:
            self.history = None

        # Scheduler for auto/interval modes
        self.scheduler = ExecutionScheduler()

    def create_execution(self, config: ExecutionConfig) -> UUID:
        """Create a new execution instance.

        Args:
            config: Execution configuration

        Returns:
            Execution ID

        Raises:
            ValueError: If tree not found or invalid
        """
        # Load tree definition
        tree_def = self.library.get_tree(config.tree_id, config.tree_version)

        # Create serializer and deserialize tree
        serializer = TreeSerializer()
        tree = serializer.deserialize(tree_def)

        # Apply initial blackboard values
        if config.initial_blackboard:
            bb = py_trees.blackboard.Client(name="Initializer")
            for key, value in config.initial_blackboard.items():
                bb.register_key(key=key, access=py_trees.common.Access.WRITE)
                bb.set(key, value, overwrite=True)

        # Setup tree
        tree.setup()

        # Create execution instance
        execution_id = uuid4()
        instance = ExecutionInstance(
            execution_id=execution_id,
            tree_def=tree_def,
            tree=tree,
            serializer=serializer,
            config=config,
            event_emitter=EventEmitter(),
            history=self.history,
        )

        # Store instance
        self.instances[execution_id] = instance

        return execution_id

    def get_execution(self, execution_id: UUID) -> ExecutionInstance:
        """Get an execution instance.

        Args:
            execution_id: Execution identifier

        Returns:
            Execution instance

        Raises:
            ValueError: If execution not found
        """
        if execution_id not in self.instances:
            raise ValueError(f"Execution not found: {execution_id}")
        return self.instances[execution_id]

    def list_executions(self) -> List[ExecutionSummary]:
        """List all execution instances.

        Returns:
            List of execution summaries
        """
        return [instance.get_summary() for instance in self.instances.values()]

    def tick_execution(
        self, execution_id: UUID, count: int = 1, capture_snapshot: bool = True
    ) -> TickResponse:
        """Tick an execution instance.

        Args:
            execution_id: Execution identifier
            count: Number of ticks
            capture_snapshot: Whether to capture snapshot after ticking

        Returns:
            Tick response

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)

        # Tick the tree
        response = instance.tick(count)

        # Capture snapshot if requested
        if capture_snapshot:
            response.snapshot = instance.get_snapshot()

        return response

    def get_snapshot(self, execution_id: UUID) -> ExecutionSnapshot:
        """Get current snapshot of an execution.

        Args:
            execution_id: Execution identifier

        Returns:
            Execution snapshot

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        return instance.get_snapshot()

    def reload_tree(
        self,
        execution_id: UUID,
        new_tree_def: TreeDefinition,
        preserve_blackboard: bool = True,
    ) -> None:
        """Hot-reload execution with new tree definition.

        Args:
            execution_id: Execution identifier
            new_tree_def: New tree definition
            preserve_blackboard: Whether to preserve blackboard state

        Raises:
            ValueError: If execution not found or reload fails
        """
        instance = self.get_execution(execution_id)
        instance.reload_tree(new_tree_def, preserve_blackboard)

    async def delete_execution(self, execution_id: UUID) -> bool:
        """Delete an execution instance.

        Args:
            execution_id: Execution identifier

        Returns:
            True if deleted, False if not found
        """
        if execution_id in self.instances:
            # Stop scheduler if running
            await self.scheduler.cleanup(execution_id)

            # Cleanup: shutdown tree
            instance = self.instances[execution_id]
            try:
                instance.tree.shutdown()
            except Exception:
                pass  # Best effort cleanup

            # Clear history if enabled
            if self.history:
                self.history.clear(execution_id)

            del self.instances[execution_id]
            return True
        return False

    def cleanup_stale_executions(self, max_age_hours: int = 24) -> int:
        """Cleanup old execution instances.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of instances cleaned up
        """
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        to_delete = []

        for exec_id, instance in self.instances.items():
            if instance.created_at.timestamp() < cutoff:
                to_delete.append(exec_id)

        for exec_id in to_delete:
            self.delete_execution(exec_id)

        return len(to_delete)

    def get_history(self, execution_id: UUID) -> List[ExecutionSnapshot]:
        """Get execution history.

        Args:
            execution_id: Execution identifier

        Returns:
            List of snapshots

        Raises:
            ValueError: If execution not found or history not enabled
        """
        if not self.history:
            raise ValueError("Execution history is not enabled")

        # Verify execution exists
        self.get_execution(execution_id)

        return self.history.get_all(execution_id)

    def get_history_snapshot(self, execution_id: UUID, tick: int) -> Optional[ExecutionSnapshot]:
        """Get specific historical snapshot.

        Args:
            execution_id: Execution identifier
            tick: Tick number

        Returns:
            Snapshot if found

        Raises:
            ValueError: If history not enabled
        """
        if not self.history:
            raise ValueError("Execution history is not enabled")

        return self.history.get_tick(execution_id, tick)

    def get_history_range(
        self, execution_id: UUID, start_tick: int, end_tick: int
    ) -> List[ExecutionSnapshot]:
        """Get historical snapshots for tick range.

        Args:
            execution_id: Execution identifier
            start_tick: Start tick (inclusive)
            end_tick: End tick (inclusive)

        Returns:
            List of snapshots in range

        Raises:
            ValueError: If history not enabled
        """
        if not self.history:
            raise ValueError("Execution history is not enabled")

        return self.history.get_range(execution_id, start_tick, end_tick)

    async def _async_tick(self, execution_id: UUID) -> TickResponse:
        """Async wrapper for tick (used by scheduler).

        Args:
            execution_id: Execution identifier

        Returns:
            Tick response
        """
        instance = self.get_execution(execution_id)
        return instance.tick(count=1)

    async def start_scheduler(
        self, execution_id: UUID, request: StartSchedulerRequest
    ) -> SchedulerStatus:
        """Start autonomous execution scheduler.

        Args:
            execution_id: Execution identifier
            request: Scheduler start request

        Returns:
            Scheduler status

        Raises:
            ValueError: If execution not found or mode invalid
        """
        # Verify execution exists
        instance = self.get_execution(execution_id)

        # Update execution mode
        instance.config.mode = request.mode
        instance.is_running = True

        # Start scheduler
        return await self.scheduler.start(
            execution_id=execution_id,
            mode=request.mode,
            tick_callback=self._async_tick,
            interval_ms=request.interval_ms,
            max_ticks=request.max_ticks,
            stop_on_terminal=request.stop_on_terminal,
        )

    async def pause_scheduler(self, execution_id: UUID) -> SchedulerStatus:
        """Pause autonomous execution.

        Args:
            execution_id: Execution identifier

        Returns:
            Scheduler status

        Raises:
            ValueError: If execution not found or not running
        """
        return await self.scheduler.pause(execution_id)

    async def resume_scheduler(self, execution_id: UUID) -> SchedulerStatus:
        """Resume paused execution.

        Args:
            execution_id: Execution identifier

        Returns:
            Scheduler status

        Raises:
            ValueError: If execution not found or not paused
        """
        return await self.scheduler.resume(execution_id)

    async def stop_scheduler(self, execution_id: UUID) -> SchedulerStatus:
        """Stop autonomous execution.

        Args:
            execution_id: Execution identifier

        Returns:
            Scheduler status

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        instance.is_running = False

        return await self.scheduler.stop(execution_id)

    def get_scheduler_status(self, execution_id: UUID) -> SchedulerStatus:
        """Get scheduler status.

        Args:
            execution_id: Execution identifier

        Returns:
            Scheduler status

        Raises:
            ValueError: If execution not found
        """
        try:
            return self.scheduler.get_status(execution_id)
        except ValueError:
            # No scheduler context, return idle status
            return SchedulerStatus(
                execution_id=execution_id,
                state="idle",
                ticks_executed=0,
            )

    # Debug control methods

    def add_breakpoint(
        self, execution_id: UUID, node_id: UUID, condition: Optional[str] = None
    ) -> DebugState:
        """Add a breakpoint.

        Args:
            execution_id: Execution identifier
            node_id: Node ID to break on
            condition: Optional Python condition

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        instance.debug.add_breakpoint(node_id, condition)
        return instance.debug.get_state()

    def remove_breakpoint(self, execution_id: UUID, node_id: UUID) -> DebugState:
        """Remove a breakpoint.

        Args:
            execution_id: Execution identifier
            node_id: Node ID

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        instance.debug.remove_breakpoint(node_id)
        return instance.debug.get_state()

    def toggle_breakpoint(self, execution_id: UUID, node_id: UUID) -> DebugState:
        """Toggle breakpoint enabled state.

        Args:
            execution_id: Execution identifier
            node_id: Node ID

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found or breakpoint not found
        """
        instance = self.get_execution(execution_id)
        instance.debug.toggle_breakpoint(node_id)
        return instance.debug.get_state()

    def add_watch(
        self, execution_id: UUID, key: str, condition: str, target_value: Any = None
    ) -> DebugState:
        """Add a watch expression.

        Args:
            execution_id: Execution identifier
            key: Blackboard key
            condition: Watch condition
            target_value: Target value for comparison

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found
        """
        from py_forest.models.debug import WatchCondition

        instance = self.get_execution(execution_id)
        watch_cond = WatchCondition(condition)
        instance.debug.add_watch(key, watch_cond, target_value)
        return instance.debug.get_state()

    def remove_watch(self, execution_id: UUID, key: str) -> DebugState:
        """Remove a watch expression.

        Args:
            execution_id: Execution identifier
            key: Blackboard key

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        instance.debug.remove_watch(key)
        return instance.debug.get_state()

    def toggle_watch(self, execution_id: UUID, key: str) -> DebugState:
        """Toggle watch enabled state.

        Args:
            execution_id: Execution identifier
            key: Blackboard key

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found or watch not found
        """
        instance = self.get_execution(execution_id)
        instance.debug.toggle_watch(key)
        return instance.debug.get_state()

    def set_step_mode(
        self, execution_id: UUID, mode: StepMode, count: int = 1
    ) -> DebugState:
        """Set step execution mode.

        Args:
            execution_id: Execution identifier
            mode: Step mode
            count: Number of steps (for STEP_OVER)

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        instance.debug.set_step_mode(mode, count)
        return instance.debug.get_state()

    def pause_debug(self, execution_id: UUID) -> DebugState:
        """Pause execution (debug).

        Args:
            execution_id: Execution identifier

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        instance.debug.pause()
        return instance.debug.get_state()

    def resume_debug(self, execution_id: UUID) -> DebugState:
        """Resume execution (debug).

        Args:
            execution_id: Execution identifier

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        instance.debug.resume()
        return instance.debug.get_state()

    def get_debug_state(self, execution_id: UUID) -> DebugState:
        """Get debug state.

        Args:
            execution_id: Execution identifier

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        return instance.debug.get_state()

    def clear_debug(self, execution_id: UUID) -> DebugState:
        """Clear all breakpoints and watches.

        Args:
            execution_id: Execution identifier

        Returns:
            Debug state

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        instance.debug.clear_all()
        return instance.debug.get_state()

    # Statistics methods

    def get_statistics(self, execution_id: UUID) -> ExecutionStatistics:
        """Get execution statistics.

        Args:
            execution_id: Execution identifier

        Returns:
            Execution statistics

        Raises:
            ValueError: If execution not found
        """
        instance = self.get_execution(execution_id)
        return instance.statistics.get_statistics()
