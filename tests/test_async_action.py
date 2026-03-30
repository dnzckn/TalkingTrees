"""Tests for WP-8: Async Node Execution."""

import sys
import time
from uuid import uuid4

import py_trees
import pytest

from talking_trees.execution.async_action import AsyncActionBehaviour, set_pool_size


# ---------------------------------------------------------------------------
# Test helper callables – placed in a module that the async resolver can find.
# We register the current module on sys.path so 'test_async_action.<func>' works.
# ---------------------------------------------------------------------------
if "tests" not in sys.path:
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))


def _slow_success(duration_s=0.1):
    """Simulate a slow task that succeeds."""
    time.sleep(duration_s)
    return py_trees.common.Status.SUCCESS


def _slow_value(value="hello", duration_s=0.1):
    """Simulate a slow task that returns a value."""
    time.sleep(duration_s)
    return value


def _always_fail():
    """Task that raises an exception."""
    raise RuntimeError("Task failed!")


def test_async_first_tick_returns_running():
    """First tick spawns task and returns RUNNING."""
    node = AsyncActionBehaviour(
        name="test",
        callable_path="test_async_action._slow_success",
        timeout_ms=5000,
    )
    status = node.update()
    assert status == py_trees.common.Status.RUNNING
    node.terminate(py_trees.common.Status.RUNNING)


def test_async_completion_returns_success():
    """Task completes and returns SUCCESS."""
    node = AsyncActionBehaviour(
        name="test",
        callable_path="test_async_action._slow_success",
        timeout_ms=5000,
    )
    # First tick: spawn
    node.update()
    # Wait for completion
    time.sleep(0.2)
    # Second tick: should be done
    status = node.update()
    assert status == py_trees.common.Status.SUCCESS


def test_async_timeout_returns_failure():
    """Timeout returns configured status."""
    node = AsyncActionBehaviour(
        name="test",
        callable_path="test_async_action._slow_success",
        timeout_ms=50,  # Very short timeout
    )
    node.update()  # spawn
    time.sleep(0.1)  # wait for timeout to elapse
    status = node.update()
    assert status == py_trees.common.Status.FAILURE


def test_async_cancellation():
    """Cancellation cleans up the task."""
    node = AsyncActionBehaviour(
        name="test",
        callable_path="test_async_action._slow_success",
        timeout_ms=5000,
    )
    node.update()  # spawn
    assert node._future is not None
    node.terminate(py_trees.common.Status.INVALID)
    assert node._future is None


def test_async_exception_returns_failure():
    """Exception in callable returns FAILURE."""
    node = AsyncActionBehaviour(
        name="test",
        callable_path="test_async_action._always_fail",
        timeout_ms=5000,
    )
    node.update()  # spawn
    time.sleep(0.1)
    status = node.update()
    assert status == py_trees.common.Status.FAILURE


def test_pool_size_configuration():
    """Thread pool size can be configured."""
    set_pool_size(4)
    # Just verify it doesn't crash
    node = AsyncActionBehaviour(
        name="test",
        callable_path="test_async_action._slow_success",
        timeout_ms=5000,
    )
    node.update()
    time.sleep(0.2)
    status = node.update()
    assert status == py_trees.common.Status.SUCCESS
    # Reset
    set_pool_size(8)
