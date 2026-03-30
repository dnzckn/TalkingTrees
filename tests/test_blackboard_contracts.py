"""Tests for WP2: Typed Blackboard Contracts."""

from uuid import uuid4

from talking_trees.core.validation import validate_dataflow
from talking_trees.models.tree import (
    BlackboardPort,
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)


def _make_tree(name, root):
    return TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(name=name, version="1.0.0", status=TreeStatus.DRAFT),
        root=root,
    )


def test_valid_dataflow():
    """Valid dataflow: output feeds input."""
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="seq",
        children=[
            TreeNodeDefinition(
                node_type="Action",
                name="producer",
                blackboard_output={"sensor_val": BlackboardPort(type="float")},
            ),
            TreeNodeDefinition(
                node_type="Action",
                name="consumer",
                blackboard_input={"sensor_val": BlackboardPort(type="float")},
            ),
        ],
    )
    tree = _make_tree("ValidFlow", root)
    result = validate_dataflow(tree)
    assert result.is_valid


def test_missing_required_input():
    """Error: required input not provided by any upstream."""
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="seq",
        children=[
            TreeNodeDefinition(
                node_type="Action",
                name="consumer",
                blackboard_input={"missing_key": BlackboardPort(type="float")},
            ),
        ],
    )
    tree = _make_tree("MissingInput", root)
    result = validate_dataflow(tree)
    assert not result.is_valid
    assert result.error_count == 1
    assert "missing_key" in result.issues[0].message


def test_type_mismatch():
    """Error: type mismatch between output and input."""
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="seq",
        children=[
            TreeNodeDefinition(
                node_type="Action",
                name="producer",
                blackboard_output={"val": BlackboardPort(type="float")},
            ),
            TreeNodeDefinition(
                node_type="Action",
                name="consumer",
                blackboard_input={"val": BlackboardPort(type="str")},
            ),
        ],
    )
    tree = _make_tree("TypeMismatch", root)
    result = validate_dataflow(tree)
    assert not result.is_valid
    assert any("type" in i.message.lower() for i in result.issues)


def test_initial_blackboard_satisfies_input():
    """Input satisfied by initial blackboard."""
    root = TreeNodeDefinition(
        node_type="Action",
        name="consumer",
        blackboard_input={"ext_val": BlackboardPort(type="float")},
    )
    tree = _make_tree("InitialBB", root)
    result = validate_dataflow(tree, initial_blackboard_keys={"ext_val": "float"})
    assert result.is_valid


def test_no_contracts_passes():
    """Trees without contracts should pass validation (backward compat)."""
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="seq",
        children=[
            TreeNodeDefinition(node_type="Success", name="step1"),
            TreeNodeDefinition(node_type="Success", name="step2"),
        ],
    )
    tree = _make_tree("NoContracts", root)
    result = validate_dataflow(tree)
    assert result.is_valid
    assert result.error_count == 0


def test_optional_input_not_required():
    """Optional inputs should not produce errors when missing."""
    root = TreeNodeDefinition(
        node_type="Action",
        name="consumer",
        blackboard_input={"opt_val": BlackboardPort(type="float", required=False)},
    )
    tree = _make_tree("OptionalInput", root)
    result = validate_dataflow(tree)
    assert result.is_valid


def test_orphan_output_warning():
    """Warning: output key written but never read."""
    root = TreeNodeDefinition(
        node_type="Action",
        name="producer",
        blackboard_output={"unused_key": BlackboardPort(type="float")},
    )
    tree = _make_tree("OrphanOutput", root)
    result = validate_dataflow(tree)
    assert result.is_valid  # warnings don't make it invalid
    assert result.warning_count >= 1
