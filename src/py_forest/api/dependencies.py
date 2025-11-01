"""Dependency injection for FastAPI."""

from collections.abc import Generator
from pathlib import Path

from py_forest.core.execution import ExecutionService
from py_forest.core.registry import BehaviorRegistry, get_registry
from py_forest.core.templates import TemplateLibrary
from py_forest.storage.base import TreeLibrary
from py_forest.storage.filesystem import FileSystemTreeLibrary

# Global instances
_tree_library: TreeLibrary | None = None
_execution_service: ExecutionService | None = None
_behavior_registry: BehaviorRegistry | None = None
_template_library: TemplateLibrary | None = None


def get_tree_library(data_path: Path | None = None) -> TreeLibrary:
    """Get or create the global TreeLibrary instance.

    Args:
        data_path: Optional path to data directory

    Returns:
        TreeLibrary instance
    """
    global _tree_library
    if _tree_library is None:
        if data_path is None:
            data_path = Path.cwd() / "data"
        _tree_library = FileSystemTreeLibrary(data_path)
    return _tree_library


def get_execution_service() -> ExecutionService:
    """Get or create the global ExecutionService instance.

    Returns:
        ExecutionService instance
    """
    global _execution_service
    if _execution_service is None:
        library = get_tree_library()
        _execution_service = ExecutionService(library)
    return _execution_service


def get_behavior_registry() -> BehaviorRegistry:
    """Get the global BehaviorRegistry instance.

    Returns:
        BehaviorRegistry instance
    """
    global _behavior_registry
    if _behavior_registry is None:
        _behavior_registry = get_registry()
    return _behavior_registry


def get_template_library(templates_path: Path | None = None) -> TemplateLibrary:
    """Get or create the global TemplateLibrary instance.

    Args:
        templates_path: Optional path to templates directory

    Returns:
        TemplateLibrary instance
    """
    global _template_library
    if _template_library is None:
        if templates_path is None:
            templates_path = Path.cwd() / "data" / "templates"
        _template_library = TemplateLibrary(templates_path)
    return _template_library


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
