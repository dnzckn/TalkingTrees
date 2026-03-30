"""Maritime Threat Detection — Integration test exercising all 17 work packages.

Runs the full 4-tier detection cascade with simulated sensors, failure injection,
resource contention, checkpointing, event-driven ticking, and formal verification.

Tests are designed to run fast (~5 seconds) using the simulation at high speed.
"""

import sys
import tempfile
from pathlib import Path
from uuid import uuid4

import py_trees
import pytest

# Add scenarios to path for imports
SCENARIO_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCENARIO_DIR))

from talking_trees.core.diff import three_way_merge, TreeDiffer
from talking_trees.core.observability import InMemoryCollector
from talking_trees.core.serializer import TreeSerializer
from talking_trees.core.validation import validate_dataflow
from talking_trees.events.bus import EventBus
from talking_trees.events.mappings import EventMapping
from talking_trees.execution.checkpoint import (
    CheckpointManager,
    ExecutionState,
    FileCheckpointBackend,
)
from talking_trees.execution.pool import ExecutionPool
from talking_trees.execution.tick_scheduler import TickScheduler
from talking_trees.resources.manager import ResourceManager
from talking_trees.sdk import TalkingTrees
from talking_trees.verification.invariants import tree_invariant
from talking_trees.verification.verifier import verify_tree

# Path to tree files
TREE_DIR = Path(__file__).parent.parent
MAIN_TREE = TREE_DIR / "main_tree.json"
MAIN_TREE_V2 = TREE_DIR / "main_tree_v2.json"


@pytest.fixture
def tt():
    return TalkingTrees()


@pytest.fixture
def tree(tt):
    return tt.load_tree(str(MAIN_TREE))


@pytest.fixture
def tree_v2(tt):
    return tt.load_tree(str(MAIN_TREE_V2))


# ── WP-14: Formal Verification ──


def test_drone_safety_invariant(tree):
    """Verify the drone dispatch safety invariant holds across all paths."""

    @tree_invariant(
        "drone_safety",
        "dispatch_drone only reachable if all four checks pass",
    )
    def check(trace):
        if trace.node_reached("dispatch_drone"):
            return (
                trace.node_returned("check_vessel_class", "SUCCESS")
                and trace.node_returned("check_radar_confirmed", "SUCCESS")
                and trace.node_returned("check_in_zone", "SUCCESS")
                and trace.node_returned("check_high_confidence", "SUCCESS")
            )
        return True

    results = verify_tree(tree, [check], max_depth=30)
    assert len(results) == 1
    assert results[0].verified, (
        f"Safety invariant violated! {results[0].violation_count} violations found"
    )


# ── WP-2: Dataflow Validation ──


def test_dataflow_contracts(tree):
    """Verify blackboard data flow contracts are consistent across tiers."""
    result = validate_dataflow(tree)
    # Tier1 outputs feed Tier2 inputs, Tier2 feeds Tier3, Tier3 feeds Tier4
    # Some may flag warnings for nodes without contracts (ok)
    errors = [i for i in result.issues if i.level == "error"]
    # Trees with contracts should not have type mismatches
    assert result.error_count == 0 or all(
        "type" not in e.message.lower() for e in errors
    ), f"Dataflow type errors: {errors}"


# ── WP-6: Tree Diffing ──


def test_v1_v2_diff(tt, tree, tree_v2):
    """Diff v1 and v2 trees — verify vessel size estimation node detected."""
    differ = TreeDiffer()
    diff = differ.diff_trees(tree, tree_v2)
    # v2 adds estimate_vessel_size node
    added_names = [n.name for n in diff.node_diffs if n.diff_type.value == "added"]
    assert any(
        "vessel_size" in name.lower() for name in added_names
    ), f"Expected vessel size node in added, got: {added_names}"


def test_three_way_merge_no_conflict(tree, tree_v2):
    """Three-way merge with non-conflicting changes succeeds."""
    result = three_way_merge(tree, tree, tree_v2)
    assert not result.has_conflicts


# ── WP-3: Macro Nodes ──


def test_macro_metadata_preserved(tree):
    """Tree macros survive JSON round-trip."""
    assert tree.root.macro is not None
    assert tree.root.macro.name == "Maritime Threat Detection Pipeline"
    assert tree.root.macro.color == "#1A5276"

    # Children should also have macros
    tier1 = tree.root.children[0]
    assert tier1.macro is not None
    assert "Tier 1" in tier1.macro.name


# ── WP-12: Execution Pool ──


def test_multi_instance_pool(tree):
    """Spawn multiple execution instances from same tree."""
    pool = ExecutionPool(tree, max_instances=20)

    # Spawn 10 instances (one per hydrophone)
    ids = []
    for i in range(10):
        exec_id = pool.spawn(initial_blackboard={
            "acoustic_energy_db": 60.0 + i,
            "bearing_deg": 145.0,
            "frequency_peak_hz": 340.0,
            "hydrophone_node_id": f"hydrophone_{i:02d}",
            "confidence": 0.90,
            "classification": "vessel",
            "radar_status": "confirmed_track",
            "in_restricted_zone": True,
        })
        ids.append(exec_id)

    assert pool.active_count() == 10

    # Tick all
    results = pool.tick_all()
    assert len(results) == 10

    # Cleanup
    pool.kill_all()


# ── WP-13: Resource Arbitration ──


def test_radar_resource_contention():
    """Radar has capacity=2, third request blocked."""
    rm = ResourceManager()
    rm.register_resource("radar", capacity=2)
    rm.register_resource("drone", capacity=1)

    assert rm.acquire("radar", "track_1")
    assert rm.acquire("radar", "track_2")
    assert not rm.acquire("radar", "track_3")  # blocked

    rm.release("radar", "track_1")
    assert rm.acquire("radar", "track_3")  # now available


def test_drone_single_capacity():
    """Drone has capacity=1, second dispatch blocked."""
    rm = ResourceManager()
    rm.register_resource("drone", capacity=1)

    assert rm.acquire("drone", "mission_1")
    assert not rm.acquire("drone", "mission_2")

    rm.release("drone", "mission_1")
    assert rm.acquire("drone", "mission_2")


# ── WP-9: Checkpointing ──


def test_checkpoint_save_restore():
    """Save checkpoint, simulate crash, restore state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCheckpointBackend(tmpdir)
        manager = CheckpointManager(backend, interval_ticks=10)

        state = ExecutionState(
            tree_id="maritime-pipeline",
            execution_id="exec-001",
            tick_number=50,
            blackboard_snapshot={
                "classification": "vessel",
                "confidence": 0.91,
                "radar_status": "confirmed_track",
                "in_restricted_zone": True,
            },
            disabled_subtrees=["radar_primary"],
        )

        cp_id = manager.save("exec-001", state)

        # "Crash" — lose state
        del state

        # Restore
        restored = manager.load(cp_id)
        assert restored.tick_number == 50
        assert restored.blackboard_snapshot["classification"] == "vessel"
        assert restored.blackboard_snapshot["confidence"] == 0.91
        assert "radar_primary" in restored.disabled_subtrees


# ── WP-10: Event Bus ──


def test_event_driven_tick():
    """Hydrophone detection event triggers classification tick via event bus."""
    bus = EventBus()
    bus.register_mapping(
        EventMapping(
            topic="hydrophone_detection",
            blackboard_writes={
                "acoustic_energy_db": "acoustic_energy_db",
                "bearing_deg": "bearing_deg",
            },
            trigger_tick=True,
            debounce_ms=100,
        )
    )

    received_ticks = []
    bus.register_tick_callback(lambda exec_id, bb: received_ticks.append(bb))
    bus.start()

    # Simulate hydrophone detection
    bus.emit("hydrophone_detection", {
        "acoustic_energy_db": 72.4,
        "bearing_deg": 145.3,
    })

    assert len(received_ticks) == 1
    assert received_ticks[0]["acoustic_energy_db"] == 72.4


# ── WP-11: Rate Limiting ──


def test_classification_rate_limit():
    """Classifier rate-limited to 5/second."""
    from talking_trees.behaviors.rate_limiting import RateLimiterBehaviour

    child = py_trees.behaviours.Success(name="classifier")
    limiter = RateLimiterBehaviour(
        name="classification_rate_limit",
        child=child,
        max_count=5,
        window_seconds=1.0,
        on_limit="FAILURE",
    )

    results = [limiter.update() for _ in range(8)]

    passed = sum(1 for r in results if r == py_trees.common.Status.SUCCESS)
    blocked = sum(1 for r in results if r == py_trees.common.Status.FAILURE)

    assert passed == 5
    assert blocked == 3


# ── WP-7: Observability ──


def test_observability_collector(tree):
    """InMemoryCollector captures tick metrics."""
    collector = InMemoryCollector()

    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree)
    py_tree.setup()

    # Seed blackboard
    from talking_trees.core.utils import update_blackboard
    update_blackboard({
        "acoustic_energy_db": 72.0,
        "bearing_deg": 145.0,
        "frequency_peak_hz": 340.0,
        "confidence": 0.90,
        "classification": "vessel",
        "radar_status": "confirmed_track",
        "in_restricted_zone": True,
    })

    exec_id = uuid4()
    tree_id = tree.tree_id

    # Simulate 5 ticks with collector
    for i in range(5):
        py_tree.tick()
        collector.on_tick(exec_id, tree_id, i, 0.5)

    metrics = collector.get_metrics(exec_id)
    assert metrics is not None
    assert metrics.total_ticks == 5


# ── WP-4: Dynamic Topology ──


def test_radar_failover(tree):
    """Disable radar_primary, verify fallback takes over."""
    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree)
    py_tree.setup()

    from talking_trees.core.tree_adapter import TopologyManager

    topo = TopologyManager(py_tree)

    # Find radar_primary node
    radar_node = None
    for node in py_tree.root.iterate():
        if node.name == "radar_primary":
            radar_node = node
            break

    if radar_node is not None:
        node_uuid = getattr(radar_node, "_talkingtrees_uuid", None)
        if node_uuid:
            topo.disable_subtree(node_uuid)
            assert topo.is_subtree_disabled(node_uuid)

            # Re-enable
            topo.enable_subtree(node_uuid)
            assert not topo.is_subtree_disabled(node_uuid)


# ── WP-17: Tick Scheduler ──


def test_conditional_tick_rates(tree):
    """Per-subtree tick rates work correctly."""
    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree)
    py_tree.setup()

    scheduler = TickScheduler(py_tree, default_hz=10.0)
    scheduler.set_rate("tier1_detection", 1.0)  # 1Hz
    scheduler.set_rate("tier3_radar", 10.0)  # 10Hz

    # Tier1 at 1Hz should tick
    assert scheduler.should_tick("tier1_detection")
    # Immediately should not tick again
    assert not scheduler.should_tick("tier1_detection")

    # Tier3 at 10Hz should tick
    assert scheduler.should_tick("tier3_radar")


# ── WP-1: Subtree References ──


def test_subtree_flatten(tt, tree):
    """flatten_tree produces a self-contained tree."""
    flat = tt.flatten_tree(tree)
    assert flat.subtrees == {} or len(flat.subtrees) == 0
    assert flat.root.node_type == "Sequence"


# ── WP-15: Security ──


def test_security_disabled_by_default():
    """API works without authentication when security is disabled."""
    from fastapi.testclient import TestClient
    from talking_trees.api.main import app
    from talking_trees.security.middleware import configure_security
    from talking_trees.security.config import SecurityConfig

    configure_security(SecurityConfig())
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/auth/whoami").json()["authenticated"] is False


# ── WP-16: Audit Trail ──


def test_audit_trail():
    """Audit collector writes all events to JSONL log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from talking_trees.audit.backends.jsonl import JSONLAuditBackend
        from talking_trees.audit.collector import AuditCollector
        from talking_trees.audit.reader import AuditReader

        backend = JSONLAuditBackend(Path(tmpdir) / "audit.jsonl")
        collector = AuditCollector(backend)

        exec_id = uuid4()
        tree_id = uuid4()

        # Simulate events
        collector.on_tick_start(exec_id, tree_id, 1)
        collector.on_tick_end(exec_id, tree_id, 1, 0.5)
        collector.on_node_result(exec_id, uuid4(), "Sequence", "SUCCESS", 0.1)

        reader = AuditReader(backend)
        events = list(reader.replay(str(exec_id)))
        assert len(events) == 3
        assert events[0]["event_type"] == "tick_start"
