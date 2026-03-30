"""Event bus for mapping events to tree ticks."""

import logging
import time
from typing import Any

from talking_trees.events.mappings import EventMapping
from talking_trees.events.transports.inprocess import InProcessEventTransport

logger = logging.getLogger(__name__)


class EventBus:
    """Maps incoming events to blackboard writes and tick triggers.

    The event bus connects external event sources (sensors, MQTT, webhooks)
    to the execution engine via configurable mappings.

    Args:
        transport: Event transport backend (default: InProcessEventTransport)
    """

    def __init__(self, transport: InProcessEventTransport | None = None):
        self.transport = transport or InProcessEventTransport()
        self._mappings: list[EventMapping] = []
        self._tick_callbacks: list[Any] = []  # Callable[[str, dict], None]
        self._debounce_timers: dict[str, float] = {}
        self._subscribed_topics: set[str] = set()
        self._running = False

    def register_mapping(self, mapping: EventMapping) -> None:
        """Register an event mapping.

        Args:
            mapping: Event-to-tick mapping configuration
        """
        self._mappings.append(mapping)
        if mapping.topic not in self._subscribed_topics:
            self._subscribed_topics.add(mapping.topic)
            self.transport.subscribe(mapping.topic, self._on_event)

    def register_tick_callback(self, callback) -> None:
        """Register a callback invoked when a tick should be triggered.

        The callback receives (execution_id, blackboard_updates).
        """
        self._tick_callbacks.append(callback)

    def start(self) -> None:
        """Start listening for events."""
        self._running = True
        logger.info("EventBus started with %d mappings", len(self._mappings))

    def stop(self) -> None:
        """Stop listening for events."""
        self._running = False
        logger.info("EventBus stopped")

    def emit(self, topic: str, data: dict[str, Any]) -> None:
        """Manually emit an event (useful for testing).

        Args:
            topic: Event topic
            data: Event data
        """
        self.transport.publish(topic, data)

    def _on_event(self, topic: str, data: dict[str, Any]) -> None:
        """Handle an incoming event."""
        if not self._running:
            return

        for mapping in self._mappings:
            if not self._topic_matches(mapping.topic, topic):
                continue

            # Apply filter
            if mapping.filter and not self._evaluate_filter(mapping.filter, data):
                continue

            # Check debounce
            if mapping.debounce_ms:
                key = f"{mapping.topic}:{mapping.target_execution or 'all'}"
                now = time.monotonic() * 1000
                last = self._debounce_timers.get(key, 0)
                if now - last < mapping.debounce_ms:
                    continue
                self._debounce_timers[key] = now

            # Extract blackboard writes
            bb_updates = {}
            for bb_key, json_path in mapping.blackboard_writes.items():
                value = self._extract_value(data, json_path)
                if value is not None:
                    bb_updates[bb_key] = value

            # Trigger tick
            if mapping.trigger_tick:
                for callback in self._tick_callbacks:
                    try:
                        callback(mapping.target_execution, bb_updates)
                    except Exception as e:
                        logger.error("Tick callback error: %s", e)

    @staticmethod
    def _topic_matches(pattern: str, topic: str) -> bool:
        """Check if topic matches pattern."""
        if pattern == topic:
            return True
        return InProcessEventTransport._matches(pattern, topic)

    @staticmethod
    def _evaluate_filter(filter_expr: str, data: dict) -> bool:
        """Evaluate a simple filter expression against event data."""
        try:
            return bool(eval(filter_expr, {"__builtins__": {}}, data))
        except Exception:
            return False

    @staticmethod
    def _extract_value(data: dict, path: str) -> Any:
        """Extract a value from event data using dot-notation path."""
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def get_mappings(self) -> list[EventMapping]:
        """Get all registered mappings."""
        return list(self._mappings)

    def load_mappings_from_json(self, path: str) -> None:
        """Load event mappings from a JSON file."""
        import json
        with open(path) as f:
            data = json.load(f)
        for entry in data.get("mappings", []):
            self.register_mapping(EventMapping.model_validate(entry))
