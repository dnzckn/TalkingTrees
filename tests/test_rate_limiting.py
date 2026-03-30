"""Tests for WP-11: Rate Limiting & Backpressure."""

import time

import py_trees

from talking_trees.behaviors.rate_limiting import (
    DebounceBehaviour,
    RateLimiterBehaviour,
    WindowedAggregatorBehaviour,
)


def test_rate_limiter_blocks_after_max():
    child = py_trees.behaviours.Success(name="fast")
    limiter = RateLimiterBehaviour(name="limiter", child=child, max_count=3, window_seconds=1.0)

    results = [limiter.update() for _ in range(5)]
    assert results[:3] == [py_trees.common.Status.SUCCESS] * 3
    assert results[3] == py_trees.common.Status.FAILURE


def test_rate_limiter_resets_after_window():
    child = py_trees.behaviours.Success(name="fast")
    limiter = RateLimiterBehaviour(name="limiter", child=child, max_count=2, window_seconds=0.1)

    limiter.update()
    limiter.update()
    assert limiter.update() == py_trees.common.Status.FAILURE
    time.sleep(0.15)
    assert limiter.update() == py_trees.common.Status.SUCCESS


def test_debounce_suppresses_rapid():
    child = py_trees.behaviours.Success(name="fast")
    debounce = DebounceBehaviour(name="debounce", child=child, cooldown_seconds=0.1)

    assert debounce.update() == py_trees.common.Status.SUCCESS
    assert debounce.update() == py_trees.common.Status.RUNNING


def test_debounce_allows_after_cooldown():
    child = py_trees.behaviours.Success(name="fast")
    debounce = DebounceBehaviour(name="debounce", child=child, cooldown_seconds=0.05)

    debounce.update()
    time.sleep(0.06)
    assert debounce.update() == py_trees.common.Status.SUCCESS


def test_windowed_aggregator_needs_n_successes():
    child = py_trees.behaviours.Success(name="sensor")
    agg = WindowedAggregatorBehaviour(name="agg", child=child, window_seconds=5.0, min_successes=3)

    assert agg.update() == py_trees.common.Status.RUNNING
    assert agg.update() == py_trees.common.Status.RUNNING
    assert agg.update() == py_trees.common.Status.SUCCESS


def test_decorators_compose():
    child = py_trees.behaviours.Success(name="sensor")
    debounced = DebounceBehaviour(name="debounce", child=child, cooldown_seconds=0.01)
    limited = RateLimiterBehaviour(name="limiter", child=debounced, max_count=5, window_seconds=1.0)

    assert limited.update() == py_trees.common.Status.SUCCESS
