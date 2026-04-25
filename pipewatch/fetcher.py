"""Fetchers for retrieving pipeline health metrics from configured sources."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from pipewatch.config import SourceConfig

logger = logging.getLogger(__name__)


@dataclass
class MetricResult:
    """Holds a fetched metric value along with metadata."""

    source_name: str
    metric_name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: dict[str, str] = field(default_factory=dict)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def fetch_source(source: SourceConfig, timeout: float = 10.0) -> list[MetricResult]:
    """Fetch metrics from a single source config.

    Args:
        source: The source configuration to fetch from.
        timeout: HTTP request timeout in seconds.

    Returns:
        A list of MetricResult objects parsed from the response.
    """
    results: list[MetricResult] = []
    try:
        response = httpx.get(
            source.url,
            headers=source.headers or {},
            timeout=timeout,
        )
        response.raise_for_status()
        payload: Any = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("HTTP error fetching %s: %s", source.name, exc)
        return [
            MetricResult(
                source_name=source.name,
                metric_name="fetch_error",
                value=0.0,
                error=str(exc),
            )
        ]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch %s: %s", source.name, exc)
        return [
            MetricResult(
                source_name=source.name,
                metric_name="fetch_error",
                value=0.0,
                error=str(exc),
            )
        ]

    metrics: dict[str, Any] = payload if isinstance(payload, dict) else {}
    for metric_name, raw_value in metrics.items():
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        results.append(
            MetricResult(
                source_name=source.name,
                metric_name=metric_name,
                value=value,
            )
        )

    logger.debug("Fetched %d metric(s) from %s", len(results), source.name)
    return results


def fetch_all(sources: list[SourceConfig], timeout: float = 10.0) -> list[MetricResult]:
    """Fetch metrics from all sources sequentially."""
    all_results: list[MetricResult] = []
    for source in sources:
        all_results.extend(fetch_source(source, timeout=timeout))
    return all_results
