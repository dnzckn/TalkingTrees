"""Debug control endpoints for breakpoints, watches, and step execution."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from talking_trees.api.dependencies import execution_service_dependency
from talking_trees.core.execution import ExecutionService
from talking_trees.models.debug import (
    AddBreakpointRequest,
    AddWatchRequest,
    DebugState,
    StepRequest,
)

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/executions/{execution_id}", response_model=DebugState)
def get_debug_state(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> DebugState:
    """Get current debug state.

    Args:
        execution_id: Execution identifier
        service: Execution service

    Returns:
        Debug state

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.get_debug_state(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/executions/{execution_id}/breakpoints", response_model=DebugState)
def add_breakpoint(
    execution_id: UUID,
    request: AddBreakpointRequest,
    service: ExecutionService = Depends(execution_service_dependency),
) -> DebugState:
    """Add a breakpoint.

    Args:
        execution_id: Execution identifier
        request: Breakpoint request
        service: Execution service

    Returns:
        Updated debug state

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.add_breakpoint(execution_id, request.node_id, request.condition)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/executions/{execution_id}/breakpoints/{node_id}", response_model=DebugState
)
def remove_breakpoint(
    execution_id: UUID,
    node_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> DebugState:
    """Remove a breakpoint.

    Args:
        execution_id: Execution identifier
        node_id: Node ID
        service: Execution service

    Returns:
        Updated debug state

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.remove_breakpoint(execution_id, node_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/executions/{execution_id}/breakpoints/{node_id}/toggle",
    response_model=DebugState,
)
def toggle_breakpoint(
    execution_id: UUID,
    node_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> DebugState:
    """Toggle breakpoint enabled/disabled.

    Args:
        execution_id: Execution identifier
        node_id: Node ID
        service: Execution service

    Returns:
        Updated debug state

    Raises:
        HTTPException: If execution or breakpoint not found
    """
    try:
        return service.toggle_breakpoint(execution_id, node_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/executions/{execution_id}/watches", response_model=DebugState)
def add_watch(
    execution_id: UUID,
    request: AddWatchRequest,
    service: ExecutionService = Depends(execution_service_dependency),
) -> DebugState:
    """Add a watch expression.

    Args:
        execution_id: Execution identifier
        request: Watch request
        service: Execution service

    Returns:
        Updated debug state

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.add_watch(
            execution_id,
            request.key,
            request.condition.value,
            request.target_value,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/executions/{execution_id}/watches/{key}", response_model=DebugState)
def remove_watch(
    execution_id: UUID,
    key: str,
    service: ExecutionService = Depends(execution_service_dependency),
) -> DebugState:
    """Remove a watch expression.

    Args:
        execution_id: Execution identifier
        key: Blackboard key
        service: Execution service

    Returns:
        Updated debug state

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.remove_watch(execution_id, key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/executions/{execution_id}/watches/{key}/toggle", response_model=DebugState
)
def toggle_watch(
    execution_id: UUID,
    key: str,
    service: ExecutionService = Depends(execution_service_dependency),
) -> DebugState:
    """Toggle watch enabled/disabled.

    Args:
        execution_id: Execution identifier
        key: Blackboard key
        service: Execution service

    Returns:
        Updated debug state

    Raises:
        HTTPException: If execution or watch not found
    """
    try:
        return service.toggle_watch(execution_id, key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/executions/{execution_id}/step", response_model=DebugState)
def step_execution(
    execution_id: UUID,
    request: StepRequest,
    service: ExecutionService = Depends(execution_service_dependency),
) -> DebugState:
    """Set step execution mode.

    Args:
        execution_id: Execution identifier
        request: Step request
        service: Execution service

    Returns:
        Updated debug state

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.set_step_mode(execution_id, request.mode, request.count)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/executions/{execution_id}/pause", response_model=DebugState)
def pause_execution(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> DebugState:
    """Pause execution (debugger).

    Args:
        execution_id: Execution identifier
        service: Execution service

    Returns:
        Updated debug state

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.pause_debug(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/executions/{execution_id}/continue", response_model=DebugState)
def continue_execution(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> DebugState:
    """Continue execution (debugger).

    Args:
        execution_id: Execution identifier
        service: Execution service

    Returns:
        Updated debug state

    Raises:
        HTTPException: If execution not found
    """
    try:
        return service.resume_debug(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/executions/{execution_id}", status_code=204)
def clear_debug(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> None:
    """Clear all breakpoints and watches.

    Args:
        execution_id: Execution identifier
        service: Execution service

    Raises:
        HTTPException: If execution not found
    """
    try:
        service.clear_debug(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
