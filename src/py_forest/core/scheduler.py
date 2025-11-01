"""Background execution scheduler for auto and interval modes."""

import asyncio
from datetime import datetime
from uuid import UUID

from py_forest.models.execution import (
    ExecutionMode,
    SchedulerState,
    SchedulerStatus,
    Status,
)


class SchedulerContext:
    """Context for a scheduled execution."""

    def __init__(
        self,
        execution_id: UUID,
        mode: ExecutionMode,
        interval_ms: int | None = None,
        max_ticks: int | None = None,
        stop_on_terminal: bool = True,
    ):
        """Initialize scheduler context.

        Args:
            execution_id: Execution instance ID
            mode: Execution mode (AUTO or INTERVAL)
            interval_ms: Interval in milliseconds (for INTERVAL mode)
            max_ticks: Maximum ticks before auto-stop
            stop_on_terminal: Stop on terminal status
        """
        self.execution_id = execution_id
        self.mode = mode
        self.interval_ms = interval_ms
        self.max_ticks = max_ticks
        self.stop_on_terminal = stop_on_terminal

        # State tracking
        self.state = SchedulerState.IDLE
        self.ticks_executed = 0
        self.started_at: datetime | None = None
        self.stopped_at: datetime | None = None
        self.error_message: str | None = None

        # Task management
        self.task: asyncio.Task | None = None
        self.should_pause = False
        self.should_stop = False

    def get_status(self) -> SchedulerStatus:
        """Get scheduler status.

        Returns:
            SchedulerStatus instance
        """
        return SchedulerStatus(
            execution_id=self.execution_id,
            state=self.state,
            mode=self.mode,
            interval_ms=self.interval_ms,
            ticks_executed=self.ticks_executed,
            started_at=self.started_at,
            stopped_at=self.stopped_at,
            error_message=self.error_message,
        )


class ExecutionScheduler:
    """Background scheduler for autonomous tree execution.

    Supports:
    - AUTO mode: Tick as fast as possible
    - INTERVAL mode: Tick at specified intervals
    - Pause/Resume/Stop control
    - Stop conditions (terminal status, max ticks)
    - Error handling and recovery
    """

    def __init__(self):
        """Initialize execution scheduler."""
        self._contexts: dict[UUID, SchedulerContext] = {}
        self._lock = asyncio.Lock()

    async def start(
        self,
        execution_id: UUID,
        mode: ExecutionMode,
        tick_callback,
        interval_ms: int | None = None,
        max_ticks: int | None = None,
        stop_on_terminal: bool = True,
    ) -> SchedulerStatus:
        """Start scheduled execution.

        Args:
            execution_id: Execution instance ID
            mode: Execution mode
            tick_callback: Async function to call for ticking
            interval_ms: Interval in milliseconds (INTERVAL mode)
            max_ticks: Maximum ticks
            stop_on_terminal: Stop on terminal status

        Returns:
            Scheduler status

        Raises:
            ValueError: If mode is MANUAL or already running
        """
        if mode == ExecutionMode.MANUAL:
            raise ValueError("Cannot schedule MANUAL mode execution")

        async with self._lock:
            if execution_id in self._contexts:
                ctx = self._contexts[execution_id]
                if ctx.state == SchedulerState.RUNNING:
                    raise ValueError("Execution is already running")

            # Create context
            context = SchedulerContext(
                execution_id=execution_id,
                mode=mode,
                interval_ms=interval_ms,
                max_ticks=max_ticks,
                stop_on_terminal=stop_on_terminal,
            )

            context.state = SchedulerState.RUNNING
            context.started_at = datetime.utcnow()
            context.should_pause = False
            context.should_stop = False

            # Create background task
            if mode == ExecutionMode.AUTO:
                task = asyncio.create_task(self._run_auto(context, tick_callback))
            else:  # INTERVAL
                task = asyncio.create_task(self._run_interval(context, tick_callback))

            context.task = task
            self._contexts[execution_id] = context

        return context.get_status()

    async def pause(self, execution_id: UUID) -> SchedulerStatus:
        """Pause execution.

        Args:
            execution_id: Execution instance ID

        Returns:
            Scheduler status

        Raises:
            ValueError: If execution not found or not running
        """
        async with self._lock:
            context = self._get_context(execution_id)

            if context.state != SchedulerState.RUNNING:
                raise ValueError("Execution is not running")

            context.should_pause = True
            context.state = SchedulerState.PAUSED

        return context.get_status()

    async def resume(self, execution_id: UUID) -> SchedulerStatus:
        """Resume paused execution.

        Args:
            execution_id: Execution instance ID

        Returns:
            Scheduler status

        Raises:
            ValueError: If execution not found or not paused
        """
        async with self._lock:
            context = self._get_context(execution_id)

            if context.state != SchedulerState.PAUSED:
                raise ValueError("Execution is not paused")

            context.should_pause = False
            context.state = SchedulerState.RUNNING

        return context.get_status()

    async def stop(self, execution_id: UUID) -> SchedulerStatus:
        """Stop execution.

        Args:
            execution_id: Execution instance ID

        Returns:
            Scheduler status

        Raises:
            ValueError: If execution not found
        """
        async with self._lock:
            context = self._get_context(execution_id)

            context.should_stop = True

            # Cancel task if running
            if context.task and not context.task.done():
                context.task.cancel()

            context.state = SchedulerState.STOPPED
            context.stopped_at = datetime.utcnow()

        return context.get_status()

    def get_status(self, execution_id: UUID) -> SchedulerStatus:
        """Get scheduler status.

        Args:
            execution_id: Execution instance ID

        Returns:
            Scheduler status

        Raises:
            ValueError: If execution not found
        """
        context = self._get_context(execution_id)
        return context.get_status()

    def is_running(self, execution_id: UUID) -> bool:
        """Check if execution is running.

        Args:
            execution_id: Execution instance ID

        Returns:
            True if running
        """
        if execution_id not in self._contexts:
            return False

        context = self._contexts[execution_id]
        return context.state == SchedulerState.RUNNING

    async def cleanup(self, execution_id: UUID) -> None:
        """Cleanup scheduler context.

        Args:
            execution_id: Execution instance ID
        """
        async with self._lock:
            if execution_id in self._contexts:
                context = self._contexts[execution_id]

                # Cancel task if running
                if context.task and not context.task.done():
                    context.task.cancel()

                del self._contexts[execution_id]

    async def _run_auto(self, context: SchedulerContext, tick_callback) -> None:
        """Run in AUTO mode (tick as fast as possible).

        Args:
            context: Scheduler context
            tick_callback: Tick function
        """
        try:
            while not context.should_stop:
                # Handle pause
                while context.should_pause and not context.should_stop:
                    await asyncio.sleep(0.1)

                if context.should_stop:
                    break

                # Tick the tree
                try:
                    response = await tick_callback(execution_id=context.execution_id)
                    context.ticks_executed += response.ticks_executed

                    # Check stop conditions
                    if (
                        context.max_ticks
                        and context.ticks_executed >= context.max_ticks
                    ):
                        break

                    if context.stop_on_terminal:
                        if response.root_status in [Status.SUCCESS, Status.FAILURE]:
                            break

                except Exception as e:
                    context.state = SchedulerState.ERROR
                    context.error_message = str(e)
                    break

                # Small yield to prevent blocking
                await asyncio.sleep(0)

        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                if not context.should_stop:
                    context.state = SchedulerState.STOPPED
                    context.stopped_at = datetime.utcnow()

    async def _run_interval(self, context: SchedulerContext, tick_callback) -> None:
        """Run in INTERVAL mode (tick at specified intervals).

        Args:
            context: Scheduler context
            tick_callback: Tick function
        """
        interval_sec = context.interval_ms / 1000.0

        try:
            while not context.should_stop:
                # Handle pause
                while context.should_pause and not context.should_stop:
                    await asyncio.sleep(0.1)

                if context.should_stop:
                    break

                # Tick the tree
                try:
                    response = await tick_callback(execution_id=context.execution_id)
                    context.ticks_executed += response.ticks_executed

                    # Check stop conditions
                    if (
                        context.max_ticks
                        and context.ticks_executed >= context.max_ticks
                    ):
                        break

                    if context.stop_on_terminal:
                        if response.root_status in [Status.SUCCESS, Status.FAILURE]:
                            break

                except Exception as e:
                    context.state = SchedulerState.ERROR
                    context.error_message = str(e)
                    break

                # Wait for interval
                await asyncio.sleep(interval_sec)

        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                if not context.should_stop:
                    context.state = SchedulerState.STOPPED
                    context.stopped_at = datetime.utcnow()

    def _get_context(self, execution_id: UUID) -> SchedulerContext:
        """Get scheduler context.

        Args:
            execution_id: Execution instance ID

        Returns:
            SchedulerContext

        Raises:
            ValueError: If not found
        """
        if execution_id not in self._contexts:
            raise ValueError(f"No scheduler context for execution: {execution_id}")
        return self._contexts[execution_id]
