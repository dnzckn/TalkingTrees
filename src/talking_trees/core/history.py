"""Execution history storage and management."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from uuid import UUID

from talking_trees.models.execution import ExecutionSnapshot


class HistoryStore(ABC):
    """Abstract base class for execution history storage."""

    @abstractmethod
    def add_snapshot(self, execution_id: UUID, snapshot: ExecutionSnapshot) -> None:
        """Add a snapshot to history.

        Args:
            execution_id: Execution instance ID
            snapshot: Execution snapshot
        """
        pass

    @abstractmethod
    def get_snapshot(self, execution_id: UUID, tick: int) -> ExecutionSnapshot | None:
        """Get snapshot for a specific tick.

        Args:
            execution_id: Execution instance ID
            tick: Tick number

        Returns:
            Snapshot if found, None otherwise
        """
        pass

    @abstractmethod
    def get_range(
        self, execution_id: UUID, start_tick: int, end_tick: int
    ) -> list[ExecutionSnapshot]:
        """Get snapshots for a tick range.

        Args:
            execution_id: Execution instance ID
            start_tick: Start tick (inclusive)
            end_tick: End tick (inclusive)

        Returns:
            List of snapshots in range
        """
        pass

    @abstractmethod
    def get_all(self, execution_id: UUID) -> list[ExecutionSnapshot]:
        """Get all snapshots for an execution.

        Args:
            execution_id: Execution instance ID

        Returns:
            List of all snapshots
        """
        pass

    @abstractmethod
    def get_latest(self, execution_id: UUID) -> ExecutionSnapshot | None:
        """Get the latest snapshot.

        Args:
            execution_id: Execution instance ID

        Returns:
            Latest snapshot if exists, None otherwise
        """
        pass

    @abstractmethod
    def clear(self, execution_id: UUID) -> int:
        """Clear history for an execution.

        Args:
            execution_id: Execution instance ID

        Returns:
            Number of snapshots cleared
        """
        pass

    @abstractmethod
    def count(self, execution_id: UUID) -> int:
        """Count snapshots for an execution.

        Args:
            execution_id: Execution instance ID

        Returns:
            Number of snapshots
        """
        pass


class InMemoryHistoryStore(HistoryStore):
    """In-memory implementation of history storage.

    Features:
    - Fast access
    - Configurable max snapshots per execution
    - Automatic cleanup of old snapshots
    - LRU eviction when limit reached
    """

    def __init__(self, max_snapshots_per_execution: int = 1000):
        """Initialize in-memory history store.

        Args:
            max_snapshots_per_execution: Maximum snapshots to keep per execution
        """
        self.max_snapshots = max_snapshots_per_execution
        # execution_id -> tick -> snapshot
        self._history: dict[UUID, dict[int, ExecutionSnapshot]] = {}

    def add_snapshot(self, execution_id: UUID, snapshot: ExecutionSnapshot) -> None:
        """Add a snapshot to history."""
        if execution_id not in self._history:
            self._history[execution_id] = {}

        history = self._history[execution_id]
        history[snapshot.tick_count] = snapshot

        # Enforce max snapshots limit (FIFO eviction)
        if len(history) > self.max_snapshots:
            # Remove oldest tick
            oldest_tick = min(history.keys())
            del history[oldest_tick]

    def get_snapshot(self, execution_id: UUID, tick: int) -> ExecutionSnapshot | None:
        """Get snapshot for a specific tick."""
        history = self._history.get(execution_id, {})
        return history.get(tick)

    def get_range(
        self, execution_id: UUID, start_tick: int, end_tick: int
    ) -> list[ExecutionSnapshot]:
        """Get snapshots for a tick range."""
        history = self._history.get(execution_id, {})
        snapshots = []

        for tick in range(start_tick, end_tick + 1):
            if tick in history:
                snapshots.append(history[tick])

        return snapshots

    def get_all(self, execution_id: UUID) -> list[ExecutionSnapshot]:
        """Get all snapshots for an execution."""
        history = self._history.get(execution_id, {})
        # Sort by tick count
        return [history[tick] for tick in sorted(history.keys())]

    def get_latest(self, execution_id: UUID) -> ExecutionSnapshot | None:
        """Get the latest snapshot."""
        history = self._history.get(execution_id, {})
        if not history:
            return None

        latest_tick = max(history.keys())
        return history[latest_tick]

    def clear(self, execution_id: UUID) -> int:
        """Clear history for an execution."""
        if execution_id not in self._history:
            return 0

        count = len(self._history[execution_id])
        del self._history[execution_id]
        return count

    def count(self, execution_id: UUID) -> int:
        """Count snapshots for an execution."""
        return len(self._history.get(execution_id, {}))

    def cleanup_old_executions(self, max_age_hours: int = 24) -> int:
        """Cleanup history for old executions.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of executions cleaned up
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_delete = []

        for execution_id, history in self._history.items():
            if not history:
                to_delete.append(execution_id)
                continue

            # Check latest snapshot timestamp
            latest_tick = max(history.keys())
            latest_snapshot = history[latest_tick]

            if latest_snapshot.timestamp < cutoff:
                to_delete.append(execution_id)

        for execution_id in to_delete:
            del self._history[execution_id]

        return len(to_delete)

    def get_memory_usage(self) -> dict[str, int]:
        """Get memory usage statistics.

        Returns:
            Dictionary with usage stats
        """
        total_snapshots = sum(len(h) for h in self._history.values())
        total_executions = len(self._history)

        return {
            "total_executions": total_executions,
            "total_snapshots": total_snapshots,
            "max_snapshots_per_execution": self.max_snapshots,
        }


class ExecutionHistory:
    """Execution history manager.

    Provides high-level interface for execution history operations.
    """

    def __init__(self, store: HistoryStore):
        """Initialize execution history.

        Args:
            store: History storage backend
        """
        self.store = store

    def record_snapshot(self, snapshot: ExecutionSnapshot) -> None:
        """Record a snapshot.

        Args:
            snapshot: Execution snapshot
        """
        self.store.add_snapshot(snapshot.execution_id, snapshot)

    def get_tick(self, execution_id: UUID, tick: int) -> ExecutionSnapshot | None:
        """Get snapshot for specific tick.

        Args:
            execution_id: Execution instance ID
            tick: Tick number

        Returns:
            Snapshot if found
        """
        return self.store.get_snapshot(execution_id, tick)

    def get_range(
        self, execution_id: UUID, start_tick: int, end_tick: int
    ) -> list[ExecutionSnapshot]:
        """Get snapshots for tick range.

        Args:
            execution_id: Execution instance ID
            start_tick: Start tick (inclusive)
            end_tick: End tick (inclusive)

        Returns:
            List of snapshots
        """
        return self.store.get_range(execution_id, start_tick, end_tick)

    def get_all(self, execution_id: UUID) -> list[ExecutionSnapshot]:
        """Get all history snapshots.

        Args:
            execution_id: Execution instance ID

        Returns:
            List of all snapshots, ordered by tick
        """
        return self.store.get_all(execution_id)

    def get_latest(self, execution_id: UUID) -> ExecutionSnapshot | None:
        """Get latest snapshot.

        Args:
            execution_id: Execution instance ID

        Returns:
            Latest snapshot
        """
        return self.store.get_latest(execution_id)

    def get_changes(
        self, execution_id: UUID, from_tick: int, to_tick: int
    ) -> dict[str, list[str]]:
        """Get changes between two ticks.

        Args:
            execution_id: Execution instance ID
            from_tick: Starting tick
            to_tick: Ending tick

        Returns:
            Dictionary of changes
        """
        from_snapshot = self.store.get_snapshot(execution_id, from_tick)
        to_snapshot = self.store.get_snapshot(execution_id, to_tick)

        if not from_snapshot or not to_snapshot:
            return {}

        changes = {
            "status_changes": [],
            "blackboard_changes": [],
            "node_changes": [],
        }

        # Compare root status
        if from_snapshot.root_status != to_snapshot.root_status:
            changes["status_changes"].append(
                f"Root: {from_snapshot.root_status} → {to_snapshot.root_status}"
            )

        # Compare blackboard
        for key, value in to_snapshot.blackboard.items():
            old_value = from_snapshot.blackboard.get(key)
            if old_value != value:
                changes["blackboard_changes"].append(f"{key}: {old_value} → {value}")

        # Compare node states
        for node_id, state in to_snapshot.node_states.items():
            old_state = from_snapshot.node_states.get(node_id)
            if old_state and old_state.status != state.status:
                changes["node_changes"].append(
                    f"{node_id}: {old_state.status} → {state.status}"
                )

        return changes

    def clear(self, execution_id: UUID) -> int:
        """Clear history for execution.

        Args:
            execution_id: Execution instance ID

        Returns:
            Number of snapshots cleared
        """
        return self.store.clear(execution_id)

    def count(self, execution_id: UUID) -> int:
        """Count snapshots for execution.

        Args:
            execution_id: Execution instance ID

        Returns:
            Number of snapshots
        """
        return self.store.count(execution_id)
