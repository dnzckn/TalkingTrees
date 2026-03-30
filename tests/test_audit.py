"""Tests for WP-16: Audit Trail & Forensic Replay."""

import tempfile
from pathlib import Path
from uuid import uuid4

from talking_trees.audit.backends.jsonl import JSONLAuditBackend
from talking_trees.audit.collector import AuditCollector
from talking_trees.audit.reader import AuditReader


def test_all_event_types_written():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name

    try:
        backend = JSONLAuditBackend(path)
        collector = AuditCollector(backend)
        eid = uuid4()
        tid = uuid4()

        collector.on_tick_start(eid, tid, 1)
        collector.on_tick_end(eid, tid, 1, 0.5)
        collector.on_tick(eid, tid, 1, 0.5)
        collector.on_node_result(eid, uuid4(), "Action", "SUCCESS", 0.1)
        collector.on_error(eid, uuid4(), RuntimeError("test"))
        collector.on_blackboard_write(eid, "key", "value")
        collector.on_cascade_trigger(eid, uuid4(), uuid4())

        entries = backend.read_all()
        assert len(entries) == 7
        types = {e["event_type"] for e in entries}
        assert "tick_start" in types
        assert "tick_end" in types
        assert "error" in types
    finally:
        Path(path).unlink(missing_ok=True)


def test_filter_by_execution():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name

    try:
        backend = JSONLAuditBackend(path)
        collector = AuditCollector(backend)

        eid1, eid2, tid = uuid4(), uuid4(), uuid4()
        collector.on_tick(eid1, tid, 1, 0.1)
        collector.on_tick(eid2, tid, 1, 0.2)
        collector.on_tick(eid1, tid, 2, 0.1)

        reader = AuditReader(backend)
        filtered = reader.filter(execution_id=str(eid1))
        assert len(filtered) == 2
    finally:
        Path(path).unlink(missing_ok=True)


def test_replay_chronological():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name

    try:
        backend = JSONLAuditBackend(path)
        collector = AuditCollector(backend)
        eid, tid = uuid4(), uuid4()

        collector.on_tick(eid, tid, 1, 0.1)
        collector.on_tick(eid, tid, 2, 0.2)
        collector.on_tick(eid, tid, 3, 0.3)

        reader = AuditReader(backend)
        events = list(reader.replay(str(eid)))
        assert len(events) == 3
        # Should be in chronological order
        ticks = [e.get("tick_number") for e in events]
        assert ticks == [1, 2, 3]
    finally:
        Path(path).unlink(missing_ok=True)


def test_log_rotation():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "audit.jsonl"
        backend = JSONLAuditBackend(path, max_size_bytes=100)
        collector = AuditCollector(backend)
        eid, tid = uuid4(), uuid4()

        # Write enough to trigger rotation
        for i in range(20):
            collector.on_tick(eid, tid, i, 0.1)

        # Original file should exist (new after rotation)
        assert path.exists()
        # Rotated file should also exist
        rotated = list(Path(tmpdir).glob("audit.*.jsonl"))
        assert len(rotated) >= 1


def test_corrupt_entry_skipped():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"event_type": "tick", "tick_number": 1}\n')
        f.write('CORRUPT LINE\n')
        f.write('{"event_type": "tick", "tick_number": 2}\n')
        path = f.name

    try:
        backend = JSONLAuditBackend(path)
        entries = backend.read_all()
        assert len(entries) == 2  # corrupt line skipped
    finally:
        Path(path).unlink(missing_ok=True)
