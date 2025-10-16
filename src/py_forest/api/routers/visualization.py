"""Visualization and statistics endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from py_forest.api.dependencies import execution_service_dependency
from py_forest.core.execution import ExecutionService
from py_forest.core.visualization import TreeVisualizer
from py_forest.models.visualization import (
    DotGraph,
    DotGraphOptions,
    ExecutionStatistics,
    VisualizationSnapshot,
)

router = APIRouter(prefix="/visualizations", tags=["visualizations"])

# Shared visualizer instance
visualizer = TreeVisualizer()


@router.get("/executions/{execution_id}/dot", response_model=DotGraph)
def get_dot_graph(
    execution_id: UUID,
    include_status: bool = True,
    include_ids: bool = False,
    use_colors: bool = True,
    rankdir: str = "TB",
    service: ExecutionService = Depends(execution_service_dependency),
) -> DotGraph:
    """Get DOT graph representation of execution.

    Args:
        execution_id: Execution identifier
        include_status: Include node status in labels
        include_ids: Include node UUIDs in labels
        use_colors: Color nodes by status/type
        rankdir: Graph direction (TB/LR/BT/RL)
        service: Execution service

    Returns:
        DOT graph representation

    Raises:
        HTTPException: If execution not found
    """
    try:
        # Get snapshot
        snapshot = service.get_snapshot(execution_id)

        # Create options
        options = DotGraphOptions(
            include_status=include_status,
            include_ids=include_ids,
            use_colors=use_colors,
            rankdir=rankdir,
        )

        # Generate DOT graph
        return visualizer.to_dot(snapshot, options)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/executions/{execution_id}/pytrees_js", response_model=VisualizationSnapshot)
def get_pytrees_js(
    execution_id: UUID,
    include_blackboard: bool = False,
    service: ExecutionService = Depends(execution_service_dependency),
) -> VisualizationSnapshot:
    """Get py_trees_js compatible visualization format.

    This format is compatible with the py_trees_js library
    used in py_trees_ros_viewer.

    Args:
        execution_id: Execution identifier
        include_blackboard: Include blackboard data
        service: Execution service

    Returns:
        Visualization snapshot in py_trees_js format

    Raises:
        HTTPException: If execution not found
    """
    try:
        # Get snapshot
        snapshot = service.get_snapshot(execution_id)

        # Convert to py_trees_js format
        return visualizer.to_pytrees_js(snapshot, include_blackboard)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/executions/{execution_id}/svg")
def get_svg(
    execution_id: UUID,
    include_status: bool = True,
    include_ids: bool = False,
    use_colors: bool = True,
    rankdir: str = "TB",
    service: ExecutionService = Depends(execution_service_dependency),
) -> Response:
    """Get SVG visualization of execution.

    Note: Requires graphviz package to be installed.

    Args:
        execution_id: Execution identifier
        include_status: Include node status in labels
        include_ids: Include node UUIDs in labels
        use_colors: Color nodes by status/type
        rankdir: Graph direction (TB/LR/BT/RL)
        service: Execution service

    Returns:
        SVG response

    Raises:
        HTTPException: If execution not found or graphviz not installed
    """
    try:
        # Get snapshot
        snapshot = service.get_snapshot(execution_id)

        # Create options
        options = DotGraphOptions(
            include_status=include_status,
            include_ids=include_ids,
            use_colors=use_colors,
            rankdir=rankdir,
        )

        # Generate SVG
        svg_content = visualizer.snapshot_to_svg(snapshot, options)

        return Response(content=svg_content, media_type="image/svg+xml")

    except ImportError as e:
        raise HTTPException(
            status_code=501,
            detail="SVG export requires graphviz package: pip install graphviz",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/executions/{execution_id}/png")
def get_png(
    execution_id: UUID,
    include_status: bool = True,
    include_ids: bool = False,
    use_colors: bool = True,
    rankdir: str = "TB",
    service: ExecutionService = Depends(execution_service_dependency),
) -> Response:
    """Get PNG visualization of execution.

    Note: Requires graphviz package to be installed.

    Args:
        execution_id: Execution identifier
        include_status: Include node status in labels
        include_ids: Include node UUIDs in labels
        use_colors: Color nodes by status/type
        rankdir: Graph direction (TB/LR/BT/RL)
        service: Execution service

    Returns:
        PNG response

    Raises:
        HTTPException: If execution not found or graphviz not installed
    """
    try:
        # Get snapshot
        snapshot = service.get_snapshot(execution_id)

        # Create options
        options = DotGraphOptions(
            include_status=include_status,
            include_ids=include_ids,
            use_colors=use_colors,
            rankdir=rankdir,
        )

        # Generate PNG
        png_bytes = visualizer.snapshot_to_png(snapshot, options)

        return Response(content=png_bytes, media_type="image/png")

    except ImportError as e:
        raise HTTPException(
            status_code=501,
            detail="PNG export requires graphviz package: pip install graphviz",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/executions/{execution_id}/statistics", response_model=ExecutionStatistics)
def get_statistics(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> ExecutionStatistics:
    """Get execution statistics.

    Includes:
    - Overall execution metrics (tick count, timing, success rates)
    - Per-node statistics (execution counts, timing, success rates)

    Args:
        execution_id: Execution identifier
        service: Execution service

    Returns:
        Execution statistics

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.get_statistics(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
