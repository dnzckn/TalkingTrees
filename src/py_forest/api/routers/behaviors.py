"""Behavior schema endpoints for editor support."""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from py_forest.api.dependencies import behavior_registry_dependency
from py_forest.core.registry import BehaviorRegistry
from py_forest.models.schema import BehaviorSchema, NodeCategory

router = APIRouter(prefix="/behaviors", tags=["behaviors"])


@router.get("/", response_model=Dict[str, BehaviorSchema])
def get_all_schemas(
    registry: BehaviorRegistry = Depends(behavior_registry_dependency),
) -> Dict[str, BehaviorSchema]:
    """Get all behavior schemas.

    Returns:
        Dictionary mapping node_type to BehaviorSchema
    """
    return registry.get_all_schemas()


@router.get("/types", response_model=List[str])
def list_behavior_types(
    registry: BehaviorRegistry = Depends(behavior_registry_dependency),
) -> List[str]:
    """List all registered behavior types.

    Returns:
        List of behavior type identifiers
    """
    return registry.list_all()


@router.get("/category/{category}", response_model=List[str])
def list_by_category(
    category: NodeCategory,
    registry: BehaviorRegistry = Depends(behavior_registry_dependency),
) -> List[str]:
    """List behaviors by category.

    Args:
        category: Category to filter by (composite, decorator, action, condition)

    Returns:
        List of behavior type identifiers in that category
    """
    return registry.list_by_category(category)


@router.get("/{node_type}", response_model=BehaviorSchema)
def get_schema(
    node_type: str,
    registry: BehaviorRegistry = Depends(behavior_registry_dependency),
) -> BehaviorSchema:
    """Get schema for a specific behavior type.

    Args:
        node_type: Behavior type identifier

    Returns:
        Behavior schema

    Raises:
        HTTPException: If behavior type not found
    """
    schema = registry.get_schema(node_type)
    if schema is None:
        raise HTTPException(
            status_code=404, detail=f"Behavior type not found: {node_type}"
        )
    return schema
