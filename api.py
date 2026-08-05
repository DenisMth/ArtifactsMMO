from fastapi import FastAPI, Depends
from Schemas.Command import Command
from fastapi.responses import FileResponse
from pathlib import Path

from auth import authenticate

BASE_DIR = Path(__file__).resolve().parent

def create_app(controller):
    app = FastAPI()

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