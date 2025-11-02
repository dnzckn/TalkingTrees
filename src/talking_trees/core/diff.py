"""Tree diff and merge utilities for comparing and combining tree versions."""

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from talking_trees.models.tree import TreeDefinition, TreeNodeDefinition


class DiffType(str, Enum):
    """Types of differences between trees."""

    ADDED = "added"  # Node exists in new tree but not old
    REMOVED = "removed"  # Node exists in old tree but not new
    MODIFIED = "modified"  # Node exists in both but has changes
    MOVED = "moved"  # Node changed parent
    UNCHANGED = "unchanged"  # Node is identical


class PropertyDiffType(str, Enum):
    """Types of property changes."""

    VALUE_CHANGED = "value_changed"
    TYPE_CHANGED = "type_changed"
    ADDED = "added"
    REMOVED = "removed"


@dataclass
class PropertyDiff:
    """Difference in a node property."""

    property_name: str
    diff_type: PropertyDiffType
    old_value: Any = None
    new_value: Any = None

    def __repr__(self) -> str:
        """String representation."""
        if self.diff_type == PropertyDiffType.VALUE_CHANGED:
            return f"{self.property_name}: {self.old_value} → {self.new_value}"
        elif self.diff_type == PropertyDiffType.TYPE_CHANGED:
            return f"{self.property_name}: type changed from {type(self.old_value).__name__} to {type(self.new_value).__name__}"
        elif self.diff_type == PropertyDiffType.ADDED:
            return f"{self.property_name}: added = {self.new_value}"
        elif self.diff_type == PropertyDiffType.REMOVED:
            return f"{self.property_name}: removed (was {self.old_value})"
        return f"{self.property_name}: {self.diff_type}"


@dataclass
class NodeDiff:
    """Difference information for a single node."""

    node_id: UUID
    name: str
    node_type: str
    diff_type: DiffType
    path: str  # Hierarchical path like "Root → Selector → Sequence"
    property_diffs: list[PropertyDiff]
    old_parent_id: UUID | None = None
    new_parent_id: UUID | None = None
    child_index_old: int | None = None  # Position in sibling list
    child_index_new: int | None = None

    def __repr__(self) -> str:
        """String representation."""
        status = f"[{self.diff_type.value.upper()}]"
        details = f"{status} {self.node_type} '{self.name}' @ {self.path}"

        if self.property_diffs:
            details += f"\n  Properties changed ({len(self.property_diffs)}):"
            for prop_diff in self.property_diffs[:5]:  # Show first 5
                details += f"\n    - {prop_diff}"
            if len(self.property_diffs) > 5:
                details += f"\n    ... and {len(self.property_diffs) - 5} more"

        if self.diff_type == DiffType.MOVED:
            details += f"\n  Moved: child index {self.child_index_old} → {self.child_index_new}"

        return details


@dataclass
class TreeDiff:
    """Complete diff between two tree versions."""

    old_version: str
    new_version: str
    old_tree_id: UUID
    new_tree_id: UUID
    node_diffs: list[NodeDiff]
    metadata_changes: list[PropertyDiff]

    @property
    def has_changes(self) -> bool:
        """Check if there are any differences."""
        return len(self.node_diffs) > 0 or len(self.metadata_changes) > 0

    @property
    def summary(self) -> dict[str, int]:
        """Get summary statistics."""
        counts = {
            "added": 0,
            "removed": 0,
            "modified": 0,
            "moved": 0,
            "unchanged": 0,
            "metadata_changes": len(self.metadata_changes),
        }

        for node_diff in self.node_diffs:
            counts[node_diff.diff_type.value] += 1

        return counts

    def __repr__(self) -> str:
        """String representation."""
        summary = self.summary
        lines = [
            f"Tree Diff: {self.old_version} → {self.new_version}",
            f"  Added: {summary['added']}",
            f"  Removed: {summary['removed']}",
            f"  Modified: {summary['modified']}",
            f"  Moved: {summary['moved']}",
            f"  Metadata changes: {summary['metadata_changes']}",
        ]

        if self.node_diffs:
            lines.append("\nNode Changes:")
            for node_diff in self.node_diffs[:10]:  # Show first 10
                lines.append(f"  {node_diff}")
            if len(self.node_diffs) > 10:
                lines.append(f"  ... and {len(self.node_diffs) - 10} more")

        return "\n".join(lines)


class TreeDiffer:
    """Computes differences between tree versions."""

    def __init__(self):
        """Initialize the differ."""
        self.old_nodes: dict[UUID, TreeNodeDefinition] = {}
        self.new_nodes: dict[UUID, TreeNodeDefinition] = {}
        self.old_paths: dict[UUID, str] = {}
        self.new_paths: dict[UUID, str] = {}
        self.old_parents: dict[UUID, UUID | None] = {}
        self.new_parents: dict[UUID, UUID | None] = {}
        self.old_indices: dict[UUID, int] = {}
        self.new_indices: dict[UUID, int] = {}

    def diff_trees(
        self,
        old_tree: TreeDefinition,
        new_tree: TreeDefinition,
        semantic: bool = True,
    ) -> TreeDiff:
        """Compare two tree versions.

        Args:
            old_tree: Original tree definition
            new_tree: New tree definition
            semantic: If True, match nodes by name+type even if UUID changed

        Returns:
            TreeDiff object with all differences
        """
        # Build node maps
        self._build_node_map(
            old_tree.root,
            self.old_nodes,
            self.old_paths,
            self.old_parents,
            self.old_indices,
            "Root",
        )
        self._build_node_map(
            new_tree.root,
            self.new_nodes,
            self.new_paths,
            self.new_parents,
            self.new_indices,
            "Root",
        )

        # Match nodes (by UUID or semantically)
        matched_pairs, added_ids, removed_ids = self._match_nodes(semantic)

        # Compute node diffs
        node_diffs = []

        # Removed nodes
        for node_id in removed_ids:
            node = self.old_nodes[node_id]
            node_diffs.append(
                NodeDiff(
                    node_id=node_id,
                    name=node.name,
                    node_type=node.node_type,
                    diff_type=DiffType.REMOVED,
                    path=self.old_paths[node_id],
                    property_diffs=[],
                    old_parent_id=self.old_parents.get(node_id),
                    child_index_old=self.old_indices.get(node_id),
                )
            )

        # Added nodes
        for node_id in added_ids:
            node = self.new_nodes[node_id]
            node_diffs.append(
                NodeDiff(
                    node_id=node_id,
                    name=node.name,
                    node_type=node.node_type,
                    diff_type=DiffType.ADDED,
                    path=self.new_paths[node_id],
                    property_diffs=[],
                    new_parent_id=self.new_parents.get(node_id),
                    child_index_new=self.new_indices.get(node_id),
                )
            )

        # Modified/Moved/Unchanged nodes
        for old_id, new_id in matched_pairs:
            old_node = self.old_nodes[old_id]
            new_node = self.new_nodes[new_id]

            # Check for property changes
            prop_diffs = self._diff_node_properties(old_node, new_node)

            # Check for move (parent or position change)
            old_parent = self.old_parents.get(old_id)
            new_parent = self.new_parents.get(new_id)
            old_index = self.old_indices.get(old_id)
            new_index = self.new_indices.get(new_id)

            is_moved = (old_parent != new_parent) or (old_index != new_index)

            # Determine diff type
            if is_moved and prop_diffs:
                diff_type = DiffType.MODIFIED  # Both moved and modified
            elif is_moved:
                diff_type = DiffType.MOVED
            elif prop_diffs:
                diff_type = DiffType.MODIFIED
            else:
                diff_type = DiffType.UNCHANGED

            if diff_type != DiffType.UNCHANGED:  # Only include changes
                node_diffs.append(
                    NodeDiff(
                        node_id=new_id,  # Use new ID for reference
                        name=new_node.name,
                        node_type=new_node.node_type,
                        diff_type=diff_type,
                        path=self.new_paths[new_id],
                        property_diffs=prop_diffs,
                        old_parent_id=old_parent,
                        new_parent_id=new_parent,
                        child_index_old=old_index,
                        child_index_new=new_index,
                    )
                )

        # Diff metadata
        metadata_changes = self._diff_metadata(old_tree, new_tree)

        return TreeDiff(
            old_version=old_tree.metadata.version,
            new_version=new_tree.metadata.version,
            old_tree_id=old_tree.tree_id,
            new_tree_id=new_tree.tree_id,
            node_diffs=node_diffs,
            metadata_changes=metadata_changes,
        )

    def _build_node_map(
        self,
        node: TreeNodeDefinition,
        node_map: dict[UUID, TreeNodeDefinition],
        path_map: dict[UUID, str],
        parent_map: dict[UUID, UUID | None],
        index_map: dict[UUID, int],
        path: str,
        parent_id: UUID | None = None,
        child_index: int = 0,
    ):
        """Recursively build node maps."""
        node_map[node.node_id] = node
        path_map[node.node_id] = path
        parent_map[node.node_id] = parent_id
        index_map[node.node_id] = child_index

        for idx, child in enumerate(node.children):
            child_path = f"{path} → {child.name}"
            self._build_node_map(
                child,
                node_map,
                path_map,
                parent_map,
                index_map,
                child_path,
                node.node_id,
                idx,
            )

    def _match_nodes(
        self,
        semantic: bool,
    ) -> tuple[list[tuple[UUID, UUID]], set[UUID], set[UUID]]:
        """Match nodes between old and new trees.

        Args:
            semantic: Match by name+type even if UUID differs

        Returns:
            Tuple of (matched_pairs, added_ids, removed_ids)
        """
        matched_pairs = []
        old_ids = set(self.old_nodes.keys())
        new_ids = set(self.new_nodes.keys())

        # First pass: exact UUID matches
        common_ids = old_ids & new_ids
        matched_pairs.extend([(uid, uid) for uid in common_ids])

        remaining_old = old_ids - common_ids
        remaining_new = new_ids - common_ids

        # Second pass: semantic matching (if enabled)
        if semantic and remaining_old and remaining_new:
            # Build signature maps: (name, type, parent_path) → UUID
            old_sigs = {}
            for old_id in remaining_old:
                node = self.old_nodes[old_id]
                parent_id = self.old_parents.get(old_id)
                parent_path = self.old_paths.get(parent_id, "") if parent_id else ""
                sig = (node.name, node.node_type, parent_path)
                old_sigs[sig] = old_id

            new_sigs = {}
            for new_id in remaining_new:
                node = self.new_nodes[new_id]
                parent_id = self.new_parents.get(new_id)
                parent_path = self.new_paths.get(parent_id, "") if parent_id else ""
                sig = (node.name, node.node_type, parent_path)
                new_sigs[sig] = new_id

            # Match by signature
            common_sigs = set(old_sigs.keys()) & set(new_sigs.keys())
            for sig in common_sigs:
                old_id = old_sigs[sig]
                new_id = new_sigs[sig]
                matched_pairs.append((old_id, new_id))
                remaining_old.discard(old_id)
                remaining_new.discard(new_id)

        return matched_pairs, remaining_new, remaining_old

    def _diff_node_properties(
        self,
        old_node: TreeNodeDefinition,
        new_node: TreeNodeDefinition,
    ) -> list[PropertyDiff]:
        """Compare node properties."""
        diffs = []

        # Compare name
        if old_node.name != new_node.name:
            diffs.append(
                PropertyDiff(
                    property_name="name",
                    diff_type=PropertyDiffType.VALUE_CHANGED,
                    old_value=old_node.name,
                    new_value=new_node.name,
                )
            )

        # Compare node_type
        if old_node.node_type != new_node.node_type:
            diffs.append(
                PropertyDiff(
                    property_name="node_type",
                    diff_type=PropertyDiffType.VALUE_CHANGED,
                    old_value=old_node.node_type,
                    new_value=new_node.node_type,
                )
            )

        # Compare config
        diffs.extend(self._diff_dict(old_node.config, new_node.config, "config"))

        # Compare description if present
        if old_node.description != new_node.description:
            diffs.append(
                PropertyDiff(
                    property_name="description",
                    diff_type=PropertyDiffType.VALUE_CHANGED,
                    old_value=old_node.description,
                    new_value=new_node.description,
                )
            )

        return diffs

    def _diff_dict(
        self,
        old_dict: dict[str, Any],
        new_dict: dict[str, Any],
        prefix: str,
    ) -> list[PropertyDiff]:
        """Compare two dictionaries."""
        diffs = []

        old_keys = set(old_dict.keys())
        new_keys = set(new_dict.keys())

        # Added keys
        for key in new_keys - old_keys:
            diffs.append(
                PropertyDiff(
                    property_name=f"{prefix}.{key}",
                    diff_type=PropertyDiffType.ADDED,
                    new_value=new_dict[key],
                )
            )

        # Removed keys
        for key in old_keys - new_keys:
            diffs.append(
                PropertyDiff(
                    property_name=f"{prefix}.{key}",
                    diff_type=PropertyDiffType.REMOVED,
                    old_value=old_dict[key],
                )
            )

        # Modified keys
        for key in old_keys & new_keys:
            old_val = old_dict[key]
            new_val = new_dict[key]

            if old_val != new_val:
                # Check if type changed
                if type(old_val) is not type(new_val):
                    diffs.append(
                        PropertyDiff(
                            property_name=f"{prefix}.{key}",
                            diff_type=PropertyDiffType.TYPE_CHANGED,
                            old_value=old_val,
                            new_value=new_val,
                        )
                    )
                else:
                    diffs.append(
                        PropertyDiff(
                            property_name=f"{prefix}.{key}",
                            diff_type=PropertyDiffType.VALUE_CHANGED,
                            old_value=old_val,
                            new_value=new_val,
                        )
                    )

        return diffs

    def _diff_metadata(
        self,
        old_tree: TreeDefinition,
        new_tree: TreeDefinition,
    ) -> list[PropertyDiff]:
        """Compare tree metadata."""
        old_meta = old_tree.metadata.model_dump(exclude={"created_at", "modified_at"})
        new_meta = new_tree.metadata.model_dump(exclude={"created_at", "modified_at"})
        return self._diff_dict(old_meta, new_meta, "metadata")


class TreeMerger:
    """Merges changes from different tree versions."""

    def merge_trees(
        self,
        base: TreeDefinition,
        ours: TreeDefinition,
        theirs: TreeDefinition,
        strategy: str = "ours",
    ) -> tuple[TreeDefinition, list[str]]:
        """Three-way merge of tree definitions.

        Args:
            base: Common ancestor tree
            ours: Our version of the tree
            theirs: Their version of the tree
            strategy: Conflict resolution strategy ("ours", "theirs", "manual")

        Returns:
            Tuple of (merged_tree, conflicts)

        Raises:
            ValueError: If strategy is "manual" and conflicts exist
        """
        # Compute diffs from base
        differ = TreeDiffer()
        our_diff = differ.diff_trees(base, ours, semantic=True)
        their_diff = differ.diff_trees(base, theirs, semantic=True)

        # Detect conflicts
        conflicts = self._detect_conflicts(our_diff, their_diff)

        # If manual strategy and conflicts exist, raise
        if strategy == "manual" and conflicts:
            raise ValueError(f"Manual merge required. Conflicts: {conflicts}")

        # Apply merge strategy (pass actual tree objects for simple strategies)
        merged = self._apply_merge(base, ours, theirs, our_diff, their_diff, conflicts, strategy)

        return merged, conflicts

    def _detect_conflicts(
        self,
        our_diff: TreeDiff,
        their_diff: TreeDiff,
    ) -> list[str]:
        """Detect merge conflicts."""
        conflicts = []

        # Build maps of changes by node ID
        our_changes = {nd.node_id: nd for nd in our_diff.node_diffs}
        their_changes = {nd.node_id: nd for nd in their_diff.node_diffs}

        # Check for conflicting changes to same nodes
        common_ids = set(our_changes.keys()) & set(their_changes.keys())

        for node_id in common_ids:
            our_change = our_changes[node_id]
            their_change = their_changes[node_id]

            # Both modified the same node
            if our_change.diff_type in [
                DiffType.MODIFIED,
                DiffType.MOVED,
            ] and their_change.diff_type in [DiffType.MODIFIED, DiffType.MOVED]:
                # Check if they modified different properties
                our_props = {pd.property_name for pd in our_change.property_diffs}
                their_props = {pd.property_name for pd in their_change.property_diffs}

                conflicting_props = our_props & their_props
                if conflicting_props:
                    conflicts.append(
                        f"Node {our_change.name}: Both sides modified {conflicting_props}"
                    )

            # One deleted, one modified
            if (
                our_change.diff_type == DiffType.REMOVED
                and their_change.diff_type == DiffType.MODIFIED
            ):
                conflicts.append(
                    f"Node {our_change.name}: Deleted in ours, modified in theirs"
                )

            if (
                our_change.diff_type == DiffType.MODIFIED
                and their_change.diff_type == DiffType.REMOVED
            ):
                conflicts.append(
                    f"Node {our_change.name}: Modified in ours, deleted in theirs"
                )

        return conflicts

    def _apply_merge(
        self,
        base: TreeDefinition,
        ours: TreeDefinition,
        theirs: TreeDefinition,
        our_diff: TreeDiff,
        their_diff: TreeDiff,
        conflicts: list[str],
        strategy: str,
    ) -> TreeDefinition:
        """Apply merge using conflict resolution strategy.

        Note: This is a simplified implementation for basic strategies.
        For "ours" and "theirs" strategies, we simply return the chosen version.

        TODO: Implement true 3-way merge that:
        1. Clones base tree
        2. Applies non-conflicting changes from both sides
        3. Applies only conflicting changes based on strategy

        This would allow merging changes from both sides while resolving conflicts,
        rather than accepting one entire version.

        Args:
            base: Base tree (common ancestor)
            ours: Our version of the tree
            theirs: Their version of the tree
            our_diff: Changes from base to our version (for future use)
            their_diff: Changes from base to their version (for future use)
            conflicts: List of detected conflicts (for future use)
            strategy: Resolution strategy

        Returns:
            Merged tree

        Raises:
            ValueError: If strategy is unknown
        """
        if strategy == "ours":
            # Accept our version completely
            return ours
        elif strategy == "theirs":
            # Accept their version completely
            return theirs
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")


def format_diff_as_text(diff: TreeDiff, verbose: bool = False) -> str:
    """Format a tree diff as human-readable text.

    Args:
        diff: Tree diff to format
        verbose: Include unchanged nodes

    Returns:
        Formatted string
    """
    lines = [
        "=" * 80,
        f"TREE DIFF: {diff.old_version} → {diff.new_version}",
        "=" * 80,
        "",
    ]

    summary = diff.summary
    lines.extend(
        [
            "SUMMARY:",
            f"  Added:     {summary['added']:3d} nodes",
            f"  Removed:   {summary['removed']:3d} nodes",
            f"  Modified:  {summary['modified']:3d} nodes",
            f"  Moved:     {summary['moved']:3d} nodes",
            f"  Metadata:  {summary['metadata_changes']:3d} changes",
            "",
        ]
    )

    if diff.metadata_changes:
        lines.append("METADATA CHANGES:")
        for change in diff.metadata_changes:
            lines.append(f"  {change}")
        lines.append("")

    if diff.node_diffs:
        lines.append("NODE CHANGES:")

        # Group by type
        by_type = {}
        for node_diff in diff.node_diffs:
            dtype = node_diff.diff_type
            if dtype not in by_type:
                by_type[dtype] = []
            by_type[dtype].append(node_diff)

        # Show in order: removed, modified, moved, added
        for dtype in [
            DiffType.REMOVED,
            DiffType.MODIFIED,
            DiffType.MOVED,
            DiffType.ADDED,
        ]:
            if dtype in by_type:
                lines.append(f"\n  {dtype.value.upper()}:")
                for node_diff in by_type[dtype]:
                    lines.append(f"    • {node_diff.name} ({node_diff.node_type})")
                    lines.append(f"      Path: {node_diff.path}")

                    if node_diff.property_diffs:
                        lines.append("      Properties:")
                        for prop_diff in node_diff.property_diffs:
                            lines.append(f"        - {prop_diff}")

                    if node_diff.diff_type == DiffType.MOVED:
                        lines.append(
                            f"      Position: {node_diff.child_index_old} → "
                            f"{node_diff.child_index_new}"
                        )

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)
