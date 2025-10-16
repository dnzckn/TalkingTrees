"""Abstract base class for tree library storage."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from py_forest.models.tree import (
    TreeCatalogEntry,
    TreeDefinition,
    VersionInfo,
)


class TreeLibrary(ABC):
    """Abstract interface for tree library storage.

    Implementations can use:
    - File system (JSON files)
    - Database (PostgreSQL, MongoDB, etc.)
    - Git repository
    - Cloud storage (S3, etc.)
    """

    @abstractmethod
    def list_trees(
        self,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> List[TreeCatalogEntry]:
        """List all trees in the library.

        Args:
            tags: Filter by tags (optional)
            status: Filter by status (optional)

        Returns:
            List of catalog entries
        """
        pass

    @abstractmethod
    def get_tree(
        self,
        tree_id: UUID,
        version: Optional[str] = None,
    ) -> TreeDefinition:
        """Get a specific tree definition.

        Args:
            tree_id: Tree identifier
            version: Specific version (latest if not specified)

        Returns:
            Tree definition

        Raises:
            ValueError: If tree or version not found
        """
        pass

    @abstractmethod
    def save_tree(
        self,
        tree: TreeDefinition,
        create_version: bool = True,
    ) -> str:
        """Save a tree definition.

        Args:
            tree: Tree definition to save
            create_version: Whether to create a new version

        Returns:
            Version string that was created/updated

        Raises:
            ValueError: If tree data is invalid
        """
        pass

    @abstractmethod
    def delete_tree(
        self,
        tree_id: UUID,
        version: Optional[str] = None,
    ) -> bool:
        """Delete a tree or specific version.

        Args:
            tree_id: Tree identifier
            version: Specific version (all versions if not specified)

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def list_versions(self, tree_id: UUID) -> List[VersionInfo]:
        """List all versions of a tree.

        Args:
            tree_id: Tree identifier

        Returns:
            List of version information

        Raises:
            ValueError: If tree not found
        """
        pass

    @abstractmethod
    def tree_exists(self, tree_id: UUID, version: Optional[str] = None) -> bool:
        """Check if a tree (or version) exists.

        Args:
            tree_id: Tree identifier
            version: Specific version (any version if not specified)

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    def search_trees(self, query: str) -> List[TreeCatalogEntry]:
        """Search trees by name, description, or tags.

        Args:
            query: Search query string

        Returns:
            List of matching catalog entries
        """
        pass
