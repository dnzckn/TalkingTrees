"""Pydantic models for execution state and runtime configuration."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Status(str, Enum):
    """Behavior tree execution status (mirrors py_trees.common.Status)."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"
    INVALID = "INVALID"


class ExecutionMode(str, Enum):
    """Execution mode for tree instances."""

    MANUAL = "manual"  # Step-through via explicit tick commands
    AUTO = "auto"  # Continuous autonomous ticking
    INTERVAL = "interval"  # Tick at specified interval


class SchedulerState(str, Enum):
    """Scheduler execution state."""

    IDLE = "idle"  # Not running
    RUNNING = "running"  # Actively ticking
    PAUSED = "paused"  # Paused (can resume)
    STOPPED = "stopped"  # Stopped (terminal)
    ERROR = "error"  # Error occurred


class NodeState(BaseModel):
    """Runtime state of a single node in the tree."""

    status: Status = Field(description="Current execution status")
    feedback_message: str = Field(
        default="",
        description="Feedback message from the node",
    )
    is_current_child: bool = Field(
        default=False,
        description="Whether this node is the current child of its parent",
    )
    is_tip: bool = Field(
        default=False,
        description="Whether this is the deepest running node",
    )
    tick_count: int = Field(
        default=0,
        description="Number of times this node has been ticked",
    )


class ExecutionConfig(BaseModel):
    """Configuration for a tree execution instance."""

    tree_id: UUID = Field(description="ID of the tree definition to execute")
    tree_version: str | None = Field(
        default=None,
        description="Specific version to execute (latest if not specified)",
    )
    mode: ExecutionMode = Field(
        default=ExecutionMode.MANUAL,
        description="Execution mode",
    )
    initial_blackboard: dict[str, Any] = Field(
        default_factory=dict,
        description="Initial blackboard values",
    )
    tick_interval_ms: int | None = Field(
        default=None,
        description="Tick interval in milliseconds (for interval mode)",
    )
    max_ticks: int | None = Field(
        default=None,
        description="Maximum number of ticks before auto-stop",
    )
    stop_on_terminal: bool = Field(
        default=False,
        description="Stop automatically on SUCCESS or FAILURE",
    )


class ExecutionSnapshot(BaseModel):
    """Complete snapshot of tree execution state at a point in time."""

    execution_id: UUID = Field(
        description="Unique identifier for this execution instance"
    )
    tree_id: UUID = Field(description="ID of the tree definition being executed")
    tree_version: str = Field(description="Version of the tree being executed")
    tick_count: int = Field(description="Total number of ticks executed")
    root_status: Status = Field(description="Status of the root node")
    tip_node_id: UUID | None = Field(
        default=None,
        description="ID of the deepest running node (the 'tip')",
    )
    node_states: dict[str, NodeState] = Field(
        default_factory=dict,
        description="State of each node, keyed by node_id (as string)",
    )
    blackboard: dict[str, Any] = Field(
        default_factory=dict,
        description="Current blackboard values",
    )
    blackboard_metadata: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Blackboard metadata (readers, writers, activity)",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Snapshot timestamp",
    )
    mode: ExecutionMode = Field(description="Current execution mode")
    is_running: bool = Field(description="Whether execution is currently active")
    tree: dict[str, Any] | None = Field(
        default=None,
        description="Tree structure (root node definition)",
    )

    model_config = ConfigDict()


class ExecutionSummary(BaseModel):
    """Summary information about an execution instance."""

    execution_id: UUID = Field(description="Execution instance ID")
    tree_id: UUID = Field(description="Tree definition ID")
    tree_name: str = Field(description="Human-readable tree name")
    tree_version: str = Field(description="Tree version")
    status: Status = Field(description="Current execution status")
    mode: ExecutionMode = Field(description="Execution mode")
    tick_count: int = Field(description="Total ticks executed")
    started_at: datetime = Field(description="Execution start time")
    last_tick_at: datetime | None = Field(
        default=None,
        description="Last tick timestamp",
    )
    is_running: bool = Field(description="Whether actively running")


class TickRequest(BaseModel):
    """Request to tick an execution instance."""

    count: int = Field(
        default=1,
        ge=1,
        description="Number of ticks to execute",
    )
    capture_snapshot: bool = Field(
        default=True,
        description="Whether to return a full snapshot after ticking",
    )
    blackboard_updates: dict[str, Any] = Field(
        default_factory=dict,
        description="Blackboard values to update before ticking (sensor inputs)",
    )


class TickResponse(BaseModel):
    """Response from a tick operation."""

    execution_id: UUID = Field(description="Execution instance ID")
    ticks_executed: int = Field(description="Number of ticks that were executed")
    new_tick_count: int = Field(description="Total tick count after operation")
    root_status: Status = Field(description="Root status after ticking")
    snapshot: ExecutionSnapshot | None = Field(
        default=None,
        description="Full state snapshot (if requested)",
    )


class SchedulerStatus(BaseModel):
    """Status of the execution scheduler."""

    execution_id: UUID = Field(description="Execution instance ID")
    state: SchedulerState = Field(description="Current scheduler state")
    mode: ExecutionMode | None = Field(
        default=None, description="Execution mode (AUTO or INTERVAL)"
    )
    interval_ms: int | None = Field(
        default=None, description="Interval in milliseconds (for INTERVAL mode)"
    )
    ticks_executed: int = Field(
        default=0, description="Total ticks executed by scheduler"
    )
    started_at: datetime | None = Field(
        default=None, description="When scheduler started"
    )
    stopped_at: datetime | None = Field(
        default=None, description="When scheduler stopped"
    )
    error_message: str | None = Field(
        default=None, description="Error message if state is ERROR"
    )


class StartSchedulerRequest(BaseModel):
    """Request to start execution scheduler."""

    mode: ExecutionMode = Field(description="Execution mode (AUTO or INTERVAL)")
    interval_ms: int | None = Field(
        default=100,
        ge=10,
        description="Interval in milliseconds (for INTERVAL mode, min 10ms)",
    )
    max_ticks: int | None = Field(
        default=None, ge=1, description="Maximum ticks before auto-stop"
    )
    stop_on_terminal: bool = Field(
        default=True, description="Stop when tree reaches SUCCESS or FAILURE"
    )
