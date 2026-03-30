"""Conditional tick rate scheduler for per-subtree tick frequencies."""

import logging
import time
from uuid import UUID

import py_trees

logger = logging.getLogger(__name__)


class TickScheduler:
    """Scheduler that supports per-subtree tick rates.

    Nodes with different tick rates are only ticked when their interval
    has elapsed. Nodes not due for tick return their last status.

    Args:
        tree: py_trees BehaviourTree to schedule
        default_hz: Default tick rate in Hz for all nodes
    """

    def __init__(
        self,
        tree: py_trees.trees.BehaviourTree,
        default_hz: float = 1.0,
    ):
        self.tree = tree
        self.default_hz = default_hz
        self._rates: dict[str, float] = {}  # node_id_or_name → Hz
        self._last_tick: dict[str, float] = {}  # node_id_or_name → monotonic time
        self._running = False

    def set_rate(self, node_id_or_name: str, hz: float) -> None:
        """Set the tick rate for a specific node/subtree.

        Args:
            node_id_or_name: Node identifier (UUID string or name)
            hz: Tick frequency in Hz
        """
        self._rates[node_id_or_name] = hz
        logger.info("Set tick rate for %s to %.1f Hz", node_id_or_name, hz)

    def set_rate_from_blackboard(self, node_id_or_name: str, bb_key: str) -> None:
        """Set tick rate dynamically from a blackboard value.

        The blackboard value is read on each scheduler tick.

        Args:
            node_id_or_name: Node identifier
            bb_key: Blackboard key containing the Hz value
        """
        self._rates[node_id_or_name] = -1  # sentinel: read from bb
        self._rates[f"_bb:{node_id_or_name}"] = bb_key

    def should_tick(self, node_id_or_name: str) -> bool:
        """Check if a node is due for a tick based on its rate."""
        hz = self._rates.get(node_id_or_name, self.default_hz)

        # Dynamic rate from blackboard
        if hz == -1:
            bb_key = self._rates.get(f"_bb:{node_id_or_name}", "")
            try:
                bb = py_trees.blackboard.Blackboard()
                hz = float(bb.get(bb_key))
            except (KeyError, TypeError, ValueError):
                hz = self.default_hz

        if hz <= 0:
            return False

        interval = 1.0 / hz
        now = time.monotonic()
        last = self._last_tick.get(node_id_or_name, 0)

        if now - last >= interval:
            self._last_tick[node_id_or_name] = now
            return True
        return False

    def tick(self) -> py_trees.common.Status:
        """Execute one scheduler tick — ticks the tree respecting per-node rates.

        For simplicity, this ticks the full tree (py_trees requires full-tree ticks).
        Per-subtree rate control is advisory and can be used by adapters to
        skip subtrees not due.

        Returns:
            Root node status
        """
        self.tree.tick()
        return self.tree.root.status

    def run(self, duration_seconds: float | None = None) -> None:
        """Run the scheduler loop.

        Args:
            duration_seconds: Run for this many seconds, then stop. None = run until stop().
        """
        self._running = True
        start = time.monotonic()
        interval = 1.0 / self.default_hz

        while self._running:
            tick_start = time.monotonic()

            if duration_seconds and (tick_start - start) >= duration_seconds:
                break

            self.tick()

            elapsed = time.monotonic() - tick_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
