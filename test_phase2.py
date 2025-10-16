#!/usr/bin/env python3
"""Test script for Phase 2 - FastAPI REST API.

This script demonstrates the PyForest REST API functionality.

Usage:
    1. Start the API server in one terminal:
       uvicorn py_forest.api.main:app --reload

    2. Run this test script in another terminal:
       python test_phase2.py
"""

import json
import time
from pathlib import Path
from uuid import UUID

import requests

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_health():
    """Test health check endpoint."""
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200


def test_behaviors():
    """Test behavior schema endpoints."""
    print_section("2. Behavior Schemas")

    # Get all schemas
    print("Getting all behavior schemas...")
    response = requests.get(f"{BASE_URL}/behaviors/")
    assert response.status_code == 200
    schemas = response.json()
    print(f"Found {len(schemas)} behavior types:")
    for node_type in list(schemas.keys())[:5]:  # Show first 5
        print(f"  - {node_type}: {schemas[node_type]['display_name']}")

    # Get behaviors by category
    print("\nGetting composites...")
    response = requests.get(f"{BASE_URL}/behaviors/category/composite")
    assert response.status_code == 200
    composites = response.json()
    print(f"Composites: {composites}")

    # Get specific schema
    print("\nGetting Sequence schema...")
    response = requests.get(f"{BASE_URL}/behaviors/Sequence")
    assert response.status_code == 200
    schema = response.json()
    print(f"Sequence schema: {json.dumps(schema, indent=2)}")


def test_tree_library():
    """Test tree library endpoints."""
    print_section("3. Tree Library Management")

    # Load example tree
    example_path = Path("examples/simple_tree.json")
    if not example_path.exists():
        print("⚠️  Warning: examples/simple_tree.json not found, skipping tree tests")
        return None

    with open(example_path) as f:
        tree_def = json.load(f)

    # Create tree
    print("Creating tree...")
    response = requests.post(f"{BASE_URL}/trees/", json=tree_def)
    assert response.status_code == 201
    created = response.json()
    tree_id = created["tree_id"]
    print(f"Created tree: {created['metadata']['name']} (ID: {tree_id})")

    # List trees
    print("\nListing all trees...")
    response = requests.get(f"{BASE_URL}/trees/")
    assert response.status_code == 200
    trees = response.json()
    print(f"Found {len(trees)} tree(s):")
    for tree in trees:
        print(f"  - {tree['name']} v{tree['latest_version']}")

    # Get specific tree
    print(f"\nGetting tree {tree_id}...")
    response = requests.get(f"{BASE_URL}/trees/{tree_id}")
    assert response.status_code == 200
    retrieved = response.json()
    print(f"Retrieved: {retrieved['metadata']['name']}")

    # Search trees
    print("\nSearching for 'patrol'...")
    response = requests.get(f"{BASE_URL}/trees/search/", params={"query": "patrol"})
    assert response.status_code == 200
    results = response.json()
    print(f"Found {len(results)} matching tree(s)")

    return tree_id


def test_execution(tree_id: str):
    """Test execution endpoints."""
    print_section("4. Execution Control")

    # Create execution
    print(f"Creating execution for tree {tree_id}...")
    config = {
        "tree_id": tree_id,
        "mode": "manual",
        "initial_blackboard": {
            "/battery/level": 0.75
        }
    }
    response = requests.post(f"{BASE_URL}/executions/", json=config)
    assert response.status_code == 201
    summary = response.json()
    execution_id = summary["execution_id"]
    print(f"Created execution: {execution_id}")
    print(f"Initial status: {summary['status']}")

    # List executions
    print("\nListing all executions...")
    response = requests.get(f"{BASE_URL}/executions/")
    assert response.status_code == 200
    executions = response.json()
    print(f"Found {len(executions)} execution(s)")

    # Tick the tree
    print(f"\nTicking execution {execution_id}...")
    tick_request = {
        "count": 1,
        "capture_snapshot": True
    }
    response = requests.post(
        f"{BASE_URL}/executions/{execution_id}/tick",
        json=tick_request
    )
    assert response.status_code == 200
    tick_response = response.json()
    print(f"Ticked {tick_response['ticks_executed']} time(s)")
    print(f"Root status: {tick_response['root_status']}")
    print(f"Total ticks: {tick_response['new_tick_count']}")

    # Get snapshot
    print(f"\nGetting snapshot...")
    response = requests.get(f"{BASE_URL}/executions/{execution_id}/snapshot")
    assert response.status_code == 200
    snapshot = response.json()
    print(f"Tick count: {snapshot['tick_count']}")
    print(f"Root status: {snapshot['root_status']}")
    print(f"Blackboard: {snapshot['blackboard']}")
    print(f"Node states: {len(snapshot['node_states'])} nodes")

    # Tick multiple times
    print(f"\nTicking 3 more times...")
    tick_request["count"] = 3
    tick_request["capture_snapshot"] = False  # Skip snapshot for speed
    response = requests.post(
        f"{BASE_URL}/executions/{execution_id}/tick",
        json=tick_request
    )
    assert response.status_code == 200
    tick_response = response.json()
    print(f"Total ticks: {tick_response['new_tick_count']}")

    # Get updated summary
    print(f"\nGetting execution summary...")
    response = requests.get(f"{BASE_URL}/executions/{execution_id}")
    assert response.status_code == 200
    summary = response.json()
    print(f"Status: {summary['status']}")
    print(f"Tick count: {summary['tick_count']}")
    print(f"Started at: {summary['started_at']}")

    # Delete execution
    print(f"\nDeleting execution {execution_id}...")
    response = requests.delete(f"{BASE_URL}/executions/{execution_id}")
    assert response.status_code == 204
    print("Execution deleted successfully")

    return execution_id


def cleanup(tree_id: str):
    """Cleanup test data."""
    print_section("5. Cleanup")

    if tree_id:
        print(f"Deleting tree {tree_id}...")
        response = requests.delete(f"{BASE_URL}/trees/{tree_id}")
        if response.status_code == 204:
            print("Tree deleted successfully")
        else:
            print(f"Warning: Could not delete tree (status {response.status_code})")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  PyForest Phase 2 API Test")
    print("=" * 60)

    try:
        # Check if server is running
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
        except requests.exceptions.RequestException:
            print("\n❌ Error: API server is not running!")
            print("\nPlease start the server first:")
            print("  uvicorn py_forest.api.main:app --reload")
            return

        # Run tests
        test_health()
        test_behaviors()
        tree_id = test_tree_library()

        if tree_id:
            test_execution(tree_id)
            cleanup(tree_id)

        print_section("✅ All Tests Passed!")
        print("Phase 2 API is working correctly!\n")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        raise


if __name__ == "__main__":
    main()
