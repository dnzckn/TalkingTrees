"""Observability collector system for production monitoring.

Provides a protocol for collecting execution metrics and two built-in
implementations: LogCollector (structured JSON logging) and InMemoryCollector
(for testing and GUI timeline).
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

logger = logging.getLogger(__name__)


@runtime_checkable
class ObservabilityCollector(Protocol):
    """Protocol for execution metrics collection.

    Register collectors on ExecutionInstance to receive metrics.
    Zero overhead when no collector is registered.
    """

    def on_tick(
        self,
        execution_id: UUID,
        tree_id: UUID,
        tick_number: int,
        duration_ms: float,
    ) -> None:
        """Called after each tick with timing data."""
        ...

    def on_node_result(
        self,
        execution_id: UUID,
        node_id: UUID,
        node_type: str,
        status: str,
        duration_ms: float,
    ) -> None:
        """Called with per-node result data."""
        ...

    def on_error(
        self,
        execution_id: UUID,
        node_id: UUID | None,
        error: Exception,
    ) -> None:
        """Called when an error occurs during execution."""
        ...

    def on_tick_start(
        self,
        execution_id: UUID,
        tree_id: UUID,
        tick_number: int,
    ) -> None:
        """Called at the start of a tick."""
        ...

    def on_tick_end(
        self,
        execution_id: UUID,
        tree_id: UUID,
        tick_number: int,
        duration_ms: float,
    ) -> None:
        """Called at the end of a tick with timing."""
        ...

    def on_cascade_trigger(
        self,
        execution_id: UUID,
        source_id: UUID,
        target_id: UUID,
    ) -> None:
        """Called when one node triggers a cascade to another."""
        ...

    def on_blackboard_write(
        self,
        execution_id: UUID,
        key: str,
        value: Any,
    ) -> None:
        """Called when a blackboard key is written."""
        ...


class LogCollector:
    """Structured JSON logging collector using stdlib logging.

    Outputs tick and node metrics as structured JSON log entries.
    """

    def __init__(self, logger_name: str = "talking_trees.observability"):
        self._logger = logging.getLogger(logger_name)

    def on_tick(self, execution_id, tree_id, tick_number, duration_ms):
        self._logger.info(json.dumps({
            "event": "tick",
            "execution_id": str(execution_id),
            "tree_id": str(tree_id),
            "tick": tick_number,
            "duration_ms": round(duration_ms, 4),
        }))

    def on_node_result(self, execution_id, node_id, node_type, status, duration_ms):
        self._logger.info(json.dumps({
            "event": "node_result",
            "execution_id": str(execution_id),
            "node_id": str(node_id),
            "node_type": node_type,
            "status": status,
            "duration_ms": round(duration_ms, 4),
        }))

    def on_error(self, execution_id, node_id, error):
        self._logger.error(json.dumps({
            "event": "error",
            "execution_id": str(execution_id),
            "node_id": str(node_id) if node_id else None,
            "error": str(error),
            "error_type": type(error).__name__,
        }))

    def on_tick_start(self, execution_id, tree_id, tick_number):
        self._logger.info(json.dumps({
            "event": "tick_start",
            "execution_id": str(execution_id),
            "tree_id": str(tree_id),
            "tick": tick_number,
        }))

    def on_tick_end(self, execution_id, tree_id, tick_number, duration_ms):
        self._logger.info(json.dumps({
            "event": "tick_end",
            "execution_id": str(execution_id),
            "tree_id": str(tree_id),
            "tick": tick_number,
            "duration_ms": round(duration_ms, 4),
        }))

    def on_cascade_trigger(self, execution_id, source_id, target_id):
        self._logger.info(json.dumps({
            "event": "cascade_trigger",
            "execution_id": str(execution_id),
            "source_id": str(source_id),
            "target_id": str(target_id),
        }))

    def on_blackboard_write(self, execution_id, key, value):
        self._logger.info(json.dumps({
            "event": "blackboard_write",
            "execution_id": str(execution_id),
            "key": key,
            "value": str(value),
        }))


@dataclass
class TickMetric:
    """Recorded metric for a single tick."""
    tick_number: int
    duration_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class NodeMetric:
    """Aggregate metrics for a single node."""
    node_id: UUID
    node_type: str
    tick_count: int = 0
    total_duration_ms: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    running_count: int = 0
    error_count: int = 0

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.tick_count if self.tick_count > 0 else 0.0


@dataclass
class ExecutionMetrics:
    """Aggregate metrics for an execution."""
    execution_id: UUID
    tree_id: UUID
    total_ticks: int = 0
    total_duration_ms: float = 0.0
    tick_history: list[TickMetric] = field(default_factory=list)
    node_metrics: dict[UUID, NodeMetric] = field(default_factory=dict)
    error_count: int = 0

    @property
    def avg_tick_ms(self) -> float:
        return self.total_duration_ms / self.total_ticks if self.total_ticks > 0 else 0.0

    def summary(self) -> dict[str, Any]:
        """Get a summary dict of metrics."""
        return {
            "execution_id": str(self.execution_id),
            "tree_id": str(self.tree_id),
            "total_ticks": self.total_ticks,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "avg_tick_ms": round(self.avg_tick_ms, 4),
            "error_count": self.error_count,
            "node_count": len(self.node_metrics),
        }


class InMemoryCollector:
    """In-memory collector for testing and GUI timeline.

    Stores all metrics in memory for querying.
    """

    def __init__(self, max_tick_history: int = 10000):
        self._executions: dict[UUID, ExecutionMetrics] = {}
        self._max_history = max_tick_history
        self._cascade_events: list[dict[str, Any]] = []
        self._blackboard_writes: list[dict[str, Any]] = []

    def on_tick(self, execution_id, tree_id, tick_number, duration_ms):
        metrics = self._get_or_create(execution_id, tree_id)
        metrics.total_ticks += 1
        metrics.total_duration_ms += duration_ms

        metrics.tick_history.append(TickMetric(
            tick_number=tick_number,
            duration_ms=duration_ms,
        ))
        # Trim history
        if len(metrics.tick_history) > self._max_history:
            metrics.tick_history = metrics.tick_history[-self._max_history:]

    def on_node_result(self, execution_id, node_id, node_type, status, duration_ms):
        metrics = self._get_or_create(execution_id, None)

        if node_id not in metrics.node_metrics:
            metrics.node_metrics[node_id] = NodeMetric(
                node_id=node_id, node_type=node_type
            )

        nm = metrics.node_metrics[node_id]
        nm.tick_count += 1
        nm.total_duration_ms += duration_ms

        if status == "SUCCESS":
            nm.success_count += 1
        elif status == "FAILURE":
            nm.failure_count += 1
        elif status == "RUNNING":
            nm.running_count += 1

    def on_error(self, execution_id, node_id, error):
        metrics = self._get_or_create(execution_id, None)
        metrics.error_count += 1

        if node_id and node_id in metrics.node_metrics:
            metrics.node_metrics[node_id].error_count += 1

    def on_tick_start(self, execution_id, tree_id, tick_number):
        # Ensure execution metrics exist before tick starts
        self._get_or_create(execution_id, tree_id)

    def on_tick_end(self, execution_id, tree_id, tick_number, duration_ms):
        metrics = self._get_or_create(execution_id, tree_id)
        metrics.total_ticks += 1
        metrics.total_duration_ms += duration_ms
        metrics.tick_history.append(TickMetric(
            tick_number=tick_number,
            duration_ms=duration_ms,
        ))
        if len(metrics.tick_history) > self._max_history:
            metrics.tick_history = metrics.tick_history[-self._max_history:]

    def on_cascade_trigger(self, execution_id, source_id, target_id):
        self._cascade_events.append({
            "execution_id": execution_id,
            "source_id": source_id,
            "target_id": target_id,
            "timestamp": time.time(),
        })

    def on_blackboard_write(self, execution_id, key, value):
        self._blackboard_writes.append({
            "execution_id": execution_id,
            "key": key,
            "value": value,
            "timestamp": time.time(),
        })

    def get_metrics(self, execution_id: UUID) -> ExecutionMetrics | None:
        """Get metrics for an execution."""
        return self._executions.get(execution_id)

    def get_all_summaries(self) -> list[dict[str, Any]]:
        """Get summary of all tracked executions."""
        return [m.summary() for m in self._executions.values()]

    def _get_or_create(self, execution_id, tree_id):
        if execution_id not in self._executions:
            self._executions[execution_id] = ExecutionMetrics(
                execution_id=execution_id,
                tree_id=tree_id or UUID(int=0),
            )
        return self._executions[execution_id]


class CompositeCollector:
    """Composes multiple collectors into one.

    Dispatches events to all registered collectors.
    """

    def __init__(self, collectors: list | None = None):
        self._collectors = collectors or []

    def add(self, collector) -> None:
        """Add a collector."""
        self._collectors.append(collector)

    def remove(self, collector) -> None:
        """Remove a collector."""
        self._collectors.remove(collector)

    def on_tick(self, execution_id, tree_id, tick_number, duration_ms):
        for c in self._collectors:
            c.on_tick(execution_id, tree_id, tick_number, duration_ms)

    def on_node_result(self, execution_id, node_id, node_type, status, duration_ms):
        for c in self._collectors:
            c.on_node_result(execution_id, node_id, node_type, status, duration_ms)

    def on_error(self, execution_id, node_id, error):
        for c in self._collectors:
            c.on_error(execution_id, node_id, error)

    def on_tick_start(self, execution_id, tree_id, tick_number):
        for c in self._collectors:
            c.on_tick_start(execution_id, tree_id, tick_number)

    def on_tick_end(self, execution_id, tree_id, tick_number, duration_ms):
        for c in self._collectors:
            c.on_tick_end(execution_id, tree_id, tick_number, duration_ms)

    def on_cascade_trigger(self, execution_id, source_id, target_id):
        for c in self._collectors:
            c.on_cascade_trigger(execution_id, source_id, target_id)

    def on_blackboard_write(self, execution_id, key, value):
        for c in self._collectors:
            c.on_blackboard_write(execution_id, key, value)
