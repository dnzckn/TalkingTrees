"""Tests for WP-9: State Persistence & Recovery."""

import tempfile
from pathlib import Path

from talking_trees.execution.checkpoint import (
    CheckpointManager,
    ExecutionState,
    FileCheckpointBackend,
)


def test_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCheckpointBackend(tmpdir)
        manager = CheckpointManager(backend)

        state = ExecutionState(
            tree_id="tree-1",
            execution_id="exec-1",
            tick_number=42,
            blackboard_snapshot={"sensor": 3.14, "active": True},
            disabled_subtrees=["node-a"],
        )

        cp_id = manager.save("exec-1", state)
        loaded = manager.load(cp_id)

        assert loaded.tick_number == 42
        assert loaded.blackboard_snapshot["sensor"] == 3.14
        assert "node-a" in loaded.disabled_subtrees


def test_list_checkpoints():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCheckpointBackend(tmpdir)
        manager = CheckpointManager(backend)

        for tick in range(3):
            state = ExecutionState(
                tree_id="t", execution_id="exec-1", tick_number=tick,
            )
            manager.save("exec-1", state)

        cps = manager.list_checkpoints("exec-1")
        assert len(cps) == 3


def test_prune_keeps_last_n():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCheckpointBackend(tmpdir)
        manager = CheckpointManager(backend)

        for tick in range(10):
            state = ExecutionState(
                tree_id="t", execution_id="exec-1", tick_number=tick,
            )
            manager.save("exec-1", state)

        deleted = manager.prune("exec-1", keep_last=3)
        assert deleted == 7
        remaining = manager.list_checkpoints("exec-1")
        assert len(remaining) == 3


def test_auto_checkpoint():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCheckpointBackend(tmpdir)
        manager = CheckpointManager(backend, interval_ticks=5)

        for tick in range(12):
            state = ExecutionState(
                tree_id="t", execution_id="exec-1", tick_number=tick,
            )
            manager.on_tick("exec-1", state)

        cps = manager.list_checkpoints("exec-1")
        assert len(cps) == 2  # tick 4 and tick 9


def test_corrupt_checkpoint_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCheckpointBackend(tmpdir)
        path = Path(tmpdir) / "bad.json"
        path.write_text("{invalid json")

        import pytest
        with pytest.raises(Exception):
            backend.load("bad")
