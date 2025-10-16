"""Models for tree visualization and statistics."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NodeStatistics(BaseModel):
    """Statistics for a single node."""

    node_id: UUID = Field(description="Node UUID")
    node_name: str = Field(description="Node name")
    node_type: str = Field(description="Node type")

    # Execution counts
    tick_count: int = Field(default=0, description="Total times ticked")
    success_count: int = Field(default=0, description="Times returned SUCCESS")
    failure_count: int = Field(default=0, description="Times returned FAILURE")
    running_count: int = Field(default=0, description="Times returned RUNNING")

    # Timing statistics (milliseconds)
    total_time_ms: float = Field(default=0.0, description="Total execution time")
    avg_time_ms: float = Field(default=0.0, description="Average execution time")
    min_time_ms: float = Field(
        default=float("inf"), description="Minimum execution time"
    )
    max_time_ms: float = Field(default=0.0, description="Maximum execution time")

    # Rates
    success_rate: float = Field(default=0.0, description="Success rate (0-1)")
    failure_rate: float = Field(default=0.0, description="Failure rate (0-1)")

    # Last execution
    last_status: Optional[str] = Field(default=None, description="Last status")
    last_tick_at: Optional[datetime] = Field(
        default=None, description="Last tick timestamp"
    )


class ExecutionStatistics(BaseModel):
    """Aggregate statistics for an execution."""

    execution_id: UUID = Field(description="Execution identifier")

    # Overall metrics
    total_ticks: int = Field(default=0, description="Total ticks executed")
    total_time_ms: float = Field(default=0.0, description="Total execution time")
    avg_tick_time_ms: float = Field(default=0.0, description="Average tick time")

    # Success/failure
    successful_ticks: int = Field(default=0, description="Ticks ending in SUCCESS")
    failed_ticks: int = Field(default=0, description="Ticks ending in FAILURE")
    running_ticks: int = Field(default=0, description="Ticks ending in RUNNING")

    # Per-node statistics
    node_stats: Dict[str, NodeStatistics] = Field(
        default_factory=dict, description="Statistics per node (UUID as key)"
    )

    # Timeline
    started_at: Optional[datetime] = Field(
        default=None, description="Execution start time"
    )
    last_tick_at: Optional[datetime] = Field(
        default=None, description="Last tick time"
    )


class VisualizationNode(BaseModel):
    """Node data for visualization (py_trees_js compatible)."""

    id: str = Field(description="Node UUID as string")
    status: str = Field(description="Node status (SUCCESS/FAILURE/RUNNING/INVALID)")
    name: str = Field(description="Node name")
    colour: str = Field(description="Node color in hex format")
    details: str = Field(default="", description="Additional details")
    children: List[str] = Field(
        default_factory=list, description="Child node UUIDs as strings"
    )
    data: Dict[str, str] = Field(
        default_factory=dict, description="Additional node data"
    )


class VisualizationSnapshot(BaseModel):
    """Tree snapshot for visualization (py_trees_js compatible).

    This format is compatible with the py_trees_js library used in
    py_trees_ros_viewer.
    """

    timestamp: float = Field(description="Snapshot timestamp (seconds since epoch)")
    changed: str = Field(
        default="true", description="Whether tree changed ('true'/'false')"
    )
    behaviours: Dict[str, VisualizationNode] = Field(
        default_factory=dict, description="Node data keyed by UUID"
    )
    visited_path: List[str] = Field(
        default_factory=list, description="UUIDs of nodes on visited path"
    )
    blackboard: Dict[str, Dict] = Field(
        default_factory=lambda: {"behaviours": {}, "data": {}},
        description="Blackboard data",
    )
    activity: List[str] = Field(
        default_factory=list, description="Blackboard activity (XHTML)"
    )


class DotGraphOptions(BaseModel):
    """Options for DOT graph generation."""

    include_status: bool = Field(
        default=True, description="Include node status in visualization"
    )
    include_ids: bool = Field(default=False, description="Include node UUIDs")
    use_colors: bool = Field(default=True, description="Color nodes by status")
    rankdir: str = Field(default="TB", description="Graph direction (TB/LR/BT/RL)")
    node_shape: str = Field(default="box", description="Node shape")
    font_name: str = Field(default="Arial", description="Font name")
    font_size: int = Field(default=12, description="Font size")


class DotGraph(BaseModel):
    """DOT graph representation."""

    source: str = Field(description="DOT graph source code")
    format: str = Field(default="dot", description="Graph format")
    options: DotGraphOptions = Field(
        default_factory=DotGraphOptions, description="Generation options"
    )
