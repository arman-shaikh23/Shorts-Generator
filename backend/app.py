"""
Legacy compatibility entrypoint.

Use `uvicorn main:app` as the primary runtime command.
This module simply re-exports the FastAPI app to avoid stale imports.
"""

from main import app

__all__ = ["app"]
