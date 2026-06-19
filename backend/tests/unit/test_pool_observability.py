import httpx

from app.core.pool_observability import (
    configure_http_pool,
    configure_mongo_pool,
    get_pool_diagnostics,
    get_http_pool_snapshot,
    get_mongo_pool_snapshot,
    http_request_completed,
    http_request_failed,
    http_request_started,
    mark_http_client_closed,
    mark_http_client_initialized,
    mark_mongo_client_closed,
    mark_mongo_client_initialized,
    mongo_connect_failed,
    mongo_connect_succeeded,
    mongo_ping_failed,
    mongo_ping_succeeded,
    reset_pool_metrics_for_tests,
)


def test_http_pool_metrics_capture_success_and_timeout():
    reset_pool_metrics_for_tests()
    configure_http_pool(max_connections=40, max_keepalive_connections=10, pool_timeout_sec=15.0)
    mark_http_client_initialized()

    first = http_request_started()
    http_request_completed(first, 200)

    second = http_request_started()
    http_request_failed(second, httpx.PoolTimeout("pool wait exceeded"))

    snapshot = get_http_pool_snapshot()
    assert snapshot["client_initialized"] is True
    assert snapshot["config"]["max_connections"] == 40
    assert snapshot["requests_total"] == 2
    assert snapshot["requests_error_total"] == 1
    assert snapshot["timeouts"]["pool"] == 1
    assert snapshot["latency_ms"]["samples"] == 2

    mark_http_client_closed()
    snapshot = get_http_pool_snapshot()
    assert snapshot["client_initialized"] is False


def test_mongo_pool_metrics_capture_connect_ping_and_failures():
    reset_pool_metrics_for_tests()
    configure_mongo_pool(
        db_name="realestate_shorts",
        max_pool_size=100,
        min_pool_size=5,
        wait_queue_timeout_ms=10000,
        server_selection_timeout_ms=5000,
    )
    mark_mongo_client_initialized()
    mongo_connect_succeeded(12.5)
    mongo_ping_succeeded(5.0)
    mongo_ping_failed(11.0, RuntimeError("ping timeout"))
    mongo_connect_failed(22.0, RuntimeError("server selection timeout"))

    snapshot = get_mongo_pool_snapshot()
    assert snapshot["client_initialized"] is True
    assert snapshot["config"]["db_name"] == "realestate_shorts"
    assert snapshot["connect"]["success_total"] == 1
    assert snapshot["connect"]["failure_total"] == 1
    assert snapshot["ping"]["success_total"] == 1
    assert snapshot["ping"]["failure_total"] == 1
    assert snapshot["ping"]["avg_latency_ms"] is not None

    mark_mongo_client_closed()
    snapshot = get_mongo_pool_snapshot()
    assert snapshot["client_initialized"] is False


def test_pool_diagnostics_degraded_when_timeouts_present():
    reset_pool_metrics_for_tests()
    configure_http_pool(max_connections=10, max_keepalive_connections=5, pool_timeout_sec=5.0)
    mark_http_client_initialized()
    started = http_request_started()
    http_request_failed(started, httpx.PoolTimeout("pool timeout"))

    diagnostics = get_pool_diagnostics()
    assert diagnostics["status"] == "degraded"
    assert diagnostics["issues"]
    assert "http_pool" in diagnostics
    assert "mongo_pool" in diagnostics
