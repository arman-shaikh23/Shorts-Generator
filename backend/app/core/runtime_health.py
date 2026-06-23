import time
from copy import deepcopy
from threading import Lock
from datetime import datetime, timezone
from typing import Any

_lock = Lock()

_runtime_state: dict[str, Any] = {
    "started_at_unix": time.time(),
    "components": {
        "mongo": {"ready": False, "last_error": None, "last_updated": None},
        "http_client": {"ready": False, "last_error": None, "last_updated": None},
        "cache": {"ready": False, "last_error": None, "last_updated": None},
    },
    "background_tasks": {},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def mark_component_status(component: str, ready: bool, error: str | None = None) -> None:
    with _lock:
        current = _runtime_state["components"].setdefault(
            component,
            {"ready": False, "last_error": None, "last_updated": None},
        )
        current["ready"] = bool(ready)
        current["last_error"] = str(error)[:300] if error else None
        current["last_updated"] = _now_iso()


def mark_background_task_running(task_name: str) -> None:
    with _lock:
        state = _runtime_state["background_tasks"].setdefault(
            task_name,
            {
                "running": False,
                "restart_count": 0,
                "consecutive_failures": 0,
                "last_error": None,
                "last_started_at": None,
                "last_crashed_at": None,
                "last_updated": None,
            },
        )
        state["running"] = True
        state["consecutive_failures"] = 0
        state["last_error"] = None
        state["last_started_at"] = _now_iso()
        state["last_updated"] = _now_iso()


def mark_background_task_crash(task_name: str, error: Exception) -> int:
    with _lock:
        state = _runtime_state["background_tasks"].setdefault(
            task_name,
            {
                "running": False,
                "restart_count": 0,
                "consecutive_failures": 0,
                "last_error": None,
                "last_started_at": None,
                "last_crashed_at": None,
                "last_updated": None,
            },
        )
        state["running"] = False
        state["restart_count"] = int(state["restart_count"]) + 1
        state["consecutive_failures"] = int(state["consecutive_failures"]) + 1
        state["last_error"] = f"{error.__class__.__name__}: {error}"[:300]
        state["last_crashed_at"] = _now_iso()
        state["last_updated"] = _now_iso()
        return int(state["consecutive_failures"])


def mark_background_task_success(task_name: str) -> None:
    with _lock:
        state = _runtime_state["background_tasks"].setdefault(
            task_name,
            {
                "running": False,
                "restart_count": 0,
                "consecutive_failures": 0,
                "last_error": None,
                "last_started_at": None,
                "last_crashed_at": None,
                "last_updated": None,
            },
        )
        state["running"] = True
        state["consecutive_failures"] = 0
        state["last_error"] = None
        state["last_updated"] = _now_iso()


def mark_background_task_stopped(task_name: str) -> None:
    with _lock:
        state = _runtime_state["background_tasks"].setdefault(
            task_name,
            {
                "running": False,
                "restart_count": 0,
                "consecutive_failures": 0,
                "last_error": None,
                "last_started_at": None,
                "last_crashed_at": None,
                "last_updated": None,
            },
        )
        state["running"] = False
        state["last_updated"] = _now_iso()


def get_runtime_snapshot() -> dict[str, Any]:
    with _lock:
        snapshot = deepcopy(_runtime_state)

    uptime_seconds = max(0, int(time.time() - float(snapshot["started_at_unix"])))
    snapshot["uptime_seconds"] = uptime_seconds
    return snapshot
