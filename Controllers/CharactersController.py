import asyncio
from Models.Character import Character
from Schemas.Command import Command

class CharactersController:
    def __init__(self, api) -> None:
        self.api = api
        self.characters = {}

    async def handle_command(self, cmd):
        parts = cmd.strip().split()

        if not parts:
            return

        names = (
            list(self.characters.keys())
            if parts[0] in ["all", "a", "avengers"]
            else parts[0].split(",")
        )
        action = parts[1]
        target = parts[2] if len(parts) > 2 else None
        option = parts[3] if len(parts) > 3 else None

        command = Command(
            characters=names,
            action=action,
            target=target,
            option=option
        )

        await self.execute(command)


    async def execute(self, command: Command):


        if command.action in ["bf", "bossfight"]:

            character = self.characters.get(command.characters[0])
            await character.set_action(command.action, command.target, command.characters)

        else:



            for name in command.characters:

                character = self.characters.get(name)
                await character.set_action(
                    command.action,
                    command.target,
                    None,
                    command.option)

    async def load(self):
        response = await self.api.get_characters()

        for data in response["data"]:
            character = Character(self.api, data)
            self.characters[character.name] = character

        print("Loaded characters:", list(self.characters.keys()))


    async def console(self):

        while True:
            cmd = await asyncio.to_thread(input, "> ")

            try:
                await self.handle_command(cmd)
            except Exception as e:
                print(f"Command failed: {e}")
