"""Remote subtree behaviour for distributed execution.

Proxies tree execution to a remote TalkingTrees API endpoint,
enabling distributed behavior trees across networked devices.
"""

import logging
import time
from typing import Any

import py_trees
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RetryPolicy(BaseModel):
    """Retry policy for remote subtree requests."""
    max_retries: int = Field(default=0, description="Max retry attempts")
    backoff_ms: int = Field(default=100, description="Initial backoff in ms")
    backoff_multiplier: float = Field(default=2.0, description="Backoff multiplier")


class RemoteSubtreeBehaviour(py_trees.behaviour.Behaviour):
    """Behaviour that proxies ticks to a remote TalkingTrees endpoint.

    On each tick, sends a POST request to the remote endpoint with
    blackboard data, and maps the response status back to py_trees.

    Args:
        name: Behaviour name
        endpoint: Remote API base URL (e.g., "http://remote-host:8000")
        remote_execution_id: Execution ID on the remote instance
        timeout_ms: Request timeout in milliseconds
        blackboard_send: Keys to send to remote (None = send all)
        blackboard_receive: Keys to accept from remote (None = accept all)
        auth_token: Optional bearer token for authentication
        fallback_status: Status to return on connection failure
        retry_policy: Optional retry policy for failed requests
    """

    def __init__(
        self,
        name: str,
        endpoint: str,
        remote_execution_id: str | None = None,
        timeout_ms: int = 5000,
        blackboard_send: list[str] | None = None,
        blackboard_receive: list[str] | None = None,
        auth_token: str | None = None,
        fallback_status: py_trees.common.Status = py_trees.common.Status.FAILURE,
        retry_policy: RetryPolicy | None = None,
    ):
        super().__init__(name=name)
        self.endpoint = endpoint.rstrip("/")
        self.remote_execution_id = remote_execution_id
        self.timeout_s = timeout_ms / 1000.0
        self.blackboard_send = blackboard_send
        self.blackboard_receive = blackboard_receive
        self.auth_token = auth_token
        self.fallback_status = fallback_status
        self.retry_policy = retry_policy

        self._session = requests.Session()
        if auth_token:
            self._session.headers["Authorization"] = f"Bearer {auth_token}"

        # Track remote state
        self.last_remote_status: str | None = None
        self.last_error: str | None = None

    def update(self) -> py_trees.common.Status:
        """Tick the remote subtree via HTTP."""
        max_attempts = 1
        backoff_s = 0.1
        backoff_multiplier = 2.0

        if self.retry_policy:
            max_attempts = 1 + self.retry_policy.max_retries
            backoff_s = self.retry_policy.backoff_ms / 1000.0
            backoff_multiplier = self.retry_policy.backoff_multiplier

        last_exception: Exception | None = None

        for attempt in range(max_attempts):
            try:
                # Collect blackboard data to send
                bb_updates = self._get_blackboard_slice()

                # Build request
                url = f"{self.endpoint}/executions/{self.remote_execution_id}/tick"
                payload = {
                    "count": 1,
                    "blackboard_updates": bb_updates,
                }

                response = self._session.post(
                    url,
                    json=payload,
                    timeout=self.timeout_s,
                )
                response.raise_for_status()

                data = response.json()
                remote_status = data.get("root_status", "FAILURE")
                self.last_remote_status = remote_status
                self.last_error = None

                # Map remote blackboard updates back to local
                if "snapshot" in data and data["snapshot"]:
                    remote_bb = data["snapshot"].get("blackboard", {})
                    self._apply_remote_blackboard(remote_bb)

                # Map status
                status_map = {
                    "SUCCESS": py_trees.common.Status.SUCCESS,
                    "FAILURE": py_trees.common.Status.FAILURE,
                    "RUNNING": py_trees.common.Status.RUNNING,
                }
                return status_map.get(remote_status, py_trees.common.Status.FAILURE)

            except requests.Timeout as e:
                last_exception = e
                self.last_error = f"Timeout after {self.timeout_s}s"
                logger.warning(
                    "Remote subtree timeout: %s (attempt %d/%d)",
                    self.name, attempt + 1, max_attempts,
                )
            except requests.ConnectionError as e:
                last_exception = e
                self.last_error = f"Connection error: {e}"
                logger.warning(
                    "Remote subtree connection error: %s - %s (attempt %d/%d)",
                    self.name, e, attempt + 1, max_attempts,
                )
            except Exception as e:
                last_exception = e
                self.last_error = f"Error: {e}"
                logger.error(
                    "Remote subtree error: %s - %s (attempt %d/%d)",
                    self.name, e, attempt + 1, max_attempts,
                )

            # If we have more attempts, wait with exponential backoff
            if attempt < max_attempts - 1:
                sleep_time = backoff_s * (backoff_multiplier ** attempt)
                logger.debug(
                    "Retrying remote subtree %s in %.1fms",
                    self.name, sleep_time * 1000,
                )
                time.sleep(sleep_time)

        # All attempts exhausted
        logger.warning(
            "Remote subtree %s: all %d attempts failed", self.name, max_attempts
        )
        return self.fallback_status

    def _get_blackboard_slice(self) -> dict[str, Any]:
        """Get blackboard data to send to remote."""
        bb = py_trees.blackboard.Blackboard()
        result = {}

        keys = self.blackboard_send or list(bb.keys())
        for key in keys:
            try:
                result[key] = bb.get(key)
            except KeyError:
                pass

        return result

    def _apply_remote_blackboard(self, remote_bb: dict[str, Any]) -> None:
        """Merge remote blackboard updates into local blackboard."""
        if not remote_bb:
            return

        # Filter by blackboard_receive if set
        if self.blackboard_receive is not None:
            remote_bb = {
                k: v for k, v in remote_bb.items()
                if k in self.blackboard_receive
            }

        from talking_trees.core.utils import update_blackboard

        update_blackboard(remote_bb, client_name=f"Remote:{self.name}")

    def terminate(self, new_status: py_trees.common.Status) -> None:
        """Cleanup on termination."""
        pass
