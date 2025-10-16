"""Event emitter system for execution monitoring."""

import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from py_forest.models.events import EventFilter, EventType, ExecutionEvent


class EventEmitter:
    """Event emitter for execution events.

    Supports synchronous and asynchronous listeners.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        """Initialize the event emitter."""
        self._listeners: Dict[EventType, List[Callable]] = defaultdict(list)
        self._async_listeners: Dict[EventType, List[Callable]] = defaultdict(list)
        self._wildcard_listeners: List[Callable] = []
        self._async_wildcard_listeners: List[Callable] = []
        self._lock = asyncio.Lock()

    def on(self, event_type: EventType, callback: Callable[[ExecutionEvent], None]) -> None:
        """Register a synchronous event listener.

        Args:
            event_type: Type of event to listen for
            callback: Function to call when event is emitted
        """
        self._listeners[event_type].append(callback)

    def on_async(
        self, event_type: EventType, callback: Callable[[ExecutionEvent], Any]
    ) -> None:
        """Register an asynchronous event listener.

        Args:
            event_type: Type of event to listen for
            callback: Async function to call when event is emitted
        """
        self._async_listeners[event_type].append(callback)

    def on_any(self, callback: Callable[[ExecutionEvent], None]) -> None:
        """Register a wildcard listener that receives all events.

        Args:
            callback: Function to call for any event
        """
        self._wildcard_listeners.append(callback)

    def on_any_async(self, callback: Callable[[ExecutionEvent], Any]) -> None:
        """Register an async wildcard listener that receives all events.

        Args:
            callback: Async function to call for any event
        """
        self._async_wildcard_listeners.append(callback)

    def off(self, event_type: EventType, callback: Callable) -> None:
        """Unregister an event listener.

        Args:
            event_type: Type of event
            callback: Callback to remove
        """
        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)
        if callback in self._async_listeners[event_type]:
            self._async_listeners[event_type].remove(callback)

    def off_any(self, callback: Callable) -> None:
        """Unregister a wildcard listener.

        Args:
            callback: Callback to remove
        """
        if callback in self._wildcard_listeners:
            self._wildcard_listeners.remove(callback)
        if callback in self._async_wildcard_listeners:
            self._async_wildcard_listeners.remove(callback)

    def emit(self, event: ExecutionEvent) -> None:
        """Emit an event synchronously.

        Args:
            event: Event to emit
        """
        # Call type-specific listeners
        for callback in self._listeners[event.type]:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in event listener: {e}")

        # Call wildcard listeners
        for callback in self._wildcard_listeners:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in wildcard listener: {e}")

    async def emit_async(self, event: ExecutionEvent) -> None:
        """Emit an event asynchronously.

        Calls both sync and async listeners.

        Args:
            event: Event to emit
        """
        # Call sync listeners
        self.emit(event)

        # Call async listeners
        tasks = []

        for callback in self._async_listeners[event.type]:
            tasks.append(asyncio.create_task(self._safe_call_async(callback, event)))

        for callback in self._async_wildcard_listeners:
            tasks.append(asyncio.create_task(self._safe_call_async(callback, event)))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_call_async(self, callback: Callable, event: ExecutionEvent) -> None:
        """Safely call an async callback with error handling.

        Args:
            callback: Async callback to call
            event: Event to pass to callback
        """
        try:
            await callback(event)
        except Exception as e:
            print(f"Error in async event listener: {e}")

    def clear(self) -> None:
        """Clear all listeners."""
        self._listeners.clear()
        self._async_listeners.clear()
        self._wildcard_listeners.clear()
        self._async_wildcard_listeners.clear()

    def listener_count(self, event_type: Optional[EventType] = None) -> int:
        """Get count of registered listeners.

        Args:
            event_type: Specific event type, or None for total

        Returns:
            Number of listeners
        """
        if event_type:
            return len(self._listeners[event_type]) + len(
                self._async_listeners[event_type]
            )
        else:
            total = len(self._wildcard_listeners) + len(self._async_wildcard_listeners)
            for listeners in self._listeners.values():
                total += len(listeners)
            for listeners in self._async_listeners.values():
                total += len(listeners)
            return total


class FilteredEventEmitter:
    """Event emitter with filtering support."""

    def __init__(self, emitter: EventEmitter, event_filter: EventFilter):
        """Initialize filtered event emitter.

        Args:
            emitter: Base event emitter
            event_filter: Filter criteria
        """
        self.emitter = emitter
        self.filter = event_filter

    def should_emit(self, event: ExecutionEvent) -> bool:
        """Check if event matches filter.

        Args:
            event: Event to check

        Returns:
            True if event passes filter
        """
        # Check event type
        if self.filter.event_types is not None:
            if event.type not in self.filter.event_types:
                return False

        # Check tick range
        if event.tick is not None:
            if self.filter.min_tick is not None and event.tick < self.filter.min_tick:
                return False
            if self.filter.max_tick is not None and event.tick > self.filter.max_tick:
                return False

        # Check node IDs (if event has node_id)
        if self.filter.node_ids is not None:
            node_id = getattr(event, "node_id", None)
            if node_id is not None and node_id not in self.filter.node_ids:
                return False

        # Check blackboard keys (if event has key)
        if self.filter.blackboard_keys is not None:
            key = getattr(event, "key", None)
            if key is not None and key not in self.filter.blackboard_keys:
                return False

        return True

    def on(self, event_type: EventType, callback: Callable[[ExecutionEvent], None]) -> None:
        """Register filtered listener."""

        def filtered_callback(event: ExecutionEvent) -> None:
            if self.should_emit(event):
                callback(event)

        self.emitter.on(event_type, filtered_callback)

    def on_async(
        self, event_type: EventType, callback: Callable[[ExecutionEvent], Any]
    ) -> None:
        """Register filtered async listener."""

        async def filtered_callback(event: ExecutionEvent) -> None:
            if self.should_emit(event):
                await callback(event)

        self.emitter.on_async(event_type, filtered_callback)
