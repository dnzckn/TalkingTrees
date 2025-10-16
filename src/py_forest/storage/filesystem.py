"""File system based tree library storage."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from py_forest.models.tree import (
    TreeCatalogEntry,
    TreeDefinition,
    TreeStatus,
    VersionInfo,
)
from py_forest.storage.base import TreeLibrary


class FileSystemTreeLibrary(TreeLibrary):
    """File system based tree library storage.

    Directory structure:
    base_path/
    ├── trees/
    │   ├── tree_name_1/
    │   │   ├── metadata.json
    │   │   ├── v1.0.0.json
    │   │   ├── v1.1.0.json
    │   │   └── draft.json (optional)
    │   └── tree_name_2/
    │       └── ...
    └── catalog.json (index of all trees)
    """

    def __init__(self, base_path: Path):
        """Initialize the file system library.

        Args:
            base_path: Root directory for tree storage
        """
        self.base_path = Path(base_path)
        self.trees_path = self.base_path / "trees"
        self.catalog_path = self.base_path / "catalog.json"

        # Create directories if they don't exist
        self.trees_path.mkdir(parents=True, exist_ok=True)

        # Load or create catalog
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> Dict[str, TreeCatalogEntry]:
        """Load the catalog from disk.

        Returns:
            Dictionary mapping tree_id to catalog entry
        """
        if self.catalog_path.exists():
            with open(self.catalog_path, "r") as f:
                data = json.load(f)
                return {
                    entry["tree_id"]: TreeCatalogEntry(**entry)
                    for entry in data.get("entries", [])
                }
        return {}

    def _save_catalog(self) -> None:
        """Save the catalog to disk."""
        data = {
            "entries": [entry.model_dump(mode="json") for entry in self.catalog.values()]
        }
        with open(self.catalog_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _get_tree_dir(self, tree_id: UUID) -> Optional[Path]:
        """Get the directory path for a tree.

        Args:
            tree_id: Tree identifier

        Returns:
            Path to tree directory, or None if not found
        """
        # Find tree directory by scanning for matching tree_id in metadata files
        for tree_dir in self.trees_path.iterdir():
            if tree_dir.is_dir():
                metadata_path = tree_dir / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                        if metadata.get("tree_id") == str(tree_id):
                            return tree_dir
        return None

    def _create_tree_dir(self, tree_name: str) -> Path:
        """Create a directory for a new tree.

        Args:
            tree_name: Tree name (will be sanitized for filesystem)

        Returns:
            Path to created directory
        """
        # Sanitize tree name for filesystem
        safe_name = "".join(
            c if c.isalnum() or c in "-_" else "_" for c in tree_name
        ).lower()

        tree_dir = self.trees_path / safe_name

        # Handle name collisions
        if tree_dir.exists():
            counter = 1
            while (self.trees_path / f"{safe_name}_{counter}").exists():
                counter += 1
            tree_dir = self.trees_path / f"{safe_name}_{counter}"

        tree_dir.mkdir(parents=True, exist_ok=True)
        return tree_dir

    def _load_metadata(self, tree_dir: Path) -> Dict:
        """Load tree metadata file.

        Args:
            tree_dir: Path to tree directory

        Returns:
            Metadata dictionary

        Raises:
            ValueError: If metadata file doesn't exist or is invalid
        """
        metadata_path = tree_dir / "metadata.json"
        if not metadata_path.exists():
            raise ValueError(f"Metadata file not found: {metadata_path}")

        with open(metadata_path, "r") as f:
            return json.load(f)

    def _save_metadata(self, tree_dir: Path, metadata: Dict) -> None:
        """Save tree metadata file.

        Args:
            tree_dir: Path to tree directory
            metadata: Metadata dictionary
        """
        metadata_path = tree_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

    def list_trees(
        self,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> List[TreeCatalogEntry]:
        """List all trees in the library."""
        entries = list(self.catalog.values())

        # Filter by tags
        if tags:
            entries = [
                e for e in entries if any(tag in e.tags for tag in tags)
            ]

        # Filter by status
        if status:
            entries = [e for e in entries if e.status.value == status]

        return entries

    def get_tree(
        self,
        tree_id: UUID,
        version: Optional[str] = None,
    ) -> TreeDefinition:
        """Get a specific tree definition."""
        tree_dir = self._get_tree_dir(tree_id)
        if tree_dir is None:
            raise ValueError(f"Tree not found: {tree_id}")

        metadata = self._load_metadata(tree_dir)

        # Determine which version to load
        if version is None:
            # Load latest version
            latest = next(
                (v for v in metadata.get("versions", []) if v.get("is_latest")),
                None,
            )
            if latest is None:
                raise ValueError(f"No versions found for tree: {tree_id}")
            version_file = latest["file_name"]
        else:
            # Load specific version
            version_info = next(
                (v for v in metadata.get("versions", []) if v["version"] == version),
                None,
            )
            if version_info is None:
                raise ValueError(f"Version not found: {version}")
            version_file = version_info["file_name"]

        # Load tree definition
        tree_path = tree_dir / version_file
        if not tree_path.exists():
            raise ValueError(f"Tree file not found: {tree_path}")

        with open(tree_path, "r") as f:
            data = json.load(f)
            return TreeDefinition(**data)

    def save_tree(
        self,
        tree: TreeDefinition,
        create_version: bool = True,
    ) -> str:
        """Save a tree definition."""
        # Get or create tree directory
        tree_dir = self._get_tree_dir(tree.tree_id)
        if tree_dir is None:
            tree_dir = self._create_tree_dir(tree.metadata.name)

        # Load or create metadata
        try:
            metadata = self._load_metadata(tree_dir)
        except ValueError:
            metadata = {
                "tree_id": str(tree.tree_id),
                "tree_name": tree.metadata.name,
                "versions": [],
            }

        # Determine version to save
        version = tree.metadata.version
        version_file = f"v{version}.json"

        if tree.metadata.status == TreeStatus.DRAFT:
            version_file = "draft.json"

        # Save tree definition
        tree_path = tree_dir / version_file
        with open(tree_path, "w") as f:
            json.dump(tree.model_dump(mode="json"), f, indent=2, default=str)

        # Update metadata
        if create_version and tree.metadata.status != TreeStatus.DRAFT:
            # Mark all other versions as not latest
            for v in metadata["versions"]:
                v["is_latest"] = False

            # Add new version
            version_info = {
                "version": version,
                "file_name": version_file,
                "created_at": datetime.utcnow().isoformat(),
                "status": tree.metadata.status.value,
                "is_latest": True,
                "changelog": tree.metadata.changelog,
            }
            metadata["versions"].append(version_info)

        self._save_metadata(tree_dir, metadata)

        # Update catalog
        self.catalog[str(tree.tree_id)] = TreeCatalogEntry(
            tree_id=tree.tree_id,
            tree_name=metadata["tree_name"],
            display_name=tree.metadata.name,
            latest_version=version,
            status=tree.metadata.status,
            tags=tree.metadata.tags,
            description=tree.metadata.description,
            modified_at=tree.metadata.modified_at,
        )
        self._save_catalog()

        return version

    def delete_tree(
        self,
        tree_id: UUID,
        version: Optional[str] = None,
    ) -> bool:
        """Delete a tree or specific version."""
        tree_dir = self._get_tree_dir(tree_id)
        if tree_dir is None:
            return False

        if version is None:
            # Delete entire tree
            import shutil

            shutil.rmtree(tree_dir)
            if str(tree_id) in self.catalog:
                del self.catalog[str(tree_id)]
                self._save_catalog()
            return True
        else:
            # Delete specific version
            metadata = self._load_metadata(tree_dir)
            version_info = next(
                (v for v in metadata.get("versions", []) if v["version"] == version),
                None,
            )
            if version_info is None:
                return False

            # Delete file
            version_file = tree_dir / version_info["file_name"]
            if version_file.exists():
                version_file.unlink()

            # Update metadata
            metadata["versions"] = [
                v for v in metadata["versions"] if v["version"] != version
            ]
            self._save_metadata(tree_dir, metadata)

            return True

    def list_versions(self, tree_id: UUID) -> List[VersionInfo]:
        """List all versions of a tree."""
        tree_dir = self._get_tree_dir(tree_id)
        if tree_dir is None:
            raise ValueError(f"Tree not found: {tree_id}")

        metadata = self._load_metadata(tree_dir)
        return [VersionInfo(**v) for v in metadata.get("versions", [])]

    def tree_exists(self, tree_id: UUID, version: Optional[str] = None) -> bool:
        """Check if a tree (or version) exists."""
        tree_dir = self._get_tree_dir(tree_id)
        if tree_dir is None:
            return False

        if version is None:
            return True

        metadata = self._load_metadata(tree_dir)
        return any(v["version"] == version for v in metadata.get("versions", []))

    def search_trees(self, query: str) -> List[TreeCatalogEntry]:
        """Search trees by name, description, or tags."""
        query_lower = query.lower()
        results = []

        for entry in self.catalog.values():
            if (
                query_lower in entry.display_name.lower()
                or (entry.description and query_lower in entry.description.lower())
                or any(query_lower in tag.lower() for tag in entry.tags)
            ):
                results.append(entry)

        return results
