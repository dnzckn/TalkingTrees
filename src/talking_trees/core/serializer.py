"""Tree serialization between JSON and py_trees objects."""

import json
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

import py_trees
from py_trees import behaviour

from talking_trees.core.builders import build_behavior, build_decorator
from talking_trees.core.constants import ConfigKeys, DefaultValues, NodeTypes
from talking_trees.core.registry import get_registry
from talking_trees.core.utils import ParallelPolicyFactory
from talking_trees.models.schema import NodeCategory
from talking_trees.models.tree import TreeDefinition, TreeNodeDefinition


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
        self.node_map: dict[UUID, behaviour.Behaviour] = {}
        self.reverse_map: dict[behaviour.Behaviour, UUID] = {}
        self.max_depth = max_depth

        # Cache decorator types from registry for efficient lookup
        self.decorator_types = self.registry.get_node_types_by_category(
            NodeCategory.DECORATOR
        )

    def deserialize(
        self,
        tree_def: TreeDefinition,
        resolver: Callable[[str], TreeDefinition] | None = None,
    ) -> py_trees.trees.BehaviourTree:
        """Convert TreeDefinition to executable py_trees.BehaviourTree.

        Args:
            tree_def: Tree definition from JSON
            resolver: Optional callback to resolve tree_id references to TreeDefinition

        Returns:
            Executable behaviour tree

        Raises:
            ValueError: If tree definition is invalid
        """
        self.node_map = {}
        self.reverse_map = {}

        # Resolve subtree references first (with cycle detection)
        visited_refs = set()
        resolved_root = self._resolve_subtrees(
            tree_def.root, tree_def.subtrees, visited_refs, resolver
        )

        # Build the tree recursively (with depth limits)
        root_node = self._build_node(resolved_root, depth=0)

        # Create BehaviourTree wrapper
        tree = py_trees.trees.BehaviourTree(root=root_node)

        return tree

    def _resolve_subtrees(
        self,
        node: TreeNodeDefinition,
        subtrees: dict[str, TreeNodeDefinition],
        visited_refs: set[str],
        resolver: Callable[[str], TreeDefinition] | None = None,
    ) -> TreeNodeDefinition:
        """Resolve $ref, tree_file, and tree_id pointers with cycle detection.

        Args:
            node: Node definition (may have $ref, tree_file, or tree_id)
            subtrees: Available subtree definitions
            visited_refs: Set of already visited refs (for cycle detection)
            resolver: Optional callback to resolve tree_id references

        Returns:
            Resolved node definition

        Raises:
            ValueError: If referenced subtree not found or circular reference detected
        """
        # If this node has a $ref, replace it with the subtree
        if node.ref:
            ref_name = node.ref.removeprefix("#/subtrees/")

            # Cycle detection: check if we've already visited this ref
            if ref_name in visited_refs:
                raise ValueError(
                    f"Circular subtree reference detected: {node.ref} (path: {visited_refs})"
                )

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

        # Handle external file reference
        if node.tree_file:
            ref_key = f"file:{node.tree_file}"
            if ref_key in visited_refs:
                raise ValueError(f"Circular subtree reference detected: {node.tree_file}")
            visited_refs.add(ref_key)

            file_path = Path(node.tree_file)
            if not file_path.exists():
                raise ValueError(f"Subtree file not found: {node.tree_file}")
            with open(file_path) as f:
                ext_tree = TreeDefinition.model_validate(json.load(f))

            # Apply parameter map (blackboard key remapping)
            resolved_root = ext_tree.root
            if node.parameter_map:
                resolved_root = self._apply_parameter_map(resolved_root, node.parameter_map)

            node = TreeNodeDefinition(
                node_type=resolved_root.node_type,
                node_id=node.node_id,
                name=node.name or resolved_root.name,
                config=resolved_root.config,
                description=node.description or resolved_root.description,
                children=resolved_root.children,
            )

        # Handle external ID reference
        if node.tree_id and resolver:
            ref_key = f"id:{node.tree_id}"
            if ref_key in visited_refs:
                raise ValueError(f"Circular subtree reference detected: {node.tree_id}")
            visited_refs.add(ref_key)

            ext_tree = resolver(node.tree_id)
            resolved_root = ext_tree.root
            if node.parameter_map:
                resolved_root = self._apply_parameter_map(resolved_root, node.parameter_map)

            node = TreeNodeDefinition(
                node_type=resolved_root.node_type,
                node_id=node.node_id,
                name=node.name or resolved_root.name,
                config=resolved_root.config,
                description=node.description or resolved_root.description,
                children=resolved_root.children,
            )

        # Recursively resolve children (share visited_refs to detect cycles)
        if node.children:
            resolved_children = [
                self._resolve_subtrees(child, subtrees, visited_refs, resolver)
                for child in node.children
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

    def _apply_parameter_map(
        self, node: TreeNodeDefinition, param_map: dict[str, str]
    ) -> TreeNodeDefinition:
        """Remap blackboard keys in node configs according to parameter_map.

        Args:
            node: Node to remap
            param_map: Mapping of {local_key: subtree_key}

        Returns:
            Node with remapped config keys
        """
        config = dict(node.config) if node.config else {}
        # Remap variable/key references in config
        for local_key, subtree_key in param_map.items():
            for config_key in ["variable", "key", "var1_key", "var2_key", "source_key", "target_key"]:
                if config.get(config_key) == subtree_key:
                    config[config_key] = local_key

        children = [
            self._apply_parameter_map(child, param_map)
            for child in node.children
        ]

        return TreeNodeDefinition(
            node_type=node.node_type,
            node_id=node.node_id,
            name=node.name,
            config=config,
            description=node.description,
            children=children,
        )

    def _build_node(
        self, node_def: TreeNodeDefinition, depth: int = 0
    ) -> behaviour.Behaviour:
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
            # Fallback 1: try _py_trees_class from config if node_type not found
            py_trees_class = node_def.config.get("_py_trees_class") if node_def.config else None
            if py_trees_class:
                implementation = self.registry.get_implementation(py_trees_class)

            # Fallback 2: Handle generic CheckBlackboardCondition
            if implementation is None and node_def.node_type == "CheckBlackboardCondition":
                # Infer specific implementation from config
                config = node_def.config or {}
                if "value" in config and "operator" in config:
                    # Has comparison value/operator -> CheckBlackboardVariableValue
                    implementation = self.registry.get_implementation("CheckBlackboardVariableValue")
                elif "variable" in config:
                    # Just checks existence -> CheckBlackboardVariableExists
                    implementation = self.registry.get_implementation("CheckBlackboardVariableExists")

            if implementation is None:
                raise ValueError(f"Unknown node type: {node_def.node_type}")

        # Handle different node categories differently
        if node_def.node_type in [NodeTypes.SEQUENCE, NodeTypes.SELECTOR]:
            # Composites: build children first, then composite
            return self._build_composite(node_def, depth)
        elif node_def.node_type == NodeTypes.PARALLEL:
            return self._build_parallel(node_def, depth)
        elif node_def.node_type in self.decorator_types:
            # Decorators: need child in constructor
            # Uses cached set from registry for efficient lookup
            return self._build_decorator(node_def, depth)
        else:
            # Simple behaviors (leaf nodes)
            return self._build_behavior(node_def)

    def _build_composite(
        self, node_def: TreeNodeDefinition, depth: int
    ) -> behaviour.Behaviour:
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
        if node_def.node_type == NodeTypes.SEQUENCE:
            memory = node_def.config.get(ConfigKeys.MEMORY, True)
            composite = py_trees.composites.Sequence(
                name=node_def.name, memory=memory, children=children
            )
        elif node_def.node_type == NodeTypes.SELECTOR:
            memory = node_def.config.get(ConfigKeys.MEMORY, False)
            composite = py_trees.composites.Selector(
                name=node_def.name, memory=memory, children=children
            )
        else:
            raise ValueError(f"Unknown composite type: {node_def.node_type}")

        # Store UUID mapping
        self._store_node_mapping(node_def.node_id, composite)

        return composite

    def _build_parallel(
        self, node_def: TreeNodeDefinition, depth: int
    ) -> behaviour.Behaviour:
        """Build a parallel node.

        Args:
            node_def: Node definition
            depth: Current depth in tree

        Returns:
            Parallel behaviour
        """
        # Build children first (increment depth)
        children = [self._build_node(child, depth + 1) for child in node_def.children]

        # Create policy using factory
        policy_name = node_def.config.get(ConfigKeys.POLICY, DefaultValues.POLICY)
        synchronise = node_def.config.get(ConfigKeys.SYNCHRONISE, DefaultValues.SYNCHRONISE)
        policy = ParallelPolicyFactory.create(policy_name, synchronise)

        # Create parallel
        parallel = py_trees.composites.Parallel(
            name=node_def.name, policy=policy, children=children
        )

        # Store UUID mapping
        self._store_node_mapping(node_def.node_id, parallel)

        return parallel

    def _build_decorator(
        self, node_def: TreeNodeDefinition, depth: int
    ) -> behaviour.Behaviour:
        """Build a decorator node using the builder registry.

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

        # Use builder registry to create decorator
        decorator = build_decorator(
            node_def.node_type, node_def.name, node_def.config or {}, child
        )

        # Store UUID mapping
        self._store_node_mapping(node_def.node_id, decorator)

        return decorator

    def _build_behavior(self, node_def: TreeNodeDefinition) -> behaviour.Behaviour:
        """Build a leaf behavior node using the builder registry.

        Args:
            node_def: Node definition

        Returns:
            Behavior instance
        """
        # Use builder registry to create the behavior
        # Use _py_trees_class from config if available (for generic node types)
        config = node_def.config or {}
        node_type_to_build = config.get("_py_trees_class", node_def.node_type)

        # Handle generic CheckBlackboardCondition
        if node_type_to_build == "CheckBlackboardCondition":
            if "value" in config and "operator" in config:
                node_type_to_build = "CheckBlackboardVariableValue"
            elif "variable" in config:
                node_type_to_build = "CheckBlackboardVariableExists"

        node = build_behavior(node_type_to_build, node_def.name, config)

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
        node._talkingtrees_uuid = uuid

    def get_node_uuid(self, node: behaviour.Behaviour) -> UUID | None:
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
        return getattr(node, "_talkingtrees_uuid", None)

    def get_node_by_uuid(self, uuid: UUID) -> behaviour.Behaviour | None:
        """Get a py_trees node by UUID.

        Args:
            uuid: Tree definition UUID

        Returns:
            Behaviour instance if found, None otherwise
        """
        return self.node_map.get(uuid)
