"""Pydantic models for behavior tree definitions."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class TreeStatus(str, Enum):
    """Status of a tree definition in the library."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class TreeNodeDefinition(BaseModel):
    """Definition of a single node in a behavior tree.

    This represents both the structure and configuration of a node.
    Supports references to subtrees via $ref.
    """

    node_type: str = Field(
        description="Type identifier (e.g., 'Sequence', 'Selector', 'CheckBattery')"
    )
    node_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this node instance",
    )
    name: str = Field(description="Human-readable name for this node")
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Node-specific configuration parameters",
    )
    description: str | None = Field(
        default=None,
        description="Optional semantic description/notes for this node",
    )
    children: list["TreeNodeDefinition"] = Field(
        default_factory=list,
        description="Child nodes (composites only)",
    )
    ref: str | None = Field(
        default=None,
        alias="$ref",
        description="Reference to a subtree definition",
    )

    @field_validator("node_type")
    @classmethod
    def validate_node_type(cls, v: str) -> str:
        """Ensure node type is not empty."""
        if not v or not v.strip():
            raise ValueError("node_type cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()


class TreeDependencies(BaseModel):
    """Dependencies required by a tree definition."""

    behaviors: list[str] = Field(
        default_factory=list,
        description="Required behavior types",
    )
    subtrees: list[str] = Field(
        default_factory=list,
        description="Referenced subtree IDs",
    )
    external: list[str] = Field(
        default_factory=list,
        description="External dependencies (packages, services)",
    )


class ValidationResult(BaseModel):
    """Results from tree validation."""

    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal issues",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Fatal issues preventing execution",
    )

    @property
    def is_valid(self) -> bool:
        """Check if tree is valid (no errors)."""
        return len(self.errors) == 0


class TreeMetadata(BaseModel):
    """Metadata about a tree definition."""

    name: str = Field(description="Human-readable tree name")
    version: str = Field(description="Semantic version (e.g., '1.0.0')")
    author: str | None = Field(
        default=None,
        description="Author email or identifier",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp",
    )
    modified_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last modification timestamp",
    )
    description: str | None = Field(
        default=None,
        description="Detailed description of tree purpose",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Search tags",
    )
    changelog: str | None = Field(
        default=None,
        description="Changes in this version",
    )
    status: TreeStatus = Field(
        default=TreeStatus.DRAFT,
        description="Tree status in library",
    )


class TreeDefinition(BaseModel):
    """Complete definition of a behavior tree.

    This is the root model for tree definitions, containing all
    information needed to instantiate and execute a tree.
    """

    schema_version: str = Field(
        default="1.0.0",
        alias="$schema",
        description="Schema version for compatibility",
    )
    tree_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this tree",
    )
    metadata: TreeMetadata = Field(
        description="Tree metadata (name, version, author, etc.)"
    )
    root: TreeNodeDefinition = Field(description="Root node of the tree")
    subtrees: dict[str, TreeNodeDefinition] = Field(
        default_factory=dict,
        description="Named subtree definitions for reuse",
    )
    dependencies: TreeDependencies = Field(
        default_factory=TreeDependencies,
        description="Required dependencies",
    )
    validation: ValidationResult = Field(
        default_factory=ValidationResult,
        description="Validation results",
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True  # Allow both 'schema_version' and '$schema'
        json_schema_extra = {
            "example": {
                "$schema": "1.0.0",
                "tree_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {
                    "name": "Simple Patrol",
                    "version": "1.0.0",
                    "description": "Basic patrol behavior",
                    "tags": ["patrol", "example"],
                },
                "root": {
                    "node_type": "Sequence",
                    "name": "patrol_sequence",
                    "config": {"memory": True},
                    "children": [],
                },
            }
        }


class VersionInfo(BaseModel):
    """Information about a specific tree version."""

    version: str = Field(description="Semantic version string")
    file_name: str = Field(description="Storage file name")
    created_at: datetime = Field(description="Version creation timestamp")
    status: TreeStatus = Field(description="Version status")
    is_latest: bool = Field(
        default=False,
        description="Whether this is the latest version",
    )
    changelog: str | None = Field(
        default=None,
        description="Changes in this version",
    )


class TreeCatalogEntry(BaseModel):
    """Entry in the tree library catalog."""

    tree_id: UUID = Field(description="Unique tree identifier")
    tree_name: str = Field(description="Tree name (folder name)")
    display_name: str = Field(description="Human-readable display name")
    latest_version: str = Field(description="Latest version number")
    status: TreeStatus = Field(description="Current status")
    tags: list[str] = Field(
        default_factory=list,
        description="Search tags",
    )
    description: str | None = Field(
        default=None,
        description="Brief description",
    )
    modified_at: datetime = Field(description="Last modification time")


# Enable forward references for self-referential models
TreeNodeDefinition.model_rebuild()
