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
    """

    def __init__(self):
        """Initialize the serializer."""
        self.registry = get_registry()
        self.node_map: Dict[UUID, behaviour.Behaviour] = {}
        self.reverse_map: Dict[behaviour.Behaviour, UUID] = {}

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

        # Resolve subtree references first
        resolved_root = self._resolve_subtrees(tree_def.root, tree_def.subtrees)

        # Build the tree recursively
        root_node = self._build_node(resolved_root)

        # Create BehaviourTree wrapper
        tree = py_trees.trees.BehaviourTree(root=root_node)

        # Initialize blackboard with schema defaults
        self._initialize_blackboard(tree_def)

        return tree

    def _resolve_subtrees(
        self,
        node: TreeNodeDefinition,
        subtrees: Dict[str, TreeNodeDefinition],
    ) -> TreeNodeDefinition:
        """Resolve $ref pointers to subtrees.

        Args:
            node: Node definition (may have $ref)
            subtrees: Available subtree definitions

        Returns:
            Resolved node definition

        Raises:
            ValueError: If referenced subtree not found
        """
        # If this node has a $ref, replace it with the subtree
        if node.ref:
            ref_name = node.ref.lstrip("#/subtrees/")
            if ref_name not in subtrees:
                raise ValueError(f"Subtree reference not found: {node.ref}")

            # Get the subtree definition
            subtree = subtrees[ref_name]

            # Create a new node with subtree content but keep original node_id and name
            resolved = TreeNodeDefinition(
                node_type=subtree.node_type,
                node_id=node.node_id,
                name=node.name or subtree.name,
                config=subtree.config,
                ui_metadata=node.ui_metadata or subtree.ui_metadata,
                children=subtree.children,
            )
            node = resolved

        # Recursively resolve children
        if node.children:
            resolved_children = [
                self._resolve_subtrees(child, subtrees) for child in node.children
            ]
            node = TreeNodeDefinition(
                node_type=node.node_type,
                node_id=node.node_id,
                name=node.name,
                config=node.config,
                ui_metadata=node.ui_metadata,
                children=resolved_children,
            )

        return node

    def _build_node(self, node_def: TreeNodeDefinition) -> behaviour.Behaviour:
        """Recursively build a py_trees node from definition.

        Args:
            node_def: Node definition

        Returns:
            Instantiated py_trees Behaviour

        Raises:
            ValueError: If node type is unknown or construction fails
        """
        # Get implementation from registry
        implementation = self.registry.get_implementation(node_def.node_type)
        if implementation is None:
            raise ValueError(f"Unknown node type: {node_def.node_type}")

        # Handle different node categories differently
        if node_def.node_type in ["Sequence", "Selector"]:
            # Composites: build children first, then composite
            return self._build_composite(node_def)
        elif node_def.node_type == "Parallel":
            return self._build_parallel(node_def)
        elif node_def.node_type in ["Inverter", "Timeout", "Retry", "OneShot"]:
            # Decorators: need child in constructor
            return self._build_decorator(node_def)
        else:
            # Simple behaviors (leaf nodes)
            return self._build_behavior(node_def)

    def _build_composite(self, node_def: TreeNodeDefinition) -> behaviour.Behaviour:
        """Build a composite node (Sequence, Selector).

        Args:
            node_def: Node definition

        Returns:
            Composite behaviour with children attached
        """
        # Build children first
        children = [self._build_node(child) for child in node_def.children]

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

    def _build_parallel(self, node_def: TreeNodeDefinition) -> behaviour.Behaviour:
        """Build a parallel node.

        Args:
            node_def: Node definition

        Returns:
            Parallel behaviour
        """
        # Build children first
        children = [self._build_node(child) for child in node_def.children]

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

    def _build_decorator(self, node_def: TreeNodeDefinition) -> behaviour.Behaviour:
        """Build a decorator node.

        Args:
            node_def: Node definition

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

        # Build child first
        child = self._build_node(node_def.children[0])

        # Create decorator based on type
        if node_def.node_type == "Inverter":
            decorator = py_trees.decorators.Inverter(name=node_def.name, child=child)

        elif node_def.node_type == "Timeout":
            duration = node_def.config.get("duration", 5.0)
            decorator = py_trees.decorators.Timeout(
                name=node_def.name, child=child, duration=duration
            )

        elif node_def.node_type == "Retry":
            num_failures = node_def.config.get("num_failures", 3)
            decorator = py_trees.decorators.Retry(
                name=node_def.name, child=child, num_failures=num_failures
            )

        elif node_def.node_type == "OneShot":
            policy_str = node_def.config.get("policy", "ON_COMPLETION")
            policy = getattr(py_trees.common.OneShotPolicy, policy_str)
            decorator = py_trees.decorators.OneShot(
                name=node_def.name, child=child, policy=policy
            )

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

    def _initialize_blackboard(self, tree_def: TreeDefinition) -> None:
        """Initialize blackboard with default values from schema.

        Args:
            tree_def: Tree definition with blackboard schema
        """
        bb = blackboard.Client(name="TreeInitializer")

        for key, schema in tree_def.blackboard_schema.items():
            # Register key for writing
            bb.register_key(key=key, access=py_trees.common.Access.WRITE)

            # Set default value if specified
            if schema.default is not None:
                bb.set(key, schema.default, overwrite=False)

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
