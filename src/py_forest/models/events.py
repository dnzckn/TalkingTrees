"""Event models for real-time execution monitoring."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from py_forest.models.execution import Status


class EventType(str, Enum):
    """Types of events emitted during execution."""

    # Execution lifecycle
    EXECUTION_STARTED = "execution_started"
    EXECUTION_STOPPED = "execution_stopped"
    EXECUTION_PAUSED = "execution_paused"
    EXECUTION_RESUMED = "execution_resumed"
    EXECUTION_COMPLETED = "execution_completed"
    TREE_RELOADED = "tree_reloaded"

    # Tick events
    TICK_START = "tick_start"
    TICK_COMPLETE = "tick_complete"

    # Node events
    NODE_INITIALISED = "node_initialised"
    NODE_UPDATED = "node_updated"
    NODE_TERMINATED = "node_terminated"

    # Blackboard events
    BLACKBOARD_UPDATE = "blackboard_update"
    BLACKBOARD_ACCESS = "blackboard_access"

    # Debug events
    BREAKPOINT_HIT = "breakpoint_hit"
    WATCH_TRIGGERED = "watch_triggered"

    # Error events
    EXECUTION_ERROR = "execution_error"


class ExecutionEvent(BaseModel):
    """Base event emitted during execution."""

    type: EventType = Field(description="Event type")
    execution_id: UUID = Field(description="Execution instance ID")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    tick: Optional[int] = Field(default=None, description="Tick number when event occurred")


class TickStartEvent(ExecutionEvent):
    """Event emitted at the start of a tick."""

    type: EventType = Field(default=EventType.TICK_START)
    count: int = Field(description="Number of ticks requested")


class TickCompleteEvent(ExecutionEvent):
    """Event emitted when a tick completes."""

    type: EventType = Field(default=EventType.TICK_COMPLETE)
    root_status: Status = Field(description="Root status after tick")
    ticks_executed: int = Field(description="Number of ticks executed")
    tip_node_id: Optional[UUID] = Field(default=None, description="Current tip node")
    changes: Dict[str, Any] = Field(
        default_factory=dict, description="State changes during tick"
    )


class NodeUpdateEvent(ExecutionEvent):
    """Event emitted when a node's status changes."""

    type: EventType = Field(default=EventType.NODE_UPDATED)
    node_id: UUID = Field(description="Node ID")
    node_name: str = Field(description="Node name")
    old_status: Optional[Status] = Field(default=None, description="Previous status")
    new_status: Status = Field(description="New status")
    feedback: str = Field(default="", description="Feedback message")


class BlackboardUpdateEvent(ExecutionEvent):
    """Event emitted when blackboard value changes."""

    type: EventType = Field(default=EventType.BLACKBOARD_UPDATE)
    key: str = Field(description="Blackboard key")
    old_value: Optional[Any] = Field(default=None, description="Previous value")
    new_value: Any = Field(description="New value")
    writer: Optional[str] = Field(default=None, description="Node that wrote the value")


class BreakpointHitEvent(ExecutionEvent):
    """Event emitted when a breakpoint is hit."""

    type: EventType = Field(default=EventType.BREAKPOINT_HIT)
    node_id: UUID = Field(description="Node ID where breakpoint hit")
    node_name: str = Field(description="Node name")
    node_status: Status = Field(description="Node status")


class WatchTriggeredEvent(ExecutionEvent):
    """Event emitted when a watch condition is met."""

    type: EventType = Field(default=EventType.WATCH_TRIGGERED)
    key: str = Field(description="Watched blackboard key")
    condition: str = Field(description="Watch condition")
    value: Any = Field(description="Current value")


class ExecutionErrorEvent(ExecutionEvent):
    """Event emitted when an error occurs during execution."""

    type: EventType = Field(default=EventType.EXECUTION_ERROR)
    error_type: str = Field(description="Error type")
    error_message: str = Field(description="Error message")
    node_id: Optional[UUID] = Field(default=None, description="Node where error occurred")


class TreeReloadedEvent(ExecutionEvent):
    """Event emitted when tree is hot-reloaded."""

    type: EventType = Field(default=EventType.TREE_RELOADED)
    old_tree_id: UUID = Field(description="Previous tree definition ID")
    new_tree_id: UUID = Field(description="New tree definition ID")
    old_version: str = Field(description="Previous tree version")
    new_version: str = Field(description="New tree version")
    blackboard_preserved: bool = Field(description="Whether blackboard state was preserved")


class EventFilter(BaseModel):
    """Filter for event subscriptions."""

    event_types: Optional[list[EventType]] = Field(
        default=None, description="Event types to include (None = all)"
    )
    node_ids: Optional[list[UUID]] = Field(
        default=None, description="Node IDs to filter by (None = all)"
    )
    blackboard_keys: Optional[list[str]] = Field(
        default=None, description="Blackboard keys to filter by (None = all)"
    )
    min_tick: Optional[int] = Field(default=None, description="Minimum tick number")
    max_tick: Optional[int] = Field(default=None, description="Maximum tick number")


class WebSocketMessage(BaseModel):
    """Message sent over WebSocket."""

    action: str = Field(description="Action type: event, subscribe, unsubscribe, error")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Message timestamp"
    )
