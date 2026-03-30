"""In-memory resource backend using threading locks."""

import threading
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class ResourceState:
    """State of a single resource."""
    capacity: int = 1
    holders: list[str] = field(default_factory=list)
    wait_queue: OrderedDict = field(default_factory=OrderedDict)
    lock: threading.Lock = field(default_factory=threading.Lock)


class InMemoryResourceBackend:
    """In-memory resource backend with threading locks and semaphore support."""

    def __init__(self):
        self._resources: dict[str, ResourceState] = {}

    def register(self, resource_id: str, capacity: int = 1) -> None:
        self._resources[resource_id] = ResourceState(capacity=capacity)

    def acquire(self, resource_id: str, requester_id: str, timeout_ms: int = 0) -> bool:
        state = self._resources.get(resource_id)
        if state is None:
            raise ValueError(f"Resource not registered: {resource_id}")

        with state.lock:
            if len(state.holders) < state.capacity:
                state.holders.append(requester_id)
                return True
            return False

    def release(self, resource_id: str, requester_id: str) -> bool:
        state = self._resources.get(resource_id)
        if state is None:
            return False

        with state.lock:
            if requester_id in state.holders:
                state.holders.remove(requester_id)
                return True
            return False

    def status(self, resource_id: str) -> dict:
        state = self._resources.get(resource_id)
        if state is None:
            raise ValueError(f"Resource not registered: {resource_id}")

        return {
            "resource_id": resource_id,
            "capacity": state.capacity,
            "available": state.capacity - len(state.holders),
            "holders": list(state.holders),
        }

    def release_all(self, requester_id: str) -> int:
        count = 0
        for state in self._resources.values():
            with state.lock:
                while requester_id in state.holders:
                    state.holders.remove(requester_id)
                    count += 1
        return count

    def list_resources(self) -> list[str]:
        return list(self._resources.keys())
