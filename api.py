from fastapi import FastAPI, Depends, HTTPException
from Schemas.Command import Command
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from auth import authenticate, check_user, create_jwt_token

BASE_DIR = Path(__file__).resolve().parent

def create_app(controller):
    app = FastAPI()

    origins = [
        "http://localhost:56478",
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

    @app.post("/login")
    async def login(data: LoginRequest):
        user = check_user(data.username, data.password)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        token = create_jwt_token(user)

        return {
            "access_token": token,
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