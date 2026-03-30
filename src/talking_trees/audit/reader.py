"""Audit log reader for querying and replay."""

from collections.abc import Iterator
from typing import Any

from talking_trees.audit.backends.jsonl import JSONLAuditBackend


class AuditReader:
    """Reads and queries audit log entries.

    Args:
        backend: JSONL audit backend to read from
    """

    def __init__(self, backend: JSONLAuditBackend):
        self.backend = backend

    def filter(
        self,
        execution_id: str | None = None,
        event_type: str | None = None,
        node_id: str | None = None,
        after: str | None = None,
        before: str | None = None,
    ) -> list[dict[str, Any]]:
        """Filter audit entries.

        Args:
            execution_id: Filter by execution ID
            event_type: Filter by event type
            node_id: Filter by node ID
            after: ISO timestamp lower bound
            before: ISO timestamp upper bound
        """
        entries = self.backend.read_all()
        result = []

        for entry in entries:
            if execution_id and entry.get("execution_id") != execution_id:
                continue
            if event_type and entry.get("event_type") != event_type:
                continue
            if node_id and entry.get("node_id") != node_id:
                continue
            if after and entry.get("timestamp", "") < after:
                continue
            if before and entry.get("timestamp", "") > before:
                continue
            result.append(entry)

        return result

    def replay(self, execution_id: str) -> Iterator[dict[str, Any]]:
        """Replay events for an execution in chronological order."""
        entries = self.filter(execution_id=execution_id)
        entries.sort(key=lambda e: e.get("timestamp", ""))
        yield from entries
