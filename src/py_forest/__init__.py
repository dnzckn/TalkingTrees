"""
PyForest - Serializable behavior trees with REST API.

Built on py_trees with added features:
- Tree library management with versioning
- JSON/YAML serialization for visual editors
- REST API for remote execution
- Behavior registry for custom nodes
- Comprehensive SDK with validation, search, and analysis

Quick Start:
    from py_forest.sdk import PyForest

    pf = PyForest()
    tree = pf.load_tree("my_tree.json")

    # Validate before running
    validation = pf.validate_tree(tree)
    if not validation.is_valid:
        print("Tree has errors!")
        return

    # Search nodes
    timeouts = pf.find_nodes_by_type(tree, "Timeout")

    # Get statistics
    stats = pf.get_tree_stats(tree)
    print(stats.summary())

    # Execute
    execution = pf.create_execution(tree)
    result = execution.tick(blackboard_updates={"battery": 75})
"""

__version__ = "0.1.0"

from py_forest.core.registry import BehaviorRegistry
from py_forest.models.tree import TreeDefinition, TreeNodeDefinition
from py_forest.models.execution import ExecutionSnapshot, ExecutionConfig

# Import SDK
from py_forest.sdk import PyForest

__all__ = [
    # Core classes
    "BehaviorRegistry",
    "TreeDefinition",
    "TreeNodeDefinition",
    "ExecutionSnapshot",
    "ExecutionConfig",
    # SDK
    "PyForest",
]
