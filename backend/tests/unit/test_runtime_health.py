import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.runtime_health import (  # noqa: E402
    get_runtime_snapshot,
    mark_background_task_crash,
    mark_background_task_running,
    mark_background_task_stopped,
    mark_component_status,
)


def test_runtime_snapshot_contains_components_and_uptime():
    mark_component_status("mongo", True)
    mark_component_status("http_client", True)
    mark_background_task_running("upload_worker")
    mark_background_task_crash("upload_worker", RuntimeError("boom"))
    mark_background_task_stopped("upload_worker")

    snapshot = get_runtime_snapshot()
    assert "components" in snapshot
    assert "background_tasks" in snapshot
    assert "uptime_seconds" in snapshot
    assert snapshot["uptime_seconds"] >= 0
    assert "mongo" in snapshot["components"]
    assert "upload_worker" in snapshot["background_tasks"]

