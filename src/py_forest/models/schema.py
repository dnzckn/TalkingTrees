"""Pydantic models for behavior schemas (editor support)."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NodeCategory(str, Enum):
    """Category classification for behaviors."""

    COMPOSITE = "composite"  # Sequence, Selector, Parallel
    DECORATOR = "decorator"  # Inverter, Retry, Timeout, etc.
    CONDITION = "condition"  # Checks that return SUCCESS/FAILURE
    ACTION = "action"  # Actions that do work
    CUSTOM = "custom"  # User-defined behaviors


class WidgetType(str, Enum):
    """UI widget types for configuration parameters."""

    TEXT = "text"
    NUMBER = "number"
    SLIDER = "slider"
    CHECKBOX = "checkbox"
    SELECT = "select"
    MULTISELECT = "multiselect"
    COLOR = "color"
    TEXTAREA = "textarea"


class ConfigPropertySchema(BaseModel):
    """Schema for a single configuration property."""

    type: str = Field(
        description="JSON schema type (string, number, boolean, array, object)"
    )
    default: Any | None = Field(
        default=None,
        description="Default value",
    )
    description: str | None = Field(
        default=None,
        description="Human-readable description",
    )
    minimum: float | None = Field(
        default=None,
        description="Minimum value (for numbers)",
    )
    maximum: float | None = Field(
        default=None,
        description="Maximum value (for numbers)",
    )
    enum: list[Any] | None = Field(
        default=None,
        description="Allowed values (for enums)",
    )
    items: dict[str, Any] | None = Field(
        default=None,
        description="Array item schema",
    )
    properties: dict[str, "ConfigPropertySchema"] | None = Field(
        default=None,
        description="Object property schemas",
    )
    required: list[str] | None = Field(
        default=None,
        description="Required properties (for objects)",
    )
    ui_hints: dict[str, Any] | None = Field(
        default=None,
        description="UI rendering hints (widget type, formatting, etc.)",
    )


class ChildConstraints(BaseModel):
    """Constraints on children for a behavior node."""

    min_children: int = Field(
        default=0,
        ge=0,
        description="Minimum number of children",
    )
    max_children: int | None = Field(
        default=None,
        ge=0,
        description="Maximum number of children (None = unlimited)",
    )
    allowed_types: list[str] | None = Field(
        default=None,
        description="Allowed child node types (None = any type)",
    )


class BlackboardAccess(BaseModel):
    """Blackboard variable access specification."""

    reads: list[str] = Field(
        default_factory=list,
        description="Blackboard keys this behavior reads",
    )
    writes: list[str] = Field(
        default_factory=list,
        description="Blackboard keys this behavior writes",
    )


class StatusBehavior(BaseModel):
    """Information about status return behavior."""

    returns: list[str] = Field(
        description="Possible return statuses (SUCCESS, FAILURE, RUNNING)"
    )
    description: str | None = Field(
        default=None,
        description="Explanation of when each status is returned",
    )


class BehaviorExample(BaseModel):
    """Example usage of a behavior."""

    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Example configuration",
    )
    scenario: str | None = Field(
        default=None,
        description="Scenario description",
    )
    expected_status: str | None = Field(
        default=None,
        description="Expected return status",
    )


class BehaviorSchema(BaseModel):
    """Complete schema for a behavior type.

    Used by visual editors to:
    - Display available behaviors in a palette
    - Validate configuration parameters
    - Show appropriate UI widgets
    - Enforce child constraints
    """

    node_type: str = Field(description="Unique identifier for this behavior type")
    category: NodeCategory = Field(description="Behavior category")
    display_name: str = Field(description="Human-readable name")
    description: str | None = Field(
        default=None,
        description="Detailed description of behavior",
    )
    icon: str | None = Field(
        default=None,
        description="Icon identifier",
    )
    color: str | None = Field(
        default=None,
        description="Color in hex format",
    )
    documentation_url: str | None = Field(
        default=None,
        description="Link to full documentation",
    )
    config_schema: dict[str, ConfigPropertySchema] = Field(
        default_factory=dict,
        description="Configuration parameter schemas",
    )
    child_constraints: ChildConstraints = Field(
        default_factory=ChildConstraints,
        description="Constraints on children",
    )
    blackboard_access: BlackboardAccess = Field(
        default_factory=BlackboardAccess,
        description="Blackboard variable access",
    )
    status_behavior: StatusBehavior | None = Field(
        default=None,
        description="Status return behavior",
    )
    example: BehaviorExample | None = Field(
        default=None,
        description="Usage example",
    )
    is_builtin: bool = Field(
        default=False,
        description="Whether this is a built-in py_trees behavior",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "node_type": "CheckBattery",
                "category": "condition",
                "display_name": "Battery Level Check",
                "description": "Checks if battery level is above threshold",
                "icon": "battery",
                "color": "#F39C12",
                "config_schema": {
                    "threshold": {
                        "type": "number",
                        "default": 0.2,
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Minimum battery level",
                        "ui_hints": {"widget": "slider", "step": 0.05},
                    }
                },
                "child_constraints": {
                    "min_children": 0,
                    "max_children": 0,
                },
                "blackboard_access": {
                    "reads": ["/battery/level"],
                    "writes": [],
                },
            }
        }
    )


# Enable forward references
ConfigPropertySchema.model_rebuild()
