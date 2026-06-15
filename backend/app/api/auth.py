from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from ..core.auth import create_access_token, create_refresh_token, verify_token
from ..core.database import get_db
from ..core.dependencies import get_current_user
import bcrypt
import datetime
import uuid
import asyncio

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── Request Models ──────────────────────────────────────

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# ── Helpers ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

async def issue_tokens(user_id: str) -> dict:
    """Issue a new access + refresh token pair and store the refresh token in DB."""
    db = get_db()
    family = str(uuid.uuid4())

    access_token = create_access_token({"sub": user_id})
    refresh_token = create_refresh_token({"sub": user_id, "family": family})

    await db.refresh_tokens.insert_one({
        "token": refresh_token,
        "user_id": user_id,
        "family": family,
        "expires_at": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        "is_revoked": False,
        "created_at": datetime.datetime.utcnow(),
    })

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# ── Endpoints ───────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignupRequest):
    db = get_db()

    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Offload CPU-bound hash generation to a background thread
    password_hash = await asyncio.to_thread(hash_password, req.password)

    result = await db.users.insert_one({
        "email": req.email,
        "name": req.name,
        "passwordHash": password_hash,
        "authProvider": "email",
        "googleId": None,
        "avatar": None,
        "plan": "FREE",
        "usage": {"monthlyShorts": 0, "monthlyUploads": 0, "totalStorageMB": 0},
        "settings": {"defaultStyle": "Luxury", "defaultDuration": "30 sec", "watermark": True, "brandKit": None},
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
    })

    return await issue_tokens(str(result.inserted_id))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    db = get_db()

    user = await db.users.find_one({"email": req.email})
    
    # Offload CPU-bound hash verification to a background thread
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    is_valid = await asyncio.to_thread(verify_password, req.password, user["passwordHash"])
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return await issue_tokens(str(user["_id"]))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    """Rotate refresh token. Old token is revoked, new pair is issued."""
    db = get_db()

    # Find the token in DB
    stored = await db.refresh_tokens.find_one({"token": req.refresh_token})

    if not stored:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if stored["is_revoked"]:
        # Possible token theft — revoke entire family
        await db.refresh_tokens.update_many(
            {"family": stored["family"]},
            {"$set": {"is_revoked": True}}
        )
        raise HTTPException(status_code=401, detail="Token reuse detected. All sessions revoked.")

    if stored["expires_at"] < datetime.datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Verify JWT signature
    try:
        payload = verify_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Revoke old token
    await db.refresh_tokens.update_one(
        {"_id": stored["_id"]},
        {"$set": {"is_revoked": True}}
    )

    # Issue new pair in the same family
    return await issue_tokens(stored["user_id"])


@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    """Revoke all refresh tokens for this user."""
    db = get_db()
    await db.refresh_tokens.update_many(
        {"user_id": str(user["_id"])},
        {"$set": {"is_revoked": True}}
    )
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    """Return current user profile (no password hash)."""
    return {
        "_id": str(user["_id"]),
        "email": user.get("email"),
        "name": user.get("name"),
        "plan": user.get("plan", "FREE"),
        "avatar": user.get("avatar"),
        "settings": user.get("settings", {}),
        "usage": user.get("usage", {}),
        "createdAt": str(user.get("createdAt", "")),
    }
