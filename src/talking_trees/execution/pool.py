"""Multi-instance execution pool for concurrent tree execution."""

import logging
import time
from typing import Any
from uuid import UUID, uuid4

import py_trees

from talking_trees.core.serializer import TreeSerializer
from talking_trees.models.tree import TreeDefinition

logger = logging.getLogger(__name__)


class ExecutionPool:
    """Manages multiple concurrent execution instances of a single tree definition.

    Args:
        tree_def: Tree definition to use for all instances
        max_instances: Maximum concurrent instances (0 = unlimited)
        gc_ttl_seconds: TTL for completed instances before garbage collection
    """

    def __init__(
        self,
        tree_def: TreeDefinition,
        max_instances: int = 1000,
        gc_ttl_seconds: float = 60.0,
    ):
        self.tree_def = tree_def
        self.max_instances = max_instances
        self.gc_ttl_seconds = gc_ttl_seconds
        self._instances: dict[UUID, _PoolInstance] = {}

    def spawn(self, initial_blackboard: dict[str, Any] | None = None) -> UUID:
        """Spawn a new execution instance."""
        if self.max_instances > 0 and self.active_count() >= self.max_instances:
            raise RuntimeError(f"Max instances reached ({self.max_instances})")

        exec_id = uuid4()
        serializer = TreeSerializer()
        py_tree = serializer.deserialize(self.tree_def)

        if initial_blackboard:
            from talking_trees.core.utils import update_blackboard
            update_blackboard(initial_blackboard, client_name=f"Pool:{exec_id}")

        py_tree.setup()
        self._instances[exec_id] = _PoolInstance(exec_id, py_tree, serializer)
        return exec_id

    def tick_all(self) -> dict[UUID, str]:
        """Tick all active instances. Returns {exec_id: status_string}."""
        results = {}
        for exec_id, inst in list(self._instances.items()):
            if inst.completed:
                continue
            try:
                inst.py_tree.tick()
                status = inst.py_tree.root.status
                results[exec_id] = status.value
                if status in (py_trees.common.Status.SUCCESS, py_trees.common.Status.FAILURE):
                    inst.completed = True
                    inst.completed_at = time.monotonic()
            except Exception as e:
                logger.error("Error ticking instance %s: %s", exec_id, e)
                results[exec_id] = "FAILURE"
                inst.completed = True
                inst.completed_at = time.monotonic()
        return results

    def kill(self, execution_id: UUID) -> None:
        """Kill and remove a specific instance."""
        if execution_id in self._instances:
            inst = self._instances.pop(execution_id)
            try:
                inst.py_tree.shutdown()
            except Exception:
                pass

    def kill_all(self) -> int:
        """Kill all instances. Returns count killed."""
        count = len(self._instances)
        for inst in self._instances.values():
            try:
                inst.py_tree.shutdown()
            except Exception:
                pass
        self._instances.clear()
        return count

    def query(self, node_id: str | None = None, status: str | None = None) -> list[UUID]:
        """Query instances by root status."""
        results = []
        for exec_id, inst in self._instances.items():
            if status:
                root_status = inst.py_tree.root.status.value
                if root_status == status:
                    results.append(exec_id)
            elif not inst.completed:
                results.append(exec_id)
        return results

    def active_count(self) -> int:
        return sum(1 for i in self._instances.values() if not i.completed)

    def total_count(self) -> int:
        return len(self._instances)

    def collect_garbage(self) -> int:
        """Remove completed instances past their TTL."""
        now = time.monotonic()
        to_remove = [
            eid for eid, inst in self._instances.items()
            if inst.completed and inst.completed_at and now - inst.completed_at > self.gc_ttl_seconds
        ]
        for eid in to_remove:
            del self._instances[eid]
        return len(to_remove)

    def stats(self) -> dict[str, Any]:
        active = sum(1 for i in self._instances.values() if not i.completed)
        completed = sum(1 for i in self._instances.values() if i.completed)
        return {
            "tree_id": str(self.tree_def.tree_id),
            "max_instances": self.max_instances,
            "total": len(self._instances),
            "active": active,
            "completed": completed,
        }


class _PoolInstance:
    __slots__ = ("execution_id", "py_tree", "serializer", "completed", "completed_at")

    def __init__(self, execution_id, py_tree, serializer):
        self.execution_id = execution_id
        self.py_tree = py_tree
        self.serializer = serializer
        self.completed = False
        self.completed_at: float | None = None
