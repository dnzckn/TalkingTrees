"""API client for CLI commands."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import ConnectionError, RequestException

from py_forest.cli.config import get_config


class APIClient:
    """Client for interacting with PyForest API."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        """Initialize API client."""
        config = get_config()
        self.base_url = base_url or config.api_url
        self.timeout = timeout or config.timeout

    def _request(
        self, method: str, endpoint: str, **kwargs
    ) -> requests.Response:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method, url, timeout=self.timeout, **kwargs
            )
            response.raise_for_status()
            return response
        except ConnectionError:
            raise Exception(
                f"Could not connect to API at {self.base_url}. "
                "Is the server running?"
            )
        except RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    raise Exception(f"API Error: {error_data.get('detail', str(e))}")
                except json.JSONDecodeError:
                    raise Exception(f"API Error: {e.response.text}")
            raise Exception(f"Request failed: {str(e)}")

    # Tree operations
    def list_trees(self) -> List[Dict[str, Any]]:
        """List all trees in the library."""
        response = self._request("GET", "/trees/")
        return response.json()

    def get_tree(self, tree_id: str) -> Dict[str, Any]:
        """Get a specific tree."""
        response = self._request("GET", f"/trees/{tree_id}")
        return response.json()

    def create_tree(self, tree_def: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tree."""
        response = self._request("POST", "/trees/", json=tree_def)
        return response.json()

    def delete_tree(self, tree_id: str) -> None:
        """Delete a tree."""
        self._request("DELETE", f"/trees/{tree_id}")

    def search_trees(
        self, name: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for trees."""
        params = {}
        if name:
            params["name"] = name
        if tags:
            params["tags"] = ",".join(tags)

        response = self._request("GET", "/trees/search", params=params)
        return response.json()

    # Validation operations
    def validate_tree(self, tree_def: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a tree definition."""
        response = self._request("POST", "/validation/trees", json=tree_def)
        return response.json()

    def validate_tree_file(self, tree_id: str) -> Dict[str, Any]:
        """Validate a tree from the library."""
        response = self._request("POST", f"/validation/trees/{tree_id}")
        return response.json()

    # Template operations
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all templates."""
        response = self._request("GET", "/validation/templates")
        return response.json()

    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get a specific template."""
        response = self._request("GET", f"/validation/templates/{template_id}")
        return response.json()

    def create_template(self, template_def: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new template."""
        response = self._request("POST", "/validation/templates", json=template_def)
        return response.json()

    def instantiate_template(
        self, template_id: str, params: Dict[str, Any], tree_name: str
    ) -> Dict[str, Any]:
        """Instantiate a template with parameters."""
        request_data = {
            "template_id": template_id,
            "parameters": params,
            "tree_name": tree_name,
        }
        response = self._request(
            "POST",
            f"/validation/templates/{template_id}/instantiate",
            json=request_data,
        )
        return response.json()

    # Execution operations
    def list_executions(self) -> List[Dict[str, Any]]:
        """List all executions."""
        response = self._request("GET", "/executions/")
        return response.json()

    def create_execution(
        self, tree_id: str, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new execution."""
        exec_config = {"tree_id": tree_id}
        if config:
            exec_config.update(config)

        response = self._request("POST", "/executions/", json=exec_config)
        return response.json()

    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get execution details."""
        response = self._request("GET", f"/executions/{execution_id}")
        return response.json()

    def tick_execution(
        self, execution_id: str, count: int = 1, capture_snapshot: bool = False
    ) -> Dict[str, Any]:
        """Tick an execution."""
        response = self._request(
            "POST",
            f"/executions/{execution_id}/tick",
            json={"count": count, "capture_snapshot": capture_snapshot},
        )
        return response.json()

    def get_snapshot(self, execution_id: str) -> Dict[str, Any]:
        """Get execution snapshot."""
        response = self._request("GET", f"/executions/{execution_id}/snapshot")
        return response.json()

    def delete_execution(self, execution_id: str) -> None:
        """Delete an execution."""
        self._request("DELETE", f"/executions/{execution_id}")

    # Scheduler operations
    def start_auto(self, execution_id: str) -> Dict[str, Any]:
        """Start AUTO mode execution."""
        response = self._request("POST", f"/executions/{execution_id}/scheduler/auto")
        return response.json()

    def start_interval(
        self, execution_id: str, interval_ms: int
    ) -> Dict[str, Any]:
        """Start INTERVAL mode execution."""
        response = self._request(
            "POST",
            f"/executions/{execution_id}/scheduler/interval",
            json={"interval_ms": interval_ms},
        )
        return response.json()

    def stop_scheduler(self, execution_id: str) -> Dict[str, Any]:
        """Stop scheduled execution."""
        response = self._request("POST", f"/executions/{execution_id}/scheduler/stop")
        return response.json()

    # Visualization
    def get_statistics(self, execution_id: str) -> Dict[str, Any]:
        """Get execution statistics."""
        response = self._request(
            "GET", f"/visualizations/executions/{execution_id}/statistics"
        )
        return response.json()

    def get_dot_graph(self, execution_id: str) -> str:
        """Get DOT graph representation."""
        response = self._request(
            "GET", f"/visualizations/executions/{execution_id}/dot"
        )
        return response.json()["source"]


def get_client(base_url: Optional[str] = None) -> APIClient:
    """Get an API client instance."""
    return APIClient(base_url=base_url)
