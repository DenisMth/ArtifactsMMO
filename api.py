from fastapi import FastAPI, Depends, HTTPException
from Schemas.Command import Command
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone

from auth import authenticate, check_user, create_access_token, create_refresh_token, refresh_tokens, users

BASE_DIR = Path(__file__).resolve().parent

def create_app(controller):
    app = FastAPI()

    origins = [
        "http://localhost:51487",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class LoginRequest(BaseModel):
        username: str
        password: str

    class RefreshRequest(BaseModel):
        refresh_token: str

    @app.post("/login")
    async def login(data: LoginRequest):
        user = check_user(data.username, data.password)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @app.post("/refresh")
    async def refresh(data: RefreshRequest):
        session = refresh_tokens.get(data.refresh_token)

        if not session:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

        now = datetime.now(timezone.utc)

        if session["expires_at"] <= now:
            del refresh_tokens[data.refresh_token]

            raise HTTPException(
                status_code=401,
                detail="Refresh token expired"
            )

        username = session["username"]
        user = users.get(username)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User no longer exists"
            )

        user_data = {
            "username": username,
            "role": user["role"]
        }

        access_token = create_access_token(user_data)

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return FileResponse(BASE_DIR / "favicon.ico")

    @app.get("/", dependencies=[Depends(authenticate)])
    async def root():
        return {
            "status": "running",
            "characters": list(controller.characters.keys())
        }

    @app.post("/command", dependencies=[Depends(authenticate)])
    async def command(cmd: Command):
        await controller.execute(cmd)
        return {"success": True}

    return app