"""Configuration loading and validation for pipewatch."""

import os
from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class SourceConfig:
    name: str
    type: str
    connection_string: str
    interval_seconds: int = 60
    tags: List[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    channel: str
    threshold_failures: int = 3
    cooldown_seconds: int = 300
    webhook_url: Optional[str] = None


@dataclass
class PipewatchConfig:
    sources: List[SourceConfig]
    alert: AlertConfig
    log_level: str = "INFO"
    metrics_retention_days: int = 7


def load_config(path: str) -> PipewatchConfig:
    """Load and parse configuration from a YAML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if not raw:
        raise ValueError("Config file is empty or invalid YAML.")

    sources = [
        SourceConfig(
            name=s["name"],
            type=s["type"],
            connection_string=s["connection_string"],
            interval_seconds=s.get("interval_seconds", 60),
            tags=s.get("tags", []),
        )
        for s in raw.get("sources", [])
    ]

    if not sources:
        raise ValueError("At least one source must be defined in config.")

    alert_raw = raw.get("alert", {})
    alert = AlertConfig(
        channel=alert_raw.get("channel", "log"),
        threshold_failures=alert_raw.get("threshold_failures", 3),
        cooldown_seconds=alert_raw.get("cooldown_seconds", 300),
        webhook_url=alert_raw.get("webhook_url"),
    )

    return PipewatchConfig(
        sources=sources,
        alert=alert,
        log_level=raw.get("log_level", "INFO"),
        metrics_retention_days=raw.get("metrics_retention_days", 7),
    )
