"""
TalkingTrees - Serializable behavior trees with REST API.

Built on py_trees with added features:
- Tree library management with versioning
- JSON/YAML serialization for visual editors
- REST API for remote execution
- Behavior registry for custom nodes
- Comprehensive SDK with validation, search, and analysis

Quick Start:
    from talking_trees.sdk import TalkingTrees

    tt = TalkingTrees()
    tree = tt.load_tree("my_tree.json")

    # Validate before running
    validation = tt.validate_tree(tree)
    if not validation.is_valid:
        print("Tree has errors!")
        return

    # Search nodes
    timeouts = tt.find_nodes_by_type(tree, "Timeout")

    # Get statistics
    stats = tt.get_tree_stats(tree)
    print(stats.summary())

    # Execute
    execution = tt.create_execution(tree)
    result = execution.tick(blackboard_updates={"battery": 75})
"""

__version__ = "0.1.0"

from talking_trees.core.registry import BehaviorRegistry
from talking_trees.models.execution import ExecutionConfig, ExecutionSnapshot
from talking_trees.models.tree import TreeDefinition, TreeNodeDefinition

# Import SDK
from talking_trees.sdk import TalkingTrees

__all__ = [
    # Core classes
    "BehaviorRegistry",
    "TreeDefinition",
    "TreeNodeDefinition",
    "ExecutionSnapshot",
    "ExecutionConfig",
    # SDK
    "TalkingTrees",
]
