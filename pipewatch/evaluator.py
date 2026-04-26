"""Evaluates fetched metrics against configured alert thresholds."""

from __future__ import annotations

import operator as op
from dataclasses import dataclass
from typing import List

from pipewatch.config import AlertConfig, PipewatchConfig
from pipewatch.fetcher import MetricResult

_OPS = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "==": op.eq,
    "!=": op.ne,
}


@dataclass
class AlertEvent:
    source_name: str
    metric: str
    value: float
    alert: AlertConfig
    triggered: bool

    @property
    def message(self) -> str:
        status = "TRIGGERED" if self.triggered else "OK"
        return (
            f"[{status}] {self.source_name}/{self.metric} = {self.value} "
            f"{self.alert.operator} {self.alert.threshold} "
            f"(alert: {self.alert.name})"
        )


def evaluate_result(result: MetricResult, config: PipewatchConfig) -> List[AlertEvent]:
    """Check a single MetricResult against all matching alerts in config."""
    events: List[AlertEvent] = []

    source_cfg = next(
        (s for s in config.sources if s.name == result.source_name), None
    )
    if source_cfg is None or result.error is not None:
        return events

    for alert in config.alerts:
        if alert.source != result.source_name:
            continue
        value = result.metrics.get(alert.metric)
        if value is None:
            continue
        compare = _OPS[alert.operator]
        triggered = compare(value, alert.threshold)
        events.append(
            AlertEvent(
                source_name=result.source_name,
                metric=alert.metric,
                value=value,
                alert=alert,
                triggered=triggered,
            )
        )

    return events


def evaluate_all(
    results: List[MetricResult], config: PipewatchConfig
) -> List[AlertEvent]:
    """Evaluate all metric results and return every AlertEvent produced."""
    events: List[AlertEvent] = []
    for result in results:
        events.extend(evaluate_result(result, config))
    return events
