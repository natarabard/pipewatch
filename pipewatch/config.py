"""Configuration loading and validation for pipewatch."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class SourceConfig(BaseModel):
    """Configuration for a single metrics source endpoint."""

    name: str
    url: str
    headers: dict[str, str] | None = None
    interval_seconds: int = 60

    @field_validator("url")
    @classmethod
    def url_must_have_scheme(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return v


class AlertConfig(BaseModel):
    """Configuration for a single alert rule."""

    name: str
    source: str
    metric: str
    operator: str  # gt | lt | gte | lte | eq
    threshold: float
    message: str | None = None

    @field_validator("operator")
    @classmethod
    def operator_must_be_valid(cls, v: str) -> str:
        allowed = {"gt", "lt", "gte", "lte", "eq"}
        if v not in allowed:
            raise ValueError(f"operator must be one of {allowed}")
        return v


class PipewatchConfig(BaseModel):
    """Root configuration model for pipewatch."""

    sources: list[SourceConfig] = Field(default_factory=list)
    alerts: list[AlertConfig] = Field(default_factory=list)
    log_level: str = "INFO"
    default_interval_seconds: int = 60


def load_config(path: str | Path) -> PipewatchConfig:
    """Load and validate a pipewatch YAML config file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A validated PipewatchConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the file is empty or cannot be parsed.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw_text = config_path.read_text(encoding="utf-8")
    data: Any = yaml.safe_load(raw_text)

    if data is None:
        raise ValueError(f"Config file is empty: {config_path}")

    return PipewatchConfig.model_validate(data)
