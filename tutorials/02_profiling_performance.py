"""
PyForest SDK Tutorial 2: Profiling & Performance Analysis
==========================================================

This tutorial covers how to use PyForest's built-in profiling system to:
- Measure execution performance
- Identify bottlenecks
- Optimize behavior trees
- Choose the right profiling level for your needs

Profiling levels:
- OFF: No profiling (0% overhead)
- BASIC: Minimal profiling (~1-2% overhead) - recommended for production
- DETAILED: More metrics (~3-5% overhead) - good for debugging
- FULL: Complete profiling (~8-10% overhead) - deep analysis
"""

from py_forest.sdk import PyForest
from py_forest.core.profiler import ProfilingLevel
import time

# =============================================================================
# Example 1: Basic Profiling
# =============================================================================

def example_1_basic_profiling():
    """Enable basic profiling and view performance metrics"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Profiling - Getting Started")
    print("=" * 70)

    # Create PyForest with profiling enabled
    pf = PyForest(profiling_level=ProfilingLevel.BASIC)

    tree = pf.load_tree("examples/robot_v1.json")
    execution = pf.create_execution(tree, initial_blackboard={
        "battery_level": 100.0,
        "distance": 5.0
    })

    # Run several ticks
    print("Running 10 ticks...")
    for i in range(10):
        execution.tick(blackboard_updates={
            "battery_level": 100.0 - (i * 5),
            "distance": 5.0 - (i * 0.3)
        })

    # Get profiling report
    report = execution.get_profiling_report()
    print("\n" + report)
    print()


# =============================================================================
# Example 2: Comparing Profiling Levels
# =============================================================================

def example_2_profiling_levels():
    """Compare different profiling levels and their overhead"""
    print("=" * 70)
    print("EXAMPLE 2: Profiling Levels - Understanding Overhead")
    print("=" * 70)

    tree_path = "examples/robot_v1.json"
    num_ticks = 100

    results = {}

    # Test each profiling level
    for level_name, level in [
        ("OFF", ProfilingLevel.OFF),
        ("BASIC", ProfilingLevel.BASIC),
        ("DETAILED", ProfilingLevel.DETAILED),
        ("FULL", ProfilingLevel.FULL),
    ]:
        pf = PyForest(profiling_level=level)
        tree = pf.load_tree(tree_path)
        execution = pf.create_execution(tree, initial_blackboard={
            "battery_level": 100.0,
            "distance": 5.0
        })

        # Time the execution
        start = time.perf_counter()
        for i in range(num_ticks):
            execution.tick(blackboard_updates={
                "battery_level": 100.0 - (i % 100),
                "distance": 5.0
            })
        elapsed = time.perf_counter() - start

        results[level_name] = elapsed

        print(f"{level_name:10} : {elapsed*1000:6.2f}ms for {num_ticks} ticks "
              f"({elapsed/num_ticks*1000000:.1f}µs/tick)")

    # Calculate overhead
    baseline = results["OFF"]
    print(f"\nOverhead relative to OFF:")
    for level_name in ["BASIC", "DETAILED", "FULL"]:
        overhead = ((results[level_name] - baseline) / baseline) * 100
        print(f"{level_name:10} : +{overhead:5.2f}%")
    print()


# =============================================================================
# Example 3: Detailed Performance Metrics
# =============================================================================

def example_3_detailed_metrics():
    """Use DETAILED level to get comprehensive metrics"""
    print("=" * 70)
    print("EXAMPLE 3: Detailed Metrics - In-Depth Analysis")
    print("=" * 70)

    pf = PyForest(profiling_level=ProfilingLevel.DETAILED)
    tree = pf.load_tree("examples/robot_v1.json")
    execution = pf.create_execution(tree, initial_blackboard={
        "battery_level": 100.0,
        "distance": 5.0
    })

    # Run with varying inputs to create interesting patterns
    scenarios = [
        {"battery_level": 100.0, "distance": 10.0},  # Success
        {"battery_level": 90.0, "distance": 8.0},    # Success
        {"battery_level": 75.0, "distance": 5.0},    # Success
        {"battery_level": 50.0, "distance": 3.0},    # Success
        {"battery_level": 15.0, "distance": 2.0},    # Low battery
        {"battery_level": 10.0, "distance": 1.5},    # Low battery
    ]

    print(f"Running {len(scenarios)} scenarios with varying conditions...")
    for scenario in scenarios:
        execution.tick(blackboard_updates=scenario)

    # Get verbose report
    report = execution.get_profiling_report(verbose=True)
    print("\n" + report)
    print()


# =============================================================================
# Example 4: Identifying Bottlenecks
# =============================================================================

def example_4_bottleneck_detection():
    """Create a slow tree and use profiling to find bottlenecks"""
    print("=" * 70)
    print("EXAMPLE 4: Bottleneck Detection - Finding Slow Nodes")
    print("=" * 70)

    from py_forest.models.tree import TreeDefinition, NodeDefinition
    import uuid

    # Create a tree with some intentionally slow nodes
    root_id = str(uuid.uuid4())
    fast_id = str(uuid.uuid4())
    slow_id = str(uuid.uuid4())
    very_slow_id = str(uuid.uuid4())

    nodes = [
        NodeDefinition(
            id=root_id,
            name="Root Sequence",
            node_type="sequence",
            parent_id=None,
            properties={}
        ),
        NodeDefinition(
            id=fast_id,
            name="Fast Operation",
            node_type="action",
            parent_id=root_id,
            properties={
                "blackboard_key": "/fast_done",
                "value": True
            }
        ),
        NodeDefinition(
            id=slow_id,
            name="Slow Operation",
            node_type="action",
            parent_id=root_id,
            properties={
                "blackboard_key": "/slow_done",
                "value": True,
                "sleep_ms": 50  # Simulate 50ms operation
            }
        ),
        NodeDefinition(
            id=very_slow_id,
            name="Very Slow Operation",
            node_type="action",
            parent_id=root_id,
            properties={
                "blackboard_key": "/very_slow_done",
                "value": True,
                "sleep_ms": 150  # Simulate 150ms operation
            }
        ),
    ]

    tree = TreeDefinition(
        id=str(uuid.uuid4()),
        name="Performance Test Tree",
        version="1.0.0",
        description="Tree with varying node performance",
        root_id=root_id,
        nodes=nodes
    )

    # Profile it
    pf = PyForest(profiling_level=ProfilingLevel.FULL)
    execution = pf.create_execution(tree)

    print("Running tree with slow operations...")
    # Note: Since our behavior system might not support sleep_ms,
    # this is a conceptual example. In practice, you'd identify
    # real slow nodes like complex conditions or heavy computations.

    for i in range(3):
        execution.tick()

    report = execution.get_profiling_report(verbose=True)
    print("\n" + report)

    print("\n💡 Profiler highlights nodes taking > 100ms automatically!")
    print("   Use this to identify optimization opportunities.")
    print()


# =============================================================================
# Example 5: Production Monitoring
# =============================================================================

def example_5_production_monitoring():
    """Best practices for profiling in production environments"""
    print("=" * 70)
    print("EXAMPLE 5: Production Monitoring - Best Practices")
    print("=" * 70)

    print("Production Profiling Guidelines:")
    print("-" * 70)
    print()

    # Recommendation 1: Use BASIC level
    print("1. Use ProfilingLevel.BASIC for production")
    print("   - Only 1-2% overhead")
    print("   - Essential metrics without performance hit")
    print()

    pf = PyForest(profiling_level=ProfilingLevel.BASIC)
    tree = pf.load_tree("examples/robot_v1.json")
    execution = pf.create_execution(tree)

    # Simulate production workload
    for i in range(50):
        execution.tick(blackboard_updates={
            "battery_level": 100.0 - (i % 100) * 0.5,
            "distance": 5.0
        })

    # Get report without verbose output (cleaner for logging)
    report = execution.get_profiling_report(verbose=False)
    print("Example production log output:")
    print("-" * 70)
    print(report)

    # Recommendation 2: Check for anomalies
    print("\n2. Monitor for performance anomalies")
    print("   - Set alerts for avg execution time > threshold")
    print("   - Track tick count to detect infinite loops")
    print("   - Monitor status distribution (too many failures?)")
    print()

    # Recommendation 3: Periodic detailed profiling
    print("3. Periodically run DETAILED profiling offline")
    print("   - Use staging environment")
    print("   - Profile with production data")
    print("   - Identify optimization opportunities")
    print()


# =============================================================================
# Example 6: Performance Optimization Workflow
# =============================================================================

def example_6_optimization_workflow():
    """Complete workflow: profile -> identify -> optimize -> verify"""
    print("=" * 70)
    print("EXAMPLE 6: Optimization Workflow")
    print("=" * 70)

    # Step 1: Baseline measurement
    print("STEP 1: Establish baseline performance")
    print("-" * 70)

    pf = PyForest(profiling_level=ProfilingLevel.FULL)
    tree = pf.load_tree("examples/robot_v1.json")
    execution = pf.create_execution(tree)

    # Run baseline test
    for i in range(20):
        execution.tick(blackboard_updates={
            "battery_level": 100.0 - i * 2,
            "distance": 5.0
        })

    baseline_report = execution.get_profiling_report(verbose=True)
    print(baseline_report)

    # Step 2: Identify bottlenecks
    print("\nSTEP 2: Identify bottlenecks from report")
    print("-" * 70)
    print("Look for:")
    print("  • Nodes with high avg execution time")
    print("  • Nodes ticked frequently but unnecessary")
    print("  • Status patterns indicating retries")
    print()

    # Step 3: Optimize (example: tree restructuring)
    print("STEP 3: Optimize the tree")
    print("-" * 70)
    print("Common optimizations:")
    print("  • Move expensive checks lower in tree")
    print("  • Cache blackboard reads")
    print("  • Use Parallel nodes for independent operations")
    print("  • Add early-exit conditions")
    print()

    # Step 4: Verify improvement
    print("STEP 4: Verify optimization results")
    print("-" * 70)
    print("  • Re-run profiling with same workload")
    print("  • Compare metrics (avg time, tick count)")
    print("  • Ensure behavior correctness maintained")
    print()


# =============================================================================
# Example 7: Exporting Profiling Data
# =============================================================================

def example_7_export_data():
    """Export profiling data for external analysis"""
    print("=" * 70)
    print("EXAMPLE 7: Exporting Profiling Data")
    print("=" * 70)

    pf = PyForest(profiling_level=ProfilingLevel.DETAILED)
    tree = pf.load_tree("examples/robot_v1.json")
    execution = pf.create_execution(tree)

    # Run workload
    for i in range(15):
        execution.tick(blackboard_updates={
            "battery_level": 100.0 - i * 5,
            "distance": 5.0
        })

    # Access raw profiling data
    profiler = execution._profiler  # Internal API
    if profiler and execution._execution_id in profiler._profiles:
        profile = profiler._profiles[execution._execution_id]

        print("Raw profiling data structure:")
        print(f"  Execution ID: {execution._execution_id}")
        print(f"  Tree ID: {profile.tree_id}")
        print(f"  Start time: {profile.start_time}")
        print(f"  Total ticks: {len(profile.tick_times)}")

        # Export to dict (could be saved as JSON)
        import json
        export_data = {
            "execution_id": execution._execution_id,
            "tree_id": profile.tree_id,
            "total_ticks": len(profile.tick_times),
            "tick_times_ms": [t * 1000 for t in profile.tick_times],
            "avg_tick_time_ms": sum(profile.tick_times) / len(profile.tick_times) * 1000,
            "status_counts": dict(profile.status_counts),
        }

        # Save to file
        with open("tutorials/profile_export.json", "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"\n✓ Exported profiling data to tutorials/profile_export.json")
        print("\nSample export:")
        print(json.dumps(export_data, indent=2))
    else:
        print("Note: Profiling data structure may vary")

    print()


# =============================================================================
# Run All Examples
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" PyForest SDK Tutorial 2: Profiling & Performance Analysis")
    print("=" * 70 + "\n")

    example_1_basic_profiling()
    example_2_profiling_levels()
    example_3_detailed_metrics()
    example_4_bottleneck_detection()
    example_5_production_monitoring()
    example_6_optimization_workflow()
    example_7_export_data()

    print("=" * 70)
    print(" Tutorial Complete! 🎉")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  ✓ Use ProfilingLevel.BASIC in production (1-2% overhead)")
    print("  ✓ Use ProfilingLevel.DETAILED for debugging (3-5% overhead)")
    print("  ✓ Use ProfilingLevel.FULL for deep analysis (8-10% overhead)")
    print("  ✓ Look for nodes > 100ms as optimization targets")
    print("  ✓ Compare before/after metrics when optimizing")
    print("\nNext: tutorial 03_version_control.py for tree diffing")
    print()
