"""Models for tree and behavior validation."""

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ValidationLevel(str, Enum):
    """Severity level of validation issue."""

    ERROR = "error"  # Fatal issue preventing execution
    WARNING = "warning"  # Non-fatal issue that may cause problems
    INFO = "info"  # Informational note


class ValidationIssue(BaseModel):
    """A single validation issue."""

    level: ValidationLevel = Field(description="Severity level")
    code: str = Field(description="Issue code (e.g., 'CIRCULAR_REF')")
    message: str = Field(description="Human-readable message")
    node_id: Optional[UUID] = Field(
        default=None, description="Node ID where issue occurs"
    )
    node_path: Optional[str] = Field(
        default=None, description="Path to node (e.g., 'root.child[0].child[1]')"
    )
    field: Optional[str] = Field(
        default=None, description="Field name with issue"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )


class TreeValidationResult(BaseModel):
    """Result of tree validation."""

    is_valid: bool = Field(description="Whether tree is valid (no errors)")
    issues: List[ValidationIssue] = Field(
        default_factory=list, description="List of validation issues"
    )
    error_count: int = Field(default=0, description="Number of errors")
    warning_count: int = Field(default=0, description="Number of warnings")
    info_count: int = Field(default=0, description="Number of info messages")

    @property
    def has_errors(self) -> bool:
        """Check if validation found errors."""
        return self.error_count > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation found warnings."""
        return self.warning_count > 0


class BehaviorParameter(BaseModel):
    """Parameter definition for behavior validation."""

    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type (string/int/float/bool/object/array)")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value")
    description: Optional[str] = Field(
        default=None, description="Parameter description"
    )
    min_value: Optional[float] = Field(default=None, description="Minimum value (numeric)")
    max_value: Optional[float] = Field(default=None, description="Maximum value (numeric)")
    allowed_values: Optional[List[Any]] = Field(
        default=None, description="Allowed values (enum)"
    )


class BehaviorValidationSchema(BaseModel):
    """Validation schema for a behavior type."""

    behavior_type: str = Field(description="Behavior type identifier")
    display_name: str = Field(description="Human-readable name")
    category: str = Field(
        default="behavior", description="Category (composite/decorator/behavior)"
    )
    description: Optional[str] = Field(default=None, description="Behavior description")
    parameters: List[BehaviorParameter] = Field(
        default_factory=list, description="Expected parameters"
    )
    allows_children: bool = Field(
        default=False, description="Whether behavior can have children"
    )
    requires_children: bool = Field(
        default=False, description="Whether behavior must have children"
    )
    min_children: Optional[int] = Field(
        default=None, description="Minimum number of children"
    )
    max_children: Optional[int] = Field(
        default=None, description="Maximum number of children"
    )


class TemplateParameter(BaseModel):
    """Parameter for a tree template."""

    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type")
    description: str = Field(description="Parameter description")
    default: Optional[Any] = Field(default=None, description="Default value")
    required: bool = Field(default=True, description="Whether parameter is required")


class TreeTemplate(BaseModel):
    """Template for generating trees."""

    template_id: str = Field(description="Unique template identifier")
    name: str = Field(description="Template name")
    description: str = Field(description="Template description")
    category: str = Field(default="general", description="Template category")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    parameters: List[TemplateParameter] = Field(
        default_factory=list, description="Template parameters"
    )
    tree_structure: Dict[str, Any] = Field(
        description="Tree definition with parameter placeholders"
    )
    example_params: Dict[str, Any] = Field(
        default_factory=dict, description="Example parameter values"
    )


class TemplateInstantiationRequest(BaseModel):
    """Request to instantiate a template."""

    template_id: str = Field(description="Template to instantiate")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameter values"
    )
    tree_name: Optional[str] = Field(
        default=None, description="Name for generated tree"
    )
    tree_version: str = Field(default="1.0.0", description="Version for generated tree")
