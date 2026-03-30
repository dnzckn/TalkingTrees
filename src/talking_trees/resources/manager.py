"""Resource manager for shared resource arbitration."""

import logging
from typing import Any

from talking_trees.resources.backends.memory import InMemoryResourceBackend

logger = logging.getLogger(__name__)


class ResourceManager:
    """Manages shared resources with acquire/release semantics.

    Supports capacity-based resources (semaphore mode) and
    auto-release on execution end.

    Args:
        backend: Resource storage backend
    """

    def __init__(self, backend: InMemoryResourceBackend | None = None):
        self.backend = backend or InMemoryResourceBackend()

    def register_resource(self, resource_id: str, capacity: int = 1) -> None:
        """Register a new shared resource."""
        self.backend.register(resource_id, capacity)
        logger.info("Registered resource '%s' with capacity %d", resource_id, capacity)

    def acquire(self, resource_id: str, requester_id: str, timeout_ms: int = 0) -> bool:
        """Acquire a resource. Returns True if acquired, False if unavailable."""
        return self.backend.acquire(resource_id, requester_id, timeout_ms)

    def release(self, resource_id: str, requester_id: str) -> bool:
        """Release a held resource."""
        return self.backend.release(resource_id, requester_id)

    def status(self, resource_id: str) -> dict[str, Any]:
        """Get resource status."""
        return self.backend.status(resource_id)

    def release_all(self, requester_id: str) -> int:
        """Release all resources held by a requester. Returns count released."""
        return self.backend.release_all(requester_id)

    def list_resources(self) -> list[str]:
        """List all registered resource IDs."""
        return self.backend.list_resources()
