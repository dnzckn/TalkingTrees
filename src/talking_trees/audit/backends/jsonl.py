"""JSONL append-only audit backend."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JSONLAuditBackend:
    """Append-only JSONL file audit backend with log rotation.

    Args:
        filepath: Path to the JSONL log file
        max_size_bytes: Max file size before rotation (0 = no rotation)
    """

    def __init__(self, filepath: str | Path, max_size_bytes: int = 0):
        self.filepath = Path(filepath)
        self.max_size_bytes = max_size_bytes
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def write(self, entry: dict[str, Any]) -> None:
        """Append an audit entry to the log."""
        if self.max_size_bytes > 0:
            self._rotate_if_needed()

        with open(self.filepath, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        """Read all entries from the log."""
        if not self.filepath.exists():
            return []

        entries = []
        with open(self.filepath) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Skipping corrupt audit entry")
        return entries

    def _rotate_if_needed(self) -> None:
        if not self.filepath.exists():
            return
        size = os.path.getsize(self.filepath)
        if size >= self.max_size_bytes:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            rotated = self.filepath.with_suffix(f".{ts}.jsonl")
            self.filepath.rename(rotated)
            logger.info("Rotated audit log to %s", rotated)
