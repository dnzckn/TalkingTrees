"""Tree partitioning for distributed execution.

Splits a monolithic tree into partitions that can be executed on
different machines, connected by RemoteSubtree proxy nodes.
"""

from uuid import UUID, uuid4

from talking_trees.models.tree import (
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)


def partition_tree(
    tree: TreeDefinition,
    partition_map: dict[str, str],
) -> dict[str, TreeDefinition]:
    """Partition a tree into distributed subtrees.

    Takes a monolithic tree and a mapping of node_id -> endpoint,
    and produces multiple tree definitions: one for the "main" tree
    (with RemoteSubtree proxies at partition boundaries) and one for
    each remote partition.

    Args:
        tree: Monolithic tree to partition
        partition_map: Dict of {node_id_str: endpoint_url}

    Returns:
        Dict of {partition_name: TreeDefinition} where "main" is the
        coordinating tree and other keys are endpoint-based names.
    """
    partition_ids = {UUID(k) for k in partition_map}
    result = {}
    remote_partitions: dict[str, list[TreeNodeDefinition]] = {}

    def process_node(node: TreeNodeDefinition) -> TreeNodeDefinition:
        if node.node_id in partition_ids:
            endpoint = partition_map[str(node.node_id)]

            # Create the remote partition tree
            partition_key = _endpoint_to_key(endpoint)
            if partition_key not in remote_partitions:
                remote_partitions[partition_key] = []

            # Store the original node as a partition root
            remote_partitions[partition_key].append(node)

            # Replace with RemoteSubtree proxy
            return TreeNodeDefinition(
                node_type="RemoteSubtree",
                node_id=node.node_id,
                name=f"[remote] {node.name}",
                config={
                    "endpoint": endpoint,
                    "timeout_ms": 5000,
                },
            )

        # Recursively process children
        if node.children:
            new_children = [process_node(child) for child in node.children]
            return TreeNodeDefinition(
                node_type=node.node_type,
                node_id=node.node_id,
                name=node.name,
                config=node.config,
                description=node.description,
                children=new_children,
                blackboard_input=node.blackboard_input,
                blackboard_output=node.blackboard_output,
                macro=node.macro,
            )

        return node

    # Build main tree with proxies
    main_root = process_node(tree.root)
    main_tree = TreeDefinition(
        tree_id=tree.tree_id,
        metadata=tree.metadata.model_copy(deep=True),
        root=main_root,
    )
    result["main"] = main_tree

    # Build partition trees
    for partition_key, nodes in remote_partitions.items():
        for i, node in enumerate(nodes):
            partition_name = f"{partition_key}_{i}" if len(nodes) > 1 else partition_key
            partition_tree_def = TreeDefinition(
                tree_id=uuid4(),
                metadata=TreeMetadata(
                    name=f"Partition: {node.name}",
                    version=tree.metadata.version,
                    description=f"Distributed partition from {tree.metadata.name}",
                    status=TreeStatus.DRAFT,
                ),
                root=node,
            )
            result[partition_name] = partition_tree_def

    return result


def _endpoint_to_key(endpoint: str) -> str:
    """Convert an endpoint URL to a safe dictionary key."""
    return (
        endpoint
        .replace("http://", "")
        .replace("https://", "")
        .replace(":", "_")
        .replace("/", "_")
        .rstrip("_")
    )
