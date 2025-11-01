"""Profiling endpoints for performance analysis."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from py_forest.api.dependencies import execution_service_dependency
from py_forest.core.execution import ExecutionService

router = APIRouter(prefix="/profiling", tags=["profiling"])


@router.get("/{execution_id}")
def get_profiling_report(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> dict[str, Any]:
    """Get current profiling report for an execution.

    Args:
        execution_id: Execution identifier

    Returns:
        Profiling report with timing statistics

    Raises:
        HTTPException: If execution not found or profiling disabled
    """
    try:
        report = service.get_profiling_report(execution_id)

        if report is None:
            raise HTTPException(
                status_code=400, detail="Profiling is not enabled for this execution"
            )

        return report

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{execution_id}/stop")
def stop_profiling(
    execution_id: UUID,
    service: ExecutionService = Depends(execution_service_dependency),
) -> dict[str, Any]:
    """Stop profiling and get final report.

    Args:
        execution_id: Execution identifier

    Returns:
        Final profiling report with aggregated statistics

    Raises:
        HTTPException: If execution not found or profiling disabled
    """
    try:
        report = service.stop_profiling(execution_id)

        if report is None:
            raise HTTPException(
                status_code=400, detail="Profiling is not enabled for this execution"
            )

        return report

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
