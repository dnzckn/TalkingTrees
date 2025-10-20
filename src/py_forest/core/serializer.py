"""Tree serialization between JSON and py_trees objects."""

from typing import Any, Dict, Optional
from uuid import UUID

import py_trees
from py_trees import behaviour, blackboard

from py_forest.core.registry import get_registry
from py_forest.models.tree import TreeDefinition, TreeNodeDefinition


class TreeSerializer:
    """Converts between TreeDefinition (JSON) and py_trees.BehaviourTree.

    Maintains bidirectional mapping between:
    - TreeNodeDefinition UUID ↔ py_trees Behaviour instance

    Security Features:
    - Cycle detection in subtree resolution (prevents infinite loops)
    - Depth limits (prevents stack overflow from deeply nested trees)
    """

    def __init__(self, max_depth: int = 100):
        """Initialize the serializer.

        Args:
            max_depth: Maximum tree depth allowed (default: 100)
        """
        self.registry = get_registry()
        self.node_map: Dict[UUID, behaviour.Behaviour] = {}
        self.reverse_map: Dict[behaviour.Behaviour, UUID] = {}
        self.max_depth = max_depth

    def deserialize(self, tree_def: TreeDefinition) -> py_trees.trees.BehaviourTree:
        """Convert TreeDefinition to executable py_trees.BehaviourTree.

        Args:
            tree_def: Tree definition from JSON

        Returns:
            Executable behaviour tree

        Raises:
            ValueError: If tree definition is invalid
        """
        self.node_map = {}
        self.reverse_map = {}

        # Resolve subtree references first (with cycle detection)
        visited_refs = set()
        resolved_root = self._resolve_subtrees(tree_def.root, tree_def.subtrees, visited_refs)

        # Build the tree recursively (with depth limits)
        root_node = self._build_node(resolved_root, depth=0)

        # Create BehaviourTree wrapper
        tree = py_trees.trees.BehaviourTree(root=root_node)

        return tree

    def _resolve_subtrees(
        self,
        node: TreeNodeDefinition,
        subtrees: Dict[str, TreeNodeDefinition],
        visited_refs: set[str],
    ) -> TreeNodeDefinition:
        """Resolve $ref pointers to subtrees with cycle detection.

        Args:
            node: Node definition (may have $ref)
            subtrees: Available subtree definitions
            visited_refs: Set of already visited refs (for cycle detection)

        Returns:
            Resolved node definition

        Raises:
            ValueError: If referenced subtree not found or circular reference detected
        """
        # If this node has a $ref, replace it with the subtree
        if node.ref:
            ref_name = node.ref.lstrip("#/subtrees/")

            # Cycle detection: check if we've already visited this ref
            if ref_name in visited_refs:
                raise ValueError(f"Circular subtree reference detected: {node.ref} (path: {visited_refs})")

            if ref_name not in subtrees:
                raise ValueError(f"Subtree reference not found: {node.ref}")

            # Mark this ref as visited
            visited_refs.add(ref_name)

            # Get the subtree definition
            subtree = subtrees[ref_name]

            # Create a new node with subtree content but keep original node_id and name
            resolved = TreeNodeDefinition(
                node_type=subtree.node_type,
                node_id=node.node_id,
                name=node.name or subtree.name,
                config=subtree.config,
                description=node.description or subtree.description,
                children=subtree.children,
            )
            node = resolved

        # Recursively resolve children (share visited_refs to detect cycles)
        if node.children:
            resolved_children = [
                self._resolve_subtrees(child, subtrees, visited_refs) for child in node.children
            ]
            node = TreeNodeDefinition(
                node_type=node.node_type,
                node_id=node.node_id,
                name=node.name,
                config=node.config,
                description=node.description,
                children=resolved_children,
            )

        return node

    def _build_node(self, node_def: TreeNodeDefinition, depth: int = 0) -> behaviour.Behaviour:
        """Recursively build a py_trees node from definition with depth limits.

        Args:
            node_def: Node definition
            depth: Current depth in the tree

        Returns:
            Instantiated py_trees Behaviour

        Raises:
            ValueError: If node type is unknown, construction fails, or max depth exceeded
        """
        # Depth limit check
        if depth > self.max_depth:
            raise ValueError(
                f"Tree depth exceeded maximum ({self.max_depth}). "
                f"This may indicate a circular reference or excessively deep nesting."
            )

        # Get implementation from registry
        implementation = self.registry.get_implementation(node_def.node_type)
        if implementation is None:
            raise ValueError(f"Unknown node type: {node_def.node_type}")

        # Handle different node categories differently
        if node_def.node_type in ["Sequence", "Selector"]:
            # Composites: build children first, then composite
            return self._build_composite(node_def, depth)
        elif node_def.node_type == "Parallel":
            return self._build_parallel(node_def, depth)
        elif node_def.node_type in [
            # Basic
            "Inverter",
            # Status converters
            "SuccessIsFailure", "FailureIsSuccess", "FailureIsRunning",
            "RunningIsFailure", "RunningIsSuccess", "SuccessIsRunning",
            # Repetition
            "Repeat", "Retry", "OneShot",
            # Time-based
            "Timeout",
            # Advanced
            "EternalGuard", "Condition", "Count",
            "StatusToBlackboard", "PassThrough"
        ]:
            # Decorators: need child in constructor
            return self._build_decorator(node_def, depth)
        else:
            # Simple behaviors (leaf nodes)
            return self._build_behavior(node_def)

    def _build_composite(self, node_def: TreeNodeDefinition, depth: int) -> behaviour.Behaviour:
        """Build a composite node (Sequence, Selector).

        Args:
            node_def: Node definition
            depth: Current depth in tree

        Returns:
            Composite behaviour with children attached
        """
        # Build children first (increment depth)
        children = [self._build_node(child, depth + 1) for child in node_def.children]

        # Create composite with correct memory defaults
        # Sequence defaults to memory=True (committed - completes steps in order)
        # Selector defaults to memory=False (reactive - re-evaluates priorities each tick)
        if node_def.node_type == "Sequence":
            memory = node_def.config.get("memory", True)
            composite = py_trees.composites.Sequence(
                name=node_def.name, memory=memory, children=children
            )
        elif node_def.node_type == "Selector":
            memory = node_def.config.get("memory", False)
            composite = py_trees.composites.Selector(
                name=node_def.name, memory=memory, children=children
            )
        else:
            raise ValueError(f"Unknown composite type: {node_def.node_type}")

        # Store UUID mapping
        self._store_node_mapping(node_def.node_id, composite)

        return composite

    def _build_parallel(self, node_def: TreeNodeDefinition, depth: int) -> behaviour.Behaviour:
        """Build a parallel node.

        Args:
            node_def: Node definition
            depth: Current depth in tree

        Returns:
            Parallel behaviour
        """
        # Build children first (increment depth)
        children = [self._build_node(child, depth + 1) for child in node_def.children]

        # Create policy
        policy_name = node_def.config.get("policy", "SuccessOnAll")
        synchronise = node_def.config.get("synchronise", True)

        if policy_name == "SuccessOnAll":
            policy = py_trees.common.ParallelPolicy.SuccessOnAll(
                synchronise=synchronise
            )
        elif policy_name == "SuccessOnOne":
            policy = py_trees.common.ParallelPolicy.SuccessOnOne()
        elif policy_name == "SuccessOnSelected":
            # For now, default to SuccessOnAll
            # Proper implementation needs child selection
            policy = py_trees.common.ParallelPolicy.SuccessOnAll(
                synchronise=synchronise
            )
        else:
            raise ValueError(f"Unknown parallel policy: {policy_name}")

        # Create parallel
        parallel = py_trees.composites.Parallel(
            name=node_def.name, policy=policy, children=children
        )

        # Store UUID mapping
        self._store_node_mapping(node_def.node_id, parallel)

        return parallel

    def _build_decorator(self, node_def: TreeNodeDefinition, depth: int) -> behaviour.Behaviour:
        """Build a decorator node.

        Args:
            node_def: Node definition
            depth: Current depth in tree

        Returns:
            Decorator behaviour

        Raises:
            ValueError: If decorator has wrong number of children
        """
        # Decorators must have exactly one child
        if len(node_def.children) != 1:
            raise ValueError(
                f"Decorator {node_def.name} must have exactly 1 child, "
                f"got {len(node_def.children)}"
            )

        # Build child first (increment depth)
        child = self._build_node(node_def.children[0], depth + 1)

        # Create decorator based on type
        # Basic decorators
        if node_def.node_type == "Inverter":
            decorator = py_trees.decorators.Inverter(name=node_def.name, child=child)

        # Status converter decorators
        elif node_def.node_type == "SuccessIsFailure":
            decorator = py_trees.decorators.SuccessIsFailure(name=node_def.name, child=child)

        elif node_def.node_type == "FailureIsSuccess":
            decorator = py_trees.decorators.FailureIsSuccess(name=node_def.name, child=child)

        elif node_def.node_type == "FailureIsRunning":
            decorator = py_trees.decorators.FailureIsRunning(name=node_def.name, child=child)

        elif node_def.node_type == "RunningIsFailure":
            decorator = py_trees.decorators.RunningIsFailure(name=node_def.name, child=child)

        elif node_def.node_type == "RunningIsSuccess":
            decorator = py_trees.decorators.RunningIsSuccess(name=node_def.name, child=child)

        elif node_def.node_type == "SuccessIsRunning":
            decorator = py_trees.decorators.SuccessIsRunning(name=node_def.name, child=child)

        # Repetition decorators
        elif node_def.node_type == "Repeat":
            num_success = node_def.config.get("num_success", 1)
            decorator = py_trees.decorators.Repeat(
                name=node_def.name, child=child, num_success=num_success
            )

        elif node_def.node_type == "Retry":
            num_failures = node_def.config.get("num_failures", 3)
            decorator = py_trees.decorators.Retry(
                name=node_def.name, child=child, num_failures=num_failures
            )

        elif node_def.node_type == "OneShot":
            policy_str = node_def.config.get("policy", "ON_COMPLETION")
            policy = getattr(py_trees.common.OneShotPolicy, policy_str, py_trees.common.OneShotPolicy.ON_COMPLETION)
            decorator = py_trees.decorators.OneShot(
                name=node_def.name, child=child, policy=policy
            )

        # Time-based decorators
        elif node_def.node_type == "Timeout":
            duration = node_def.config.get("duration", 5.0)
            decorator = py_trees.decorators.Timeout(
                name=node_def.name, child=child, duration=duration
            )

        # Advanced decorators
        elif node_def.node_type == "EternalGuard":
            variable = node_def.config.get("variable", "condition")
            value = node_def.config.get("value", True)
            op_str = node_def.config.get("operator", "==")
            import operator as op_module
            op_map = {
                ">": op_module.gt,
                ">=": op_module.ge,
                "<": op_module.lt,
                "<=": op_module.le,
                "==": op_module.eq,
                "!=": op_module.ne,
            }
            comparison_op = op_map.get(op_str, op_module.eq)
            from py_trees.common import ComparisonExpression
            check = ComparisonExpression(variable, comparison_op, value)
            decorator = py_trees.decorators.EternalGuard(
                name=node_def.name,
                child=child,
                blackboard_keys=[variable],
                condition=check
            )

        elif node_def.node_type == "Condition":
            variable = node_def.config.get("variable", "condition")
            value = node_def.config.get("value", True)
            op_str = node_def.config.get("operator", "==")
            import operator as op_module
            op_map = {
                ">": op_module.gt,
                ">=": op_module.ge,
                "<": op_module.lt,
                "<=": op_module.le,
                "==": op_module.eq,
                "!=": op_module.ne,
            }
            comparison_op = op_map.get(op_str, op_module.eq)
            from py_trees.common import ComparisonExpression
            check = ComparisonExpression(variable, comparison_op, value)
            decorator = py_trees.decorators.Condition(
                name=node_def.name,
                child=child,
                blackboard_keys=[variable],
                status=check
            )

        elif node_def.node_type == "Count":
            decorator = py_trees.decorators.Count(name=node_def.name, child=child)

        elif node_def.node_type == "StatusToBlackboard":
            variable = node_def.config.get("variable", "status")
            decorator = py_trees.decorators.StatusToBlackboard(
                name=node_def.name,
                child=child,
                variable_name=variable
            )

        elif node_def.node_type == "PassThrough":
            decorator = py_trees.decorators.PassThrough(name=node_def.name, child=child)

        else:
            raise ValueError(f"Unknown decorator type: {node_def.node_type}")

        # Store UUID mapping
        self._store_node_mapping(node_def.node_id, decorator)

        return decorator

    def _build_behavior(self, node_def: TreeNodeDefinition) -> behaviour.Behaviour:
        """Build a leaf behavior node.

        Args:
            node_def: Node definition

        Returns:
            Behavior instance
        """
        # Use registry to create the behavior
        node = self.registry.create_node(
            node_type=node_def.node_type, name=node_def.name, config=node_def.config
        )

        # Store UUID mapping
        self._store_node_mapping(node_def.node_id, node)

        return node

    def _store_node_mapping(self, uuid: UUID, node: behaviour.Behaviour) -> None:
        """Store bidirectional mapping between UUID and node.

        Args:
            uuid: Our tree definition UUID
            node: py_trees Behaviour instance
        """
        self.node_map[uuid] = node
        self.reverse_map[node] = uuid

        # Also store UUID as attribute on the node for later retrieval
        setattr(node, "_pyforest_uuid", uuid)

    def get_node_uuid(self, node: behaviour.Behaviour) -> Optional[UUID]:
        """Get the UUID for a py_trees node.

        Args:
            node: py_trees Behaviour instance

        Returns:
            UUID if found, None otherwise
        """
        # Try reverse map first
        if node in self.reverse_map:
            return self.reverse_map[node]

        # Try attribute
        return getattr(node, "_pyforest_uuid", None)

    def get_node_by_uuid(self, uuid: UUID) -> Optional[behaviour.Behaviour]:
        """Get a py_trees node by UUID.

        Args:
            uuid: Tree definition UUID

        Returns:
            Behaviour instance if found, None otherwise
        """
        return self.node_map.get(uuid)
