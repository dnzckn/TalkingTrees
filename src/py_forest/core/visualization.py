"""Tree visualization and graph generation."""

from py_forest.models.execution import ExecutionSnapshot
from py_forest.models.visualization import (
    DotGraph,
    DotGraphOptions,
    VisualizationNode,
    VisualizationSnapshot,
)


class TreeVisualizer:
    """Generate visualizations from tree snapshots.

    Supports:
    - Graphviz DOT format for static diagrams
    - py_trees_js JSON format for interactive visualization
    """

    # Status colors (matching py_trees conventions)
    STATUS_COLORS = {
        "SUCCESS": "#5CB85C",  # Green
        "FAILURE": "#D9534F",  # Red
        "RUNNING": "#5BC0DE",  # Blue
        "INVALID": "#999999",  # Gray
    }

    # Node type colors (matching py_trees_ros_viewer)
    TYPE_COLORS = {
        "Sequence": "#FFA500",  # Orange
        "Selector": "#00FFFF",  # Cyan
        "Parallel": "#FFFF00",  # Yellow
        "Behaviour": "#555555",  # Dark gray
        "Decorator": "#DDDDDD",  # Light gray
    }

    def __init__(self):
        """Initialize visualizer."""
        pass

    def to_dot(
        self, snapshot: ExecutionSnapshot, options: DotGraphOptions | None = None
    ) -> DotGraph:
        """Convert execution snapshot to Graphviz DOT format.

        Args:
            snapshot: Execution snapshot
            options: Visualization options

        Returns:
            DOT graph representation
        """
        if options is None:
            options = DotGraphOptions()

        lines = []

        # Graph header
        lines.append("digraph BehaviorTree {")
        lines.append(f'    rankdir="{options.rankdir}";')
        lines.append(
            f'    node [shape="{options.node_shape}", '
            f'fontname="{options.font_name}", '
            f"fontsize={options.font_size}];"
        )
        lines.append("")

        # Process nodes recursively
        self._add_node_to_dot(
            snapshot.tree["root"],
            lines,
            options,
            snapshot.node_states,
        )

        lines.append("}")

        return DotGraph(source="\n".join(lines), options=options)

    def _add_node_to_dot(
        self,
        node: dict,
        lines: list[str],
        options: DotGraphOptions,
        node_states: dict,
        parent_id: str | None = None,
    ) -> None:
        """Recursively add node to DOT graph.

        Args:
            node: Node dictionary from snapshot
            lines: Output lines list
            options: Visualization options
            node_states: Node states from snapshot
            parent_id: Parent node ID
        """
        node_id = node["id"]
        node_name = node["name"]
        node_type = node["type"]

        # Get node state
        state = node_states.get(node_id, {})
        status = state.get("status", "INVALID")

        # Build label
        label_parts = [node_name]
        if options.include_status:
            label_parts.append(f"[{status}]")
        if options.include_ids:
            label_parts.append(f"\\n{node_id}")

        label = " ".join(label_parts)

        # Determine color
        color = "#FFFFFF"  # Default white
        if options.use_colors:
            # Color by status if available, otherwise by type
            if status in self.STATUS_COLORS:
                color = self.STATUS_COLORS[status]
            else:
                # Determine type category
                if node_type in ["Sequence", "Selector", "Parallel"]:
                    color = self.TYPE_COLORS[node_type]
                elif node_type.endswith("Decorator"):
                    color = self.TYPE_COLORS["Decorator"]
                else:
                    color = self.TYPE_COLORS["Behaviour"]

        # Add node
        lines.append(
            f'    "{node_id}" [label="{label}", fillcolor="{color}", style=filled];'
        )

        # Add edge from parent
        if parent_id:
            lines.append(f'    "{parent_id}" -> "{node_id}";')

        # Process children
        for child in node.get("children", []):
            self._add_node_to_dot(child, lines, options, node_states, node_id)

    def to_pytrees_js(
        self, snapshot: ExecutionSnapshot, include_blackboard: bool = False
    ) -> VisualizationSnapshot:
        """Convert execution snapshot to py_trees_js format.

        Args:
            snapshot: Execution snapshot
            include_blackboard: Include blackboard data

        Returns:
            Visualization snapshot compatible with py_trees_js
        """
        timestamp = snapshot.timestamp.timestamp() if snapshot.timestamp else 0.0

        vis_snapshot = VisualizationSnapshot(
            timestamp=timestamp,
            changed="true",  # Always true for now
            behaviours={},
            visited_path=[],
        )

        # Process nodes recursively
        self._add_node_to_vis(
            snapshot.tree["root"],
            vis_snapshot,
            snapshot.node_states,
        )

        # Add blackboard data if requested
        if include_blackboard:
            # Simple blackboard representation
            # In a real implementation, this would extract actual blackboard values
            vis_snapshot.blackboard["data"] = snapshot.blackboard

        return vis_snapshot

    def _add_node_to_vis(
        self,
        node: dict,
        vis_snapshot: VisualizationSnapshot,
        node_states: dict,
    ) -> None:
        """Recursively add node to visualization snapshot.

        Args:
            node: Node dictionary from snapshot
            vis_snapshot: Visualization snapshot being built
            node_states: Node states from snapshot
        """
        node_id = node["id"]
        node_name = node["name"]
        node_type = node["type"]

        # Get node state
        state = node_states.get(node_id, {})
        status = state.get("status", "INVALID")
        is_active = state.get("is_active", False)

        # Determine color by type
        if node_type in ["Sequence", "Selector", "Parallel"]:
            colour = self.TYPE_COLORS[node_type]
        elif node_type.endswith("Decorator"):
            colour = self.TYPE_COLORS["Decorator"]
        else:
            colour = self.TYPE_COLORS["Behaviour"]

        # Create visualization node
        vis_node = VisualizationNode(
            id=node_id,
            status=status,
            name=node_name,
            colour=colour,
            details="",
            children=[child["id"] for child in node.get("children", [])],
            data={
                "Class": node_type,
                "Feedback": state.get("feedback", ""),
            },
        )

        vis_snapshot.behaviours[node_id] = vis_node

        # Add to visited path if active
        if is_active:
            vis_snapshot.visited_path.append(node_id)

        # Process children
        for child in node.get("children", []):
            self._add_node_to_vis(child, vis_snapshot, node_states)

    def snapshot_to_svg(
        self, snapshot: ExecutionSnapshot, options: DotGraphOptions | None = None
    ) -> str:
        """Convert snapshot to SVG via Graphviz.

        Note: Requires graphviz package to be installed.

        Args:
            snapshot: Execution snapshot
            options: Visualization options

        Returns:
            SVG string

        Raises:
            ImportError: If graphviz not installed
        """
        try:
            import graphviz
        except ImportError:
            raise ImportError(
                "graphviz package required for SVG export. "
                "Install with: pip install graphviz"
            )

        dot_graph = self.to_dot(snapshot, options)
        graph = graphviz.Source(dot_graph.source)

        # Render to SVG string
        svg_bytes = graph.pipe(format="svg")
        return svg_bytes.decode("utf-8")

    def snapshot_to_png(
        self, snapshot: ExecutionSnapshot, options: DotGraphOptions | None = None
    ) -> bytes:
        """Convert snapshot to PNG via Graphviz.

        Note: Requires graphviz package to be installed.

        Args:
            snapshot: Execution snapshot
            options: Visualization options

        Returns:
            PNG bytes

        Raises:
            ImportError: If graphviz not installed
        """
        try:
            import graphviz
        except ImportError:
            raise ImportError(
                "graphviz package required for PNG export. "
                "Install with: pip install graphviz"
            )

        dot_graph = self.to_dot(snapshot, options)
        graph = graphviz.Source(dot_graph.source)

        # Render to PNG bytes
        return graph.pipe(format="png")
