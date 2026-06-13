import os
import jwt
from datetime import datetime, timedelta, timezone

# We assume RSA private/public keys are stored as env vars or mounted files
PRIVATE_KEY = os.environ.get("RSA_PRIVATE_KEY", "mock_private_key_for_dev")
PUBLIC_KEY = os.environ.get("RSA_PUBLIC_KEY", "mock_public_key_for_dev")
ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    # For dev, if no real RSA key is provided, we fallback to HS256 to avoid crashes
    if PRIVATE_KEY == "mock_private_key_for_dev":
        return jwt.encode(to_encode, "dev_secret", algorithm="HS256")
    return jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    if PRIVATE_KEY == "mock_private_key_for_dev":
        return jwt.encode(to_encode, "dev_secret", algorithm="HS256")
    return jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    if PUBLIC_KEY == "mock_public_key_for_dev":
        return jwt.decode(token, "dev_secret", algorithms=["HS256"])
    return jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
