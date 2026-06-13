from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import verify_token
from .database import get_db
from bson import ObjectId

security = HTTPBearer(auto_error=False)

async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and verify JWT from Authorization header or query param. Returns user dict or None."""
    token = request.query_params.get("token")
    if not credentials and not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    actual_token = credentials.credentials if credentials else token

    try:
        payload = verify_token(actual_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token")

        db = get_db()
        user = await db.users.find_one({"_id": ObjectId(user_id)})

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # Convert ObjectId to string for JSON serialization
        user["_id"] = str(user["_id"])
        return user

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_optional_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Same as get_current_user but returns None instead of raising on failure."""
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None
