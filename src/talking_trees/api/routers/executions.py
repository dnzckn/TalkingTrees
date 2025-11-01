"""Execution control endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from talking_trees.api.dependencies import execution_service_dependency
from talking_trees.core.execution import ExecutionService
from talking_trees.models.execution import (
    ExecutionConfig,
    ExecutionSnapshot,
    ExecutionSummary,
    SchedulerStatus,
    StartSchedulerRequest,
    TickRequest,
    TickResponse,
)
from talking_trees.models.tree import TreeDefinition

router = APIRouter(prefix="/executions", tags=["executions"])


@router.post("/", response_model=ExecutionSummary, status_code=201)
def create_execution(
    config: ExecutionConfig,
    service: ExecutionService = Depends(execution_service_dependency),
) -> ExecutionSummary:
    """Create a new execution instance.

    Args:
        config: Execution configuration

    Returns:
        Execution summary

    Raises:
        HTTPException: If tree not found or creation fails
    """
    try:
        execution_id = service.create_execution(config)
        instance = service.get_execution(execution_id)
        return instance.get_summary()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[ExecutionSummary])
def list_executions(
    service: ExecutionService = Depends(execution_service_dependency),
) -> list[ExecutionSummary]:
    """List all execution instances.

    Returns:
        List of execution summaries
    """
    return service.list_executions()


@router.get("/{execution_id}", response_model=ExecutionSummary)
def get_execution(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> ExecutionSummary:
    """Get execution summary.

    Args:
        execution_id: Execution identifier

    Returns:
        Execution summary

    Raises:
        HTTPException: If execution not found
    """
    try:
        instance = service.get_execution(execution_id)
        return instance.get_summary()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{execution_id}/tick", response_model=TickResponse)
def tick_execution(
    execution_id: UUID,
    request: TickRequest,
    service: ExecutionService = Depends(execution_service_dependency),
) -> TickResponse:
    """Tick an execution instance.

    Args:
        execution_id: Execution identifier
        request: Tick request with count and snapshot options

    Returns:
        Tick response with status and optional snapshot

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.tick_execution(
            execution_id=execution_id,
            count=request.count,
            capture_snapshot=request.capture_snapshot,
            blackboard_updates=request.blackboard_updates,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{execution_id}/snapshot", response_model=ExecutionSnapshot)
def get_snapshot(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> ExecutionSnapshot:
    """Get current snapshot of an execution.

    Args:
        execution_id: Execution identifier

    Returns:
        Execution snapshot

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.get_snapshot(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{execution_id}", status_code=204)
async def delete_execution(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> None:
    """Delete an execution instance.

    Args:
        execution_id: Execution identifier

    Raises:
        HTTPException: If execution not found
    """
    success = await service.delete_execution(execution_id)
    if not success:
        raise HTTPException(status_code=404, detail="Execution not found")


@router.post("/cleanup", response_model=dict)
def cleanup_stale_executions(
    max_age_hours: int = 24,
    service: ExecutionService = Depends(execution_service_dependency),
) -> dict:
    """Cleanup old execution instances.

    Args:
        max_age_hours: Maximum age in hours

    Returns:
        Cleanup summary
    """
    count = service.cleanup_stale_executions(max_age_hours)
    return {"cleaned_up": count, "max_age_hours": max_age_hours}


@router.put("/{execution_id}/tree", response_model=ExecutionSummary)
def reload_tree(
    execution_id: UUID,
    tree_def: TreeDefinition,
    preserve_blackboard: bool = True,
    service: ExecutionService = Depends(execution_service_dependency),
) -> ExecutionSummary:
    """Hot-reload execution with new tree definition.

    Like a container restart but without container software.
    Cleanly shuts down current tree and loads new one.

    Args:
        execution_id: Execution identifier
        tree_def: New tree definition
        preserve_blackboard: Whether to preserve blackboard state
        service: Execution service

    Returns:
        Updated execution summary

    Raises:
        HTTPException: If execution not found or reload fails
    """
    try:
        service.reload_tree(execution_id, tree_def, preserve_blackboard)
        instance = service.get_execution(execution_id)
        return instance.get_summary()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{execution_id}/start", response_model=SchedulerStatus)
async def start_scheduler(
    execution_id: UUID,
    request: StartSchedulerRequest,
    service: ExecutionService = Depends(execution_service_dependency),
) -> SchedulerStatus:
    """Start autonomous execution (AUTO or INTERVAL mode).

    Args:
        execution_id: Execution identifier
        request: Scheduler start request
        service: Execution service

    Returns:
        Scheduler status

    Raises:
        HTTPException: If execution not found or already running
    """
    try:
        return await service.start_scheduler(execution_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{execution_id}/pause", response_model=SchedulerStatus)
async def pause_scheduler(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> SchedulerStatus:
    """Pause autonomous execution.

    Args:
        execution_id: Execution identifier
        service: Execution service

    Returns:
        Scheduler status

    Raises:
        HTTPException: If execution not found or not running
    """
    try:
        return await service.pause_scheduler(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{execution_id}/resume", response_model=SchedulerStatus)
async def resume_scheduler(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> SchedulerStatus:
    """Resume paused execution.

    Args:
        execution_id: Execution identifier
        service: Execution service

    Returns:
        Scheduler status

    Raises:
        HTTPException: If execution not found or not paused
    """
    try:
        return await service.resume_scheduler(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{execution_id}/stop", response_model=SchedulerStatus)
async def stop_scheduler(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> SchedulerStatus:
    """Stop autonomous execution.

    Args:
        execution_id: Execution identifier
        service: Execution service

    Returns:
        Scheduler status

    Raises:
        HTTPException: If execution not found
    """
    try:
        return await service.stop_scheduler(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{execution_id}/scheduler/status", response_model=SchedulerStatus)
def get_scheduler_status(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> SchedulerStatus:
    """Get scheduler status.

    Args:
        execution_id: Execution identifier
        service: Execution service

    Returns:
        Scheduler status
    """
    try:
        return service.get_scheduler_status(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
