"""Execution history endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from py_forest.api.dependencies import execution_service_dependency
from py_forest.core.execution import ExecutionService
from py_forest.models.execution import ExecutionSnapshot

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/executions/{execution_id}", response_model=list[ExecutionSnapshot])
def get_execution_history(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> list[ExecutionSnapshot]:
    """Get complete execution history.

    Args:
        execution_id: Execution identifier
        service: Execution service

    Returns:
        List of all snapshots

    Raises:
        HTTPException: If execution not found or history not enabled
    """
    try:
        return service.get_history(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/executions/{execution_id}/tick/{tick}", response_model=ExecutionSnapshot)
def get_history_tick(
    execution_id: UUID,
    tick: int,
    service: ExecutionService = Depends(execution_service_dependency),
) -> ExecutionSnapshot:
    """Get snapshot for specific tick.

    Args:
        execution_id: Execution identifier
        tick: Tick number
        service: Execution service

    Returns:
        Snapshot at that tick

    Raises:
        HTTPException: If not found
    """
    try:
        snapshot = service.get_history_snapshot(execution_id, tick)
        if snapshot is None:
            raise HTTPException(
                status_code=404, detail=f"Snapshot at tick {tick} not found"
            )
        return snapshot
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/executions/{execution_id}/range", response_model=list[ExecutionSnapshot])
def get_history_range(
    execution_id: UUID,
    start_tick: int = Query(..., description="Start tick (inclusive)"),
    end_tick: int = Query(..., description="End tick (inclusive)"),
    service: ExecutionService = Depends(execution_service_dependency),
) -> list[ExecutionSnapshot]:
    """Get snapshots for tick range.

    Args:
        execution_id: Execution identifier
        start_tick: Start tick
        end_tick: End tick
        service: Execution service

    Returns:
        List of snapshots in range

    Raises:
        HTTPException: If invalid range or history not enabled
    """
    if start_tick > end_tick:
        raise HTTPException(status_code=400, detail="start_tick must be <= end_tick")

    try:
        return service.get_history_range(execution_id, start_tick, end_tick)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/executions/{execution_id}/changes", response_model=dict)
def get_history_changes(
    execution_id: UUID,
    from_tick: int = Query(..., description="From tick"),
    to_tick: int = Query(..., description="To tick"),
    service: ExecutionService = Depends(execution_service_dependency),
) -> dict:
    """Get changes between two ticks.

    Args:
        execution_id: Execution identifier
        from_tick: Starting tick
        to_tick: Ending tick
        service: Execution service

    Returns:
        Dictionary of changes

    Raises:
        HTTPException: If history not enabled
    """
    if not service.history:
        raise HTTPException(status_code=400, detail="Execution history is not enabled")

    changes = service.history.get_changes(execution_id, from_tick, to_tick)
    return changes
