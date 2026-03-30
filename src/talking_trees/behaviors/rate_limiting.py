"""Rate limiting and backpressure decorator behaviours.

These wrap a child behaviour and control how often it is ticked.
They work as py_trees Behaviours that manually manage their child's lifecycle.
"""

import time
from collections import deque

import py_trees


class RateLimiterBehaviour(py_trees.behaviour.Behaviour):
    """Limits child execution to max_count times per window_seconds."""

    def __init__(self, name, child, max_count=10, window_seconds=1.0, on_limit="FAILURE"):
        super().__init__(name=name)
        self.child = child
        self.max_count = max_count
        self.window_seconds = window_seconds
        self.on_limit = on_limit
        self._timestamps: deque = deque()

    def setup(self, **kwargs):
        self.child.setup(**kwargs)

    def update(self):
        now = time.monotonic()
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        if len(self._timestamps) >= self.max_count:
            return _status_from_str(self.on_limit)

        self._timestamps.append(now)
        self.child.tick_once()
        return self.child.status


class DebounceBehaviour(py_trees.behaviour.Behaviour):
    """Only ticks child if cooldown_seconds have passed since last tick."""

    def __init__(self, name, child, cooldown_seconds=1.0, on_cooldown="RUNNING"):
        super().__init__(name=name)
        self.child = child
        self.cooldown_seconds = cooldown_seconds
        self.on_cooldown = on_cooldown
        self._last_tick_time: float | None = None

    def setup(self, **kwargs):
        self.child.setup(**kwargs)

    def update(self):
        now = time.monotonic()
        if self._last_tick_time is not None:
            if now - self._last_tick_time < self.cooldown_seconds:
                return _status_from_str(self.on_cooldown)

        self._last_tick_time = now
        self.child.tick_once()
        return self.child.status


class WindowedAggregatorBehaviour(py_trees.behaviour.Behaviour):
    """Requires N child successes within a time window to propagate SUCCESS."""

    def __init__(self, name, child, window_seconds=10.0, min_successes=3):
        super().__init__(name=name)
        self.child = child
        self.window_seconds = window_seconds
        self.min_successes = min_successes
        self._success_times: deque = deque()

    def setup(self, **kwargs):
        self.child.setup(**kwargs)

    def update(self):
        self.child.tick_once()
        result = self.child.status
        now = time.monotonic()

        cutoff = now - self.window_seconds
        while self._success_times and self._success_times[0] < cutoff:
            self._success_times.popleft()

        if result == py_trees.common.Status.SUCCESS:
            self._success_times.append(now)

        if len(self._success_times) >= self.min_successes:
            return py_trees.common.Status.SUCCESS

        if result == py_trees.common.Status.FAILURE:
            return py_trees.common.Status.FAILURE

        return py_trees.common.Status.RUNNING


def _status_from_str(s: str) -> py_trees.common.Status:
    return {
        "FAILURE": py_trees.common.Status.FAILURE,
        "RUNNING": py_trees.common.Status.RUNNING,
        "SUCCESS": py_trees.common.Status.SUCCESS,
    }.get(s, py_trees.common.Status.FAILURE)
