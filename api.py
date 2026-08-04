from fastapi import FastAPI
from Schemas.Command import Command

def create_app(controller):
    app = FastAPI()

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