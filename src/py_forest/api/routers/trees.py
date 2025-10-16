"""Tree library management endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from py_forest.api.dependencies import tree_library_dependency
from py_forest.models.tree import TreeCatalogEntry, TreeDefinition, VersionInfo
from py_forest.storage.base import TreeLibrary

router = APIRouter(prefix="/trees", tags=["trees"])


@router.get("/", response_model=List[TreeCatalogEntry])
def list_trees(
    library: TreeLibrary = Depends(tree_library_dependency),
) -> List[TreeCatalogEntry]:
    """List all trees in the library.

    Returns:
        List of tree catalog entries
    """
    return library.list_trees()


@router.get("/{tree_id}", response_model=TreeDefinition)
def get_tree(
    tree_id: UUID,
    version: str | None = Query(None, description="Specific version (default: latest)"),
    library: TreeLibrary = Depends(tree_library_dependency),
) -> TreeDefinition:
    """Get a specific tree definition.

    Args:
        tree_id: Tree identifier
        version: Optional version string

    Returns:
        Tree definition

    Raises:
        HTTPException: If tree not found
    """
    try:
        return library.get_tree(tree_id, version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=TreeDefinition, status_code=201)
def create_tree(
    tree_def: TreeDefinition,
    library: TreeLibrary = Depends(tree_library_dependency),
) -> TreeDefinition:
    """Create or update a tree definition.

    Args:
        tree_def: Tree definition to save

    Returns:
        Saved tree definition

    Raises:
        HTTPException: If save fails
    """
    try:
        library.save_tree(tree_def)
        return tree_def
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{tree_id}", response_model=TreeDefinition)
def update_tree(
    tree_id: UUID,
    tree_def: TreeDefinition,
    library: TreeLibrary = Depends(tree_library_dependency),
) -> TreeDefinition:
    """Update an existing tree definition.

    Args:
        tree_id: Tree identifier
        tree_def: Updated tree definition

    Returns:
        Updated tree definition

    Raises:
        HTTPException: If tree not found or update fails
    """
    if tree_id != tree_def.tree_id:
        raise HTTPException(
            status_code=400, detail="Tree ID in URL does not match tree definition"
        )

    try:
        library.save_tree(tree_def)
        return tree_def
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tree_id}", status_code=204)
def delete_tree(
    tree_id: UUID,
    library: TreeLibrary = Depends(tree_library_dependency),
) -> None:
    """Delete a tree and all its versions.

    Args:
        tree_id: Tree identifier

    Raises:
        HTTPException: If tree not found
    """
    success = library.delete_tree(tree_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tree not found")


@router.get("/{tree_id}/versions", response_model=List[VersionInfo])
def list_versions(
    tree_id: UUID,
    library: TreeLibrary = Depends(tree_library_dependency),
) -> List[VersionInfo]:
    """List all versions of a tree.

    Args:
        tree_id: Tree identifier

    Returns:
        List of version information

    Raises:
        HTTPException: If tree not found
    """
    versions = library.list_versions(tree_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Tree not found")
    return versions


@router.get("/search/", response_model=List[TreeCatalogEntry])
def search_trees(
    query: str = Query(..., description="Search query string"),
    library: TreeLibrary = Depends(tree_library_dependency),
) -> List[TreeCatalogEntry]:
    """Search trees by name, description, or tags.

    Args:
        query: Search query string

    Returns:
        List of matching tree catalog entries
    """
    return library.search_trees(query)
