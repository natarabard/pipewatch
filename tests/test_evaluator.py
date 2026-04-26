"""Tests for pipewatch.evaluator."""

from __future__ import annotations

import pytest

from pipewatch.config import AlertConfig, PipewatchConfig, SourceConfig
from pipewatch.evaluator import AlertEvent, evaluate_all, evaluate_result
from pipewatch.fetcher import MetricResult


def _make_config(
    source_name: str = "svc",
    metric: str = "latency_ms",
    operator: str = ">",
    threshold: float = 200.0,
) -> PipewatchConfig:
    source = SourceConfig(name=source_name, url="http://example.com/metrics")
    alert = AlertConfig(
        name="high_latency",
        source=source_name,
        metric=metric,
        operator=operator,
        threshold=threshold,
    )
    return PipewatchConfig(sources=[source], alerts=[alert])


def test_triggered_alert_when_threshold_exceeded():
    config = _make_config(operator=">", threshold=200.0)
    result = MetricResult(source_name="svc", metrics={"latency_ms": 350.0})
    events = evaluate_result(result, config)
    assert len(events) == 1
    assert events[0].triggered is True


def test_not_triggered_when_below_threshold():
    config = _make_config(operator=">", threshold=200.0)
    result = MetricResult(source_name="svc", metrics={"latency_ms": 100.0})
    events = evaluate_result(result, config)
    assert len(events) == 1
    assert events[0].triggered is False


def test_skips_result_with_error():
    config = _make_config()
    result = MetricResult(
        source_name="svc", metrics={}, error="connection refused"
    )
    events = evaluate_result(result, config)
    assert events == []


def test_skips_unknown_source():
    config = _make_config(source_name="svc")
    result = MetricResult(source_name="other", metrics={"latency_ms": 999.0})
    events = evaluate_result(result, config)
    assert events == []


def test_skips_missing_metric():
    config = _make_config(metric="latency_ms")
    result = MetricResult(source_name="svc", metrics={"error_rate": 0.5})
    events = evaluate_result(result, config)
    assert events == []


def test_alert_message_format():
    config = _make_config(operator=">", threshold=200.0)
    result = MetricResult(source_name="svc", metrics={"latency_ms": 350.0})
    event = evaluate_result(result, config)[0]
    assert "TRIGGERED" in event.message
    assert "svc/latency_ms" in event.message
    assert "350.0" in event.message


def test_evaluate_all_aggregates_multiple_results():
    config = _make_config(operator=">=", threshold=100.0)
    results = [
        MetricResult(source_name="svc", metrics={"latency_ms": 50.0}),
        MetricResult(source_name="svc", metrics={"latency_ms": 150.0}),
    ]
    events = evaluate_all(results, config)
    assert len(events) == 2
    triggered = [e.triggered for e in events]
    assert triggered == [False, True]


@pytest.mark.parametrize(
    "operator,value,expected",
    [
        ("<", 50.0, True),
        ("<=", 100.0, True),
        ("==", 100.0, True),
        ("!=", 99.0, True),
        (">", 100.0, False),
    ],
)
def test_all_operators(operator, value, expected):
    config = _make_config(operator=operator, threshold=100.0)
    result = MetricResult(source_name="svc", metrics={"latency_ms": value})
    events = evaluate_result(result, config)
    assert events[0].triggered is expected
