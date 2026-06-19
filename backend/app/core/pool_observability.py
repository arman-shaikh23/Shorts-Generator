import logging
import time
from collections import defaultdict, deque
from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_lock = Lock()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_http_metrics: Dict[str, Any] = {}
_mongo_metrics: Dict[str, Any] = {}


def _fresh_http_metrics() -> Dict[str, Any]:
    return {
        "client_initialized": False,
        "config": {
            "max_connections": None,
            "max_keepalive_connections": None,
            "pool_timeout_sec": None,
        },
        "requests_total": 0,
        "requests_error_total": 0,
        "requests_in_flight": 0,
        "status_buckets": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "other": 0},
        "timeouts": {"pool": 0, "connect": 0, "read": 0, "write": 0, "other": 0},
        "latency_ms": {
            "last": None,
            "max": 0.0,
            "total": 0.0,
            "samples": 0,
            "avg": None,
        },
        "last_error": None,
        "last_updated": _utc_now_iso(),
    }


def _fresh_mongo_metrics() -> Dict[str, Any]:
    return {
        "client_initialized": False,
        "config": {
            "db_name": None,
            "max_pool_size": None,
            "min_pool_size": None,
            "wait_queue_timeout_ms": None,
            "server_selection_timeout_ms": None,
        },
        "connect": {
            "success_total": 0,
            "failure_total": 0,
            "last_latency_ms": None,
            "last_error": None,
        },
        "ping": {
            "success_total": 0,
            "failure_total": 0,
            "last_latency_ms": None,
            "max_latency_ms": 0.0,
            "total_latency_ms": 0.0,
            "samples": 0,
            "avg_latency_ms": None,
            "last_error": None,
        },
        "checkout": {
            "started_total": 0,
            "succeeded_total": 0,
            "failed_total": 0,
            "timeout_total": 0,
            "wait_last_ms": None,
            "wait_max_ms": 0.0,
            "wait_total_ms": 0.0,
            "wait_samples": 0,
            "wait_avg_ms": None,
            "last_failure_reason": None,
        },
        "pool_events": {
            "created_total": 0,
            "ready_total": 0,
            "cleared_total": 0,
            "closed_total": 0,
            "connections_created_total": 0,
            "connections_closed_total": 0,
        },
        "last_updated": _utc_now_iso(),
    }


def _mark_http_updated() -> None:
    _http_metrics["last_updated"] = _utc_now_iso()


def _mark_mongo_updated() -> None:
    _mongo_metrics["last_updated"] = _utc_now_iso()


def _update_latency_bucket(bucket: Dict[str, Any], elapsed_ms: float) -> None:
    bucket["last"] = round(elapsed_ms, 3)
    bucket["max"] = round(max(float(bucket["max"]), elapsed_ms), 3)
    bucket["total"] = float(bucket["total"]) + float(elapsed_ms)
    bucket["samples"] = int(bucket["samples"]) + 1
    bucket["avg"] = round(bucket["total"] / bucket["samples"], 3)


def reset_pool_metrics_for_tests() -> None:
    with _lock:
        _http_metrics.clear()
        _http_metrics.update(_fresh_http_metrics())
        _mongo_metrics.clear()
        _mongo_metrics.update(_fresh_mongo_metrics())


reset_pool_metrics_for_tests()


def configure_http_pool(max_connections: int, max_keepalive_connections: int, pool_timeout_sec: float) -> None:
    with _lock:
        _http_metrics["config"] = {
            "max_connections": int(max_connections),
            "max_keepalive_connections": int(max_keepalive_connections),
            "pool_timeout_sec": float(pool_timeout_sec),
        }
        _mark_http_updated()


def mark_http_client_initialized() -> None:
    with _lock:
        _http_metrics["client_initialized"] = True
        _mark_http_updated()


def mark_http_client_closed() -> None:
    with _lock:
        _http_metrics["client_initialized"] = False
        _http_metrics["requests_in_flight"] = 0
        _mark_http_updated()


def http_request_started() -> float:
    started_at = time.perf_counter()
    with _lock:
        _http_metrics["requests_in_flight"] = int(_http_metrics["requests_in_flight"]) + 1
        _mark_http_updated()
    return started_at


def _record_http_common(started_at: float) -> float:
    elapsed_ms = max(0.0, (time.perf_counter() - float(started_at)) * 1000.0)
    _http_metrics["requests_total"] = int(_http_metrics["requests_total"]) + 1
    _http_metrics["requests_in_flight"] = max(0, int(_http_metrics["requests_in_flight"]) - 1)
    _update_latency_bucket(_http_metrics["latency_ms"], elapsed_ms)
    return elapsed_ms


def http_request_completed(started_at: float, status_code: int) -> None:
    with _lock:
        _record_http_common(started_at)
        code = int(status_code)
        if 200 <= code < 300:
            _http_metrics["status_buckets"]["2xx"] += 1
        elif 300 <= code < 400:
            _http_metrics["status_buckets"]["3xx"] += 1
        elif 400 <= code < 500:
            _http_metrics["status_buckets"]["4xx"] += 1
            _http_metrics["requests_error_total"] += 1
        elif 500 <= code < 600:
            _http_metrics["status_buckets"]["5xx"] += 1
            _http_metrics["requests_error_total"] += 1
        else:
            _http_metrics["status_buckets"]["other"] += 1
        _mark_http_updated()


def http_request_failed(started_at: float, exc: Exception) -> None:
    error_name = exc.__class__.__name__.lower()
    error_text = f"{exc.__class__.__name__}: {exc}"
    with _lock:
        _record_http_common(started_at)
        _http_metrics["requests_error_total"] = int(_http_metrics["requests_error_total"]) + 1
        _http_metrics["status_buckets"]["other"] += 1
        if "pooltimeout" in error_name:
            _http_metrics["timeouts"]["pool"] += 1
        elif "connecttimeout" in error_name:
            _http_metrics["timeouts"]["connect"] += 1
        elif "readtimeout" in error_name:
            _http_metrics["timeouts"]["read"] += 1
        elif "writetimeout" in error_name:
            _http_metrics["timeouts"]["write"] += 1
        elif "timeout" in error_name:
            _http_metrics["timeouts"]["other"] += 1
        _http_metrics["last_error"] = error_text[:300]
        _mark_http_updated()

    if "timeout" in error_name:
        logger.warning("[HTTP POOL] Request timeout observed: %s", error_text)


def get_http_pool_snapshot() -> Dict[str, Any]:
    with _lock:
        return deepcopy(_http_metrics)


def configure_mongo_pool(
    db_name: str,
    max_pool_size: int,
    min_pool_size: int,
    wait_queue_timeout_ms: int,
    server_selection_timeout_ms: int,
) -> None:
    with _lock:
        _mongo_metrics["config"] = {
            "db_name": db_name,
            "max_pool_size": int(max_pool_size),
            "min_pool_size": int(min_pool_size),
            "wait_queue_timeout_ms": int(wait_queue_timeout_ms),
            "server_selection_timeout_ms": int(server_selection_timeout_ms),
        }
        _mark_mongo_updated()


def mark_mongo_client_initialized() -> None:
    with _lock:
        _mongo_metrics["client_initialized"] = True
        _mark_mongo_updated()


def mark_mongo_client_closed() -> None:
    with _lock:
        _mongo_metrics["client_initialized"] = False
        _mark_mongo_updated()


def mongo_connect_succeeded(latency_ms: float) -> None:
    with _lock:
        connect = _mongo_metrics["connect"]
        connect["success_total"] = int(connect["success_total"]) + 1
        connect["last_latency_ms"] = round(float(latency_ms), 3)
        connect["last_error"] = None
        _mark_mongo_updated()


def mongo_connect_failed(latency_ms: float, exc: Exception) -> None:
    with _lock:
        connect = _mongo_metrics["connect"]
        connect["failure_total"] = int(connect["failure_total"]) + 1
        connect["last_latency_ms"] = round(float(latency_ms), 3)
        connect["last_error"] = f"{exc.__class__.__name__}: {exc}"[:300]
        _mark_mongo_updated()

    logger.warning("[MONGO POOL] Connect failure observed: %s", connect["last_error"])


def mongo_ping_succeeded(latency_ms: float) -> None:
    with _lock:
        ping = _mongo_metrics["ping"]
        ping["success_total"] = int(ping["success_total"]) + 1
        ping["last_latency_ms"] = round(float(latency_ms), 3)
        ping["max_latency_ms"] = round(max(float(ping["max_latency_ms"]), float(latency_ms)), 3)
        ping["total_latency_ms"] = float(ping["total_latency_ms"]) + float(latency_ms)
        ping["samples"] = int(ping["samples"]) + 1
        ping["avg_latency_ms"] = round(float(ping["total_latency_ms"]) / int(ping["samples"]), 3)
        ping["last_error"] = None
        _mark_mongo_updated()


def mongo_ping_failed(latency_ms: float, exc: Exception) -> None:
    with _lock:
        ping = _mongo_metrics["ping"]
        ping["failure_total"] = int(ping["failure_total"]) + 1
        ping["last_latency_ms"] = round(float(latency_ms), 3)
        ping["last_error"] = f"{exc.__class__.__name__}: {exc}"[:300]
        _mark_mongo_updated()

    logger.warning("[MONGO POOL] Ping failure observed: %s", ping["last_error"])


def _record_checkout_wait_locked(started_at: float) -> None:
    elapsed_ms = max(0.0, (time.perf_counter() - float(started_at)) * 1000.0)
    checkout = _mongo_metrics["checkout"]
    checkout["wait_last_ms"] = round(elapsed_ms, 3)
    checkout["wait_max_ms"] = round(max(float(checkout["wait_max_ms"]), elapsed_ms), 3)
    checkout["wait_total_ms"] = float(checkout["wait_total_ms"]) + elapsed_ms
    checkout["wait_samples"] = int(checkout["wait_samples"]) + 1
    checkout["wait_avg_ms"] = round(float(checkout["wait_total_ms"]) / int(checkout["wait_samples"]), 3)


try:
    from pymongo import monitoring

    class _MongoPoolListener(monitoring.ConnectionPoolListener):  # type: ignore[misc]
        def __init__(self) -> None:
            self._checkout_started_by_address = defaultdict(deque)

        def pool_created(self, event: Any) -> None:
            with _lock:
                _mongo_metrics["pool_events"]["created_total"] += 1
                _mark_mongo_updated()

        def pool_ready(self, event: Any) -> None:
            with _lock:
                _mongo_metrics["pool_events"]["ready_total"] += 1
                _mark_mongo_updated()

        def pool_cleared(self, event: Any) -> None:
            with _lock:
                _mongo_metrics["pool_events"]["cleared_total"] += 1
                _mark_mongo_updated()

        def pool_closed(self, event: Any) -> None:
            with _lock:
                _mongo_metrics["pool_events"]["closed_total"] += 1
                _mark_mongo_updated()

        def connection_created(self, event: Any) -> None:
            with _lock:
                _mongo_metrics["pool_events"]["connections_created_total"] += 1
                _mark_mongo_updated()

        def connection_ready(self, event: Any) -> None:
            # Required override to avoid base-class NotImplementedError emissions.
            with _lock:
                _mark_mongo_updated()

        def connection_closed(self, event: Any) -> None:
            with _lock:
                _mongo_metrics["pool_events"]["connections_closed_total"] += 1
                _mark_mongo_updated()

        def connection_check_out_started(self, event: Any) -> None:
            address = getattr(event, "address", "unknown")
            with _lock:
                _mongo_metrics["checkout"]["started_total"] += 1
                self._checkout_started_by_address[address].append(time.perf_counter())
                _mark_mongo_updated()

        def connection_checked_out(self, event: Any) -> None:
            address = getattr(event, "address", "unknown")
            with _lock:
                _mongo_metrics["checkout"]["succeeded_total"] += 1
                if self._checkout_started_by_address[address]:
                    started_at = self._checkout_started_by_address[address].popleft()
                    _record_checkout_wait_locked(started_at)
                _mark_mongo_updated()

        def connection_checked_in(self, event: Any) -> None:
            # Required override to avoid base-class NotImplementedError emissions.
            with _lock:
                _mark_mongo_updated()

        def connection_check_out_failed(self, event: Any) -> None:
            address = getattr(event, "address", "unknown")
            reason = str(getattr(event, "reason", "unknown"))
            with _lock:
                checkout = _mongo_metrics["checkout"]
                checkout["failed_total"] = int(checkout["failed_total"]) + 1
                if "timeout" in reason.lower():
                    checkout["timeout_total"] = int(checkout["timeout_total"]) + 1
                checkout["last_failure_reason"] = reason[:200]
                if self._checkout_started_by_address[address]:
                    started_at = self._checkout_started_by_address[address].popleft()
                    _record_checkout_wait_locked(started_at)
                _mark_mongo_updated()

    _mongo_listener: Any = _MongoPoolListener()

except Exception:
    _mongo_listener = None


def get_mongo_event_listeners() -> List[Any]:
    if _mongo_listener is None:
        return []
    return [_mongo_listener]


def get_mongo_pool_snapshot() -> Dict[str, Any]:
    with _lock:
        return deepcopy(_mongo_metrics)


def get_pool_diagnostics() -> Dict[str, Any]:
    http_snapshot = get_http_pool_snapshot()
    mongo_snapshot = get_mongo_pool_snapshot()

    status = "ok"
    issues = []

    total_http_timeouts = sum(http_snapshot["timeouts"].values())
    if total_http_timeouts > 0:
        status = "degraded"
        issues.append(f"http_timeouts={total_http_timeouts}")

    if mongo_snapshot["checkout"]["timeout_total"] > 0:
        status = "degraded"
        issues.append(f"mongo_checkout_timeouts={mongo_snapshot['checkout']['timeout_total']}")

    if mongo_snapshot["connect"]["failure_total"] > 0:
        status = "degraded"
        issues.append(f"mongo_connect_failures={mongo_snapshot['connect']['failure_total']}")

    return {
        "status": status,
        "issues": issues,
        "http_pool": http_snapshot,
        "mongo_pool": mongo_snapshot,
        "generated_at": _utc_now_iso(),
    }
