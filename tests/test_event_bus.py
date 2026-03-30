"""Tests for WP-10: Event Ingestion & Push-Based Triggering."""

import json
import tempfile
from pathlib import Path

from talking_trees.events.bus import EventBus
from talking_trees.events.mappings import EventMapping
from talking_trees.events.transports.inprocess import InProcessEventTransport


def test_emit_triggers_tick_callback():
    """Emitting event triggers tick callback with blackboard updates."""
    bus = EventBus()
    bus.register_mapping(EventMapping(
        topic="sensor/temperature",
        blackboard_writes={"temp": "value"},
        trigger_tick=True,
    ))

    received = []
    bus.register_tick_callback(lambda exec_id, bb: received.append(bb))
    bus.start()

    bus.emit("sensor/temperature", {"value": 42.5})

    assert len(received) == 1
    assert received[0]["temp"] == 42.5


def test_debounce():
    """Debounce suppresses rapid events."""
    bus = EventBus()
    bus.register_mapping(EventMapping(
        topic="sensor/fast",
        blackboard_writes={"val": "v"},
        debounce_ms=100,
    ))

    count = []
    bus.register_tick_callback(lambda e, bb: count.append(1))
    bus.start()

    # Emit 5 events rapidly
    for i in range(5):
        bus.emit("sensor/fast", {"v": i})

    # Only first should trigger (within debounce window)
    assert len(count) == 1


def test_filter_rejects_non_matching():
    """Filter expression blocks non-matching events."""
    bus = EventBus()
    bus.register_mapping(EventMapping(
        topic="sensor/val",
        blackboard_writes={"v": "value"},
        filter="value > 50",
    ))

    received = []
    bus.register_tick_callback(lambda e, bb: received.append(bb))
    bus.start()

    bus.emit("sensor/val", {"value": 30})  # filtered out
    bus.emit("sensor/val", {"value": 80})  # passes

    assert len(received) == 1
    assert received[0]["v"] == 80


def test_multiple_mappings_same_topic():
    """Multiple mappings on same topic all fire."""
    bus = EventBus()
    bus.register_mapping(EventMapping(topic="t", blackboard_writes={"a": "x"}))
    bus.register_mapping(EventMapping(topic="t", blackboard_writes={"b": "y"}))

    received = []
    bus.register_tick_callback(lambda e, bb: received.append(bb))
    bus.start()

    bus.emit("t", {"x": 1, "y": 2})

    assert len(received) == 2


def test_stopped_bus_ignores_events():
    """Events are ignored when bus is stopped."""
    bus = EventBus()
    bus.register_mapping(EventMapping(topic="t", blackboard_writes={"a": "v"}))

    received = []
    bus.register_tick_callback(lambda e, bb: received.append(1))
    # Don't start

    bus.emit("t", {"v": 1})
    assert len(received) == 0


def test_load_mappings_from_json():
    """Load mappings from JSON file."""
    config = {
        "mappings": [
            {"topic": "sensor/temp", "blackboard_writes": {"temp": "value"}},
            {"topic": "sensor/humidity", "blackboard_writes": {"hum": "value"}},
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        path = f.name

    try:
        bus = EventBus()
        bus.load_mappings_from_json(path)
        assert len(bus.get_mappings()) == 2
    finally:
        Path(path).unlink()


def test_wildcard_topic_matching():
    """Wildcard topic patterns match correctly."""
    transport = InProcessEventTransport()

    received = []
    transport.subscribe("sensor/*", lambda t, d: received.append(t))

    transport.publish("sensor/temp", {"v": 1})
    transport.publish("sensor/humidity", {"v": 2})
    transport.publish("other/topic", {"v": 3})

    assert len(received) == 2
    assert "sensor/temp" in received
    assert "sensor/humidity" in received
