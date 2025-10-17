"""
py_trees Adapter
================

Converts between py_trees behavior trees and PyForest format.

This allows you to:
1. Create trees using py_trees (programmatic Python)
2. Convert to PyForest format
3. Visualize in PyForest editor
4. Save/load as JSON
5. Run via PyForest SDK or REST API

Example:
    import py_trees
    from py_forest.adapters import from_py_trees

    # Create tree with py_trees
    root = py_trees.composites.Sequence("MySequence", memory=False)
    root.add_child(py_trees.behaviours.Success("Step1"))
    root.add_child(py_trees.behaviours.Success("Step2"))

    # Convert to PyForest
    pf_tree, context = from_py_trees(root, name="My Tree", version="1.0.0")

    # Now use with PyForest SDK
    from py_forest.sdk import PyForest
    pf = PyForest()
    pf.save_tree(pf_tree, "my_tree.json")
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from py_forest.models.tree import (
    TreeDefinition,
    TreeNodeDefinition,
    TreeMetadata,
    TreeDependencies,
    TreeStatus
)


# =============================================================================
# Conversion Context (Warnings)
# =============================================================================

class ConversionContext:
    """
    Tracks warnings and issues during py_trees → PyForest conversion.

    Provides visibility into data loss, fallbacks, and other conversion issues.
    """

    def __init__(self):
        self.warnings: list[str] = []

    def warn(self, message: str, node_name: Optional[str] = None):
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

def _generate_deterministic_uuid(
    node,
    parent_path: str = "",
    config_keys: Optional[list] = None
) -> UUID:
    """
    Generate deterministic UUID based on node structure.

    Uses SHA-256 hash of node's identifying characteristics to ensure
    the same node always gets the same UUID across conversions.

    Args:
        node: py_trees node
        parent_path: Path from root (e.g., "Root/Selector/Sequence")
        config_keys: Optional list of config keys to include in hash

    Returns:
        Deterministic UUID

    Example:
        >>> node = py_trees.behaviours.Success("Step1")
        >>> uuid1 = _generate_deterministic_uuid(node, "Root/Sequence")
        >>> uuid2 = _generate_deterministic_uuid(node, "Root/Sequence")
        >>> assert uuid1 == uuid2  # Same UUID!
    """
    import hashlib

    # Build path including this node
    path = f"{parent_path}/{node.name}" if parent_path else node.name

    # Collect identifying characteristics
    parts = [
        type(node).__name__,  # Node class
        node.name,            # Node name
        path,                 # Full path in tree
    ]

    # Add memory parameter if present (important for composites)
    if hasattr(node, 'memory'):
        parts.append(f"memory={node.memory}")

    # Add key config values for blackboard nodes
    if hasattr(node, 'variable_name'):
        parts.append(f"var={node.variable_name}")

    # Add decorator-specific config
    if hasattr(node, 'duration'):
        parts.append(f"duration={node.duration}")
    if hasattr(node, 'num_failures'):
        parts.append(f"num_failures={node.num_failures}")
    if hasattr(node, 'num_success'):
        parts.append(f"num_success={node.num_success}")

    # Add custom config keys if specified
    if config_keys:
        for key in config_keys:
            if hasattr(node, key):
                parts.append(f"{key}={getattr(node, key)}")

    # Create deterministic string
    content = '|'.join(str(p) for p in parts)

    # Hash to bytes
    hash_bytes = hashlib.sha256(content.encode('utf-8')).digest()

    # Use first 16 bytes as UUID
    return UUID(bytes=hash_bytes[:16])


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
            'variable': check.variable,
            'comparison_value': check.operator,  # Yes, py_trees swaps these!
            'operator_function': check.value,    # Yes, py_trees swaps these!
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
        return ComparisonExpression(variable, operator_func, value)


# =============================================================================
# Node Type Mapping
# =============================================================================

# Maps py_trees node types to PyForest node types
NODE_TYPE_MAP = {
    # Composites
    "Sequence": "Sequence",
    "Selector": "Selector",
    "Parallel": "Parallel",

    # Decorators
    "Inverter": "Inverter",
    "SuccessIsFailure": "Inverter",
    "FailureIsSuccess": "Inverter",
    "Repeat": "Repeat",
    "Retry": "Retry",
    "Timeout": "Timeout",

    # Behaviors (map to generic types)
    "Success": "Success",
    "Failure": "Failure",
    "Running": "Running",
    "CheckBlackboardVariable": "CheckBlackboardCondition",
    "CheckBlackboardVariableExists": "CheckBlackboardCondition",
    "CheckBlackboardVariableValue": "CheckBlackboardCondition",
    "SetBlackboardVariable": "SetBlackboardVariable",
    "UnsetBlackboardVariable": "UnsetBlackboardVariable",
}


def _get_node_type(py_trees_node, context: Optional[ConversionContext] = None) -> str:
    """Determine PyForest node type from py_trees node"""
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
                node_name=py_trees_node.name
            )
        return "Action"

    # Default fallback
    if context:
        context.warn(
            f"Unrecognized py_trees class '{class_name}', defaulting to Action",
            node_name=py_trees_node.name
        )
    return "Action"


def _extract_config(py_trees_node, context: Optional[ConversionContext] = None) -> Dict[str, Any]:
    """Extract config from py_trees node to PyForest format"""
    config = {}
    class_name = type(py_trees_node).__name__
    import operator as op_module

    # Blackboard-related behaviors
    if class_name == "CheckBlackboardVariableValue":
        # py_trees uses ComparisonExpression via .check attribute
        if hasattr(py_trees_node, 'check'):
            # Use abstraction layer to safely extract comparison data
            extracted = ComparisonExpressionExtractor.extract(py_trees_node.check)

            config['variable'] = extracted['variable']
            config['value'] = extracted['comparison_value']

            # Convert operator function to string
            op_func = extracted['operator_function']
            op_map = {
                op_module.gt: ">",
                op_module.ge: ">=",
                op_module.lt: "<",
                op_module.le: "<=",
                op_module.eq: "==",
                op_module.ne: "!=",
            }
            config['operator'] = op_map.get(op_func, "==")

    elif class_name == "CheckBlackboardVariableExists":
        if hasattr(py_trees_node, 'variable_name'):
            config['variable'] = py_trees_node.variable_name

    elif class_name == "SetBlackboardVariable":
        # Extract variable name (exposed as both .variable_name and .key)
        if hasattr(py_trees_node, 'variable_name'):
            config['variable'] = py_trees_node.variable_name
        elif hasattr(py_trees_node, 'key'):
            config['variable'] = py_trees_node.key

        # Extract value using reflection (py_trees stores this privately)
        # Try multiple approaches to get the value
        value_extracted = False

        # Approach 1: Try _value attribute (private)
        if hasattr(py_trees_node, '_value'):
            config['value'] = py_trees_node._value
            value_extracted = True
        # Approach 2: Try variable_value (older API)
        elif hasattr(py_trees_node, 'variable_value'):
            config['value'] = py_trees_node.variable_value
            value_extracted = True
        # Approach 3: Try to access via __dict__
        elif '_value' in py_trees_node.__dict__:
            config['value'] = py_trees_node.__dict__['_value']
            value_extracted = True

        if not value_extracted:
            # WARNING: Could not extract value - data will be lost!
            warning_msg = (
                "SetBlackboardVariable value not accessible. "
                "Round-trip conversion will lose this value."
            )
            config['_data_loss_warning'] = warning_msg
            if context:
                context.warn(warning_msg, node_name=py_trees_node.name)

        if hasattr(py_trees_node, 'overwrite'):
            config['overwrite'] = py_trees_node.overwrite

    elif class_name == "UnsetBlackboardVariable":
        if hasattr(py_trees_node, 'variable_name'):
            config['variable'] = py_trees_node.variable_name

    # Decorators
    elif class_name == "Repeat":
        if hasattr(py_trees_node, 'num_success'):
            config['num_success'] = py_trees_node.num_success

    elif class_name == "Retry":
        if hasattr(py_trees_node, 'num_failures'):
            config['num_failures'] = py_trees_node.num_failures

    elif class_name == "Timeout":
        if hasattr(py_trees_node, 'duration'):
            config['duration'] = py_trees_node.duration

    # Composites - check for memory parameter
    if hasattr(py_trees_node, 'memory'):
        config['memory'] = py_trees_node.memory

    # Store original class name for reference
    config['_py_trees_class'] = class_name

    return config


def _convert_node(
    py_trees_node,
    parent_path: str = "",
    use_deterministic_uuids: bool = True,
    context: Optional[ConversionContext] = None
) -> TreeNodeDefinition:
    """
    Convert a py_trees node to PyForest TreeNodeDefinition.
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
    current_path = f"{parent_path}/{py_trees_node.name}" if parent_path else py_trees_node.name

    # Convert children first
    children = []
    if hasattr(py_trees_node, 'children'):
        # Composite nodes have 'children' (list)
        for child in py_trees_node.children:
            children.append(_convert_node(child, current_path, use_deterministic_uuids, context))
    elif hasattr(py_trees_node, 'child'):
        # Decorator nodes have 'child' (single node)
        children.append(_convert_node(py_trees_node.child, current_path, use_deterministic_uuids, context))

    # Generate UUID
    if use_deterministic_uuids:
        node_id = _generate_deterministic_uuid(py_trees_node, parent_path)
    else:
        node_id = uuid4()

    # Create PyForest node
    return TreeNodeDefinition(
        node_type=_get_node_type(py_trees_node, context),
        node_id=node_id,
        name=py_trees_node.name,
        config=_extract_config(py_trees_node, context),
        children=children
    )


def from_py_trees(
    root,
    name: str = "Converted Tree",
    version: str = "1.0.0",
    description: str = "Converted from py_trees",
    tree_id: Optional[UUID] = None,
    use_deterministic_uuids: bool = True
) -> tuple[TreeDefinition, ConversionContext]:
    """
    Convert a py_trees tree to PyForest format.

    Args:
        root: Root node of py_trees tree
        name: Name for the PyForest tree
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
        >>> from py_forest.adapters import from_py_trees
        >>>
        >>> # Create py_trees tree
        >>> root = py_trees.composites.Sequence("Root", memory=False)
        >>> root.add_child(py_trees.behaviours.Success("Step1"))
        >>>
        >>> # Convert to PyForest
        >>> pf_tree, context = from_py_trees(root, name="My Tree")
        >>>
        >>> # Check for warnings
        >>> if context.has_warnings():
        >>>     print(context.summary())
        >>>
        >>> # Use with PyForest
        >>> from py_forest.sdk import PyForest
        >>> pf = PyForest()
        >>> pf.save_tree(pf_tree, "tree.json")
    """
    # Create conversion context for tracking warnings
    context = ConversionContext()

    # Convert root node recursively
    pf_root = _convert_node(
        root,
        parent_path="",
        use_deterministic_uuids=use_deterministic_uuids,
        context=context
    )

    # Create metadata
    metadata = TreeMetadata(
        name=name,
        version=version,
        description=description,
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow(),
        status=TreeStatus.DRAFT
    )

    # Create tree definition
    tree = TreeDefinition(
        tree_id=tree_id or uuid4(),
        metadata=metadata,
        root=pf_root,
        dependencies=TreeDependencies()
    )

    return tree, context


def to_py_trees(tree: TreeDefinition):
    """
    Convert PyForest tree to py_trees format.

    Args:
        tree: PyForest TreeDefinition

    Returns:
        Root node of py_trees tree

    Note:
        This is a basic implementation that handles common node types.
        Custom PyForest behaviors may need manual mapping.

    Example:
        >>> from py_forest.sdk import PyForest
        >>> from py_forest.adapters import to_py_trees
        >>>
        >>> # Load PyForest tree
        >>> pf = PyForest()
        >>> tree = pf.load_tree("tree.json")
        >>>
        >>> # Convert to py_trees
        >>> root = to_py_trees(tree)
        >>>
        >>> # Use with py_trees
        >>> import py_trees
        >>> py_trees.display.print_ascii_tree(root)
    """
    import py_trees
    import operator as op_module

    def create_py_trees_node(pf_node: TreeNodeDefinition):
        """Create py_trees node from PyForest node"""
        node_type = pf_node.node_type
        name = pf_node.name
        config = pf_node.config or {}

        # Create appropriate py_trees node
        if node_type == "Sequence":
            memory = config.get('memory', False)
            node = py_trees.composites.Sequence(name=name, memory=memory)

        elif node_type == "Selector":
            memory = config.get('memory', False)
            node = py_trees.composites.Selector(name=name, memory=memory)

        elif node_type == "Parallel":
            node = py_trees.composites.Parallel(
                name=name,
                policy=py_trees.common.ParallelPolicy.SuccessOnAll()
            )

        elif node_type == "CheckBlackboardCondition":
            variable = config.get('variable', 'condition')
            value = config.get('value', True)
            op_str = config.get('operator', '==')

            # Map operator string to operator function
            op_map = {
                ">": op_module.gt,
                ">=": op_module.ge,
                "<": op_module.lt,
                "<=": op_module.le,
                "==": op_module.eq,
                "!=": op_module.ne,
            }
            comparison_op = op_map.get(op_str, op_module.eq)

            # Use ComparisonExpression (current py_trees API)
            from py_trees.common import ComparisonExpression
            check = ComparisonExpression(variable, comparison_op, value)
            node = py_trees.behaviours.CheckBlackboardVariableValue(
                name=name,
                check=check
            )

        elif node_type == "SetBlackboardVariable":
            variable = config.get('variable', 'output')
            value = config.get('value', None)
            overwrite = config.get('overwrite', True)  # Default to True for safety
            node = py_trees.behaviours.SetBlackboardVariable(
                name=name,
                variable_name=variable,
                variable_value=value,
                overwrite=overwrite
            )

        elif node_type == "Success":
            node = py_trees.behaviours.Success(name=name)

        elif node_type == "Failure":
            node = py_trees.behaviours.Failure(name=name)

        elif node_type == "Running":
            node = py_trees.behaviours.Running(name=name)

        elif node_type == "Inverter":
            # Will be wrapped as decorator
            node = py_trees.decorators.Inverter(
                name=name,
                child=py_trees.behaviours.Success("placeholder")
            )

        else:
            # Default to success behavior
            node = py_trees.behaviours.Success(name=name)

        return node

    def build_tree(pf_node: TreeNodeDefinition):
        """Recursively build py_trees tree"""
        node_type = pf_node.node_type

        # Handle decorators specially - they need their child at construction time
        if node_type in ["Inverter", "Repeat", "Retry", "Timeout"]:
            # Build the child first
            if pf_node.children:
                child_pt_node = build_tree(pf_node.children[0])
            else:
                # Fallback if no child specified
                child_pt_node = py_trees.behaviours.Success("placeholder")

            # Now create the decorator with the actual child
            name = pf_node.name
            config = pf_node.config or {}

            if node_type == "Inverter":
                pt_node = py_trees.decorators.Inverter(name=name, child=child_pt_node)
            elif node_type == "Repeat":
                num_success = config.get('num_success', 1)
                pt_node = py_trees.decorators.Repeat(name=name, child=child_pt_node, num_success=num_success)
            elif node_type == "Retry":
                num_failures = config.get('num_failures', 1)
                pt_node = py_trees.decorators.Retry(name=name, child=child_pt_node, num_failures=num_failures)
            elif node_type == "Timeout":
                duration = config.get('duration', 1.0)
                pt_node = py_trees.decorators.Timeout(name=name, child=child_pt_node, duration=duration)

            return pt_node

        # For non-decorators, use normal creation
        pt_node = create_py_trees_node(pf_node)

        # Add children for composites
        if hasattr(pt_node, 'children') and pf_node.children:
            # Composite node - add children
            for child in pf_node.children:
                child_pt_node = build_tree(child)
                pt_node.add_child(child_pt_node)

        return pt_node

    # Build from root
    root = build_tree(tree.root)
    return root


def print_comparison(py_trees_root, pf_tree: TreeDefinition):
    """
    Print side-by-side comparison of py_trees and PyForest trees.

    Useful for debugging conversions.
    """
    import py_trees

    print("=" * 70)
    print("py_trees Tree:")
    print("=" * 70)
    print(py_trees.display.ascii_tree(py_trees_root, show_status=True))

    print("\n" + "=" * 70)
    print("PyForest Tree:")
    print("=" * 70)
    print(f"Name: {pf_tree.metadata.name}")
    print(f"Version: {pf_tree.metadata.version}")

    def count_nodes(node):
        count = 1
        for child in node.children:
            count += count_nodes(child)
        return count

    total_nodes = count_nodes(pf_tree.root)
    print(f"Nodes: {total_nodes}")
    print()

    def print_tree(node, indent=0):
        print("  " * indent + f"- {node.name} ({node.node_type})")
        for child in node.children:
            print_tree(child, indent + 1)

    print_tree(pf_tree.root)
    print()
