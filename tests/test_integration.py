"""Comprehensive integration tests for TalkingTrees API."""

import json
import time
from pathlib import Path
from uuid import uuid4

import pytest
import requests

BASE_URL = "http://localhost:8000"

# Load example tree
EXAMPLE_TREE_PATH = (
    Path(__file__).parent.parent / "examples/trees/01_simple_sequence.json"
)


class TestTreeLibrary:
    """Test tree library operations."""

    def test_create_tree(self):
        """Test creating a tree in the library."""
        with open(EXAMPLE_TREE_PATH) as f:
            tree_def = json.load(f)

        # Create unique tree
        tree_def["metadata"]["name"] = f"Test Tree {uuid4()}"
        tree_def["tree_id"] = str(uuid4())

        response = requests.post(f"{BASE_URL}/trees/", json=tree_def)
        assert response.status_code == 201
        created_tree = response.json()
        assert created_tree["metadata"]["name"] == tree_def["metadata"]["name"]

        return created_tree["tree_id"]

    def test_list_trees(self):
        """Test listing all trees."""
        response = requests.get(f"{BASE_URL}/trees/")
        assert response.status_code == 200
        trees = response.json()
        assert isinstance(trees, list)

    def test_get_tree(self):
        """Test retrieving a specific tree."""
        tree_id = self.test_create_tree()

        response = requests.get(f"{BASE_URL}/trees/{tree_id}")
        assert response.status_code == 200
        tree = response.json()
        assert tree["tree_id"] == tree_id

    def test_validate_tree(self):
        """Test tree validation."""
        with open(EXAMPLE_TREE_PATH) as f:
            tree_def = json.load(f)

        response = requests.post(f"{BASE_URL}/validation/trees", json=tree_def)
        assert response.status_code == 200
        result = response.json()
        assert "is_valid" in result
        assert result["is_valid"] is True


class TestExecution:
    """Test execution lifecycle."""

    def setup_method(self):
        """Create a tree for testing."""
        with open(EXAMPLE_TREE_PATH) as f:
            tree_def = json.load(f)

        tree_def["metadata"]["name"] = f"Test Execution Tree {uuid4()}"
        tree_def["tree_id"] = str(uuid4())

        response = requests.post(f"{BASE_URL}/trees/", json=tree_def)
        assert response.status_code == 201
        self.tree_id = response.json()["tree_id"]

    def test_create_execution(self):
        """Test creating an execution instance."""
        config = {"tree_id": self.tree_id}
        response = requests.post(f"{BASE_URL}/executions/", json=config)
        assert response.status_code == 201
        execution = response.json()
        assert "execution_id" in execution
        return execution["execution_id"]

    def test_list_executions(self):
        """Test listing executions."""
        response = requests.get(f"{BASE_URL}/executions/")
        assert response.status_code == 200
        executions = response.json()
        assert isinstance(executions, list)

    def test_tick_execution(self):
        """Test ticking an execution."""
        exec_id = self.test_create_execution()

        response = requests.post(
            f"{BASE_URL}/executions/{exec_id}/tick",
            json={"count": 1, "capture_snapshot": True},
        )
        assert response.status_code == 200
        tick_response = response.json()
        assert "ticks_executed" in tick_response
        assert "root_status" in tick_response
        assert tick_response["ticks_executed"] > 0

    def test_get_snapshot(self):
        """Test getting execution snapshot."""
        exec_id = self.test_create_execution()

        # Tick once
        requests.post(
            f"{BASE_URL}/executions/{exec_id}/tick",
            json={"count": 1},
        )

        # Get snapshot
        response = requests.get(f"{BASE_URL}/executions/{exec_id}/snapshot")
        assert response.status_code == 200
        snapshot = response.json()
        assert "tree" in snapshot
        assert "blackboard" in snapshot
        assert "node_states" in snapshot


class TestDebugging:
    """Test debugging features."""

    def setup_method(self):
        """Create execution for testing."""
        with open(EXAMPLE_TREE_PATH) as f:
            tree_def = json.load(f)

        tree_def["metadata"]["name"] = f"Debug Test Tree {uuid4()}"
        tree_def["tree_id"] = str(uuid4())

        response = requests.post(f"{BASE_URL}/trees/", json=tree_def)
        self.tree_id = response.json()["tree_id"]

        config = {"tree_id": self.tree_id}
        response = requests.post(f"{BASE_URL}/executions/", json=config)
        self.exec_id = response.json()["execution_id"]

        # Get a node ID for testing
        response = requests.get(f"{BASE_URL}/executions/{self.exec_id}/snapshot")
        snapshot = response.json()
        self.node_id = snapshot["tree"]["root"]["id"]

    def test_get_debug_state(self):
        """Test getting debug state."""
        response = requests.get(f"{BASE_URL}/debug/executions/{self.exec_id}")
        assert response.status_code == 200
        debug_state = response.json()
        assert "is_paused" in debug_state
        assert "breakpoints" in debug_state
        assert "watches" in debug_state

    def test_add_breakpoint(self):
        """Test adding a breakpoint."""
        response = requests.post(
            f"{BASE_URL}/debug/executions/{self.exec_id}/breakpoints",
            json={"node_id": self.node_id},
        )
        assert response.status_code == 200
        debug_state = response.json()
        assert len(debug_state["breakpoints"]) > 0

    def test_add_watch(self):
        """Test adding a watch expression."""
        response = requests.post(
            f"{BASE_URL}/debug/executions/{self.exec_id}/watches",
            json={"key": "test_key", "condition": "change"},
        )
        assert response.status_code == 200
        debug_state = response.json()
        assert "test_key" in debug_state["watches"]

    def test_pause_resume(self):
        """Test pause and resume."""
        # Pause
        response = requests.post(f"{BASE_URL}/debug/executions/{self.exec_id}/pause")
        assert response.status_code == 200
        debug_state = response.json()
        assert debug_state["is_paused"] is True

        # Resume
        response = requests.post(f"{BASE_URL}/debug/executions/{self.exec_id}/continue")
        assert response.status_code == 200
        debug_state = response.json()
        assert debug_state["is_paused"] is False


class TestVisualization:
    """Test visualization endpoints."""

    def setup_method(self):
        """Create execution for testing."""
        with open(EXAMPLE_TREE_PATH) as f:
            tree_def = json.load(f)

        tree_def["metadata"]["name"] = f"Viz Test Tree {uuid4()}"
        tree_def["tree_id"] = str(uuid4())

        response = requests.post(f"{BASE_URL}/trees/", json=tree_def)
        self.tree_id = response.json()["tree_id"]

        config = {"tree_id": self.tree_id}
        response = requests.post(f"{BASE_URL}/executions/", json=config)
        self.exec_id = response.json()["execution_id"]

        # Tick once to have some data
        requests.post(
            f"{BASE_URL}/executions/{self.exec_id}/tick",
            json={"count": 1},
        )

    def test_get_dot_graph(self):
        """Test getting DOT graph."""
        response = requests.get(
            f"{BASE_URL}/visualizations/executions/{self.exec_id}/dot"
        )
        assert response.status_code == 200
        dot_graph = response.json()
        assert "source" in dot_graph
        assert "digraph BehaviorTree" in dot_graph["source"]

    def test_get_pytrees_js(self):
        """Test getting py_trees_js format."""
        response = requests.get(
            f"{BASE_URL}/visualizations/executions/{self.exec_id}/pytrees_js"
        )
        assert response.status_code == 200
        viz = response.json()
        assert "behaviours" in viz
        assert "visited_path" in viz
        assert "timestamp" in viz

    def test_get_statistics(self):
        """Test getting execution statistics."""
        response = requests.get(
            f"{BASE_URL}/visualizations/executions/{self.exec_id}/statistics"
        )
        assert response.status_code == 200
        stats = response.json()
        assert "total_ticks" in stats
        assert "node_stats" in stats
        assert stats["total_ticks"] >= 1


class TestValidation:
    """Test validation endpoints."""

    def test_validate_valid_tree(self):
        """Test validating a valid tree."""
        with open(EXAMPLE_TREE_PATH) as f:
            tree_def = json.load(f)

        response = requests.post(f"{BASE_URL}/validation/trees", json=tree_def)
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True
        assert result["error_count"] == 0

    def test_validate_invalid_tree(self):
        """Test validating an invalid tree."""
        invalid_tree = {
            "$schema": "1.0.0",
            "metadata": {"name": "Invalid", "version": "1.0.0"},
            "root": {
                "node_type": "UnknownBehavior",
                "name": "Bad Node",
                "config": {},
            },
        }

        response = requests.post(f"{BASE_URL}/validation/trees", json=invalid_tree)
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is False
        assert result["error_count"] > 0

    def test_validate_behavior(self):
        """Test behavior validation."""
        response = requests.post(
            f"{BASE_URL}/validation/behaviors",
            params={"behavior_type": "Log"},
            json={"message": "Test message"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True


class TestTemplates:
    """Test template system."""

    def test_list_templates(self):
        """Test listing templates."""
        response = requests.get(f"{BASE_URL}/validation/templates")
        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)

    def test_create_and_instantiate_template(self):
        """Test creating and instantiating a template."""
        template = {
            "template_id": f"test_template_{uuid4().hex[:8]}",
            "name": "Test Template",
            "description": "Simple test template",
            "category": "test",
            "tags": ["test"],
            "parameters": [
                {
                    "name": "message",
                    "type": "string",
                    "description": "Log message",
                    "required": True,
                    "default": "Hello",
                }
            ],
            "example_params": {"message": "Test"},
            "tree_structure": {
                "root": {
                    "node_type": "Log",
                    "name": "Test Log",
                    "config": {"message": "{{message}}"},
                }
            },
        }

        # Create template
        response = requests.post(f"{BASE_URL}/validation/templates", json=template)
        assert response.status_code == 201

        # Instantiate
        inst_request = {
            "template_id": template["template_id"],
            "parameters": {"message": "Hello from template!"},
            "tree_name": "Instance from Template",
        }

        response = requests.post(
            f"{BASE_URL}/validation/templates/{template['template_id']}/instantiate",
            json=inst_request,
        )
        assert response.status_code == 200
        tree_def = response.json()
        assert tree_def["metadata"]["name"] == "Instance from Template"
        assert tree_def["root"]["config"]["message"] == "Hello from template!"


class TestHistory:
    """Test execution history."""

    def setup_method(self):
        """Create execution for testing."""
        with open(EXAMPLE_TREE_PATH) as f:
            tree_def = json.load(f)

        tree_def["metadata"]["name"] = f"History Test Tree {uuid4()}"
        tree_def["tree_id"] = str(uuid4())

        response = requests.post(f"{BASE_URL}/trees/", json=tree_def)
        self.tree_id = response.json()["tree_id"]

        config = {"tree_id": self.tree_id}
        response = requests.post(f"{BASE_URL}/executions/", json=config)
        self.exec_id = response.json()["execution_id"]

    def test_get_history(self):
        """Test getting execution history."""
        # Tick multiple times
        for _ in range(3):
            requests.post(
                f"{BASE_URL}/executions/{self.exec_id}/tick",
                json={"count": 1},
            )
            time.sleep(0.1)

        # Get history
        response = requests.get(f"{BASE_URL}/history/executions/{self.exec_id}")
        assert response.status_code == 200
        history = response.json()
        assert isinstance(history, list)
        assert len(history) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
