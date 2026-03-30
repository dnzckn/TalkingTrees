"""Async action node for non-blocking execution of long-running tasks."""

import importlib
import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

import py_trees

logger = logging.getLogger(__name__)

# Shared thread pool (configurable via set_pool_size)
_pool: ThreadPoolExecutor | None = None
_pool_size: int = 8


def get_pool() -> ThreadPoolExecutor:
    """Get or create the shared thread pool."""
    global _pool
    if _pool is None:
        _pool = ThreadPoolExecutor(max_workers=_pool_size)
    return _pool


def set_pool_size(size: int) -> None:
    """Set the thread pool size. Must be called before first use."""
    global _pool_size, _pool
    _pool_size = size
    if _pool is not None:
        _pool.shutdown(wait=False)
        _pool = None


class AsyncActionBehaviour(py_trees.behaviour.Behaviour):
    """Behaviour that executes a callable asynchronously in a thread pool.

    First tick: spawns the callable, returns RUNNING.
    Subsequent ticks: checks completion. Done → maps result to status. Not done → RUNNING.
    On timeout: cancels and returns configured on_timeout status.

    Args:
        name: Behaviour name
        callable_path: Dotted import path to function (e.g., "mymodule.detect")
        timeout_ms: Maximum execution time
        on_timeout: Status to return on timeout ("FAILURE", "RUNNING")
        output_key: Blackboard key to write result to
        args: Positional args to pass to callable
        kwargs: Keyword args to pass to callable
    """

    def __init__(
        self,
        name: str,
        callable_path: str,
        timeout_ms: int = 5000,
        on_timeout: str = "FAILURE",
        output_key: str | None = None,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
    ):
        super().__init__(name=name)
        self.callable_path = callable_path
        self.timeout_ms = timeout_ms
        self.on_timeout = on_timeout
        self.output_key = output_key
        self.args = args
        self.kwargs = kwargs or {}

        self._future: Future | None = None
        self._start_time: float | None = None
        self._resolved_callable = None

    def initialise(self) -> None:
        """Called when the behaviour transitions to RUNNING."""
        pass

    def _resolve_callable(self):
        """Lazily resolve the dotted import path to a callable."""
        if self._resolved_callable is None:
            parts = self.callable_path.rsplit(".", 1)
            if len(parts) == 2:
                module = importlib.import_module(parts[0])
                self._resolved_callable = getattr(module, parts[1])
            else:
                raise ValueError(f"Invalid callable path: {self.callable_path}")
        return self._resolved_callable

    def update(self) -> py_trees.common.Status:
        """Tick the async action."""
        # First tick: spawn the task
        if self._future is None:
            try:
                func = self._resolve_callable()
            except (ImportError, AttributeError, ValueError) as e:
                logger.error("Failed to resolve callable %s: %s", self.callable_path, e)
                return py_trees.common.Status.FAILURE

            pool = get_pool()
            self._future = pool.submit(func, *self.args, **self.kwargs)
            self._start_time = time.monotonic()
            return py_trees.common.Status.RUNNING

        # Check timeout
        elapsed_ms = (time.monotonic() - self._start_time) * 1000
        if elapsed_ms > self.timeout_ms:
            self._future.cancel()
            logger.warning("AsyncAction '%s' timed out after %.0fms", self.name, elapsed_ms)
            self._future = None
            self._start_time = None

            status_map = {
                "FAILURE": py_trees.common.Status.FAILURE,
                "RUNNING": py_trees.common.Status.RUNNING,
            }
            return status_map.get(self.on_timeout, py_trees.common.Status.FAILURE)

        # Check if done
        if self._future.done():
            try:
                result = self._future.result()

                # Write result to blackboard if output_key configured
                if self.output_key and result is not None:
                    from talking_trees.core.utils import update_blackboard
                    update_blackboard({self.output_key: result}, client_name=f"Async:{self.name}")

                self._future = None
                self._start_time = None

                # If result is a py_trees Status, use it directly
                if isinstance(result, py_trees.common.Status):
                    return result

                return py_trees.common.Status.SUCCESS

            except Exception as e:
                logger.error("AsyncAction '%s' failed: %s", self.name, e)
                self._future = None
                self._start_time = None
                return py_trees.common.Status.FAILURE

        # Still running
        return py_trees.common.Status.RUNNING

    def terminate(self, new_status: py_trees.common.Status) -> None:
        """Cancel pending task on termination."""
        if self._future is not None and not self._future.done():
            self._future.cancel()
            self._future = None
            self._start_time = None
