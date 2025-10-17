"""High-level Python SDK for PyForest - use without API server.

This module provides simple interfaces for:
- Loading trees from JSON
- Running executions
- Debugging and profiling
- Comparing tree versions
- Converting from/to py_trees

Perfect for Jupyter notebooks, scripts, and experimentation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

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
from py_forest.models.execution import ExecutionConfig, ExecutionMode
from py_forest.models.tree import TreeDefinition

# Import adapter functions for py_trees integration
try:
    from py_forest.adapters import from_py_trees, to_py_trees
except ImportError:
    # Adapters not available
    from_py_trees = None
    to_py_trees = None


class PyForest:
    """Simple interface for working with behavior trees in Python.

    Usage:
        # Load and run a tree
        pf = PyForest()
        tree = pf.load_tree("my_tree.json")
        execution = pf.create_execution(tree)

        # Tick with sensor updates
        result = execution.tick(blackboard_updates={
            "battery_level": 15,
            "distance": 3.5
        })

        # Read outputs
        action = result.blackboard.get("/robot_action")
        print(f"Robot should: {action}")
    """

    def __init__(self, profiling_level: ProfilingLevel = ProfilingLevel.OFF):
        """Initialize PyForest SDK.

        Args:
            profiling_level: Default profiling level for executions
        """
        self.profiling_level = profiling_level
        self.profiler = get_profiler(profiling_level) if profiling_level != ProfilingLevel.OFF else None

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
