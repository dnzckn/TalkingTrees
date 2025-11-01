"""CLI configuration management."""

import json
from pathlib import Path

from pydantic import BaseModel


class CLIConfig(BaseModel):
    """CLI configuration."""

    api_url: str = "http://localhost:8000"
    timeout: int = 30
    config_path: Path | None = None


def get_config_path() -> Path:
    """Get the path to the config file."""
    config_dir = Path.home() / ".talkingtrees"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def load_config() -> CLIConfig:
    """Load configuration from file."""
    config_path = get_config_path()

    if not config_path.exists():
        config = CLIConfig()
        config.config_path = config_path
        return config

    try:
        with open(config_path) as f:
            data = json.load(f)
        config = CLIConfig(**data)
        config.config_path = config_path
        return config
    except Exception:
        # Return default config on error
        config = CLIConfig()
        config.config_path = config_path
        return config


def save_config(config: CLIConfig) -> None:
    """Save configuration to file."""
    config_path = get_config_path()

    data = config.model_dump(exclude={"config_path"})

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)


def get_config() -> CLIConfig:
    """Get current configuration."""
    return load_config()
