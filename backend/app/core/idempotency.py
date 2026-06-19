import datetime
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import HTTPException, Request
from pymongo.errors import DuplicateKeyError

from .database import get_db


IDEMPOTENCY_TTL_SECONDS = 24 * 60 * 60


@dataclass
class IdempotencyContext:
    user_id: str
    endpoint: str
    key: str
    request_hash: str


@dataclass
class IdempotencyReplay:
    status_code: int
    body: Any


def _extract_key(request: Request) -> Optional[str]:
    raw = request.headers.get("Idempotency-Key") or request.headers.get("X-Idempotency-Key")
    if raw is None:
        return None
    key = raw.strip()
    if not key:
        return None
    if len(key) > 255:
        raise HTTPException(status_code=400, detail="Idempotency-Key is too long")
    return key


def _hash_request_payload(method: str, endpoint: str, payload: Any) -> str:
    canonical = json.dumps(
        {
            "method": method.upper(),
            "endpoint": endpoint,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def begin_idempotent_operation(
    *,
    request: Request,
    user_id: str,
    payload: Any,
) -> tuple[Optional[IdempotencyContext], Optional[IdempotencyReplay]]:
    """
    Start idempotency flow.
    - Returns (None, None) when no key provided.
    - Returns (None, replay) when prior completed request should be replayed.
    - Returns (context, None) when caller should execute operation and later finalize.
    """
    key = _extract_key(request)
    if key is None:
        return None, None

    endpoint = f"{request.method.upper()}:{request.url.path}"
    request_hash = _hash_request_payload(request.method, endpoint, payload)
    now = datetime.datetime.utcnow()
    expires_at = now + datetime.timedelta(seconds=IDEMPOTENCY_TTL_SECONDS)
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    collection = db.idempotency_keys

    doc = {
        "user_id": user_id,
        "endpoint": endpoint,
        "key": key,
        "request_hash": request_hash,
        "status": "IN_PROGRESS",
        "response_status": None,
        "response_body": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
        "expires_at": expires_at,
    }

    try:
        await collection.insert_one(doc)
        return IdempotencyContext(user_id=user_id, endpoint=endpoint, key=key, request_hash=request_hash), None
    except DuplicateKeyError:
        existing = await collection.find_one({"user_id": user_id, "endpoint": endpoint, "key": key})
        if not existing:
            raise HTTPException(status_code=409, detail="Idempotency state conflict")

        if existing.get("request_hash") != request_hash:
            raise HTTPException(
                status_code=409,
                detail="Idempotency-Key already used with a different request payload",
            )

        status = existing.get("status")
        if status == "COMPLETED":
            replay_body = existing.get("response_body")
            replay_status = int(existing.get("response_status") or 200)
            return None, IdempotencyReplay(status_code=replay_status, body=replay_body)

        if status == "FAILED":
            claimed = await collection.find_one_and_update(
                {
                    "_id": existing["_id"],
                    "status": "FAILED",
                    "request_hash": request_hash,
                },
                {
                    "$set": {
                        "status": "IN_PROGRESS",
                        "updated_at": now,
                        "error": None,
                        "expires_at": expires_at,
                    }
                },
            )
            if claimed:
                return IdempotencyContext(user_id=user_id, endpoint=endpoint, key=key, request_hash=request_hash), None

        raise HTTPException(status_code=409, detail="Identical request is already being processed")


async def complete_idempotent_operation(
    context: Optional[IdempotencyContext],
    *,
    status_code: int,
    response_body: Any,
) -> None:
    if context is None:
        return

    db = get_db()
    if db is None:
        return
    await db.idempotency_keys.update_one(
        {
            "user_id": context.user_id,
            "endpoint": context.endpoint,
            "key": context.key,
            "request_hash": context.request_hash,
        },
        {
            "$set": {
                "status": "COMPLETED",
                "response_status": int(status_code),
                "response_body": response_body,
                "updated_at": datetime.datetime.utcnow(),
                "error": None,
            }
        },
    )


async def fail_idempotent_operation(
    context: Optional[IdempotencyContext],
    *,
    error_message: str,
) -> None:
    if context is None:
        return

    db = get_db()
    if db is None:
        return
    await db.idempotency_keys.update_one(
        {
            "user_id": context.user_id,
            "endpoint": context.endpoint,
            "key": context.key,
            "request_hash": context.request_hash,
        },
        {
            "$set": {
                "status": "FAILED",
                "updated_at": datetime.datetime.utcnow(),
                "error": error_message[:1000],
            }
        },
    )
