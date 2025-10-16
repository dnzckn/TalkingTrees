#!/usr/bin/env python3
"""
Test script for Day in Life visualization.
Loads the tree, creates execution, and runs some ticks to verify it works.
"""

import json
import requests
import time
from uuid import uuid4

API_BASE = "http://localhost:8000"

def main():
    print("=== Testing Day in Life Visualization ===\n")

    # Use existing tree
    tree_id = "7456df29-cf73-4011-a8f6-58a3144e1fde"  # Existing tree from catalog
    print(f"Using existing tree: {tree_id}\n")

    # Step 1: Create execution
    print("Step 1: Creating execution instance...")
    exec_config = {"tree_id": tree_id}  # Let API use default version
    response = requests.post(f"{API_BASE}/executions/", json=exec_config)
    if response.status_code == 201:
        execution_id = response.json()["execution_id"]
        print(f"  ✓ Execution created: {execution_id}")
    else:
        print(f"  ✗ Failed to create execution: {response.status_code}")
        print(response.json())
        return

    # Step 2: Run some ticks and observe
    print("\nStep 2: Running simulation ticks...\n")
    for i in range(100):  # Run more ticks to see full day cycle
        # Tick
        tick_response = requests.post(
            f"{API_BASE}/executions/{execution_id}/tick",
            json={"count": 1, "capture_snapshot": True}
        )

        if tick_response.status_code != 200:
            print(f"  ✗ Tick failed: {tick_response.status_code}")
            break

        # Get snapshot
        snapshot_response = requests.get(f"{API_BASE}/executions/{execution_id}/snapshot")
        snapshot = snapshot_response.json()

        # Extract state from blackboard (keys have / prefix)
        blackboard = snapshot["blackboard"]
        hour = blackboard.get("/hour", 0)
        phase = blackboard.get("/phase", "unknown")
        hunger = blackboard.get("/hunger", 0)
        thirst = blackboard.get("/thirst", 0)
        energy = blackboard.get("/energy", 0)
        stress = blackboard.get("/stress", 0)
        money = blackboard.get("/money", 0)

        # Extract log messages from node_states
        logs = [
            state["feedback_message"]
            for state in snapshot.get("node_states", {}).values()
            if state.get("feedback_message") and state["feedback_message"] != "success"
        ]

        print(f"Tick {i+1:2d}: Hour {hour:2d} ({phase:8s}) | "
              f"H:{hunger:5.1f} T:{thirst:5.1f} E:{energy:6.1f} "
              f"S:{stress:5.1f} $:{money:6.1f}")

        for log in logs:
            if log and log.strip():
                print(f"         └─ {log}")

        # Check if day completed (hour wrapped around from evening to next morning)
        if i > 10 and hour <= 7 and phase == "morning":
            # Only break if we've run a while and are back to morning
            prev_tick = i - 1
            if prev_tick > 0:
                print("\n  ✓ Day cycle completed! Back to morning phase.\n")
                break

        time.sleep(0.05)  # Faster updates

    # Step 3: Get statistics
    print("\nStep 3: Getting execution statistics...")
    stats_response = requests.get(f"{API_BASE}/visualizations/executions/{execution_id}/statistics")
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"  Total ticks: {stats['total_ticks']}")
        print(f"  Total time: {stats['total_time_ms']:.2f}ms")
        print(f"  Avg tick time: {stats['avg_tick_time_ms']:.2f}ms")
        print(f"  Running ticks: {stats['running_ticks']}")

    print("\n=== Test Complete ===")
    print(f"\nVisualization ready!")
    print(f"Open: visualization/day_in_life.html")
    print(f"Tree ID to use: {tree_id}")
    print(f"\nThe visualization will load the tree, create an execution, and")
    print(f"show the simulation running in real-time with live stats and logs.")

if __name__ == "__main__":
    main()
