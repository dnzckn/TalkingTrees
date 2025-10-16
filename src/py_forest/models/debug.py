"""Debugging models for breakpoints, watches, and step execution."""

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field


class StepMode(str, Enum):
    """Step execution modes."""

    NONE = "none"  # Not stepping
    STEP_OVER = "step_over"  # Execute one tick, then pause
    STEP_INTO = "step_into"  # Execute until next node status change
    STEP_OUT = "step_out"  # Execute until parent completes
    CONTINUE = "continue"  # Run until next breakpoint or terminal


class WatchCondition(str, Enum):
    """Watch condition types."""

    CHANGE = "change"  # Break when value changes
    EQUALS = "equals"  # Break when value equals target
    NOT_EQUALS = "not_equals"  # Break when value not equals target
    GREATER = "greater"  # Break when value > target
    LESS = "less"  # Break when value < target
    GREATER_EQUAL = "greater_equal"  # Break when value >= target
    LESS_EQUAL = "less_equal"  # Break when value <= target


class Breakpoint(BaseModel):
    """Breakpoint configuration."""

    node_id: UUID = Field(description="Node ID to break on")
    enabled: bool = Field(default=True, description="Whether breakpoint is active")
    condition: Optional[str] = Field(
        default=None, description="Optional Python expression condition"
    )
    hit_count: int = Field(default=0, description="Number of times hit")


class WatchExpression(BaseModel):
    """Watch expression for blackboard monitoring."""

    key: str = Field(description="Blackboard key to watch")
    condition: WatchCondition = Field(description="Condition type")
    target_value: Optional[Any] = Field(
        default=None, description="Target value for comparison"
    )
    enabled: bool = Field(default=True, description="Whether watch is active")
    hit_count: int = Field(default=0, description="Number of times triggered")


class DebugState(BaseModel):
    """Current debug state."""

    execution_id: UUID = Field(description="Execution instance ID")
    is_paused: bool = Field(description="Whether execution is paused")
    paused_at_node: Optional[UUID] = Field(
        default=None, description="Node where execution is paused"
    )
    step_mode: StepMode = Field(description="Current step mode")
    breakpoints: Dict[str, Breakpoint] = Field(
        default_factory=dict, description="Active breakpoints (node_id -> breakpoint)"
    )
    watches: Dict[str, WatchExpression] = Field(
        default_factory=dict, description="Active watches (key -> watch)"
    )
    breakpoint_hits: int = Field(default=0, description="Total breakpoint hits")
    watch_hits: int = Field(default=0, description="Total watch triggers")


class AddBreakpointRequest(BaseModel):
    """Request to add a breakpoint."""

    node_id: UUID = Field(description="Node ID to break on")
    condition: Optional[str] = Field(
        default=None, description="Optional Python condition"
    )


class AddWatchRequest(BaseModel):
    """Request to add a watch expression."""

    key: str = Field(description="Blackboard key to watch")
    condition: WatchCondition = Field(description="Condition type")
    target_value: Optional[Any] = Field(
        default=None, description="Target value for comparison"
    )


class StepRequest(BaseModel):
    """Request to step execution."""

    mode: StepMode = Field(description="Step mode")
    count: int = Field(default=1, ge=1, description="Number of steps (for STEP_OVER)")
