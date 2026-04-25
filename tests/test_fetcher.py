"""Tests for pipewatch.fetcher module."""

from __future__ import annotations

import pytest
import httpx
import respx

from pipewatch.config import SourceConfig
from pipewatch.fetcher import MetricResult, fetch_source, fetch_all


SOURCE = SourceConfig(name="test-source", url="http://example.com/metrics")


@respx.mock
def test_fetch_source_returns_metrics():
    respx.get(SOURCE.url).mock(
        return_value=httpx.Response(200, json={"lag": 42, "throughput": 1000.5})
    )
    results = fetch_source(SOURCE)
    assert len(results) == 2
    names = {r.metric_name for r in results}
    assert names == {"lag", "throughput"}
    values = {r.metric_name: r.value for r in results}
    assert values["lag"] == 42.0
    assert values["throughput"] == 1000.5
    assert all(r.ok for r in results)
    assert all(r.source_name == "test-source" for r in results)


@respx.mock
def test_fetch_source_http_error_returns_error_result():
    respx.get(SOURCE.url).mock(return_value=httpx.Response(503))
    results = fetch_source(SOURCE)
    assert len(results) == 1
    assert results[0].metric_name == "fetch_error"
    assert not results[0].ok
    assert results[0].error is not None


@respx.mock
def test_fetch_source_network_failure_returns_error_result():
    respx.get(SOURCE.url).mock(side_effect=httpx.ConnectError("refused"))
    results = fetch_source(SOURCE)
    assert len(results) == 1
    assert not results[0].ok


@respx.mock
def test_fetch_source_skips_non_numeric_values():
    respx.get(SOURCE.url).mock(
        return_value=httpx.Response(200, json={"lag": 5, "status": "ok", "count": 3})
    )
    results = fetch_source(SOURCE)
    names = {r.metric_name for r in results}
    assert "status" not in names
    assert "lag" in names
    assert "count" in names


@respx.mock
def test_fetch_all_aggregates_multiple_sources():
    source_a = SourceConfig(name="a", url="http://a.example.com/metrics")
    source_b = SourceConfig(name="b", url="http://b.example.com/metrics")
    respx.get(source_a.url).mock(
        return_value=httpx.Response(200, json={"lag": 1})
    )
    respx.get(source_b.url).mock(
        return_value=httpx.Response(200, json={"lag": 2})
    )
    results = fetch_all([source_a, source_b])
    assert len(results) == 2
    source_names = {r.source_name for r in results}
    assert source_names == {"a", "b"}


def test_metric_result_ok_false_when_error_set():
    result = MetricResult(
        source_name="s", metric_name="m", value=0.0, error="something went wrong"
    )
    assert not result.ok


def test_metric_result_ok_true_when_no_error():
    result = MetricResult(source_name="s", metric_name="m", value=99.0)
    assert result.ok
    assert result.timestamp > 0
