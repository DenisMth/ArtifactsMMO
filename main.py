import asyncio

from api import API
from Models.Character import Character
from Controllers.CharactersController import CharactersController

async def main():
    api = API()

    controller = CharactersController(api)

    await controller.load()

    results = await asyncio.gather(
        *(c.run() for c in controller.characters.values()),
        controller.console(),
        return_exceptions=True
    )

    for result in results:
        if isinstance(result, Exception):
            print(result)

if __name__ == "__main__":
    asyncio.run(main())