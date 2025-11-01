"""WebSocket endpoint for real-time execution monitoring."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from talking_trees.api.dependencies import execution_service_dependency
from talking_trees.core.execution import ExecutionService
from talking_trees.core.websocket import get_websocket_manager
from talking_trees.models.events import EventFilter, EventType

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/executions/{execution_id}")
async def execution_websocket(
    websocket: WebSocket,
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
):
    """WebSocket endpoint for real-time execution updates.

    Args:
        websocket: WebSocket connection
        execution_id: Execution instance ID
        service: Execution service

    Usage:
        Connect: ws://localhost:8000/ws/executions/{execution_id}

        Send commands:
        {"action": "subscribe", "events": ["tick_complete", "node_update"]}
        {"action": "unsubscribe", "events": ["tick_complete"]}
        {"action": "subscribe_all"}
        {"action": "ping"}

        Receive events:
        {"action": "event", "data": {...event data...}, "timestamp": "..."}
        {"action": "connected", "data": {...}, "timestamp": "..."}
        {"action": "pong", "data": {}, "timestamp": "..."}
    """
    ws_manager = get_websocket_manager()

    # Verify execution exists
    try:
        instance = service.get_execution(execution_id)
    except ValueError as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
        return

    # Connect WebSocket
    connection = await ws_manager.connect(websocket, execution_id)

    # Subscribe to execution events
    async def on_event(event):
        await connection.send_event(event)

    instance.event_emitter.on_any_async(on_event)

    try:
        # Handle incoming messages
        while connection.is_active:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                action = message.get("action", "")

                if action == "subscribe":
                    # Subscribe to specific events
                    event_types = message.get("events", [])
                    event_enums = [EventType(t) for t in event_types]
                    connection.subscribe(event_enums)
                    await connection.send_message("subscribed", {"events": event_types})

                elif action == "unsubscribe":
                    # Unsubscribe from events
                    event_types = message.get("events", [])
                    event_enums = [EventType(t) for t in event_types]
                    connection.unsubscribe(event_enums)
                    await connection.send_message(
                        "unsubscribed", {"events": event_types}
                    )

                elif action == "subscribe_all":
                    # Subscribe to all events
                    connection.subscribe_all()
                    await connection.send_message("subscribed", {"events": "all"})

                elif action == "filter":
                    # Update filter
                    filter_data = message.get("filter", {})
                    event_filter = EventFilter(**filter_data)
                    connection.update_filter(event_filter)
                    await connection.send_message("filter_updated", filter_data)

                elif action == "ping":
                    # Respond to ping
                    await connection.send_message("pong", {})

            except WebSocketDisconnect:
                break
            except Exception as e:
                await connection.send_message("error", {"message": str(e)})

    finally:
        # Cleanup
        instance.event_emitter.off_any_async(on_event)
        await ws_manager.disconnect(connection)
