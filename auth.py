from datetime import datetime, timedelta, timezone
import secrets
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import Header, HTTPException

from config import ADMIN_PASSWORD, API_KEY

JWT_SECRET_KEY = API_KEY
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


# Replace this with a database later
users = {
    "admin": {
        "password": ADMIN_PASSWORD,
        "role": "admin"
    }
}

refresh_tokens = {}


def check_user(username: str, password: str):
    user = users.get(username)

    if not user:
        return None

    if user["password"] != password:
        return None

    return {
        "username": username,
        "role": user["role"]
    }


def create_access_token(user: dict):
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=ALGORITHM
    )

def create_refresh_token(user: dict):
    token = secrets.token_urlsafe(64)

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    refresh_tokens[token] = {
        "username": user["username"],
        "expires_at": expires_at,
    }

    return token

async def authenticate(
    authorization: str = Header(...)
):
    try:
        scheme, token = authorization.split(" ", 1)

        if scheme.lower() != "bearer":
            raise ValueError()

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication"
        )