"""Execution trace for recording and querying tree execution paths."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionTrace:
    """Record of one complete path through a behavior tree.

    Built during path enumeration by the verifier. Each trace represents
    one possible execution path with specific SUCCESS/FAILURE outcomes
    at each node.
    """

    _visited: list[tuple[str, str, str]] = field(default_factory=list)
    # Each entry: (node_id, node_name, status)
    _blackboard: dict[str, Any] = field(default_factory=dict)

    def record(self, node_id: str, node_name: str, status: str) -> None:
        """Record a node visit."""
        self._visited.append((node_id, node_name, status))

    def set_blackboard(self, key: str, value: Any) -> None:
        """Set a blackboard value in this trace."""
        self._blackboard[key] = value

    def node_reached(self, node_id_or_name: str) -> bool:
        """Check if a node was reached in this trace."""
        return any(
            nid == node_id_or_name or name == node_id_or_name
            for nid, name, _ in self._visited
        )

    def node_returned(self, node_id_or_name: str, status: str) -> bool:
        """Check if a node returned a specific status."""
        return any(
            (nid == node_id_or_name or name == node_id_or_name) and s == status
            for nid, name, s in self._visited
        )

    def blackboard_value(self, key: str) -> Any:
        """Get a blackboard value from this trace."""
        return self._blackboard.get(key)

    def sequence(self) -> list[tuple[str, str]]:
        """Get ordered (node_name, status) pairs."""
        return [(name, status) for _, name, status in self._visited]

    def __repr__(self) -> str:
        steps = " → ".join(f"{name}:{status}" for _, name, status in self._visited)
        return f"Trace({steps})"
