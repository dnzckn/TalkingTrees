"""Tests for WP-14: Formal Verification / Property Checking."""

from uuid import uuid4

from talking_trees.models.tree import (
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)
from talking_trees.verification.invariants import Invariant, tree_invariant
from talking_trees.verification.verifier import verify_tree


def _make_tree(name, root):
    return TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(name=name, version="1.0.0", status=TreeStatus.DRAFT),
        root=root,
    )


def test_sequence_invariant_verified():
    """In a sequence, B is reached only if A succeeds."""
    root = TreeNodeDefinition(
        node_type="Sequence", name="seq",
        children=[
            TreeNodeDefinition(node_type="Action", name="A"),
            TreeNodeDefinition(node_type="Action", name="B"),
        ],
    )
    tree = _make_tree("SeqTest", root)

    @tree_invariant("b_requires_a", "B only reached if A succeeds")
    def check(trace):
        if trace.node_reached("B"):
            return trace.node_returned("A", "SUCCESS")
        return True

    results = verify_tree(tree, [check])
    assert len(results) == 1
    assert results[0].verified


def test_selector_all_branches_checked():
    """Selector explores all branches."""
    root = TreeNodeDefinition(
        node_type="Selector", name="sel",
        children=[
            TreeNodeDefinition(node_type="Action", name="try1"),
            TreeNodeDefinition(node_type="Action", name="try2"),
        ],
    )
    tree = _make_tree("SelTest", root)

    @tree_invariant("at_least_one_tried", "At least one branch is tried")
    def check(trace):
        return trace.node_reached("try1") or trace.node_reached("try2")

    results = verify_tree(tree, [check])
    assert results[0].verified


def test_violation_detected():
    """Invariant violation produces violation traces."""
    root = TreeNodeDefinition(
        node_type="Selector", name="sel",
        children=[
            TreeNodeDefinition(node_type="Action", name="dangerous"),
            TreeNodeDefinition(node_type="Action", name="safe"),
        ],
    )
    tree = _make_tree("ViolationTest", root)

    # This invariant says "dangerous" should never succeed
    # But in a Selector, if "dangerous" returns SUCCESS, the Selector short-circuits
    @tree_invariant("no_dangerous", "Dangerous action must not succeed")
    def check(trace):
        return not trace.node_returned("dangerous", "SUCCESS")

    results = verify_tree(tree, [check])
    assert not results[0].verified
    assert results[0].violation_count > 0


def test_depth_limit():
    """Max depth prevents infinite exploration."""
    # Deep nested tree
    current = TreeNodeDefinition(node_type="Action", name="leaf")
    for i in range(20):
        current = TreeNodeDefinition(
            node_type="Sequence", name=f"level_{i}",
            children=[current],
        )
    tree = _make_tree("DeepTest", current)

    results = verify_tree(tree, [
        Invariant(name="always_true", description="", check=lambda t: True),
    ], max_depth=5)

    assert results[0].verified
    assert results[0].total_paths_checked > 0


def test_running_exploration():
    """RUNNING mode explores RUNNING as third outcome."""
    root = TreeNodeDefinition(
        node_type="Action", name="leaf",
    )
    tree = _make_tree("RunningTest", root)

    results_no_running = verify_tree(tree, [
        Invariant(name="count", description="", check=lambda t: True),
    ], explore_running=False)

    results_with_running = verify_tree(tree, [
        Invariant(name="count", description="", check=lambda t: True),
    ], explore_running=True)

    # With RUNNING, should have more paths
    assert results_with_running[0].total_paths_checked > results_no_running[0].total_paths_checked


def test_decorator_invariant():
    """Decorator for defining invariants works."""
    @tree_invariant("test_inv", "A test invariant")
    def my_check(trace):
        return True

    assert isinstance(my_check, Invariant)
    assert my_check.name == "test_inv"
