from fastapi import FastAPI
from Schemas.Command import Command
from fastapi.responses import FileResponse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def create_app(controller):
    app = FastAPI()

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return FileResponse(BASE_DIR / "favicon.ico")

    @app.get("/")
    async def root():
        return {
            "status": "running",
            "characters": list(controller.characters.keys())
        }

    @app.post("/command")
    async def command(cmd: Command):
        await controller.execute(cmd)
        return {"success": True}

    return app