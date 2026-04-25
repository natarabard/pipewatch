"""Tests for pipewatch configuration loading."""

import os
import tempfile

import pytest
import yaml

from pipewatch.config import load_config, PipewatchConfig, SourceConfig, AlertConfig


MINIMAL_CONFIG = {
    "sources": [
        {
            "name": "test_source",
            "type": "postgres",
            "connection_string": "postgresql://localhost/test",
        }
    ],
    "alert": {"channel": "log"},
}


def write_temp_config(data: dict) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    yaml.dump(data, f)
    f.close()
    return f.name


def test_load_minimal_config():
    path = write_temp_config(MINIMAL_CONFIG)
    try:
        config = load_config(path)
        assert isinstance(config, PipewatchConfig)
        assert len(config.sources) == 1
        assert config.sources[0].name == "test_source"
        assert config.alert.channel == "log"
        assert config.log_level == "INFO"
    finally:
        os.unlink(path)


def test_load_full_config():
    data = {
        **MINIMAL_CONFIG,
        "log_level": "DEBUG",
        "metrics_retention_days": 14,
        "alert": {
            "channel": "webhook",
            "threshold_failures": 5,
            "cooldown_seconds": 600,
            "webhook_url": "https://example.com/hook",
        },
    }
    path = write_temp_config(data)
    try:
        config = load_config(path)
        assert config.log_level == "DEBUG"
        assert config.metrics_retention_days == 14
        assert config.alert.threshold_failures == 5
        assert config.alert.webhook_url == "https://example.com/hook"
    finally:
        os.unlink(path)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.yaml")


def test_empty_file_raises():
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    f.close()
    try:
        with pytest.raises(ValueError, match="empty or invalid"):
            load_config(f.name)
    finally:
        os.unlink(f.name)


def test_no_sources_raises():
    path = write_temp_config({"sources": [], "alert": {"channel": "log"}})
    try:
        with pytest.raises(ValueError, match="At least one source"):
            load_config(path)
    finally:
        os.unlink(path)


def test_source_defaults():
    path = write_temp_config(MINIMAL_CONFIG)
    try:
        config = load_config(path)
        src = config.sources[0]
        assert src.interval_seconds == 60
        assert src.tags == []
    finally:
        os.unlink(path)
