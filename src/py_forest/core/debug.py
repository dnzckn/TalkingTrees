"""Debug context for breakpoints, watches, and step execution."""

from typing import Any
from uuid import UUID

import py_trees

from py_forest.models.debug import (
    Breakpoint,
    DebugState,
    StepMode,
    WatchCondition,
    WatchExpression,
)
from py_forest.models.events import WatchTriggeredEvent
from py_forest.models.execution import Status


class DebugContext:
    """Debug context for execution debugging.

    Manages:
    - Breakpoints on specific nodes
    - Watch expressions on blackboard keys
    - Step execution modes
    - Pause/continue state
    """

    def __init__(self, execution_id: UUID):
        """Initialize debug context.

        Args:
            execution_id: Execution instance ID
        """
        self.execution_id = execution_id

        # Breakpoints
        self.breakpoints: dict[UUID, Breakpoint] = {}

        # Watches
        self.watches: dict[str, WatchExpression] = {}

        # Step mode
        self.step_mode = StepMode.NONE
        self.step_count = 0
        self.steps_remaining = 0

        # Pause state
        self.is_paused = False
        self.paused_at_node: UUID | None = None
        self.pause_requested = False

        # Step tracking
        self.last_node_statuses: dict[UUID, Status] = {}
        self.step_start_node: UUID | None = None

        # Statistics
        self.breakpoint_hits = 0
        self.watch_hits = 0

        # Watch value tracking
        self.last_watch_values: dict[str, Any] = {}

    def add_breakpoint(self, node_id: UUID, condition: str | None = None) -> Breakpoint:
        """Add a breakpoint.

        Args:
            node_id: Node ID to break on
            condition: Optional Python condition

        Returns:
            Breakpoint instance
        """
        breakpoint = Breakpoint(node_id=node_id, condition=condition)
        self.breakpoints[node_id] = breakpoint
        return breakpoint

    def remove_breakpoint(self, node_id: UUID) -> bool:
        """Remove a breakpoint.

        Args:
            node_id: Node ID

        Returns:
            True if removed, False if not found
        """
        if node_id in self.breakpoints:
            del self.breakpoints[node_id]
            return True
        return False

    def toggle_breakpoint(self, node_id: UUID) -> bool:
        """Toggle breakpoint enabled state.

        Args:
            node_id: Node ID

        Returns:
            New enabled state

        Raises:
            ValueError: If breakpoint not found
        """
        if node_id not in self.breakpoints:
            raise ValueError(f"Breakpoint not found: {node_id}")

        bp = self.breakpoints[node_id]
        bp.enabled = not bp.enabled
        return bp.enabled

    def add_watch(
        self, key: str, condition: WatchCondition, target_value: Any = None
    ) -> WatchExpression:
        """Add a watch expression.

        Args:
            key: Blackboard key
            condition: Watch condition
            target_value: Target value for comparison

        Returns:
            WatchExpression instance
        """
        watch = WatchExpression(key=key, condition=condition, target_value=target_value)
        self.watches[key] = watch
        return watch

    def remove_watch(self, key: str) -> bool:
        """Remove a watch expression.

        Args:
            key: Blackboard key

        Returns:
            True if removed, False if not found
        """
        if key in self.watches:
            del self.watches[key]
            return True
        return False

    def toggle_watch(self, key: str) -> bool:
        """Toggle watch enabled state.

        Args:
            key: Blackboard key

        Returns:
            New enabled state

        Raises:
            ValueError: If watch not found
        """
        if key not in self.watches:
            raise ValueError(f"Watch not found: {key}")

        watch = self.watches[key]
        watch.enabled = not watch.enabled
        return watch.enabled

    def set_step_mode(self, mode: StepMode, count: int = 1) -> None:
        """Set step mode.

        Args:
            mode: Step mode
            count: Number of steps (for STEP_OVER)
        """
        self.step_mode = mode
        self.step_count = count
        self.steps_remaining = count

        if mode != StepMode.NONE:
            self.is_paused = False
            self.pause_requested = False

    def should_break_at_node(
        self, node_id: UUID, node: py_trees.behaviour.Behaviour, blackboard: dict
    ) -> bool:
        """Check if should break at node.

        Args:
            node_id: Node UUID
            node: py_trees node
            blackboard: Current blackboard state

        Returns:
            True if should break
        """
        # Check if paused
        if self.is_paused:
            return True

        # Check breakpoints
        if node_id in self.breakpoints:
            bp = self.breakpoints[node_id]
            if bp.enabled:
                # Evaluate condition if present
                if bp.condition:
                    try:
                        # Create eval context
                        context = {
                            "node": node,
                            "blackboard": blackboard,
                            "status": node.status.value,
                        }
                        if eval(bp.condition, {}, context):
                            bp.hit_count += 1
                            self.breakpoint_hits += 1
                            return True
                    except Exception:
                        # Condition evaluation failed, break anyway
                        bp.hit_count += 1
                        self.breakpoint_hits += 1
                        return True
                else:
                    # No condition, always break
                    bp.hit_count += 1
                    self.breakpoint_hits += 1
                    return True

        # Check step mode
        if self.step_mode == StepMode.STEP_OVER:
            if self.steps_remaining > 0:
                self.steps_remaining -= 1
                if self.steps_remaining == 0:
                    return True

        elif self.step_mode == StepMode.STEP_INTO:
            # Break on any node status change
            old_status = self.last_node_statuses.get(node_id)
            new_status = Status(node.status.value)
            if old_status and old_status != new_status:
                return True

        elif self.step_mode == StepMode.STEP_OUT:
            # Break when we return to parent of step_start_node
            # This is complex and would need parent tracking
            # For now, just break after one tick
            if self.steps_remaining > 0:
                self.steps_remaining -= 1
                if self.steps_remaining == 0:
                    return True

        # Check pause requested
        if self.pause_requested:
            return True

        return False

    def check_watches(self, blackboard: dict) -> WatchTriggeredEvent | None:
        """Check watch expressions.

        Args:
            blackboard: Current blackboard state

        Returns:
            WatchTriggeredEvent if any watch triggered, None otherwise
        """
        for key, watch in self.watches.items():
            if not watch.enabled:
                continue

            # Get current value
            current_value = blackboard.get(key)
            last_value = self.last_watch_values.get(key)

            triggered = False

            if watch.condition == WatchCondition.CHANGE:
                if last_value is not None and current_value != last_value:
                    triggered = True

            elif watch.condition == WatchCondition.EQUALS:
                if current_value == watch.target_value:
                    triggered = True

            elif watch.condition == WatchCondition.NOT_EQUALS:
                if current_value != watch.target_value:
                    triggered = True

            elif watch.condition == WatchCondition.GREATER:
                if (
                    current_value is not None
                    and watch.target_value is not None
                    and current_value > watch.target_value
                ):
                    triggered = True

            elif watch.condition == WatchCondition.LESS:
                if (
                    current_value is not None
                    and watch.target_value is not None
                    and current_value < watch.target_value
                ):
                    triggered = True

            elif watch.condition == WatchCondition.GREATER_EQUAL:
                if (
                    current_value is not None
                    and watch.target_value is not None
                    and current_value >= watch.target_value
                ):
                    triggered = True

            elif watch.condition == WatchCondition.LESS_EQUAL:
                if (
                    current_value is not None
                    and watch.target_value is not None
                    and current_value <= watch.target_value
                ):
                    triggered = True

            # Update last value
            self.last_watch_values[key] = current_value

            if triggered:
                watch.hit_count += 1
                self.watch_hits += 1

                # Pause execution
                self.is_paused = True

                # Create event
                return WatchTriggeredEvent(
                    execution_id=self.execution_id,
                    key=key,
                    condition=watch.condition.value,
                    value=current_value,
                )

        return None

    def update_node_status(self, node_id: UUID, status: Status) -> None:
        """Update tracked node status.

        Args:
            node_id: Node UUID
            status: New status
        """
        self.last_node_statuses[node_id] = status

    def pause(self, node_id: UUID | None = None) -> None:
        """Pause execution.

        Args:
            node_id: Node where paused
        """
        self.is_paused = True
        self.paused_at_node = node_id
        self.pause_requested = False

    def resume(self) -> None:
        """Resume execution."""
        self.is_paused = False
        self.paused_at_node = None
        self.pause_requested = False
        self.step_mode = StepMode.NONE

    def request_pause(self) -> None:
        """Request pause at next opportunity."""
        self.pause_requested = True

    def get_state(self) -> DebugState:
        """Get current debug state.

        Returns:
            DebugState instance
        """
        return DebugState(
            execution_id=self.execution_id,
            is_paused=self.is_paused,
            paused_at_node=self.paused_at_node,
            step_mode=self.step_mode,
            breakpoints={str(k): v for k, v in self.breakpoints.items()},
            watches=self.watches.copy(),
            breakpoint_hits=self.breakpoint_hits,
            watch_hits=self.watch_hits,
        )

    def clear_all(self) -> None:
        """Clear all breakpoints and watches."""
        self.breakpoints.clear()
        self.watches.clear()
        self.is_paused = False
        self.paused_at_node = None
        self.step_mode = StepMode.NONE
