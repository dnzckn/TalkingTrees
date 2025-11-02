#!/usr/bin/env python3
"""Test all REST API endpoints after custom node removal and signature fixes."""

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from talking_trees.api.main import app


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def tree_id(client):
    """Create a tree and return its ID for reuse in other tests."""
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
    assert response.status_code == 201
    data = response.json()
    return data.get("tree_id")


@pytest.fixture(scope="module")
def execution_id(client, tree_id):
    """Create an execution and return its ID for reuse in other tests."""
    execution_data = {
        "tree_id": tree_id,
        "initial_blackboard": {
            "test_var": 42
        }
    }

    response = client.post("/executions", json=execution_data)
    assert response.status_code == 201
    data = response.json()
    return data.get("execution_id")


def test_health(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_behaviors(client):
    """Test getting behavior schemas."""
    response = client.get("/behaviors/")
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0

    # Verify custom nodes are NOT present
    custom_nodes = ['CheckBattery', 'Log', 'Wait', 'GetBlackboardVariable', 'CheckBlackboardCondition']

    for custom_node in custom_nodes:
        assert custom_node not in data, f"Custom node '{custom_node}' should not be in schemas"

    # Verify real py_trees nodes are present
    required_nodes = ['Sequence', 'Selector', 'Parallel', 'Success', 'Failure',
                     'CheckBlackboardVariableValue', 'SetBlackboardVariable', 'TickCounter']

    for required in required_nodes:
        assert required in data, f"Required node '{required}' missing from schemas"


def test_create_tree(client, tree_id):
    """Test creating a tree with real py_trees nodes."""
    # Tree already created by fixture, just verify it exists
    response = client.get(f"/trees/{tree_id}")
    assert response.status_code == 200


def test_get_tree(client, tree_id):
    """Test retrieving a tree."""
    response = client.get(f"/trees/{tree_id}")
    assert response.status_code == 200

    data = response.json()
    assert data['metadata']['name'] == "API Test Tree"
    assert data['root']['node_type'] == "Sequence"


def test_create_execution(client, execution_id):
    """Test creating an execution."""
    # Execution already created by fixture, just verify it exists
    assert execution_id is not None
    assert len(execution_id) > 0


def test_tick_execution(client, execution_id):
    """Test ticking an execution."""
    tick_data = {
        "count": 1,
        "capture_snapshot": True,
        "blackboard_updates": {}
    }

    response = client.post(f"/executions/{execution_id}/tick", json=tick_data)
    assert response.status_code == 200

    data = response.json()
    assert "root_status" in data
    assert data["ticks_executed"] > 0


def test_with_example_tree(client):
    """Test with a real example tree."""
    with open('examples/trees/01_simple_sequence.json') as f:
        tree_data = json.load(f)

    # Ensure tree has a unique ID
    if 'tree_id' not in tree_data:
        tree_data['tree_id'] = str(uuid4())

    # Create tree
    response = client.post("/trees", json=tree_data)
    assert response.status_code == 201

    tree_id = response.json()["tree_id"]

    # Create execution
    response = client.post("/executions", json={"tree_id": tree_id})
    assert response.status_code == 201

    execution_id = response.json()["execution_id"]

    # Tick execution
    response = client.post(f"/executions/{execution_id}/tick", json={
        "count": 1,
        "capture_snapshot": True
    })
    assert response.status_code == 200

    status = response.json()["root_status"]
    assert status in ["SUCCESS", "FAILURE", "RUNNING"]


def test_round_trip(client):
    """Test round-trip conversion via API."""
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
    assert response.status_code == 201

    # Retrieve tree
    response = client.get(f"/trees/{tree_id}")
    assert response.status_code == 200

    retrieved_tree = response.json()

    # Verify structure preserved
    assert retrieved_tree["root"]["node_type"] == "Selector"
    assert len(retrieved_tree["root"]["children"]) == 3

    # Verify TickCounter config preserved
    tick_counter = retrieved_tree["root"]["children"][0]
    assert tick_counter["node_type"] == "TickCounter"
    assert tick_counter["config"]["duration"] == 5
