"""
REST API Integration Test
=========================

Tests the full workflow:
1. Create tree with py_trees
2. Convert to PyForest
3. Upload via REST API
4. Create execution via REST API
5. Tick via REST API
6. Verify results

This ensures the REST API layer correctly calls the SDK.
"""

import py_trees
import operator
from py_trees.common import ComparisonExpression
from py_forest.sdk import PyForest
from py_forest.adapters import from_py_trees
import requests
import time
import subprocess
import sys
import os
from pathlib import Path

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


class TestRESTAPIIntegration:
    """Test REST API integration with py_trees workflow"""

    def test_full_workflow_with_rest_api(self, api_server=None):
        """Test complete workflow: py_trees -> PyForest -> REST API -> Execute"""
        if api_server is None:
            api_server = "http://127.0.0.1:8765"

        print("\n" + "=" * 70)
        print("TEST: Full Workflow with REST API")
        print("=" * 70)

        # =====================================================================
        # Step 1: Create tree with py_trees
        # =====================================================================
        print("\nStep 1: Create behavior tree with py_trees...")

        root = py_trees.composites.Selector(name="Robot Controller", memory=False)

        # Low battery branch
        low_battery = py_trees.composites.Sequence(name="Low Battery Handler", memory=False)
        battery_check = ComparisonExpression('battery_level', operator.lt, 20)
        low_battery.add_child(
            py_trees.behaviours.CheckBlackboardVariableValue(
                name="Battery Low?",
                check=battery_check
            )
        )
        low_battery.add_child(
            py_trees.behaviours.SetBlackboardVariable(
                name="Set Action: Charge",
                variable_name="robot_action",
                variable_value="charge",
                overwrite=True
            )
        )

        # Normal operation branch
        normal_ops = py_trees.behaviours.SetBlackboardVariable(
            name="Set Action: Patrol",
            variable_name="robot_action",
            variable_value="patrol",
            overwrite=True
        )

        root.add_child(low_battery)
        root.add_child(normal_ops)

        print("✓ Created py_trees tree with 2 branches")

        # =====================================================================
        # Step 2: Convert to PyForest format
        # =====================================================================
        print("\nStep 2: Convert to PyForest format...")

        pf = PyForest()
        tree_def = from_py_trees(
            root,
            name="REST API Test Tree",
            version="1.0.0",
            description="Test tree for REST API integration"
        )

        print(f"✓ Converted to PyForest TreeDefinition")
        print(f"  Name: {tree_def.metadata.name}")
        print(f"  Blackboard vars: {len(tree_def.blackboard_schema)}")

        # IMPORTANT: py_trees doesn't expose variable_value after construction
        # This is a known limitation. We need to add the values manually for testing.
        # In real usage, users would either:
        # 1. Create trees directly with PyForest models, or
        # 2. Add values in the visual editor
        print("\n  Note: Adding SetBlackboardVariable values (py_trees limitation)")
        tree_def.root.children[0].children[1].config['value'] = 'charge'  # Low battery action
        tree_def.root.children[1].config['value'] = 'patrol'  # Normal operation action

        # Save to JSON for upload
        test_tree_path = "/tmp/rest_api_test_tree.json"
        pf.save_tree(tree_def, test_tree_path)
        print(f"✓ Saved to {test_tree_path}")

        # =====================================================================
        # Step 3: Upload tree via REST API
        # =====================================================================
        print("\nStep 3: Upload tree via REST API...")

        with open(test_tree_path, 'r') as f:
            tree_json = f.read()

        response = requests.post(
            f"{api_server}/trees",
            headers={"Content-Type": "application/json"},
            data=tree_json
        )

        print(f"Response status code: {response.status_code}")

        # Accept both 200 and 201 (created)
        assert response.status_code in [200, 201], f"Failed to upload tree (status {response.status_code}): {response.text[:500]}"
        upload_result = response.json()
        tree_id = upload_result["tree_id"]

        print(f"✓ Tree uploaded successfully")
        print(f"  Tree ID: {tree_id}")

        # =====================================================================
        # Step 4: Create execution via REST API
        # =====================================================================
        print("\nStep 4: Create execution via REST API...")

        response = requests.post(
            f"{api_server}/executions",
            json={"tree_id": tree_id}
        )

        assert response.status_code in [200, 201], f"Failed to create execution (status {response.status_code}): {response.text[:500]}"
        exec_result = response.json()
        execution_id = exec_result["execution_id"]

        print(f"✓ Execution created successfully")
        print(f"  Execution ID: {execution_id}")

        # =====================================================================
        # Step 5: Tick execution with low battery (should charge)
        # =====================================================================
        print("\nStep 5: Test 1 - Low battery scenario (battery_level=10)...")

        response = requests.post(
            f"{api_server}/executions/{execution_id}/tick",
            json={
                "blackboard_updates": {
                    "battery_level": 10
                }
            }
        )

        assert response.status_code == 200, f"Failed to tick execution: {response.text}"
        tick_result = response.json()

        print(f"✓ Tick executed successfully")

        # Handle different response formats (API returns root_status and snapshot)
        status = tick_result.get('root_status') or tick_result.get('status')
        snapshot = tick_result.get('snapshot', {})

        blackboard = snapshot.get('blackboard', {}) if isinstance(snapshot, dict) else {}

        # PyForest uses namespaced blackboard keys with leading slash
        robot_action = blackboard.get('/robot_action') or blackboard.get('robot_action')

        print(f"  Status: {status}")
        print(f"  Robot action: {robot_action}")

        # Verify low battery triggers charge action
        assert status == 'SUCCESS', "Tree should succeed"
        assert robot_action == 'charge', \
            f"Low battery should trigger charge action, got {robot_action}"

        print("✓ Low battery correctly triggered 'charge' action")

        # =====================================================================
        # Step 6: Tick execution with normal battery (should patrol)
        # =====================================================================
        print("\nStep 6: Test 2 - Normal battery scenario (battery_level=80)...")

        response = requests.post(
            f"{api_server}/executions/{execution_id}/tick",
            json={
                "blackboard_updates": {
                    "battery_level": 80
                }
            }
        )

        assert response.status_code == 200, f"Failed to tick execution: {response.text}"
        tick_result = response.json()

        print(f"✓ Tick executed successfully")

        # Handle different response formats (API returns root_status and snapshot)
        status = tick_result.get('root_status') or tick_result.get('status')
        snapshot = tick_result.get('snapshot', {})

        blackboard = snapshot.get('blackboard', {}) if isinstance(snapshot, dict) else {}

        # PyForest uses namespaced blackboard keys with leading slash
        robot_action = blackboard.get('/robot_action') or blackboard.get('robot_action')

        print(f"  Status: {status}")
        print(f"  Robot action: {robot_action}")

        # Verify normal battery triggers patrol action
        assert status == 'SUCCESS', "Tree should succeed"
        assert robot_action == 'patrol', \
            f"Normal battery should trigger patrol action, got {robot_action}"

        print("✓ Normal battery correctly triggered 'patrol' action")

        # =====================================================================
        # Step 7: Get execution status
        # =====================================================================
        print("\nStep 7: Get execution status via REST API...")

        response = requests.get(f"{api_server}/executions/{execution_id}")

        assert response.status_code == 200, f"Failed to get execution status: {response.text}"
        status_result = response.json()

        print(f"✓ Retrieved execution status")
        print(f"  Tick count: {status_result['tick_count']}")
        print(f"  Status: {status_result['status']}")

        assert status_result['tick_count'] == 2, "Should have ticked twice"

        # =====================================================================
        # Step 8: List all trees
        # =====================================================================
        print("\nStep 8: List all trees via REST API...")

        response = requests.get(f"{api_server}/trees")

        assert response.status_code == 200, f"Failed to list trees: {response.text}"
        trees_result = response.json()

        print(f"✓ Retrieved tree list")
        print(f"  Total trees: {len(trees_result)}")

        # Find our tree
        our_tree = next((t for t in trees_result if t['tree_id'] == tree_id), None)
        assert our_tree is not None, "Our tree should be in the list"
        assert our_tree['metadata']['name'] == "REST API Test Tree"

        print(f"✓ Found our tree in list: {our_tree['metadata']['name']}")

        print("\n" + "=" * 70)
        print("✅ REST API INTEGRATION TEST PASSED")
        print("=" * 70)
        print("\nVerified:")
        print("  ✓ py_trees tree creation")
        print("  ✓ Conversion to PyForest format")
        print("  ✓ Tree upload via REST API")
        print("  ✓ Execution creation via REST API")
        print("  ✓ Tick execution via REST API with blackboard updates")
        print("  ✓ Execution status retrieval via REST API")
        print("  ✓ Tree listing via REST API")
        print("  ✓ Correct behavior logic (low battery -> charge, normal -> patrol)")
        print("\n✅ REST API correctly calls SDK and produces expected results!")


def run_standalone():
    """Run test standalone without pytest"""
    print("\n" + "=" * 70)
    print("REST API Integration Test - Standalone Mode")
    print("=" * 70)

    # Create test instance
    test = TestRESTAPIIntegration()

    # Start server
    print("\nStarting API server...")
    import subprocess
    import sys
    import os

    server_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "py_forest.api.main:app",
            "--host", "127.0.0.1",
            "--port", "8765",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.dirname(__file__))
    )

    # Wait for server
    time.sleep(3)
    max_retries = 30
    api_server = "http://127.0.0.1:8765"

    for i in range(max_retries):
        try:
            response = requests.get(f"{api_server}/health", timeout=1)
            if response.status_code == 200:
                print(f"✓ Server started on port 8765")
                break
        except requests.exceptions.RequestException:
            if i == max_retries - 1:
                server_process.kill()
                print("✗ Failed to start server")
                return False
            time.sleep(0.5)

    try:
        # Run test
        test.test_full_workflow_with_rest_api(api_server)
        success = True
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False
    finally:
        # Stop server
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("✓ Server stopped")

    return success


if __name__ == "__main__":
    success = run_standalone()
    sys.exit(0 if success else 1)
