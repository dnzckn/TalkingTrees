"""Tree verification engine — enumerates execution paths and checks invariants."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from talking_trees.models.tree import TreeDefinition, TreeNodeDefinition
from talking_trees.verification.invariants import Invariant
from talking_trees.verification.trace import ExecutionTrace

logger = logging.getLogger(__name__)


class VerificationResult(BaseModel):
    """Result of verifying one invariant against a tree."""

    verified: bool = Field(description="Whether the invariant holds")
    invariant_name: str = Field(description="Name of the invariant checked")
    total_paths_checked: int = Field(description="Number of paths explored")
    violation_count: int = Field(default=0, description="Number of violating paths")
    duration_ms: float = Field(description="Verification time in milliseconds")
    violations: list[str] = Field(
        default_factory=list,
        description="String representations of violating traces",
    )


def verify_tree(
    tree: TreeDefinition,
    invariants: list[Invariant],
    max_depth: int = 100,
    explore_running: bool = False,
) -> list[VerificationResult]:
    """Verify invariants against all possible execution paths of a tree.

    Enumerates paths through the tree DAG using DFS. At each node,
    branches on SUCCESS and FAILURE outcomes. Sequences short-circuit
    on FAILURE, Selectors short-circuit on SUCCESS (pruning the search).

    Args:
        tree: Tree definition to verify
        invariants: List of invariants to check
        max_depth: Maximum path depth to prevent infinite exploration
        explore_running: If True, also explore RUNNING as a third outcome

    Returns:
        List of VerificationResult, one per invariant
    """
    start = time.monotonic()

    # Enumerate all execution paths
    statuses = ["SUCCESS", "FAILURE"]
    if explore_running:
        statuses.append("RUNNING")

    all_traces: list[ExecutionTrace] = []
    _enumerate_paths(tree.root, statuses, all_traces, ExecutionTrace(), 0, max_depth)

    elapsed = (time.monotonic() - start) * 1000

    # Check each invariant against all traces
    results = []
    for invariant in invariants:
        inv_start = time.monotonic()
        violations = []

        for trace in all_traces:
            try:
                if not invariant.check(trace):
                    violations.append(repr(trace))
            except Exception as e:
                logger.warning("Invariant '%s' raised exception: %s", invariant.name, e)
                violations.append(f"ERROR: {e} on {repr(trace)}")

        inv_elapsed = (time.monotonic() - inv_start) * 1000

        results.append(VerificationResult(
            verified=len(violations) == 0,
            invariant_name=invariant.name,
            total_paths_checked=len(all_traces),
            violation_count=len(violations),
            duration_ms=round(inv_elapsed, 2),
            violations=violations[:10],  # Limit to first 10
        ))

    return results


def _enumerate_paths(
    node: TreeNodeDefinition,
    statuses: list[str],
    all_traces: list[ExecutionTrace],
    current_trace: ExecutionTrace,
    depth: int,
    max_depth: int,
) -> None:
    """Recursively enumerate execution paths through the tree."""
    if depth > max_depth:
        all_traces.append(current_trace)
        return

    node_type = node.node_type

    # Leaf nodes: branch on each possible status
    if not node.children:
        for status in statuses:
            trace = _clone_trace(current_trace)
            trace.record(str(node.node_id), node.name, status)

            # If node has blackboard_output, simulate writes
            if node.blackboard_output:
                for key in node.blackboard_output:
                    trace.set_blackboard(key, f"<{node.name}:{key}>")

            all_traces.append(trace)
        return

    # Sequence: children execute in order, short-circuit on FAILURE
    if node_type == "Sequence":
        _enumerate_sequence(node, statuses, all_traces, current_trace, depth, max_depth)
        return

    # Selector: children execute in order, short-circuit on SUCCESS
    if node_type == "Selector":
        _enumerate_selector(node, statuses, all_traces, current_trace, depth, max_depth)
        return

    # Decorators: single child, transform status
    if len(node.children) == 1:
        child_traces: list[ExecutionTrace] = []
        _enumerate_paths(node.children[0], statuses, child_traces, current_trace, depth + 1, max_depth)

        for trace in child_traces:
            # Record the decorator with the child's final status
            seq = trace.sequence()
            child_status = seq[-1][1] if seq else "SUCCESS"

            # Inverter flips the status
            if node_type == "Inverter":
                final = "FAILURE" if child_status == "SUCCESS" else "SUCCESS"
            else:
                final = child_status

            trace.record(str(node.node_id), node.name, final)
            all_traces.append(trace)
        return

    # Default: treat as parallel/composite — explore all children independently
    for status in statuses:
        trace = _clone_trace(current_trace)
        trace.record(str(node.node_id), node.name, status)
        for child in node.children:
            _enumerate_paths(child, statuses, all_traces, trace, depth + 1, max_depth)


def _enumerate_sequence(node, statuses, all_traces, current_trace, depth, max_depth):
    """Enumerate paths through a Sequence (short-circuits on FAILURE)."""
    def process_children(child_idx, trace):
        if child_idx >= len(node.children):
            # All children succeeded
            trace.record(str(node.node_id), node.name, "SUCCESS")
            all_traces.append(trace)
            return

        child = node.children[child_idx]
        child_traces: list[ExecutionTrace] = []
        _enumerate_paths(child, statuses, child_traces, trace, depth + 1, max_depth)

        for ct in child_traces:
            seq = ct.sequence()
            last_status = seq[-1][1] if seq else "SUCCESS"

            if last_status == "FAILURE":
                # Short-circuit: sequence fails
                ct.record(str(node.node_id), node.name, "FAILURE")
                all_traces.append(ct)
            elif last_status == "RUNNING":
                ct.record(str(node.node_id), node.name, "RUNNING")
                all_traces.append(ct)
            else:
                # Continue to next child
                process_children(child_idx + 1, ct)

    process_children(0, _clone_trace(current_trace))


def _enumerate_selector(node, statuses, all_traces, current_trace, depth, max_depth):
    """Enumerate paths through a Selector (short-circuits on SUCCESS)."""
    def process_children(child_idx, trace):
        if child_idx >= len(node.children):
            # All children failed
            trace.record(str(node.node_id), node.name, "FAILURE")
            all_traces.append(trace)
            return

        child = node.children[child_idx]
        child_traces: list[ExecutionTrace] = []
        _enumerate_paths(child, statuses, child_traces, trace, depth + 1, max_depth)

        for ct in child_traces:
            seq = ct.sequence()
            last_status = seq[-1][1] if seq else "FAILURE"

            if last_status == "SUCCESS":
                # Short-circuit: selector succeeds
                ct.record(str(node.node_id), node.name, "SUCCESS")
                all_traces.append(ct)
            elif last_status == "RUNNING":
                ct.record(str(node.node_id), node.name, "RUNNING")
                all_traces.append(ct)
            else:
                # Continue to next child
                process_children(child_idx + 1, ct)

    process_children(0, _clone_trace(current_trace))


def _clone_trace(trace: ExecutionTrace) -> ExecutionTrace:
    """Deep copy a trace."""
    new_trace = ExecutionTrace()
    new_trace._visited = list(trace._visited)
    new_trace._blackboard = dict(trace._blackboard)
    return new_trace
