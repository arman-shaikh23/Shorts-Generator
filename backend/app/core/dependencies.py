from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import verify_token
from .database import get_db
from bson import ObjectId

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and verify JWT from Authorization header."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    actual_token = credentials.credentials

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

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Same as get_current_user but returns None instead of raising on failure."""
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
