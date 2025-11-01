"""
py_trees Adapter
================

Converts between py_trees behavior trees and TalkingTrees format.

This allows you to:
1. Create trees using py_trees (programmatic Python)
2. Convert to TalkingTrees format
3. Visualize in TalkingTrees editor
4. Save/load as JSON
5. Run via TalkingTrees SDK or REST API

Example:
    import py_trees
    from talking_trees.adapters import from_py_trees

    # Create tree with py_trees
    root = py_trees.composites.Sequence("MySequence", memory=False)
    root.add_child(py_trees.behaviours.Success("Step1"))
    root.add_child(py_trees.behaviours.Success("Step2"))

    # Convert to TalkingTrees
    tt_tree, context = from_py_trees(root, name="My Tree", version="1.0.0")

    # Now use with TalkingTrees SDK
    from talking_trees.sdk import TalkingTrees
    pf = TalkingTrees()
    pf.save_tree(tt_tree, "my_tree.json")
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from talking_trees.core.utils import string_to_operator
from talking_trees.models.tree import (
    TreeDefinition,
    TreeDependencies,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)

# =============================================================================
# Conversion Context (Warnings)
# =============================================================================


class ConversionContext:
    """
    Tracks warnings and issues during py_trees → TalkingTrees conversion.

    Provides visibility into data loss, fallbacks, and other conversion issues.
    """

    def __init__(self):
        self.warnings: list[str] = []

    def warn(self, message: str, node_name: str | None = None):
        """
        Add a warning message.

        Args:
            message: Warning description
            node_name: Optional node name for context
        """
        if node_name:
            full_message = f"[{node_name}] {message}"
        else:
            full_message = message

        self.warnings.append(full_message)

    def has_warnings(self) -> bool:
        """Check if any warnings were recorded."""
        return len(self.warnings) > 0

    def summary(self) -> str:
        """Get a formatted summary of all warnings."""
        if not self.warnings:
            return "✓ No conversion warnings"

        lines = [f"⚠ {len(self.warnings)} conversion warning(s):"]
        for i, warning in enumerate(self.warnings, 1):
            lines.append(f"  {i}. {warning}")

        return "\n".join(lines)


# =============================================================================
# Deterministic UUID Generation
# =============================================================================


# UUID generation moved to core/utils.py - import from there
from talking_trees.core.utils import generate_deterministic_uuid as _generate_deterministic_uuid


# =============================================================================
# ComparisonExpression Abstraction
# =============================================================================


class ComparisonExpressionExtractor:
    """
    Safely extract comparison data from py_trees ComparisonExpression.

    Handles py_trees' non-intuitive attribute naming where:
    - .operator actually contains the comparison VALUE
    - .value actually contains the operator FUNCTION

    This abstraction layer makes the code clearer and less error-prone.
    """

    @staticmethod
    def extract(check) -> dict:
        """
        Extract comparison data from py_trees ComparisonExpression.

        Args:
            check: py_trees ComparisonExpression instance

        Returns:
            Dict with 'variable', 'comparison_value', 'operator_function'
        """
        return {
            "variable": check.variable,
            "comparison_value": check.operator,  # Yes, py_trees swaps these!
            "operator_function": check.value,  # Yes, py_trees swaps these!
        }

    @staticmethod
    def create(variable: str, operator_func, value: Any):
        """
        Create ComparisonExpression with clear parameter names.

        Args:
            variable: Blackboard variable name
            operator_func: Comparison operator (from operator module)
            value: Value to compare against

        Returns:
            ComparisonExpression instance
        """
        from py_trees.common import ComparisonExpression

        # NOTE: ComparisonExpression signature is (variable, value, operator)
        return ComparisonExpression(variable, value, operator_func)


# =============================================================================
# Node Type Mapping
# =============================================================================

# Maps py_trees node types to TalkingTrees node types
NODE_TYPE_MAP = {
    # Composites
    "Sequence": "Sequence",
    "Selector": "Selector",
    "Parallel": "Parallel",
    # Decorators - Status Converters
    "Inverter": "Inverter",
    "SuccessIsFailure": "SuccessIsFailure",
    "FailureIsSuccess": "FailureIsSuccess",
    "FailureIsRunning": "FailureIsRunning",
    "RunningIsFailure": "RunningIsFailure",
    "RunningIsSuccess": "RunningIsSuccess",
    "SuccessIsRunning": "SuccessIsRunning",
    # Decorators - Repetition
    "Repeat": "Repeat",
    "Retry": "Retry",
    "OneShot": "OneShot",
    # Decorators - Time-based
    "Timeout": "Timeout",
    # Decorators - Advanced
    "EternalGuard": "EternalGuard",
    "Condition": "Condition",
    "Count": "Count",
    "StatusToBlackboard": "StatusToBlackboard",
    "PassThrough": "PassThrough",
    # Basic Behaviors
    "Success": "Success",
    "Failure": "Failure",
    "Running": "Running",
    "Dummy": "Dummy",
    # Time-based Behaviors
    "TickCounter": "TickCounter",
    "Periodic": "Periodic",
    "SuccessEveryN": "SuccessEveryN",
    "StatusQueue": "StatusQueue",
    # Blackboard Behaviors - Non-blocking
    "CheckBlackboardVariable": "CheckBlackboardCondition",
    "CheckBlackboardVariableExists": "CheckBlackboardVariableExists",
    "CheckBlackboardVariableValue": "CheckBlackboardCondition",
    "CheckBlackboardVariableValues": "CheckBlackboardVariableValues",
    "SetBlackboardVariable": "SetBlackboardVariable",
    "UnsetBlackboardVariable": "UnsetBlackboardVariable",
    "BlackboardToStatus": "BlackboardToStatus",
    # Blackboard Behaviors - Blocking
    "WaitForBlackboardVariable": "WaitForBlackboardVariable",
    "WaitForBlackboardVariableValue": "WaitForBlackboardVariableValue",
    # Probabilistic
    "ProbabilisticBehaviour": "ProbabilisticBehaviour",
}


def _get_node_type(py_trees_node, context: ConversionContext | None = None) -> str:
    """Determine TalkingTrees node type from py_trees node"""
    class_name = type(py_trees_node).__name__

    # Check direct mapping
    if class_name in NODE_TYPE_MAP:
        return NODE_TYPE_MAP[class_name]

    # Check base classes
    import py_trees

    if isinstance(py_trees_node, py_trees.composites.Sequence):
        return "Sequence"
    elif isinstance(py_trees_node, py_trees.composites.Selector):
        return "Selector"
    elif isinstance(py_trees_node, py_trees.composites.Parallel):
        return "Parallel"
    elif isinstance(py_trees_node, py_trees.decorators.Decorator):
        return "Decorator"
    elif isinstance(py_trees_node, py_trees.behaviour.Behaviour):
        # Default behavior nodes to action
        if context:
            context.warn(
                f"Unknown node type '{class_name}', defaulting to Action",
                node_name=py_trees_node.name,
            )
        return "Action"

    # Default fallback
    if context:
        context.warn(
            f"Unrecognized py_trees class '{class_name}', defaulting to Action",
            node_name=py_trees_node.name,
        )
    return "Action"


def _extract_config(
    py_trees_node, context: ConversionContext | None = None
) -> dict[str, Any]:
    """Extract config from py_trees node to TalkingTrees format.

    This function now uses the extractor registry pattern instead of
    a large if/elif chain. Each node type has a dedicated extractor
    in core/extractors.py that knows how to extract its configuration.
    """
    from talking_trees.core.extractors import extract_config

    return extract_config(py_trees_node, context)


def _convert_node(
    py_trees_node,
    parent_path: str = "",
    use_deterministic_uuids: bool = True,
    context: ConversionContext | None = None,
) -> TreeNodeDefinition:
    """
    Convert a py_trees node to TalkingTrees TreeNodeDefinition.
    Recursively processes children.

    Args:
        py_trees_node: Node to convert
        parent_path: Path from root (for deterministic UUIDs)
        use_deterministic_uuids: If True, generate deterministic UUIDs
        context: Conversion context for tracking warnings

    Returns:
        TreeNodeDefinition with all children converted
    """
    # Build path for this node
    current_path = (
        f"{parent_path}/{py_trees_node.name}" if parent_path else py_trees_node.name
    )

    # Convert children first
    children = []
    if hasattr(py_trees_node, "children"):
        # Composite nodes have 'children' (list)
        for child in py_trees_node.children:
            children.append(
                _convert_node(child, current_path, use_deterministic_uuids, context)
            )
    elif hasattr(py_trees_node, "child"):
        # Decorator nodes have 'child' (single node)
        children.append(
            _convert_node(
                py_trees_node.child, current_path, use_deterministic_uuids, context
            )
        )

    # Generate UUID
    if use_deterministic_uuids:
        node_id = _generate_deterministic_uuid(py_trees_node, parent_path)
    else:
        node_id = uuid4()

    # Create TalkingTrees node
    return TreeNodeDefinition(
        node_type=_get_node_type(py_trees_node, context),
        node_id=node_id,
        name=py_trees_node.name,
        config=_extract_config(py_trees_node, context),
        children=children,
    )


def from_py_trees(
    root,
    name: str = "Converted Tree",
    version: str = "1.0.0",
    description: str = "Converted from py_trees",
    tree_id: UUID | None = None,
    use_deterministic_uuids: bool = True,
) -> tuple[TreeDefinition, ConversionContext]:
    """
    Convert a py_trees tree to TalkingTrees format.

    Args:
        root: Root node of py_trees tree
        name: Name for the TalkingTrees tree
        version: Version string
        description: Description of the tree
        tree_id: Optional tree ID (generated if not provided)
        use_deterministic_uuids: Generate deterministic UUIDs based on node structure
            (recommended for version control - same tree gets same UUIDs)

    Returns:
        Tuple of (TreeDefinition, ConversionContext)
        - TreeDefinition: The converted tree
        - ConversionContext: Warnings and issues encountered during conversion

    Note:
        Trees now contain only logic, not blackboard data schemas.
        Blackboard variables should be managed separately at execution time.
        See BLACKBOARD_ARCHITECTURE.md for details.

    Example:
        >>> import py_trees
        >>> from talking_trees.adapters import from_py_trees
        >>>
        >>> # Create py_trees tree
        >>> root = py_trees.composites.Sequence("Root", memory=False)
        >>> root.add_child(py_trees.behaviours.Success("Step1"))
        >>>
        >>> # Convert to TalkingTrees
        >>> tt_tree, context = from_py_trees(root, name="My Tree")
        >>>
        >>> # Check for warnings
        >>> if context.has_warnings():
        >>>     print(context.summary())
        >>>
        >>> # Use with TalkingTrees
        >>> from talking_trees.sdk import TalkingTrees
        >>> pf = TalkingTrees()
        >>> pf.save_tree(tt_tree, "tree.json")
    """
    # Create conversion context for tracking warnings
    context = ConversionContext()

    # Convert root node recursively
    tt_root = _convert_node(
        root,
        parent_path="",
        use_deterministic_uuids=use_deterministic_uuids,
        context=context,
    )

    # Create metadata
    metadata = TreeMetadata(
        name=name,
        version=version,
        description=description,
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow(),
        status=TreeStatus.DRAFT,
    )

    # Create tree definition
    tree = TreeDefinition(
        tree_id=tree_id or uuid4(),
        metadata=metadata,
        root=tt_root,
        dependencies=TreeDependencies(),
    )

    return tree, context


def to_py_trees(tree: TreeDefinition):
    """
    Convert TalkingTrees tree to py_trees format.

    Args:
        tree: TalkingTrees TreeDefinition

    Returns:
        Root node of py_trees tree

    Example:
        >>> from talking_trees.sdk import TalkingTrees
        >>> from talking_trees.adapters import to_py_trees
        >>>
        >>> # Load TalkingTrees tree
        >>> pf = TalkingTrees()
        >>> tree = pf.load_tree("tree.json")
        >>>
        >>> # Convert to py_trees
        >>> root = to_py_trees(tree)
        >>>
        >>> # Use with py_trees
        >>> import py_trees
        >>> py_trees.display.print_ascii_tree(root)
    """
    from talking_trees.core.serializer import TreeSerializer

    serializer = TreeSerializer()
    behaviour_tree = serializer.deserialize(tree)
    return behaviour_tree.root


def print_comparison(py_trees_root, tt_tree: TreeDefinition):
    """
    Print side-by-side comparison of py_trees and TalkingTrees trees.

    Useful for debugging conversions.
    """
    import py_trees

    print("=" * 70)
    print("py_trees Tree:")
    print("=" * 70)
    print(py_trees.display.ascii_tree(py_trees_root, show_status=True))

    print("\n" + "=" * 70)
    print("TalkingTrees Tree:")
    print("=" * 70)
    print(f"Name: {tt_tree.metadata.name}")
    print(f"Version: {tt_tree.metadata.version}")

    def count_nodes(node):
        count = 1
        for child in node.children:
            count += count_nodes(child)
        return count

    total_nodes = count_nodes(tt_tree.root)
    print(f"Nodes: {total_nodes}")
    print()

    def print_tree(node, indent=0):
        print("  " * indent + f"- {node.name} ({node.node_type})")
        for child in node.children:
            print_tree(child, indent + 1)

    print_tree(tt_tree.root)
    print()


# =============================================================================
# py_trees Comparison
# =============================================================================


def compare_py_trees(
    root1, root2, *, verbose: bool = False, raise_on_difference: bool = False
) -> bool:
    """Compare two py_trees roots for structural and functional equivalence.

    This is useful for verifying round-trip conversion or checking if two
    trees are functionally identical even if they're different objects in memory.

    Args:
        root1: First py_trees root
        root2: Second py_trees root
        verbose: If True, print detailed comparison results (default: False)
        raise_on_difference: If True, raise ValueError on differences (default: False)

    Returns:
        True if trees are functionally equivalent, False otherwise

    Raises:
        ValueError: If raise_on_difference=True and trees differ

    Example:
        >>> import py_trees
        >>> from talking_trees.adapters import from_py_trees, to_py_trees, compare_py_trees
        >>>
        >>> # Create original tree
        >>> root = py_trees.composites.Sequence("Main", memory=False, children=[
        ...     py_trees.behaviours.Success("Task1"),
        ...     py_trees.behaviours.Success("Task2"),
        ... ])
        >>>
        >>> # Round-trip conversion
        >>> tt_tree, _ = from_py_trees(root, name="Test", version="1.0")
        >>> py_trees_root = to_py_trees(tt_tree)
        >>>
        >>> # Verify they're equivalent
        >>> if compare_py_trees(root, py_trees_root):
        ...     print("✓ Trees are functionally identical!")
        >>> else:
        ...     print("✗ Trees differ!")
        >>>
        >>> # With verbose output
        >>> compare_py_trees(root, py_trees_root, verbose=True)
        >>>
        >>> # Raise error on difference
        >>> compare_py_trees(root, py_trees_root, raise_on_difference=True)
    """
    from talking_trees.core.round_trip_validator import RoundTripValidator

    validator = RoundTripValidator()
    is_equivalent = validator.validate(root1, root2)

    if verbose:
        print("=" * 70)
        print("py_trees Comparison")
        print("=" * 70)
        print(f"Tree 1: {root1.name} ({type(root1).__name__})")
        print(f"Tree 2: {root2.name} ({type(root2).__name__})")
        print()
        print(validator.get_error_summary())
        print()

        if is_equivalent:
            print("✓ Trees are functionally equivalent!")
        else:
            print(f"✗ Trees differ ({len(validator.errors)} issue(s) found)")
        print("=" * 70)

    if raise_on_difference and not is_equivalent:
        raise ValueError(
            f"Trees are not equivalent:\n{validator.get_error_summary()}"
        )

    return is_equivalent
