"""Execution profiler for performance analysis of behavior trees."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

import py_trees


class ProfilingLevel(str, Enum):
    """Level of profiling detail."""

    OFF = "off"  # No profiling
    BASIC = "basic"  # Node execution counts and times
    DETAILED = "detailed"  # Include status changes and tick patterns
    FULL = "full"  # Full instrumentation with blackboard access tracking


@dataclass
class NodeProfile:
    """Profiling data for a single node."""

    node_id: UUID
    node_name: str
    node_type: str

    # Execution metrics
    tick_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    avg_time_ms: float = 0.0

    # Status metrics
    success_count: int = 0
    failure_count: int = 0
    running_count: int = 0
    invalid_count: int = 0

    # Timing distribution (microseconds)
    time_buckets: Dict[str, int] = field(default_factory=lambda: {
        "<1ms": 0,
        "1-10ms": 0,
        "10-100ms": 0,
        "100-1000ms": 0,
        ">1000ms": 0
    })

    # Blackboard access (detailed mode)
    blackboard_reads: List[str] = field(default_factory=list)
    blackboard_writes: List[str] = field(default_factory=list)

    # Parent/child info
    parent_name: Optional[str] = None
    child_count: int = 0

    def update_timing(self, duration_ms: float):
        """Update timing statistics."""
        self.tick_count += 1
        self.total_time_ms += duration_ms
        self.min_time_ms = min(self.min_time_ms, duration_ms)
        self.max_time_ms = max(self.max_time_ms, duration_ms)
        self.avg_time_ms = self.total_time_ms / self.tick_count

        # Update bucket
        if duration_ms < 1:
            self.time_buckets["<1ms"] += 1
        elif duration_ms < 10:
            self.time_buckets["1-10ms"] += 1
        elif duration_ms < 100:
            self.time_buckets["10-100ms"] += 1
        elif duration_ms < 1000:
            self.time_buckets["100-1000ms"] += 1
        else:
            self.time_buckets[">1000ms"] += 1

    def update_status(self, status: py_trees.common.Status):
        """Update status count."""
        if status == py_trees.common.Status.SUCCESS:
            self.success_count += 1
        elif status == py_trees.common.Status.FAILURE:
            self.failure_count += 1
        elif status == py_trees.common.Status.RUNNING:
            self.running_count += 1
        else:
            self.invalid_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": str(self.node_id),
            "node_name": self.node_name,
            "node_type": self.node_type,
            "tick_count": self.tick_count,
            "total_time_ms": round(self.total_time_ms, 3),
            "min_time_ms": round(self.min_time_ms, 3) if self.min_time_ms != float('inf') else 0,
            "max_time_ms": round(self.max_time_ms, 3),
            "avg_time_ms": round(self.avg_time_ms, 3),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "running_count": self.running_count,
            "invalid_count": self.invalid_count,
            "time_distribution": self.time_buckets,
            "parent_name": self.parent_name,
            "child_count": self.child_count,
        }


@dataclass
class ProfileReport:
    """Complete profiling report for a tree execution."""

    execution_id: str
    tree_id: UUID
    total_ticks: int
    total_time_ms: float
    start_time: float
    end_time: Optional[float]

    # Per-node profiles
    node_profiles: Dict[UUID, NodeProfile] = field(default_factory=dict)

    # Aggregate statistics
    total_nodes: int = 0
    slowest_nodes: List[tuple] = field(default_factory=list)  # (node_name, avg_time_ms)
    most_ticked_nodes: List[tuple] = field(default_factory=list)  # (node_name, tick_count)
    bottlenecks: List[str] = field(default_factory=list)  # Nodes with >100ms avg

    def finalize(self):
        """Compute aggregate statistics."""
        self.total_nodes = len(self.node_profiles)

        # Sort by avg time
        sorted_by_time = sorted(
            [(p.node_name, p.avg_time_ms) for p in self.node_profiles.values()],
            key=lambda x: x[1],
            reverse=True
        )
        self.slowest_nodes = sorted_by_time[:10]

        # Sort by tick count
        sorted_by_ticks = sorted(
            [(p.node_name, p.tick_count) for p in self.node_profiles.values()],
            key=lambda x: x[1],
            reverse=True
        )
        self.most_ticked_nodes = sorted_by_ticks[:10]

        # Identify bottlenecks (>100ms avg)
        self.bottlenecks = [
            f"{p.node_name} ({p.avg_time_ms:.2f}ms avg)"
            for p in self.node_profiles.values()
            if p.avg_time_ms > 100
        ]

        if self.end_time:
            self.total_time_ms = (self.end_time - self.start_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "tree_id": str(self.tree_id),
            "total_ticks": self.total_ticks,
            "total_time_ms": round(self.total_time_ms, 3),
            "total_nodes": self.total_nodes,
            "node_profiles": {
                str(node_id): profile.to_dict()
                for node_id, profile in self.node_profiles.items()
            },
            "slowest_nodes": [
                {"name": name, "avg_time_ms": round(time_ms, 3)}
                for name, time_ms in self.slowest_nodes
            ],
            "most_ticked_nodes": [
                {"name": name, "tick_count": count}
                for name, count in self.most_ticked_nodes
            ],
            "bottlenecks": self.bottlenecks,
        }

    def __repr__(self) -> str:
        """String representation."""
        lines = [
            "=" * 80,
            f"PROFILING REPORT: {self.execution_id}",
            "=" * 80,
            "",
            "SUMMARY:",
            f"  Total ticks:        {self.total_ticks}",
            f"  Total time:         {self.total_time_ms:.2f}ms",
            f"  Total nodes:        {self.total_nodes}",
            f"  Avg time per tick:  {self.total_time_ms / self.total_ticks:.2f}ms" if self.total_ticks > 0 else "  Avg time per tick:  N/A",
            "",
        ]

        if self.bottlenecks:
            lines.extend([
                "BOTTLENECKS (>100ms avg):",
                *[f"  ⚠️  {b}" for b in self.bottlenecks],
                "",
            ])

        if self.slowest_nodes:
            lines.extend([
                "SLOWEST NODES (top 10):",
                *[f"  {i+1}. {name}: {time_ms:.2f}ms avg"
                  for i, (name, time_ms) in enumerate(self.slowest_nodes[:10])],
                "",
            ])

        if self.most_ticked_nodes:
            lines.extend([
                "MOST TICKED NODES (top 10):",
                *[f"  {i+1}. {name}: {count} ticks"
                  for i, (name, count) in enumerate(self.most_ticked_nodes[:10])],
                "",
            ])

        lines.append("=" * 80)
        return "\n".join(lines)


class TreeProfiler:
    """Profiler for behavior tree execution."""

    def __init__(self, level: ProfilingLevel = ProfilingLevel.BASIC):
        """Initialize profiler.

        Args:
            level: Profiling detail level
        """
        self.level = level
        self.reports: Dict[str, ProfileReport] = {}
        self.active_report: Optional[ProfileReport] = None
        self.node_start_times: Dict[UUID, float] = {}

    def start_profiling(
        self,
        execution_id: str,
        tree_id: UUID,
    ) -> ProfileReport:
        """Start profiling a tree execution.

        Args:
            execution_id: Execution identifier
            tree_id: Tree identifier

        Returns:
            ProfileReport object for this execution
        """
        report = ProfileReport(
            execution_id=execution_id,
            tree_id=tree_id,
            total_ticks=0,
            total_time_ms=0.0,
            start_time=time.time(),
            end_time=None,
        )

        self.reports[execution_id] = report
        self.active_report = report

        return report

    def stop_profiling(self, execution_id: str) -> ProfileReport:
        """Stop profiling and finalize report.

        Args:
            execution_id: Execution identifier

        Returns:
            Finalized ProfileReport
        """
        if execution_id not in self.reports:
            raise ValueError(f"No profiling session found for: {execution_id}")

        report = self.reports[execution_id]
        report.end_time = time.time()
        report.finalize()

        if self.active_report and self.active_report.execution_id == execution_id:
            self.active_report = None

        return report

    def get_report(self, execution_id: str) -> Optional[ProfileReport]:
        """Get profiling report.

        Args:
            execution_id: Execution identifier

        Returns:
            ProfileReport if found, None otherwise
        """
        return self.reports.get(execution_id)

    def before_tick(
        self,
        node: py_trees.behaviour.Behaviour,
        node_id: UUID,
    ):
        """Called before a node ticks.

        Args:
            node: py_trees node
            node_id: Node UUID
        """
        if self.level == ProfilingLevel.OFF or not self.active_report:
            return

        # Record start time
        self.node_start_times[node_id] = time.perf_counter()

        # Ensure profile exists
        if node_id not in self.active_report.node_profiles:
            profile = NodeProfile(
                node_id=node_id,
                node_name=node.name,
                node_type=type(node).__name__,
                parent_name=node.parent.name if node.parent else None,
                child_count=len(node.children) if hasattr(node, 'children') else 0,
            )
            self.active_report.node_profiles[node_id] = profile

    def after_tick(
        self,
        node: py_trees.behaviour.Behaviour,
        node_id: UUID,
        status: py_trees.common.Status,
    ):
        """Called after a node ticks.

        Args:
            node: py_trees node
            node_id: Node UUID
            status: Result status
        """
        if self.level == ProfilingLevel.OFF or not self.active_report:
            return

        # Calculate duration
        if node_id not in self.node_start_times:
            return

        start_time = self.node_start_times.pop(node_id)
        duration = time.perf_counter() - start_time
        duration_ms = duration * 1000

        # Update profile
        profile = self.active_report.node_profiles.get(node_id)
        if profile:
            profile.update_timing(duration_ms)
            profile.update_status(status)

    def on_tick_complete(self):
        """Called after a full tree tick completes."""
        if self.active_report:
            self.active_report.total_ticks += 1

    def clear_reports(self):
        """Clear all profiling reports."""
        self.reports.clear()
        self.active_report = None
        self.node_start_times.clear()


# Global profiler instance
_global_profiler: Optional[TreeProfiler] = None


def get_profiler(level: ProfilingLevel = ProfilingLevel.BASIC) -> TreeProfiler:
    """Get or create global profiler instance.

    Args:
        level: Profiling level (only used on first call)

    Returns:
        TreeProfiler instance
    """
    global _global_profiler

    if _global_profiler is None:
        _global_profiler = TreeProfiler(level=level)

    return _global_profiler


def format_profile_report(report: ProfileReport, verbose: bool = False) -> str:
    """Format a profile report as text.

    Args:
        report: ProfileReport to format
        verbose: Include detailed per-node stats

    Returns:
        Formatted string
    """
    lines = [str(report)]

    if verbose and report.node_profiles:
        lines.append("\nDETAILED NODE PROFILES:")
        lines.append("-" * 80)

        # Sort by avg time
        sorted_profiles = sorted(
            report.node_profiles.values(),
            key=lambda p: p.avg_time_ms,
            reverse=True
        )

        for profile in sorted_profiles:
            lines.append(f"\n{profile.node_name} ({profile.node_type}):")
            lines.append(f"  Ticks:      {profile.tick_count}")
            lines.append(f"  Avg time:   {profile.avg_time_ms:.3f}ms")
            lines.append(f"  Min time:   {profile.min_time_ms:.3f}ms")
            lines.append(f"  Max time:   {profile.max_time_ms:.3f}ms")
            lines.append(f"  Success:    {profile.success_count}")
            lines.append(f"  Failure:    {profile.failure_count}")
            lines.append(f"  Running:    {profile.running_count}")

            if any(count > 0 for count in profile.time_buckets.values()):
                lines.append(f"  Distribution:")
                for bucket, count in profile.time_buckets.items():
                    if count > 0:
                        pct = (count / profile.tick_count) * 100
                        lines.append(f"    {bucket:12s}: {count:4d} ({pct:5.1f}%)")

    return "\n".join(lines)
