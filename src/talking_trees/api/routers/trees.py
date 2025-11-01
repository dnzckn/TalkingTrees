"""Tree library management endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from talking_trees.api.dependencies import tree_library_dependency
from talking_trees.core.diff import TreeDiffer, format_diff_as_text
from talking_trees.models.tree import TreeCatalogEntry, TreeDefinition, VersionInfo
from talking_trees.storage.base import TreeLibrary

router = APIRouter(prefix="/trees", tags=["trees"])


@router.get("/", response_model=list[TreeCatalogEntry])
def list_trees(
    library: TreeLibrary = Depends(tree_library_dependency),
) -> list[TreeCatalogEntry]:
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


@router.get("/{tree_id}/versions", response_model=list[VersionInfo])
def list_versions(
    tree_id: UUID,
    library: TreeLibrary = Depends(tree_library_dependency),
) -> list[VersionInfo]:
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


@router.get("/search/", response_model=list[TreeCatalogEntry])
def search_trees(
    query: str = Query(..., description="Search query string"),
    library: TreeLibrary = Depends(tree_library_dependency),
) -> list[TreeCatalogEntry]:
    """Search trees by name, description, or tags.

    Args:
        query: Search query string

    Returns:
        List of matching tree catalog entries
    """
    return library.search_trees(query)


@router.get("/{tree_id}/diff")
def diff_tree_versions(
    tree_id: UUID,
    old_version: str = Query(..., description="Old version to compare from"),
    new_version: str = Query(..., description="New version to compare to"),
    semantic: bool = Query(True, description="Use semantic matching by name+type"),
    format: str = Query("json", description="Output format: 'json' or 'text'"),
    library: TreeLibrary = Depends(tree_library_dependency),
) -> dict[str, Any] | str:
    """Compare two versions of a tree.

    Args:
        tree_id: Tree identifier
        old_version: Version to compare from
        new_version: Version to compare to
        semantic: Use semantic matching (match by name+type even if UUID changed)
        format: Output format ('json' or 'text')

    Returns:
        Diff information in requested format

    Raises:
        HTTPException: If tree or versions not found
    """
    try:
        # Get both versions
        old_tree = library.get_tree(tree_id, old_version)
        new_tree = library.get_tree(tree_id, new_version)

        # Compute diff
        differ = TreeDiffer()
        diff = differ.diff_trees(old_tree, new_tree, semantic=semantic)

        # Return in requested format
        if format == "text":
            return format_diff_as_text(diff, verbose=False)
        else:
            # JSON format
            return {
                "old_version": diff.old_version,
                "new_version": diff.new_version,
                "old_tree_id": str(diff.old_tree_id),
                "new_tree_id": str(diff.new_tree_id),
                "summary": diff.summary,
                "has_changes": diff.has_changes,
                "node_diffs": [
                    {
                        "node_id": str(nd.node_id),
                        "name": nd.name,
                        "node_type": nd.node_type,
                        "diff_type": nd.diff_type.value,
                        "path": nd.path,
                        "property_diffs": [
                            {
                                "property_name": pd.property_name,
                                "diff_type": pd.diff_type.value,
                                "old_value": pd.old_value,
                                "new_value": pd.new_value,
                            }
                            for pd in nd.property_diffs
                        ],
                        "old_parent_id": str(nd.old_parent_id)
                        if nd.old_parent_id
                        else None,
                        "new_parent_id": str(nd.new_parent_id)
                        if nd.new_parent_id
                        else None,
                        "child_index_old": nd.child_index_old,
                        "child_index_new": nd.child_index_new,
                    }
                    for nd in diff.node_diffs
                ],
                "metadata_changes": [
                    {
                        "property_name": pd.property_name,
                        "diff_type": pd.diff_type.value,
                        "old_value": pd.old_value,
                        "new_value": pd.new_value,
                    }
                    for pd in diff.metadata_changes
                ],
            }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing diff: {str(e)}")
