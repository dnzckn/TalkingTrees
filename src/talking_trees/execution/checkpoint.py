"""State persistence and recovery via checkpoints."""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExecutionState(BaseModel):
    """Serializable execution state for checkpoint/restore."""

    tree_id: str
    execution_id: str
    tick_number: int
    blackboard_snapshot: dict[str, Any] = Field(default_factory=dict)
    node_statuses: dict[str, str] = Field(default_factory=dict)
    disabled_subtrees: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CheckpointMeta(BaseModel):
    """Metadata about a checkpoint."""

    checkpoint_id: str
    execution_id: str
    tick_number: int
    timestamp: datetime


class CheckpointBackend(ABC):
    """Abstract backend for checkpoint storage."""

    @abstractmethod
    def save(self, checkpoint_id: str, state: ExecutionState) -> None: ...

    @abstractmethod
    def load(self, checkpoint_id: str) -> ExecutionState: ...

    @abstractmethod
    def list(self, execution_id: str) -> list[CheckpointMeta]: ...

    @abstractmethod
    def delete(self, checkpoint_id: str) -> bool: ...


class FileCheckpointBackend(CheckpointBackend):
    """File-based checkpoint storage using JSON files."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint_id: str, state: ExecutionState) -> None:
        path = self.directory / f"{checkpoint_id}.json"
        with open(path, "w") as f:
            json.dump(state.model_dump(mode="json"), f, indent=2, default=str)

    def load(self, checkpoint_id: str) -> ExecutionState:
        path = self.directory / f"{checkpoint_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")
        with open(path) as f:
            data = json.load(f)
        return ExecutionState.model_validate(data)

    def list(self, execution_id: str) -> list[CheckpointMeta]:
        results = []
        for path in sorted(self.directory.glob("*.json")):
            try:
                with open(path) as f:
                    data = json.load(f)
                if data.get("execution_id") == execution_id:
                    results.append(CheckpointMeta(
                        checkpoint_id=path.stem,
                        execution_id=data["execution_id"],
                        tick_number=data.get("tick_number", 0),
                        timestamp=data.get("timestamp", datetime.now(timezone.utc)),
                    ))
            except (json.JSONDecodeError, KeyError):
                continue
        return results

    def delete(self, checkpoint_id: str) -> bool:
        path = self.directory / f"{checkpoint_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False


class CheckpointManager:
    """Manages automatic and manual checkpointing of execution state.

    Args:
        backend: Storage backend
        interval_ticks: Auto-checkpoint every N ticks (0 = manual only)
    """

    def __init__(self, backend: CheckpointBackend, interval_ticks: int = 10):
        self.backend = backend
        self.interval_ticks = interval_ticks
        self._tick_counter = 0

    def on_tick(self, execution_id: str, state: ExecutionState) -> str | None:
        """Called after each tick. Auto-saves if interval reached."""
        self._tick_counter += 1
        if self.interval_ticks > 0 and self._tick_counter >= self.interval_ticks:
            self._tick_counter = 0
            return self.save(execution_id, state)
        return None

    def save(self, execution_id: str, state: ExecutionState) -> str:
        """Manually save a checkpoint."""
        checkpoint_id = f"{execution_id}_tick{state.tick_number}"
        self.backend.save(checkpoint_id, state)
        logger.info("Checkpoint saved: %s", checkpoint_id)
        return checkpoint_id

    def load(self, checkpoint_id: str) -> ExecutionState:
        """Load a checkpoint."""
        return self.backend.load(checkpoint_id)

    def list_checkpoints(self, execution_id: str) -> list[CheckpointMeta]:
        """List all checkpoints for an execution."""
        return self.backend.list(execution_id)

    def prune(self, execution_id: str, keep_last: int = 5) -> int:
        """Remove old checkpoints, keeping only the last N."""
        checkpoints = self.backend.list(execution_id)
        if len(checkpoints) <= keep_last:
            return 0

        to_delete = sorted(checkpoints, key=lambda c: c.tick_number)[:-keep_last]
        count = 0
        for cp in to_delete:
            if self.backend.delete(cp.checkpoint_id):
                count += 1
        return count
