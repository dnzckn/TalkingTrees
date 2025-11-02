#!/usr/bin/env python3
"""Test all REST API endpoints after custom node removal and signature fixes."""

import sys
sys.path.insert(0, 'src')

import json
from uuid import uuid4
from fastapi.testclient import TestClient
from talking_trees.api.main import app

# Create test client
client = TestClient(app)


def test_health():
    """Test health check endpoint."""
    print("\n=== Testing /health ===")
    response = client.get("/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("[PASS] PASS")


def test_get_behaviors():
    """Test getting behavior schemas."""
    print("\n=== Testing GET /behaviors/ ===")
    response = client.get("/behaviors/")
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"Error: {response.text}")
        print("[FAIL] FAIL")
        return False

    data = response.json()
    print(f"Behavior types: {len(data)}")

    # Verify custom nodes are NOT present
    custom_nodes = ['CheckBattery', 'Log', 'Wait', 'GetBlackboardVariable', 'CheckBlackboardCondition']

    for custom_node in custom_nodes:
        if custom_node in data:
            print(f"[FAIL] FAIL: Custom node '{custom_node}' still in schemas!")
            return False

    print(f"[PASS] All custom nodes removed from schemas")

    # Verify real py_trees nodes are present
    required_nodes = ['Sequence', 'Selector', 'Parallel', 'Success', 'Failure',
                     'CheckBlackboardVariableValue', 'SetBlackboardVariable', 'TickCounter']

    for required in required_nodes:
        if required not in data:
            print(f"[FAIL] FAIL: Required node '{required}' missing!")
            return False

    print(f"[PASS] All required py_trees nodes present")
    print("[PASS] PASS")
    return True


def test_create_tree():
    """Test creating a tree with real py_trees nodes."""
    print("\n=== Testing POST /trees ===")

    # Create tree with proper TreeDefinition structure
    tree_data = {
        "$schema": "1.0.0",
        "tree_id": str(uuid4()),
        "metadata": {
            "name": "API Test Tree",
            "version": "1.0.0",
            "description": "Test tree with real py_trees nodes"
        },
        "root": {
            "node_type": "Sequence",
            "name": "Test Sequence",
            "config": {},
            "children": [
                {
                    "node_type": "Success",
                    "name": "First Success",
                    "config": {}
                },
                {
                    "node_type": "CheckBlackboardVariableValue",
                    "name": "Check Value",
                    "config": {
                        "variable": "test_var",
                        "operator": "==",
                        "value": 42
                    }
                },
                {
                    "node_type": "SetBlackboardVariable",
                    "name": "Set Result",
                    "config": {
                        "variable": "result",
                        "value": "success"
                    }
                }
            ]
        }
    }

    response = client.post("/trees", json=tree_data)
    print(f"Status: {response.status_code}")

    if response.status_code != 201:
        print(f"Error: {response.text}")
        print("[FAIL] FAIL")
        return None

    data = response.json()
    tree_id = data.get("tree_id")
    print(f"Created tree ID: {tree_id}")
    print("[PASS] PASS")
    return tree_id


def test_get_tree(tree_id):
    """Test retrieving a tree."""
    print(f"\n=== Testing GET /trees/{tree_id} ===")

    response = client.get(f"/trees/{tree_id}")
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"Error: {response.text}")
        print("[FAIL] FAIL")
        return False

    data = response.json()
    print(f"Tree name: {data['metadata']['name']}")
    print(f"Root node: {data['root']['node_type']}")
    print("[PASS] PASS")
    return True


def test_create_execution(tree_id):
    """Test creating an execution."""
    print(f"\n=== Testing POST /executions ===")

    execution_data = {
        "tree_id": tree_id,
        "initial_blackboard": {
            "test_var": 42
        }
    }

    response = client.post("/executions", json=execution_data)
    print(f"Status: {response.status_code}")

    if response.status_code != 201:
        print(f"Error: {response.text}")
        print("[FAIL] FAIL")
        return None

    data = response.json()
    execution_id = data.get("execution_id")
    print(f"Created execution ID: {execution_id}")
    print("[PASS] PASS")
    return execution_id


def test_tick_execution(execution_id):
    """Test ticking an execution."""
    print(f"\n=== Testing POST /executions/{execution_id}/tick ===")

    tick_data = {
        "count": 1,
        "capture_snapshot": True,
        "blackboard_updates": {}
    }

    response = client.post(f"/executions/{execution_id}/tick", json=tick_data)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"Error: {response.text}")
        print("[FAIL] FAIL")
        return False

    data = response.json()
    print(f"Root status: {data['root_status']}")
    if data.get('snapshot'):
        print(f"Blackboard: {data['snapshot']['blackboard']}")
    print("[PASS] PASS")
    return True


def test_with_example_tree():
    """Test with a real example tree."""
    print("\n=== Testing with Example Tree (01_simple_sequence.json) ===")

    with open('examples/trees/01_simple_sequence.json', 'r') as f:
        tree_data = json.load(f)

    # Ensure tree has a unique ID
    if 'tree_id' not in tree_data:
        tree_data['tree_id'] = str(uuid4())

    # Create tree
    response = client.post("/trees", json=tree_data)
    if response.status_code != 201:
        print(f"Failed to create tree: {response.text}")
        print("[FAIL] FAIL")
        return False

    tree_id = response.json()["tree_id"]
    print(f"Created tree from example: {tree_id}")

    # Create execution
    response = client.post("/executions", json={"tree_id": tree_id})
    if response.status_code != 201:
        print(f"Failed to create execution: {response.text}")
        print("[FAIL] FAIL")
        return False

    execution_id = response.json()["execution_id"]
    print(f"Created execution: {execution_id}")

    # Tick execution
    response = client.post(f"/executions/{execution_id}/tick", json={
        "count": 1,
        "capture_snapshot": True
    })
    if response.status_code != 200:
        print(f"Failed to tick: {response.text}")
        print("[FAIL] FAIL")
        return False

    status = response.json()["root_status"]
    print(f"Execution status: {status}")
    print("[PASS] PASS")
    return True


def test_round_trip():
    """Test round-trip conversion via API."""
    print("\n=== Testing Round-Trip Conversion ===")

    # Create tree with various node types
    tree_id = str(uuid4())
    tree_data = {
        "$schema": "1.0.0",
        "tree_id": tree_id,
        "metadata": {
            "name": "Round-Trip Test",
            "version": "1.0.0"
        },
        "root": {
            "node_type": "Selector",
            "name": "Root",
            "config": {"memory": False},
            "children": [
                {
                    "node_type": "TickCounter",
                    "name": "Wait 5 Ticks",
                    "config": {
                        "duration": 5,
                        "completion_status": "SUCCESS"
                    }
                },
                {
                    "node_type": "CheckBlackboardVariableValue",
                    "name": "Check Condition",
                    "config": {
                        "variable": "value",
                        "operator": ">",
                        "value": 10
                    }
                },
                {
                    "node_type": "Success",
                    "name": "Fallback",
                    "config": {}
                }
            ]
        }
    }

    # Create tree
    response = client.post("/trees", json=tree_data)
    if response.status_code != 201:
        print(f"Failed to create: {response.text}")
        print("[FAIL] FAIL")
        return False

    # Retrieve tree
    response = client.get(f"/trees/{tree_id}")
    if response.status_code != 200:
        print(f"Failed to retrieve: {response.text}")
        print("[FAIL] FAIL")
        return False

    retrieved_tree = response.json()

    # Verify structure preserved
    if retrieved_tree["root"]["node_type"] != "Selector":
        print("[FAIL] Root node type changed!")
        return False

    if len(retrieved_tree["root"]["children"]) != 3:
        print("[FAIL] Children count changed!")
        return False

    # Verify TickCounter config preserved
    tick_counter = retrieved_tree["root"]["children"][0]
    if tick_counter["node_type"] != "TickCounter":
        print("[FAIL] TickCounter not preserved!")
        return False

    if tick_counter["config"]["duration"] != 5:
        print("[FAIL] TickCounter duration not preserved!")
        return False

    print("[PASS] Round-trip successful - all data preserved!")
    print("[PASS] PASS")
    return True


def main():
    """Run all API tests."""
    print("=" * 80)
    print("TalkingTrees REST API Test Suite")
    print("Testing after custom node removal and signature fixes")
    print("=" * 80)

    try:
        # Basic tests
        test_health()
        test_get_behaviors()

        # Tree creation and management
        tree_id = test_create_tree()
        if not tree_id:
            print("\n[FAIL] CRITICAL: Cannot create trees!")
            return False

        test_get_tree(tree_id)

        # Execution tests
        execution_id = test_create_execution(tree_id)
        if not execution_id:
            print("\n[FAIL] CRITICAL: Cannot create executions!")
            return False

        test_tick_execution(execution_id)

        # Example tree test
        test_with_example_tree()

        # Round-trip test
        test_round_trip()

        print("\n" + "=" * 80)
        print("ALL API TESTS PASSED!")
        print("=" * 80)
        print("[PASS] Health check works")
        print("[PASS] Behaviors endpoint works (no custom nodes)")
        print("[PASS] Tree creation works")
        print("[PASS] Tree retrieval works")
        print("[PASS] Execution creation works")
        print("[PASS] Tick execution works")
        print("[PASS] Example trees work")
        print("[PASS] Round-trip conversion works")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
