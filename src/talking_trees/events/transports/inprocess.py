"""In-process event transport using asyncio queues."""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class InProcessEventTransport:
    """In-process event transport for single-process deployments and testing.

    Uses asyncio queues for event dispatch. No external dependencies.
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._running = False

    def subscribe(self, topic: str, callback: Callable[[str, dict[str, Any]], None]) -> None:
        """Subscribe to a topic.

        Args:
            topic: Topic pattern to subscribe to
            callback: Function called with (topic, event_data)
        """
        self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable) -> None:
        """Unsubscribe from a topic."""
        if topic in self._subscribers:
            self._subscribers[topic] = [
                cb for cb in self._subscribers[topic] if cb != callback
            ]

    def publish(self, topic: str, data: dict[str, Any]) -> None:
        """Publish an event synchronously.

        Args:
            topic: Event topic
            data: Event data dictionary
        """
        # Exact match subscribers
        for callback in self._subscribers.get(topic, []):
            try:
                callback(topic, data)
            except Exception as e:
                logger.error("Event callback error on topic %s: %s", topic, e)

        # Wildcard subscribers (topic pattern matching)
        for pattern, callbacks in self._subscribers.items():
            if pattern != topic and self._matches(pattern, topic):
                for callback in callbacks:
                    try:
                        callback(topic, data)
                    except Exception as e:
                        logger.error("Event callback error on topic %s: %s", topic, e)

    @staticmethod
    def _matches(pattern: str, topic: str) -> bool:
        """Simple wildcard matching. '*' matches any single segment, '#' matches rest."""
        if pattern == "#":
            return True
        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")

        if len(pattern_parts) != len(topic_parts):
            if pattern_parts and pattern_parts[-1] == "#":
                return len(topic_parts) >= len(pattern_parts) - 1
            return False

        return all(
            p == "*" or p == t
            for p, t in zip(pattern_parts, topic_parts)
        )
