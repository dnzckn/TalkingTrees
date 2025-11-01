"""WebSocket connection management for real-time updates."""

import asyncio
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from py_forest.models.events import (
    EventFilter,
    EventType,
    ExecutionEvent,
    WebSocketMessage,
)


class WebSocketConnection:
    """Represents a single WebSocket connection."""

    def __init__(self, websocket: WebSocket, execution_id: UUID, connection_id: str):
        """Initialize WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            execution_id: Execution instance ID
            connection_id: Unique connection identifier
        """
        self.websocket = websocket
        self.execution_id = execution_id
        self.connection_id = connection_id
        self.event_filter: EventFilter = EventFilter()
        self.subscribed_events: set[EventType] = set()
        self.is_active = True

    async def send_event(self, event: ExecutionEvent) -> bool:
        """Send an event to the client.

        Args:
            event: Event to send

        Returns:
            True if sent successfully, False if connection closed
        """
        if not self.is_active:
            return False

        # Check if event passes filter
        if not self._should_send_event(event):
            return True

        try:
            message = WebSocketMessage(
                action="event",
                data=event.model_dump(mode="json"),
            )

            await self.websocket.send_json(message.model_dump(mode="json"))
            return True

        except WebSocketDisconnect:
            self.is_active = False
            return False
        except Exception as e:
            print(f"Error sending event: {e}")
            self.is_active = False
            return False

    async def send_message(self, action: str, data: dict) -> bool:
        """Send a custom message to the client.

        Args:
            action: Message action type
            data: Message data

        Returns:
            True if sent successfully
        """
        if not self.is_active:
            return False

        try:
            message = WebSocketMessage(action=action, data=data)
            await self.websocket.send_json(message.model_dump(mode="json"))
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            self.is_active = False
            return False

    def _should_send_event(self, event: ExecutionEvent) -> bool:
        """Check if event should be sent based on filters.

        Args:
            event: Event to check

        Returns:
            True if event should be sent
        """
        # If specific events are subscribed, check membership
        if self.subscribed_events and event.type not in self.subscribed_events:
            return False

        # Apply event filter
        if self.event_filter.event_types is not None:
            if event.type not in self.event_filter.event_types:
                return False

        if event.tick is not None:
            if (
                self.event_filter.min_tick is not None
                and event.tick < self.event_filter.min_tick
            ):
                return False
            if (
                self.event_filter.max_tick is not None
                and event.tick > self.event_filter.max_tick
            ):
                return False

        return True

    def update_filter(self, event_filter: EventFilter) -> None:
        """Update event filter.

        Args:
            event_filter: New filter configuration
        """
        self.event_filter = event_filter

    def subscribe(self, event_types: list[EventType]) -> None:
        """Subscribe to specific event types.

        Args:
            event_types: Event types to subscribe to
        """
        self.subscribed_events = set(event_types)

    def unsubscribe(self, event_types: list[EventType]) -> None:
        """Unsubscribe from specific event types.

        Args:
            event_types: Event types to unsubscribe from
        """
        self.subscribed_events -= set(event_types)

    def subscribe_all(self) -> None:
        """Subscribe to all event types."""
        self.subscribed_events = set(EventType)

    async def close(self) -> None:
        """Close the WebSocket connection."""
        self.is_active = False
        try:
            await self.websocket.close()
        except Exception:
            pass


class WebSocketManager:
    """Manages WebSocket connections for executions.

    Provides:
    - Connection registration and cleanup
    - Event broadcasting to all connections
    - Per-execution connection management
    - Filtered event delivery
    """

    def __init__(self):
        """Initialize WebSocket manager."""
        # execution_id -> list of connections
        self._connections: dict[UUID, list[WebSocketConnection]] = {}
        self._lock = asyncio.Lock()
        self._connection_counter = 0

    async def connect(
        self, websocket: WebSocket, execution_id: UUID
    ) -> WebSocketConnection:
        """Register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            execution_id: Execution instance ID

        Returns:
            WebSocketConnection instance
        """
        await websocket.accept()

        async with self._lock:
            self._connection_counter += 1
            connection_id = f"{execution_id}_{self._connection_counter}"

            connection = WebSocketConnection(websocket, execution_id, connection_id)

            if execution_id not in self._connections:
                self._connections[execution_id] = []

            self._connections[execution_id].append(connection)

        # Send connection confirmation
        await connection.send_message(
            "connected",
            {
                "execution_id": str(execution_id),
                "connection_id": connection_id,
                "message": "WebSocket connected successfully",
            },
        )

        return connection

    async def disconnect(self, connection: WebSocketConnection) -> None:
        """Disconnect and remove a WebSocket connection.

        Args:
            connection: Connection to remove
        """
        async with self._lock:
            execution_id = connection.execution_id
            if execution_id in self._connections:
                if connection in self._connections[execution_id]:
                    self._connections[execution_id].remove(connection)

                # Cleanup empty connection lists
                if not self._connections[execution_id]:
                    del self._connections[execution_id]

        await connection.close()

    async def broadcast_event(self, execution_id: UUID, event: ExecutionEvent) -> int:
        """Broadcast an event to all connections for an execution.

        Args:
            execution_id: Execution instance ID
            event: Event to broadcast

        Returns:
            Number of connections that received the event
        """
        connections = self._connections.get(execution_id, [])
        if not connections:
            return 0

        sent_count = 0
        disconnected = []

        for connection in connections:
            success = await connection.send_event(event)
            if success:
                sent_count += 1
            else:
                disconnected.append(connection)

        # Cleanup disconnected connections
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if execution_id in self._connections:
                        if conn in self._connections[execution_id]:
                            self._connections[execution_id].remove(conn)

        return sent_count

    async def broadcast_message(
        self, execution_id: UUID, action: str, data: dict
    ) -> int:
        """Broadcast a custom message to all connections.

        Args:
            execution_id: Execution instance ID
            action: Message action
            data: Message data

        Returns:
            Number of connections that received the message
        """
        connections = self._connections.get(execution_id, [])
        if not connections:
            return 0

        sent_count = 0
        for connection in connections:
            success = await connection.send_message(action, data)
            if success:
                sent_count += 1

        return sent_count

    def get_connection_count(self, execution_id: UUID) -> int:
        """Get number of active connections for an execution.

        Args:
            execution_id: Execution instance ID

        Returns:
            Number of active connections
        """
        return len(self._connections.get(execution_id, []))

    def get_total_connections(self) -> int:
        """Get total number of active connections.

        Returns:
            Total connection count
        """
        return sum(len(conns) for conns in self._connections.values())

    async def disconnect_all(self, execution_id: UUID) -> int:
        """Disconnect all connections for an execution.

        Args:
            execution_id: Execution instance ID

        Returns:
            Number of connections disconnected
        """
        async with self._lock:
            connections = self._connections.get(execution_id, [])
            count = len(connections)

            for connection in connections:
                await connection.close()

            if execution_id in self._connections:
                del self._connections[execution_id]

        return count

    async def cleanup_inactive(self) -> int:
        """Remove inactive connections.

        Returns:
            Number of connections cleaned up
        """
        cleaned = 0
        async with self._lock:
            for execution_id in list(self._connections.keys()):
                connections = self._connections[execution_id]
                active = [conn for conn in connections if conn.is_active]
                removed = len(connections) - len(active)

                if removed > 0:
                    self._connections[execution_id] = active
                    cleaned += removed

                # Remove empty lists
                if not self._connections[execution_id]:
                    del self._connections[execution_id]

        return cleaned


# Global WebSocket manager instance
_ws_manager: WebSocketManager | None = None


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance.

    Returns:
        WebSocketManager instance
    """
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager
