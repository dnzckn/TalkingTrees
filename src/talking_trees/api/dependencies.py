"""Dependency injection for FastAPI."""

from collections.abc import Generator
from pathlib import Path

from talking_trees.core.execution import ExecutionService
from talking_trees.core.registry import BehaviorRegistry, get_registry
from talking_trees.core.templates import TemplateLibrary
from talking_trees.storage.base import TreeLibrary
from talking_trees.storage.filesystem import FileSystemTreeLibrary


class _AppState:
    """Application state holder for singleton services."""

    tree_library: TreeLibrary | None = None
    execution_service: ExecutionService | None = None
    behavior_registry: BehaviorRegistry | None = None
    template_library: TemplateLibrary | None = None


_state = _AppState()


def get_tree_library(data_path: Path | None = None) -> TreeLibrary:
    """Get or create the global TreeLibrary instance.

    Args:
        data_path: Optional path to data directory

    Returns:
        TreeLibrary instance
    """
    if _state.tree_library is None:
        if data_path is None:
            data_path = Path.cwd() / "data"
        _state.tree_library = FileSystemTreeLibrary(data_path)
    return _state.tree_library


def get_execution_service() -> ExecutionService:
    """Get or create the global ExecutionService instance.

    Returns:
        ExecutionService instance
    """
    if _state.execution_service is None:
        library = get_tree_library()
        _state.execution_service = ExecutionService(library)
    return _state.execution_service


def get_behavior_registry() -> BehaviorRegistry:
    """Get the global BehaviorRegistry instance.

    Returns:
        BehaviorRegistry instance
    """
    if _state.behavior_registry is None:
        _state.behavior_registry = get_registry()
    return _state.behavior_registry


def get_template_library(templates_path: Path | None = None) -> TemplateLibrary:
    """Get or create the global TemplateLibrary instance.

    Args:
        templates_path: Optional path to templates directory

    Returns:
        TemplateLibrary instance
    """
    if _state.template_library is None:
        if templates_path is None:
            templates_path = Path.cwd() / "data" / "templates"
        _state.template_library = TemplateLibrary(templates_path)
    return _state.template_library


# FastAPI dependency functions
def tree_library_dependency() -> Generator[TreeLibrary, None, None]:
    """FastAPI dependency for TreeLibrary."""
    yield get_tree_library()


def execution_service_dependency() -> Generator[ExecutionService, None, None]:
    """FastAPI dependency for ExecutionService."""
    yield get_execution_service()


def behavior_registry_dependency() -> Generator[BehaviorRegistry, None, None]:
    """FastAPI dependency for BehaviorRegistry."""
    yield get_behavior_registry()


def template_library_dependency() -> Generator[TemplateLibrary, None, None]:
    """FastAPI dependency for TemplateLibrary."""
    yield get_template_library()
