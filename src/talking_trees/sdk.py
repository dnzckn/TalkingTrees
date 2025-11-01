"""High-level Python SDK for TalkingTrees - use without API server.

This module provides simple interfaces for:
- Loading trees from JSON/YAML
- Running executions
- Tree validation and analysis
- Node search and query
- Debugging and profiling
- Comparing tree versions
- Converting from/to py_trees
- Batch operations

Perfect for Jupyter notebooks, scripts, and experimentation.
"""

import hashlib
import json
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

import py_trees

from talking_trees.core.diff import TreeDiffer, format_diff_as_text
from talking_trees.core.profiler import (
    ProfilingLevel,
    TreeProfiler,
    format_profile_report,
    get_profiler,
)
from talking_trees.core.registry import get_registry
from talking_trees.core.serializer import TreeSerializer
from talking_trees.core.validation import TreeValidator
from talking_trees.models.tree import TreeDefinition, TreeMetadata, TreeNodeDefinition
from talking_trees.models.validation import TreeValidationResult

# Import adapter functions for py_trees integration
try:
    from talking_trees.adapters import from_py_trees, to_py_trees
except ImportError:
    # Adapters not available
    from_py_trees = None
    to_py_trees = None

# Try to import YAML support
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class TreeStatistics:
    """Statistics about a tree structure."""

    def __init__(
        self,
        node_count: int,
        max_depth: int,
        avg_depth: float,
        type_distribution: dict[str, int],
        category_distribution: dict[str, int],
        leaf_count: int,
        composite_count: int,
        decorator_count: int,
    ):
        self.node_count = node_count
        self.max_depth = max_depth
        self.avg_depth = avg_depth
        self.type_distribution = type_distribution
        self.category_distribution = category_distribution
        self.leaf_count = leaf_count
        self.composite_count = composite_count
        self.decorator_count = decorator_count

    def __repr__(self) -> str:
        return (
            f"TreeStatistics(\n"
            f"  nodes={self.node_count}, "
            f"depth={self.max_depth}, "
            f"leaves={self.leaf_count}, "
            f"composites={self.composite_count}, "
            f"decorators={self.decorator_count}\n"
            f")"
        )

    def summary(self) -> str:
        """Get a formatted summary of tree statistics."""
        lines = [
            "Tree Statistics:",
            f"  Total Nodes: {self.node_count}",
            f"  Max Depth: {self.max_depth}",
            f"  Avg Depth: {self.avg_depth:.2f}",
            f"  Leaf Nodes: {self.leaf_count}",
            f"  Composites: {self.composite_count}",
            f"  Decorators: {self.decorator_count}",
            "",
            "Node Types:",
        ]

        for node_type, count in sorted(
            self.type_distribution.items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  {node_type}: {count}")

        return "\n".join(lines)


class TalkingTrees:
    """Simple interface for working with behavior trees in Python.

    Provides comprehensive features for:
    - Loading/saving trees (JSON/YAML)
    - Tree validation
    - Node search and query
    - Statistics and analysis
    - Batch operations
    - Tree manipulation
    - Execution and profiling

    Usage:
        # Basic usage
        tt = TalkingTrees()
        tree = tt.load_tree("my_tree.json")

        # Validate before running
        validation = tt.validate_tree(tree)
        if not validation.is_valid:
            print("Tree has errors!")
            return

        # Search for nodes
        timeouts = tt.find_nodes_by_type(tree, "Timeout")

        # Get statistics
        stats = tt.get_tree_stats(tree)
        print(stats.summary())

        # Execute
        execution = tt.create_execution(tree)
        result = execution.tick(blackboard_updates={
            "battery_level": 15,
            "distance": 3.5
        })

        # Read outputs
        action = result.blackboard.get("/robot_action")
        print(f"Robot should: {action}")
    """

    def __init__(
        self,
        profiling_level: ProfilingLevel = ProfilingLevel.OFF,
        enable_cache: bool = True,
    ):
        """Initialize TalkingTrees SDK.

        Args:
            profiling_level: Default profiling level for executions
            enable_cache: Enable caching for repeated operations (e.g., tree hashes)
        """
        self.profiling_level = profiling_level
        self.profiler = (
            get_profiler(profiling_level)
            if profiling_level != ProfilingLevel.OFF
            else None
        )
        self.registry = get_registry()
        self.validator = TreeValidator(self.registry)
        self.enable_cache = enable_cache
        self._tree_hash_cache: dict[str, str] = {}

    def load_tree(self, path: str) -> TreeDefinition:
        """Load a tree from JSON file.

        Args:
            path: Path to JSON file exported from editor

        Returns:
            TreeDefinition object

        Example:
            tree = tt.load_tree("examples/robot_v1.json")
        """
        with open(path) as f:
            data = json.load(f)

        return TreeDefinition.model_validate(data)

    def save_tree(self, tree: TreeDefinition, path: str) -> None:
        """Save a tree to JSON file.

        Args:
            tree: TreeDefinition to save
            path: Output file path

        Example:
            tt.save_tree(tree, "my_tree.json")
        """
        with open(path, "w") as f:
            json.dump(tree.model_dump(by_alias=True), f, indent=2, default=str)

    def create_execution(
        self,
        tree: TreeDefinition,
        initial_blackboard: dict[str, Any] | None = None,
        profiling_level: ProfilingLevel | None = None,
    ) -> "Execution":
        """Create an execution from a tree definition.

        Args:
            tree: TreeDefinition to execute
            initial_blackboard: Initial blackboard values
            profiling_level: Override default profiling level

        Returns:
            Execution object for running the tree

        Example:
            execution = tt.create_execution(tree, initial_blackboard={
                "battery_level": 100.0,
                "distance": 999.0
            })
        """
        # Deserialize tree
        serializer = TreeSerializer()
        py_tree = serializer.deserialize(tree)

        # Apply initial blackboard
        if initial_blackboard:
            bb = py_trees.blackboard.Client(name="Initializer")
            for key, value in initial_blackboard.items():
                bb.register_key(key=key, access=py_trees.common.Access.WRITE)
                bb.set(key, value, overwrite=True)

        # Setup tree
        py_tree.setup()

        # Create execution wrapper
        profiling = (
            profiling_level if profiling_level is not None else self.profiling_level
        )

        return Execution(
            tree_def=tree,
            py_tree=py_tree,
            serializer=serializer,
            profiling_level=profiling,
            profiler=self.profiler,
        )

    def diff_trees(
        self,
        old_tree: TreeDefinition,
        new_tree: TreeDefinition,
        semantic: bool = True,
        verbose: bool = False,
    ) -> str:
        """Compare two tree versions and get human-readable diff.

        Args:
            old_tree: Original tree
            new_tree: New tree
            semantic: Use semantic matching (recommended)
            verbose: Include detailed node info

        Returns:
            Formatted diff string

        Example:
            tree_v1 = tt.load_tree("robot_v1.json")
            tree_v2 = tt.load_tree("robot_v2.json")
            diff = tt.diff_trees(tree_v1, tree_v2)
            print(diff)
        """
        differ = TreeDiffer()
        diff = differ.diff_trees(old_tree, new_tree, semantic=semantic)
        return format_diff_as_text(diff, verbose=verbose)

    def from_py_trees(
        self,
        root,
        name: str = "Converted Tree",
        version: str = "1.0.0",
        description: str = "Converted from py_trees",
    ) -> TreeDefinition:
        """Convert a py_trees tree to TalkingTrees format.

        This allows you to create trees using py_trees API, then visualize
        and run them with TalkingTrees tools.

        Args:
            root: Root node of py_trees tree
            name: Name for the TalkingTrees tree
            version: Version string
            description: Description

        Returns:
            TreeDefinition compatible with TalkingTrees

        Example:
            import py_trees
            from talking_trees.sdk import TalkingTrees

            # Create tree with py_trees
            root = py_trees.composites.Sequence("MySequence")
            root.add_child(py_trees.behaviours.Success("Step1"))

            # Convert to TalkingTrees
            tt = TalkingTrees()
            tree = tt.from_py_trees(root, name="My Tree")

            # Save for editor
            tt.save_tree(tree, "my_tree.json")
        """
        if from_py_trees is None:
            raise ImportError(
                "py_trees adapter not available. Install talking_trees.adapters"
            )

        tree_def, context = from_py_trees(
            root, name=name, version=version, description=description
        )
        return tree_def

    # =============================================================================
    # Validation
    # =============================================================================

    def validate_tree(
        self, tree: TreeDefinition, verbose: bool = False
    ) -> TreeValidationResult:
        """Validate a tree definition.

        Checks for:
        - Structural issues (circular refs, duplicate IDs)
        - Unknown node types
        - Invalid configuration
        - Missing required parameters
        - Subtree reference validity

        Args:
            tree: Tree to validate
            verbose: Print validation issues

        Returns:
            Validation result with issues

        Example:
            >>> result = tt.validate_tree(tree)
            >>> if not result.is_valid:
            >>>     for issue in result.issues:
            >>>         print(f"{issue.level}: {issue.message}")
        """
        result = self.validator.validate(tree)

        if verbose:
            print(
                f"\nValidation Result: {'✓ VALID' if result.is_valid else '✗ INVALID'}"
            )
            print(
                f"Errors: {result.error_count}, Warnings: {result.warning_count}, Info: {result.info_count}"
            )

            if result.issues:
                print("\nIssues:")
                for issue in result.issues:
                    level_icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}[
                        issue.level.value
                    ]
                    path = f" [{issue.node_path}]" if issue.node_path else ""
                    print(f"  {level_icon} {issue.code}{path}: {issue.message}")

        return result

    # =============================================================================
    # Node Search & Query
    # =============================================================================

    def find_nodes(
        self, tree: TreeDefinition, predicate: Callable[[TreeNodeDefinition], bool]
    ) -> list[TreeNodeDefinition]:
        """Find all nodes matching a predicate function.

        Args:
            tree: Tree to search
            predicate: Function that returns True for matching nodes

        Returns:
            List of matching nodes

        Example:
            >>> # Find all Sequence nodes
            >>> sequences = tt.find_nodes(tree, lambda n: n.node_type == "Sequence")

            >>> # Find nodes with specific config
            >>> timeout_nodes = tt.find_nodes(
            >>>     tree,
            >>>     lambda n: n.node_type == "Timeout" and n.config.get("duration", 0) > 5
            >>> )
        """
        results = []

        def search(node: TreeNodeDefinition):
            if predicate(node):
                results.append(node)
            for child in node.children:
                search(child)

        search(tree.root)

        # Also search subtrees
        for subtree in tree.subtrees.values():
            search(subtree)

        return results

    def find_nodes_by_type(
        self, tree: TreeDefinition, node_type: str
    ) -> list[TreeNodeDefinition]:
        """Find all nodes of a specific type.

        Args:
            tree: Tree to search
            node_type: Node type to find (e.g., "Sequence", "Timeout")

        Returns:
            List of matching nodes

        Example:
            >>> timeouts = tt.find_nodes_by_type(tree, "Timeout")
            >>> print(f"Found {len(timeouts)} timeout decorators")
        """
        return self.find_nodes(tree, lambda n: n.node_type == node_type)

    def find_nodes_by_name(
        self, tree: TreeDefinition, name: str, exact: bool = True
    ) -> list[TreeNodeDefinition]:
        """Find nodes by name.

        Args:
            tree: Tree to search
            name: Node name to find
            exact: If True, match exactly; if False, match substring (case-insensitive)

        Returns:
            List of matching nodes

        Example:
            >>> # Find exact match
            >>> nodes = tt.find_nodes_by_name(tree, "CheckBattery")

            >>> # Find partial match
            >>> check_nodes = tt.find_nodes_by_name(tree, "check", exact=False)
        """
        if exact:
            return self.find_nodes(tree, lambda n: n.name == name)
        else:
            name_lower = name.lower()
            return self.find_nodes(tree, lambda n: name_lower in n.name.lower())

    def get_node_by_id(
        self, tree: TreeDefinition, node_id: UUID
    ) -> TreeNodeDefinition | None:
        """Find a node by its UUID.

        Args:
            tree: Tree to search
            node_id: UUID of node to find

        Returns:
            Node if found, None otherwise

        Example:
            >>> node = tt.get_node_by_id(tree, some_uuid)
            >>> if node:
            >>>     print(f"Found: {node.name} ({node.node_type})")
        """
        results = self.find_nodes(tree, lambda n: n.node_id == node_id)
        return results[0] if results else None

    def get_all_nodes(self, tree: TreeDefinition) -> list[TreeNodeDefinition]:
        """Get all nodes in a tree (including subtrees).

        Args:
            tree: Tree to traverse

        Returns:
            List of all nodes

        Example:
            >>> all_nodes = tt.get_all_nodes(tree)
            >>> print(f"Tree has {len(all_nodes)} nodes")
        """
        return self.find_nodes(tree, lambda _: True)

    # =============================================================================
    # Tree Statistics & Introspection
    # =============================================================================

    def get_tree_stats(self, tree: TreeDefinition) -> TreeStatistics:
        """Compute comprehensive statistics about a tree.

        Args:
            tree: Tree to analyze

        Returns:
            TreeStatistics object

        Example:
            >>> stats = tt.get_tree_stats(tree)
            >>> print(stats.summary())
            >>> print(f"Average depth: {stats.avg_depth:.2f}")
        """
        type_counts = defaultdict(int)
        category_counts = defaultdict(int)
        depths = []

        def analyze(node: TreeNodeDefinition, depth: int = 0):
            type_counts[node.node_type] += 1
            depths.append(depth)

            # Determine category from registry
            schema = self.registry.get_schema(node.node_type)
            if schema:
                category = schema.category.value
                category_counts[category] += 1
            else:
                category_counts["unknown"] += 1

            for child in node.children:
                analyze(child, depth + 1)

        analyze(tree.root)

        # Compute statistics
        node_count = len(depths)
        max_depth = max(depths) if depths else 0
        avg_depth = sum(depths) / len(depths) if depths else 0

        leaf_count = sum(
            count
            for node_type, count in type_counts.items()
            if self._is_leaf_type(node_type)
        )

        composite_count = category_counts.get("composite", 0)
        decorator_count = category_counts.get("decorator", 0)

        return TreeStatistics(
            node_count=node_count,
            max_depth=max_depth,
            avg_depth=avg_depth,
            type_distribution=dict(type_counts),
            category_distribution=dict(category_counts),
            leaf_count=leaf_count,
            composite_count=composite_count,
            decorator_count=decorator_count,
        )

    def _is_leaf_type(self, node_type: str) -> bool:
        """Check if a node type is a leaf (no children)."""
        schema = self.registry.get_schema(node_type)
        if schema:
            return schema.child_constraints.max_children == 0
        return False

    def print_tree_structure(
        self,
        tree: TreeDefinition,
        show_config: bool = False,
        max_depth: int | None = None,
    ):
        """Print a formatted tree structure.

        Args:
            tree: Tree to print
            show_config: Include node configuration
            max_depth: Maximum depth to print (None = unlimited)

        Example:
            >>> tt.print_tree_structure(tree, show_config=True, max_depth=3)
        """

        def print_node(node: TreeNodeDefinition, indent: int = 0, depth: int = 0):
            if max_depth is not None and depth > max_depth:
                return

            prefix = "  " * indent
            config_str = ""
            if show_config and node.config:
                config_str = f" {node.config}"

            print(f"{prefix}├─ {node.name} ({node.node_type}){config_str}")

            for child in node.children:
                print_node(child, indent + 1, depth + 1)

        print(f"\n{tree.metadata.name} (v{tree.metadata.version})")
        print("=" * 60)
        print_node(tree.root)

        if tree.subtrees:
            print(f"\nSubtrees: {len(tree.subtrees)}")
            for name in tree.subtrees:
                print(f"  - {name}")

    def count_nodes_by_type(self, tree: TreeDefinition) -> dict[str, int]:
        """Count nodes by type.

        Args:
            tree: Tree to analyze

        Returns:
            Dictionary mapping node type to count

        Example:
            >>> counts = tt.count_nodes_by_type(tree)
            >>> for node_type, count in sorted(counts.items()):
            >>>     print(f"{node_type}: {count}")
        """
        counts = defaultdict(int)

        for node in self.get_all_nodes(tree):
            counts[node.node_type] += 1

        return dict(counts)

    def get_node_path(self, tree: TreeDefinition, node_id: UUID) -> list[str] | None:
        """Get the path from root to a specific node.

        Args:
            tree: Tree to search
            node_id: UUID of target node

        Returns:
            List of node names from root to target, or None if not found

        Example:
            >>> path = tt.get_node_path(tree, some_node.node_id)
            >>> if path:
            >>>     print(" -> ".join(path))
        """

        def search(node: TreeNodeDefinition, path: list[str]) -> list[str] | None:
            current_path = path + [node.name]

            if node.node_id == node_id:
                return current_path

            for child in node.children:
                result = search(child, current_path)
                if result:
                    return result

            return None

        return search(tree.root, [])

    # =============================================================================
    # YAML Support
    # =============================================================================

    def load_yaml(self, path: str) -> TreeDefinition:
        """Load a tree from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            TreeDefinition object

        Raises:
            ImportError: If PyYAML is not installed

        Example:
            >>> tree = tt.load_yaml("examples/robot.yaml")
        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for YAML support. Install with: pip install pyyaml"
            )

        with open(path) as f:
            data = yaml.safe_load(f)

        return TreeDefinition.model_validate(data)

    def save_yaml(self, tree: TreeDefinition, path: str) -> None:
        """Save a tree to YAML file.

        Args:
            tree: TreeDefinition to save
            path: Output file path

        Raises:
            ImportError: If PyYAML is not installed

        Example:
            >>> tt.save_yaml(tree, "my_tree.yaml")
        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for YAML support. Install with: pip install pyyaml"
            )

        data = tree.model_dump(by_alias=True)

        with open(path, "w") as f:
            yaml.safe_dump(data, f, indent=2, default_flow_style=False, sort_keys=False)

    # =============================================================================
    # Batch Operations
    # =============================================================================

    def load_batch(self, paths: list[str]) -> dict[str, TreeDefinition]:
        """Load multiple trees from files.

        Args:
            paths: List of file paths (JSON or YAML)

        Returns:
            Dictionary mapping filename to TreeDefinition

        Example:
            >>> trees = tt.load_batch([
            >>>     "tree1.json",
            >>>     "tree2.yaml",
            >>>     "tree3.json"
            >>> ])
            >>> for name, tree in trees.items():
            >>>     print(f"{name}: {tree.metadata.name}")
        """
        results = {}

        for path in paths:
            file_path = Path(path)
            filename = file_path.stem

            if file_path.suffix.lower() in [".yaml", ".yml"]:
                results[filename] = self.load_yaml(str(path))
            else:
                results[filename] = self.load_tree(str(path))

        return results

    def validate_batch(
        self, trees: dict[str, TreeDefinition]
    ) -> dict[str, TreeValidationResult]:
        """Validate multiple trees.

        Args:
            trees: Dictionary of tree name to TreeDefinition

        Returns:
            Dictionary of tree name to validation result

        Example:
            >>> trees = tt.load_batch(["tree1.json", "tree2.json"])
            >>> results = tt.validate_batch(trees)
            >>> for name, result in results.items():
            >>>     print(f"{name}: {'✓' if result.is_valid else '✗'}")
        """
        return {name: self.validate_tree(tree) for name, tree in trees.items()}

    # =============================================================================
    # Tree Manipulation
    # =============================================================================

    def clone_tree(self, tree: TreeDefinition) -> TreeDefinition:
        """Create a deep copy of a tree.

        Args:
            tree: Tree to clone

        Returns:
            New TreeDefinition with same structure

        Example:
            >>> tree_copy = tt.clone_tree(original_tree)
            >>> tree_copy.metadata.name = "Copy of " + original_tree.metadata.name
        """
        return tree.model_copy(deep=True)

    def hash_tree(self, tree: TreeDefinition) -> str:
        """Compute a content hash of a tree for version comparison.

        The hash is based on the tree structure and configuration,
        not metadata (name, version, timestamps).

        Args:
            tree: Tree to hash

        Returns:
            SHA-256 hash hex string

        Example:
            >>> hash1 = tt.hash_tree(tree1)
            >>> hash2 = tt.hash_tree(tree2)
            >>> if hash1 == hash2:
            >>>     print("Trees are structurally identical")
        """
        # Check cache
        tree_id_str = str(tree.tree_id)
        if self.enable_cache and tree_id_str in self._tree_hash_cache:
            return self._tree_hash_cache[tree_id_str]

        # Serialize only the structure (exclude metadata)
        def serialize_node(node: TreeNodeDefinition) -> dict:
            return {
                "node_type": node.node_type,
                "config": node.config,
                "children": [serialize_node(child) for child in node.children],
                "ref": node.ref,
            }

        structure = {
            "root": serialize_node(tree.root),
            "subtrees": {
                name: serialize_node(subtree) for name, subtree in tree.subtrees.items()
            },
        }

        # Compute hash
        content_str = json.dumps(structure, sort_keys=True, default=str)
        content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

        # Cache result
        if self.enable_cache:
            self._tree_hash_cache[tree_id_str] = content_hash

        return content_hash

    def trees_equal(self, tree1: TreeDefinition, tree2: TreeDefinition) -> bool:
        """Check if two trees are structurally identical.

        Args:
            tree1: First tree
            tree2: Second tree

        Returns:
            True if trees have identical structure

        Example:
            >>> if tt.trees_equal(tree1, tree2):
            >>>     print("Trees are identical")
        """
        return self.hash_tree(tree1) == self.hash_tree(tree2)

    def get_subtree(self, tree: TreeDefinition, node_id: UUID) -> TreeDefinition | None:
        """Extract a subtree starting from a specific node.

        Args:
            tree: Source tree
            node_id: UUID of node to use as new root

        Returns:
            New TreeDefinition with node as root, or None if not found

        Example:
            >>> # Extract a subtree to test independently
            >>> subtree = tt.get_subtree(tree, some_composite.node_id)
            >>> if subtree:
            >>>     result = tt.create_execution(subtree).tick()
        """
        node = self.get_node_by_id(tree, node_id)
        if not node:
            return None

        # Create new metadata
        new_metadata = TreeMetadata(
            name=f"Subtree: {node.name}",
            version="1.0.0",
            description=f"Extracted from {tree.metadata.name}",
        )

        # Create new tree with node as root
        from uuid import uuid4

        return TreeDefinition(
            tree_id=uuid4(),
            metadata=new_metadata,
            root=node,
        )


class Execution:
    """Represents a running execution of a behavior tree.

    Provides simple interface for ticking and inspecting state.
    """

    def __init__(
        self,
        tree_def: TreeDefinition,
        py_tree: py_trees.trees.BehaviourTree,
        serializer: TreeSerializer,
        profiling_level: ProfilingLevel,
        profiler: TreeProfiler | None,
    ):
        """Initialize execution.

        Args:
            tree_def: Tree definition
            py_tree: Instantiated py_trees object
            serializer: Serializer with UUID mappings
            profiling_level: Profiling level
            profiler: Optional profiler instance
        """
        self.tree_def = tree_def
        self.py_tree = py_tree
        self.serializer = serializer
        self.profiling_level = profiling_level
        self.profiler = profiler

        # Start profiling if enabled
        if self.profiler:
            self.profiler.start_profiling(str(tree_def.tree_id), tree_def.tree_id)

    def tick(
        self,
        count: int = 1,
        blackboard_updates: dict[str, Any] | None = None,
    ) -> "TickResult":
        """Tick the tree.

        Args:
            count: Number of ticks to execute
            blackboard_updates: Sensor values to update before ticking

        Returns:
            TickResult with status and blackboard state

        Example:
            result = execution.tick(blackboard_updates={
                "battery_level": 15,
                "object_distance": 3.5
            })

            print(f"Status: {result.status}")
            print(f"Action: {result.blackboard.get('/robot_action')}")
        """
        # Apply blackboard updates
        if blackboard_updates:
            bb = py_trees.blackboard.Client(name="ExternalSensor")
            for key, value in blackboard_updates.items():
                try:
                    bb.register_key(key=key, access=py_trees.common.Access.WRITE)
                    bb.set(key, value, overwrite=True)
                except Exception:
                    try:
                        bb.set(key, value, overwrite=True)
                    except Exception as e:
                        print(f"Warning: Could not set {key}: {e}")

        # Profile if enabled
        if self.profiler:
            root_uuid = self.serializer.get_node_uuid(self.py_tree.root)
            if root_uuid:
                self.profiler.before_tick(self.py_tree.root, root_uuid)

        # Tick
        for _ in range(count):
            self.py_tree.tick()

        # Profile end
        if self.profiler:
            if root_uuid:
                self.profiler.after_tick(
                    self.py_tree.root, root_uuid, self.py_tree.root.status
                )
            self.profiler.on_tick_complete()

        # Get blackboard state
        bb = py_trees.blackboard.Blackboard()
        blackboard_dict = {}
        for key in bb.keys():
            try:
                blackboard_dict[key] = bb.get(key)
            except KeyError:
                pass

        return TickResult(
            status=self.py_tree.root.status.value,
            tick_count=self.py_tree.count,
            blackboard=Blackboard(blackboard_dict),
            tip_node=self.py_tree.tip().name if self.py_tree.tip() else None,
        )

    def get_profiling_report(self, verbose: bool = False) -> str | None:
        """Get profiling report if profiling is enabled.

        Args:
            verbose: Include detailed per-node stats

        Returns:
            Formatted profiling report or None

        Example:
            # Run some ticks
            for i in range(100):
                execution.tick(blackboard_updates={"battery": 50 + i})

            # Get performance report
            report = execution.get_profiling_report(verbose=True)
            print(report)
        """
        if not self.profiler:
            return None

        report = self.profiler.stop_profiling(str(self.tree_def.tree_id))
        return format_profile_report(report, verbose=verbose)

    def get_tree_display(self) -> str:
        """Get ASCII tree visualization.

        Returns:
            ASCII representation of tree structure

        Example:
            print(execution.get_tree_display())
        """
        return py_trees.display.unicode_tree(
            self.py_tree.root,
            show_status=True,
        )


class Blackboard:
    """Wrapper around blackboard for convenient access."""

    def __init__(self, data: dict[str, Any]):
        """Initialize with blackboard data.

        Args:
            data: Dictionary of blackboard values
        """
        self._data = data

    def get(self, key: str, default: Any = None) -> Any:
        """Get a blackboard value.

        Args:
            key: Blackboard key (with or without leading slash)
            default: Default value if key not found

        Returns:
            Value or default
        """
        # Try with and without leading slash
        if key in self._data:
            return self._data[key]

        clean_key = key.lstrip("/")
        if clean_key in self._data:
            return self._data[clean_key]

        slash_key = f"/{key.lstrip('/')}"
        if slash_key in self._data:
            return self._data[slash_key]

        return default

    def keys(self) -> list[str]:
        """Get all blackboard keys.

        Returns:
            List of keys
        """
        return list(self._data.keys())

    def items(self) -> list[tuple]:
        """Get all blackboard items.

        Returns:
            List of (key, value) tuples
        """
        return list(self._data.items())

    def __repr__(self) -> str:
        """String representation."""
        return f"Blackboard({self._data})"


class TickResult:
    """Result of a tree tick operation."""

    def __init__(
        self,
        status: str,
        tick_count: int,
        blackboard: Blackboard,
        tip_node: str | None,
    ):
        """Initialize tick result.

        Args:
            status: Root node status
            tick_count: Total ticks executed
            blackboard: Blackboard state
            tip_node: Name of tip node (currently executing)
        """
        self.status = status
        self.tick_count = tick_count
        self.blackboard = blackboard
        self.tip_node = tip_node

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TickResult(status={self.status}, "
            f"tick_count={self.tick_count}, "
            f"tip={self.tip_node})"
        )


# Convenience functions for quick usage


def load_and_run(
    tree_path: str,
    blackboard_updates: dict[str, Any],
    ticks: int = 1,
) -> TickResult:
    """Quick function to load a tree and run it.

    Args:
        tree_path: Path to tree JSON file
        blackboard_updates: Initial blackboard values
        ticks: Number of ticks to run

    Returns:
        TickResult

    Example:
        result = load_and_run(
            "robot.json",
            {"battery_level": 15, "distance": 999},
            ticks=1
        )
        print(f"Robot action: {result.blackboard.get('/robot_action')}")
    """
    tt = TalkingTrees()
    tree = tt.load_tree(tree_path)
    execution = tt.create_execution(tree)
    return execution.tick(count=ticks, blackboard_updates=blackboard_updates)


def diff_files(old_path: str, new_path: str) -> str:
    """Quick function to diff two tree files.

    Args:
        old_path: Path to old tree JSON
        new_path: Path to new tree JSON

    Returns:
        Formatted diff string

    Example:
        diff = diff_files("robot_v1.json", "robot_v2.json")
        print(diff)
    """
    tt = TalkingTrees()
    old_tree = tt.load_tree(old_path)
    new_tree = tt.load_tree(new_path)
    return tt.diff_trees(old_tree, new_tree, verbose=True)


def quick_validate(tree_path: str) -> TreeValidationResult:
    """Quick function to validate a tree file.

    Args:
        tree_path: Path to tree file

    Returns:
        Validation result

    Example:
        >>> result = quick_validate("robot.json")
        >>> if result.is_valid:
        >>>     print("✓ Tree is valid")
    """
    tt = TalkingTrees()
    tree = tt.load_tree(tree_path)
    return tt.validate_tree(tree, verbose=True)


def compare_tree_structures(path1: str, path2: str) -> bool:
    """Quick function to compare if two trees are structurally identical.

    Args:
        path1: Path to first tree
        path2: Path to second tree

    Returns:
        True if trees are identical

    Example:
        >>> if compare_tree_structures("v1.json", "v2.json"):
        >>>     print("Trees are identical")
        >>> else:
        >>>     print("Trees differ")
    """
    tt = TalkingTrees()
    tree1 = tt.load_tree(path1)
    tree2 = tt.load_tree(path2)
    return tt.trees_equal(tree1, tree2)


def analyze_tree(tree_path: str) -> str:
    """Quick function to get complete tree analysis.

    Args:
        tree_path: Path to tree file

    Returns:
        Formatted analysis report

    Example:
        >>> report = analyze_tree("robot.json")
        >>> print(report)
    """
    tt = TalkingTrees()
    tree = tt.load_tree(tree_path)

    # Validate
    validation = tt.validate_tree(tree)

    # Get statistics
    stats = tt.get_tree_stats(tree)

    # Format report
    lines = [
        f"Analysis of: {tree.metadata.name} (v{tree.metadata.version})",
        "=" * 70,
        "",
        "VALIDATION:",
        f"  Status: {'✓ VALID' if validation.is_valid else '✗ INVALID'}",
        f"  Errors: {validation.error_count}",
        f"  Warnings: {validation.warning_count}",
        "",
        stats.summary(),
    ]

    return "\n".join(lines)
