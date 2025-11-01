"""Custom exceptions for PyForest core operations."""

from py_forest.models.tree import TreeNodeDefinition


class TreeBuildError(ValueError):
    """Enhanced error with tree context for better debugging.

    Provides detailed information about where in the tree an error occurred,
    including the node path, type, and helpful suggestions.
    """

    def __init__(
        self,
        message: str,
        node_def: TreeNodeDefinition | None = None,
        path: str = "",
        suggestions: list[str] | None = None,
    ):
        """Initialize tree build error.

        Args:
            message: Primary error message
            node_def: Node definition where error occurred
            path: Path from root to this node (e.g., "root/Sequence[0]/Timeout[1]")
            suggestions: Helpful suggestions for fixing the error
        """
        self.node_def = node_def
        self.path = path
        self.suggestions = suggestions or []

        # Build comprehensive error message
        parts = [message]

        if node_def:
            parts.append(f"  Node: {node_def.name} (type: {node_def.node_type})")
            parts.append(f"  ID: {node_def.node_id}")

        if path:
            parts.append(f"  Path: {path}")

        if self.suggestions:
            parts.append("  Suggestions:")
            for suggestion in self.suggestions:
                parts.append(f"    - {suggestion}")

        full_message = "\n".join(parts)
        super().__init__(full_message)


class TreeValidationError(ValueError):
    """Error during tree validation."""

    pass


class CircularReferenceError(TreeValidationError):
    """Circular reference detected in subtree definitions."""

    pass


class DepthLimitError(TreeBuildError):
    """Tree depth exceeded maximum allowed."""

    pass
