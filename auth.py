from datetime import datetime, timedelta, timezone
from jose import jwt

from config import ADMIN_PASSWORD, API_KEY

SECRET_KEY = API_KEY
ALGORITHM = "HS256"


# Replace this with a database later
users = {
    "admin": {
        "password": ADMIN_PASSWORD,
        "role": "admin"
    }
}


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


def create_jwt_token(user: dict):
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )