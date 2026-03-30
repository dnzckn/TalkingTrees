"""Audit collector that implements ObservabilityCollector."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from talking_trees.audit.backends.jsonl import JSONLAuditBackend

logger = logging.getLogger(__name__)


class AuditCollector:
    """Writes all execution events to a persistent audit log.

    Implements the ObservabilityCollector protocol from WP-7.
    """

    def __init__(self, backend: JSONLAuditBackend):
        self.backend = backend

    def _write(self, event_type: str, **kwargs: Any) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **{k: str(v) if isinstance(v, UUID) else v for k, v in kwargs.items()},
        }
        self.backend.write(entry)

    def on_tick(self, execution_id, tree_id, tick_number, duration_ms):
        self._write("tick", execution_id=execution_id, tree_id=tree_id,
                     tick_number=tick_number, duration_ms=round(duration_ms, 4))

    def on_tick_start(self, execution_id, tree_id, tick_number):
        self._write("tick_start", execution_id=execution_id,
                     tree_id=tree_id, tick_number=tick_number)

    def on_tick_end(self, execution_id, tree_id, tick_number, duration_ms):
        self._write("tick_end", execution_id=execution_id, tree_id=tree_id,
                     tick_number=tick_number, duration_ms=round(duration_ms, 4))

    def on_node_result(self, execution_id, node_id, node_type, status, duration_ms):
        self._write("node_result", execution_id=execution_id, node_id=node_id,
                     node_type=node_type, status=status, duration_ms=round(duration_ms, 4))

    def on_cascade_trigger(self, execution_id, source_id, target_id):
        self._write("cascade_trigger", execution_id=execution_id,
                     source_id=source_id, target_id=target_id)

    def on_blackboard_write(self, execution_id, key, value):
        self._write("blackboard_write", execution_id=execution_id,
                     key=key, value=value)

    def on_error(self, execution_id, node_id, error):
        self._write("error", execution_id=execution_id, node_id=node_id,
                     error=str(error), error_type=type(error).__name__)
