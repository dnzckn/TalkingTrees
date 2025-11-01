"""Execution statistics tracking."""

from datetime import datetime
from uuid import UUID

from py_forest.models.execution import Status
from py_forest.models.visualization import ExecutionStatistics, NodeStatistics


class StatisticsTracker:
    """Track execution statistics for behavior trees.

    Monitors:
    - Per-node execution counts and timing
    - Success/failure rates
    - Overall execution metrics
    """

    def __init__(self, execution_id: UUID):
        """Initialize statistics tracker.

        Args:
            execution_id: Execution instance ID
        """
        self.execution_id = execution_id
        self.node_stats: dict[UUID, NodeStatistics] = {}
        self.total_ticks = 0
        self.successful_ticks = 0
        self.failed_ticks = 0
        self.running_ticks = 0
        self.total_time_ms = 0.0
        self.started_at: datetime | None = None
        self.last_tick_at: datetime | None = None

        # Timing tracking
        self._tick_start_time: float | None = None
        self._node_start_times: dict[UUID, float] = {}

    def on_tick_start(self) -> None:
        """Record tick start."""
        now = datetime.utcnow()
        if self.started_at is None:
            self.started_at = now

        # Record tick start time for timing
        import time

        self._tick_start_time = time.perf_counter()

    def on_tick_end(self, root_status: Status) -> None:
        """Record tick end.

        Args:
            root_status: Final status of root node
        """
        import time

        # Calculate tick time
        if self._tick_start_time is not None:
            tick_time_ms = (time.perf_counter() - self._tick_start_time) * 1000
            self.total_time_ms += tick_time_ms
            self._tick_start_time = None

        # Update counts
        self.total_ticks += 1
        self.last_tick_at = datetime.utcnow()

        if root_status == Status.SUCCESS:
            self.successful_ticks += 1
        elif root_status == Status.FAILURE:
            self.failed_ticks += 1
        elif root_status == Status.RUNNING:
            self.running_ticks += 1

    def on_node_tick_start(self, node_id: UUID, node_name: str, node_type: str) -> None:
        """Record node tick start.

        Args:
            node_id: Node UUID
            node_name: Node name
            node_type: Node type
        """
        import time

        # Ensure node stats exist
        if node_id not in self.node_stats:
            self.node_stats[node_id] = NodeStatistics(
                node_id=node_id, node_name=node_name, node_type=node_type
            )

        # Record start time
        self._node_start_times[node_id] = time.perf_counter()

    def on_node_tick_end(self, node_id: UUID, status: Status) -> None:
        """Record node tick end.

        Args:
            node_id: Node UUID
            status: Node status after tick
        """
        import time

        if node_id not in self.node_stats:
            return  # Node not tracked

        stats = self.node_stats[node_id]

        # Calculate execution time
        if node_id in self._node_start_times:
            node_time_ms = (
                time.perf_counter() - self._node_start_times[node_id]
            ) * 1000
            del self._node_start_times[node_id]

            # Update timing stats
            stats.total_time_ms += node_time_ms
            stats.min_time_ms = min(stats.min_time_ms, node_time_ms)
            stats.max_time_ms = max(stats.max_time_ms, node_time_ms)

        # Update counts
        stats.tick_count += 1
        stats.last_tick_at = datetime.utcnow()
        stats.last_status = status.value

        if status == Status.SUCCESS:
            stats.success_count += 1
        elif status == Status.FAILURE:
            stats.failure_count += 1
        elif status == Status.RUNNING:
            stats.running_count += 1

        # Update rates
        if stats.tick_count > 0:
            stats.success_rate = stats.success_count / stats.tick_count
            stats.failure_rate = stats.failure_count / stats.tick_count
            stats.avg_time_ms = stats.total_time_ms / stats.tick_count

    def get_statistics(self) -> ExecutionStatistics:
        """Get current execution statistics.

        Returns:
            Execution statistics
        """
        avg_tick_time = (
            self.total_time_ms / self.total_ticks if self.total_ticks > 0 else 0.0
        )

        return ExecutionStatistics(
            execution_id=self.execution_id,
            total_ticks=self.total_ticks,
            total_time_ms=self.total_time_ms,
            avg_tick_time_ms=avg_tick_time,
            successful_ticks=self.successful_ticks,
            failed_ticks=self.failed_ticks,
            running_ticks=self.running_ticks,
            node_stats={str(k): v for k, v in self.node_stats.items()},
            started_at=self.started_at,
            last_tick_at=self.last_tick_at,
        )

    def reset(self) -> None:
        """Reset all statistics."""
        self.node_stats.clear()
        self.total_ticks = 0
        self.successful_ticks = 0
        self.failed_ticks = 0
        self.running_ticks = 0
        self.total_time_ms = 0.0
        self.started_at = None
        self.last_tick_at = None
        self._tick_start_time = None
        self._node_start_times.clear()
