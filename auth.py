from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from config import API_KEY

api_key_header = APIKeyHeader(name="X-API-Key")


async def authenticate(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return api_key