from fastapi import APIRouter

from app.core.pool_observability import get_pool_diagnostics

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/pools")
async def pool_health() -> dict:
    """
    Read-only diagnostics for Mongo and outbound HTTP connection pools.
    """
    return get_pool_diagnostics()
