import asyncio
import json
from pathlib import Path
from Models.Character import Character
from Schemas.Command import Command

VALID_COMMANDS = [
    "fight", "f",
    "gather", "g",
    "idle", "init", "i",
    "bossfight", "bf",
    "gatheraft", "gc",
    "craft", "c",
    "craftmass", "cm",
    "craftcycle", "cc",
    "assemble", "a"
]

EVENT_PRIORITY = [
    "bandit_camp",
    "portal_demon",
    "full_moon",
    "magic_apparition",
    "strange_apparition",
    "cult_of_darkness",
    "silent_night",
    "corrupted_ogre",
    "corrupted_owlbear"
]

class CharactersController:
    def __init__(self, api) -> None:
        self.api = api
        self.characters = {}
        self.original_actions = {}

    async def handle_command(self, cmd):
        parts = cmd.strip().split()

        if not parts:
            return

        names = parts[0]
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

    async def check_events(self):

        data = await self.api.get_active_events()

        active_events = data["data"]

        active_events.sort(
            key=lambda event: EVENT_PRIORITY.index(event["code"])
        )

        Path("data/events").mkdir(exist_ok=True)

        with open(f"data/events/events.json", "w") as f:
            json.dump(active_events, f, indent=4)

        for name, character in self.characters.items():

            selected_event = None

            for event in active_events:

                if event['code'] not in EVENT_PRIORITY:
                    continue

                event_action = None

                if event["content"]["type"] == "monster":
                    event_action = "fight"

                if event["content"]["type"] == "resource":
                    event_action = "gather"

                if event_action is None:
                    continue

                if event_action == "gather":
                    if event["content"]["code"] == "strange_rocks" and character.mining_level < 35:
                        continue

                    if event["content"]["code"] == "magic_tree" and character.woodcutting_level < 35:
                        continue

                if event["content"]["code"] == character.target:
                    continue

                selected_event = event
                break

            if selected_event is None:

                if name in self.original_actions:
                    original_action = self.original_actions.pop(name)

                    character.set_action(
                        original_action["action"],
                        original_action["target"],
                        original_action["option"],
                        original_action["characters"]
                    )

                continue

            if name not in self.original_actions:
                self.original_actions[name] = {
                    "action": character.action,
                    "target": character.target,
                    "option": character.option,
                    "characters": character.characters
                }

            character.set_action(
                event_action,
                selected_event["content"]["code"]
            )


    async def execute(self, command: Command):


        if command.action in VALID_COMMANDS:

            if command.action in ["bf", "bossfight"]:

                character = self.characters.get(command.characters[0])
                await character.set_action(command.action, command.target, command.characters)

            else:

                if command.characters[0] in ['all', 'a', 'avengers']:
                    command.characters = list(self.characters.keys())

                for name in command.characters:

                    character = self.characters.get(name)

                    if character is None:
                        print(f"Unknown character: {name}")

                    await character.set_action(
                        command.action,
                        command.target,
                        None,
                        command.option)

    async def load(self):
        characters = await self.api.get_characters()

        for data in characters["data"]:
            character = Character(self.api, data)
            self.characters[character.name] = character

        print("Loaded characters:", list(self.characters.keys()))

        items = await self.api.get_all_items()

        print(f"Loaded {len(items)} items")


    async def console(self):

        while True:
            cmd = await asyncio.to_thread(input, "> ")

            try:
                await self.handle_command(cmd)
            except Exception as e:
                print(f"Command failed: {e}")

    async def events_manager(self):

        while True:
            try:
                await self.check_events()
            except Exception as e:
                print(f"Event manager failed: {e}")

            await asyncio.sleep(300)