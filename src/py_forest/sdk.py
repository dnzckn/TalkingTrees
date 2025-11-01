"""High-level Python SDK for PyForest - use without API server.

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

import json
import hashlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID
from functools import lru_cache
from collections import defaultdict

import py_trees

from py_forest.core.diff import TreeDiffer, TreeMerger, format_diff_as_text
from py_forest.core.execution import ExecutionInstance
from py_forest.core.profiler import (
    ProfilingLevel,
    TreeProfiler,
    format_profile_report,
    get_profiler,
)
from py_forest.core.serializer import TreeSerializer
from py_forest.core.registry import get_registry
from py_forest.core.validation import TreeValidator
from py_forest.models.execution import ExecutionConfig, ExecutionMode
from py_forest.models.tree import TreeDefinition, TreeNodeDefinition, TreeMetadata
from py_forest.models.validation import TreeValidationResult, ValidationLevel

# Import adapter functions for py_trees integration
try:
    from py_forest.adapters import from_py_trees, to_py_trees
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
        type_distribution: Dict[str, int],
        category_distribution: Dict[str, int],
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


class PyForest:
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
        pf = PyForest()
        tree = pf.load_tree("my_tree.json")

        # Validate before running
        validation = pf.validate_tree(tree)
        if not validation.is_valid:
            print("Tree has errors!")
            return

        # Search for nodes
        timeouts = pf.find_nodes_by_type(tree, "Timeout")

        # Get statistics
        stats = pf.get_tree_stats(tree)
        print(stats.summary())

        # Execute
        execution = pf.create_execution(tree)
        result = execution.tick(blackboard_updates={
            "battery_level": 15,
            "distance": 3.5
        })

        # Read outputs
        action = result.blackboard.get("/robot_action")
        print(f"Robot should: {action}")
    """

    def __init__(self, profiling_level: ProfilingLevel = ProfilingLevel.OFF, enable_cache: bool = True):
        """Initialize PyForest SDK.

        Args:
            profiling_level: Default profiling level for executions
            enable_cache: Enable caching for repeated operations (e.g., tree hashes)
        """
        self.profiling_level = profiling_level
        self.profiler = get_profiler(profiling_level) if profiling_level != ProfilingLevel.OFF else None
        self.registry = get_registry()
        self.validator = TreeValidator(self.registry)
        self.enable_cache = enable_cache
        self._tree_hash_cache: Dict[str, str] = {}

    def load_tree(self, path: str) -> TreeDefinition:
        """Load a tree from JSON file.

        Args:
            path: Path to JSON file exported from editor

        Returns:
            TreeDefinition object

        Example:
            tree = pf.load_tree("examples/robot_v1.json")
        """
        with open(path, 'r') as f:
            data = json.load(f)

        return TreeDefinition.model_validate(data)

    def save_tree(self, tree: TreeDefinition, path: str) -> None:
        """Save a tree to JSON file.

        Args:
            tree: TreeDefinition to save
            path: Output file path

        Example:
            pf.save_tree(tree, "my_tree.json")
        """
        with open(path, 'w') as f:
            json.dump(tree.model_dump(by_alias=True), f, indent=2, default=str)

    def create_execution(
        self,
        tree: TreeDefinition,
        initial_blackboard: Optional[Dict[str, Any]] = None,
        profiling_level: Optional[ProfilingLevel] = None,
    ) -> 'Execution':
        """Create an execution from a tree definition.

        Args:
            tree: TreeDefinition to execute
            initial_blackboard: Initial blackboard values
            profiling_level: Override default profiling level

        Returns:
            Execution object for running the tree

        Example:
            execution = pf.create_execution(tree, initial_blackboard={
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
        profiling = profiling_level if profiling_level is not None else self.profiling_level

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
            tree_v1 = pf.load_tree("robot_v1.json")
            tree_v2 = pf.load_tree("robot_v2.json")
            diff = pf.diff_trees(tree_v1, tree_v2)
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
        description: str = "Converted from py_trees"
    ) -> TreeDefinition:
        """Convert a py_trees tree to PyForest format.

        This allows you to create trees using py_trees API, then visualize
        and run them with PyForest tools.

        Args:
            root: Root node of py_trees tree
            name: Name for the PyForest tree
            version: Version string
            description: Description

        Returns:
            TreeDefinition compatible with PyForest

        Example:
            import py_trees
            from py_forest.sdk import PyForest

            # Create tree with py_trees
            root = py_trees.composites.Sequence("MySequence")
            root.add_child(py_trees.behaviours.Success("Step1"))

            # Convert to PyForest
            pf = PyForest()
            tree = pf.from_py_trees(root, name="My Tree")

            # Save for editor
            pf.save_tree(tree, "my_tree.json")
        """
        if from_py_trees is None:
            raise ImportError("py_trees adapter not available. Install py_forest.adapters")

        tree_def, context = from_py_trees(root, name=name, version=version, description=description)
        return tree_def

    # =============================================================================
    # Validation
    # =============================================================================

    def validate_tree(self, tree: TreeDefinition, verbose: bool = False) -> TreeValidationResult:
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
            >>> result = pf.validate_tree(tree)
            >>> if not result.is_valid:
            >>>     for issue in result.issues:
            >>>         print(f"{issue.level}: {issue.message}")
        """
        result = self.validator.validate(tree)

        if verbose:
            print(f"\nValidation Result: {'✓ VALID' if result.is_valid else '✗ INVALID'}")
            print(f"Errors: {result.error_count}, Warnings: {result.warning_count}, Info: {result.info_count}")

            if result.issues:
                print("\nIssues:")
                for issue in result.issues:
                    level_icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}[issue.level.value]
                    path = f" [{issue.node_path}]" if issue.node_path else ""
                    print(f"  {level_icon} {issue.code}{path}: {issue.message}")

        return result

    # =============================================================================
    # Node Search & Query
    # =============================================================================

    def find_nodes(
        self,
        tree: TreeDefinition,
        predicate: Callable[[TreeNodeDefinition], bool]
    ) -> List[TreeNodeDefinition]:
        """Find all nodes matching a predicate function.

        Args:
            tree: Tree to search
            predicate: Function that returns True for matching nodes

        Returns:
            List of matching nodes

        Example:
            >>> # Find all Sequence nodes
            >>> sequences = pf.find_nodes(tree, lambda n: n.node_type == "Sequence")

            >>> # Find nodes with specific config
            >>> timeout_nodes = pf.find_nodes(
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

    def find_nodes_by_type(self, tree: TreeDefinition, node_type: str) -> List[TreeNodeDefinition]:
        """Find all nodes of a specific type.

        Args:
            tree: Tree to search
            node_type: Node type to find (e.g., "Sequence", "Timeout")

        Returns:
            List of matching nodes

        Example:
            >>> timeouts = pf.find_nodes_by_type(tree, "Timeout")
            >>> print(f"Found {len(timeouts)} timeout decorators")
        """
        return self.find_nodes(tree, lambda n: n.node_type == node_type)

    def find_nodes_by_name(self, tree: TreeDefinition, name: str, exact: bool = True) -> List[TreeNodeDefinition]:
        """Find nodes by name.

        Args:
            tree: Tree to search
            name: Node name to find
            exact: If True, match exactly; if False, match substring (case-insensitive)

        Returns:
            List of matching nodes

        Example:
            >>> # Find exact match
            >>> nodes = pf.find_nodes_by_name(tree, "CheckBattery")

            >>> # Find partial match
            >>> check_nodes = pf.find_nodes_by_name(tree, "check", exact=False)
        """
        if exact:
            return self.find_nodes(tree, lambda n: n.name == name)
        else:
            name_lower = name.lower()
            return self.find_nodes(tree, lambda n: name_lower in n.name.lower())

    def get_node_by_id(self, tree: TreeDefinition, node_id: UUID) -> Optional[TreeNodeDefinition]:
        """Find a node by its UUID.

        Args:
            tree: Tree to search
            node_id: UUID of node to find

        Returns:
            Node if found, None otherwise

        Example:
            >>> node = pf.get_node_by_id(tree, some_uuid)
            >>> if node:
            >>>     print(f"Found: {node.name} ({node.node_type})")
        """
        results = self.find_nodes(tree, lambda n: n.node_id == node_id)
        return results[0] if results else None

    def get_all_nodes(self, tree: TreeDefinition) -> List[TreeNodeDefinition]:
        """Get all nodes in a tree (including subtrees).

        Args:
            tree: Tree to traverse

        Returns:
            List of all nodes

        Example:
            >>> all_nodes = pf.get_all_nodes(tree)
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
            >>> stats = pf.get_tree_stats(tree)
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
            count for node_type, count in type_counts.items()
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

    def print_tree_structure(self, tree: TreeDefinition, show_config: bool = False, max_depth: Optional[int] = None):
        """Print a formatted tree structure.

        Args:
            tree: Tree to print
            show_config: Include node configuration
            max_depth: Maximum depth to print (None = unlimited)

        Example:
            >>> pf.print_tree_structure(tree, show_config=True, max_depth=3)
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

    def count_nodes_by_type(self, tree: TreeDefinition) -> Dict[str, int]:
        """Count nodes by type.

        Args:
            tree: Tree to analyze

        Returns:
            Dictionary mapping node type to count

        Example:
            >>> counts = pf.count_nodes_by_type(tree)
            >>> for node_type, count in sorted(counts.items()):
            >>>     print(f"{node_type}: {count}")
        """
        counts = defaultdict(int)

        for node in self.get_all_nodes(tree):
            counts[node.node_type] += 1

        return dict(counts)

    def get_node_path(self, tree: TreeDefinition, node_id: UUID) -> Optional[List[str]]:
        """Get the path from root to a specific node.

        Args:
            tree: Tree to search
            node_id: UUID of target node

        Returns:
            List of node names from root to target, or None if not found

        Example:
            >>> path = pf.get_node_path(tree, some_node.node_id)
            >>> if path:
            >>>     print(" -> ".join(path))
        """
        def search(node: TreeNodeDefinition, path: List[str]) -> Optional[List[str]]:
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
            >>> tree = pf.load_yaml("examples/robot.yaml")
        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for YAML support. "
                "Install with: pip install pyyaml"
            )

        with open(path, 'r') as f:
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
            >>> pf.save_yaml(tree, "my_tree.yaml")
        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for YAML support. "
                "Install with: pip install pyyaml"
            )

        data = tree.model_dump(by_alias=True)

        with open(path, 'w') as f:
            yaml.safe_dump(data, f, indent=2, default_flow_style=False, sort_keys=False)

    # =============================================================================
    # Batch Operations
    # =============================================================================

    def load_batch(self, paths: List[str]) -> Dict[str, TreeDefinition]:
        """Load multiple trees from files.

        Args:
            paths: List of file paths (JSON or YAML)

        Returns:
            Dictionary mapping filename to TreeDefinition

        Example:
            >>> trees = pf.load_batch([
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

            if file_path.suffix.lower() in ['.yaml', '.yml']:
                results[filename] = self.load_yaml(str(path))
            else:
                results[filename] = self.load_tree(str(path))

        return results

    def validate_batch(self, trees: Dict[str, TreeDefinition]) -> Dict[str, TreeValidationResult]:
        """Validate multiple trees.

        Args:
            trees: Dictionary of tree name to TreeDefinition

        Returns:
            Dictionary of tree name to validation result

        Example:
            >>> trees = pf.load_batch(["tree1.json", "tree2.json"])
            >>> results = pf.validate_batch(trees)
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
            >>> tree_copy = pf.clone_tree(original_tree)
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
            >>> hash1 = pf.hash_tree(tree1)
            >>> hash2 = pf.hash_tree(tree2)
            >>> if hash1 == hash2:
            >>>     print("Trees are structurally identical")
        """
        # Check cache
        tree_id_str = str(tree.tree_id)
        if self.enable_cache and tree_id_str in self._tree_hash_cache:
            return self._tree_hash_cache[tree_id_str]

        # Serialize only the structure (exclude metadata)
        def serialize_node(node: TreeNodeDefinition) -> Dict:
            return {
                "node_type": node.node_type,
                "config": node.config,
                "children": [serialize_node(child) for child in node.children],
                "ref": node.ref,
            }

        structure = {
            "root": serialize_node(tree.root),
            "subtrees": {
                name: serialize_node(subtree)
                for name, subtree in tree.subtrees.items()
            },
        }

        # Compute hash
        content_str = json.dumps(structure, sort_keys=True, default=str)
        content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()

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
            >>> if pf.trees_equal(tree1, tree2):
            >>>     print("Trees are identical")
        """
        return self.hash_tree(tree1) == self.hash_tree(tree2)

    def get_subtree(self, tree: TreeDefinition, node_id: UUID) -> Optional[TreeDefinition]:
        """Extract a subtree starting from a specific node.

        Args:
            tree: Source tree
            node_id: UUID of node to use as new root

        Returns:
            New TreeDefinition with node as root, or None if not found

        Example:
            >>> # Extract a subtree to test independently
            >>> subtree = pf.get_subtree(tree, some_composite.node_id)
            >>> if subtree:
            >>>     result = pf.create_execution(subtree).tick()
        """
        node = self.get_node_by_id(tree, node_id)
        if not node:
            return None

        # Create new metadata
        new_metadata = TreeMetadata(
            name=f"Subtree: {node.name}",
            version="1.0.0",
            description=f"Extracted from {tree.metadata.name}"
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
        profiler: Optional[TreeProfiler],
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
            self.profiler.start_profiling(
                str(tree_def.tree_id),
                tree_def.tree_id
            )

    def tick(
        self,
        count: int = 1,
        blackboard_updates: Optional[Dict[str, Any]] = None,
    ) -> 'TickResult':
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
                    self.py_tree.root,
                    root_uuid,
                    self.py_tree.root.status
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

    def get_profiling_report(self, verbose: bool = False) -> Optional[str]:
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

    def __init__(self, data: Dict[str, Any]):
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

    def keys(self) -> List[str]:
        """Get all blackboard keys.

        Returns:
            List of keys
        """
        return list(self._data.keys())

    def items(self) -> List[tuple]:
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
        tip_node: Optional[str],
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
    blackboard_updates: Dict[str, Any],
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
    pf = PyForest()
    tree = pf.load_tree(tree_path)
    execution = pf.create_execution(tree)
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
    pf = PyForest()
    old_tree = pf.load_tree(old_path)
    new_tree = pf.load_tree(new_path)
    return pf.diff_trees(old_tree, new_tree, verbose=True)


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
    pf = PyForest()
    tree = pf.load_tree(tree_path)
    return pf.validate_tree(tree, verbose=True)


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
    pf = PyForest()
    tree1 = pf.load_tree(path1)
    tree2 = pf.load_tree(path2)
    return pf.trees_equal(tree1, tree2)


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
    pf = PyForest()
    tree = pf.load_tree(tree_path)

    # Validate
    validation = pf.validate_tree(tree)

    # Get statistics
    stats = pf.get_tree_stats(tree)

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
