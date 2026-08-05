import asyncio
import uvicorn

from Services.artifacts_api import API
from Controllers.CharactersController import CharactersController
from api import create_app

async def main():
    api = API()

    controller = CharactersController(api)

    app = create_app(controller)

    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )

    server = uvicorn.Server(config)

    await controller.load()

    results = await asyncio.gather(
        *(c.run() for c in controller.characters.values()),
        controller.console(),
        server.serve(),
        return_exceptions=True
    )

    for result in results:
        if isinstance(result, Exception):
            print(result)

if __name__ == "__main__":
    asyncio.run(main())