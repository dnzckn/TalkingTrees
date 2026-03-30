"""Event mapping models for event-to-tick configuration."""

from typing import Any

from pydantic import BaseModel, Field


class EventMapping(BaseModel):
    """Maps an event topic to blackboard writes and tick triggers."""

    topic: str = Field(description="Event topic/channel pattern")
    blackboard_writes: dict[str, str] = Field(
        default_factory=dict,
        description="Blackboard writes: {bb_key: json_path_into_event}",
    )
    trigger_tick: bool = Field(
        default=True,
        description="Whether to trigger a tick after applying writes",
    )
    target_execution: str | None = Field(
        default=None,
        description="Specific execution ID, or None for broadcast",
    )
    target_subtree: str | None = Field(
        default=None,
        description="Only tick this subtree (node ID or name)",
    )
    filter: str | None = Field(
        default=None,
        description="Simple expression to filter events (e.g., 'value > 0.5')",
    )
    debounce_ms: int | None = Field(
        default=None,
        description="Debounce window in milliseconds",
    )
