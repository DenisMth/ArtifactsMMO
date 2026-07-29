import asyncio
from Models.Character import Character

class CharactersController:
    def __init__(self, api) -> None:
        self.api = api
        self.characters = {}

    async def handle_command(self, cmd):
        parts = cmd.strip().split()

        if not parts:
            return

        name = parts[0]
        action = parts[1]
        target = parts[2]

        if action in ["bf", "bossfight"]:

            characters = name.split(",")
            character = self.characters.get(characters[0])
            character.set_action(action, target, characters)

        else:

            if name != "all":

                for char in name.split(","):

                    character = self.characters.get(char)
                    character.set_action(action, target)

            else:
                for character in self.characters.values():
                    character.set_action(action, target)

    async def load(self):
        response = await self.api.get_characters()

        for data in response["data"]:
            character = Character(self.api, data)
            self.characters[character.name] = character

        print("Loaded characters:", list(self.characters.keys()))


    async def console(self):
        while True:
            cmd = await asyncio.to_thread(input, "> ")
            await self.handle_command(cmd)
