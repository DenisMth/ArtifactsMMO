import httpx
import asyncio
import json
from pathlib import Path
from config import TOKEN, base_url

class API:

    def __init__(self) -> None:
        self.base_url = base_url

        self.client = httpx.AsyncClient(
            headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}"
            },
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=10.0,
                read=30.0,
                write=10.0,
                pool=10.0
            )
        )

    async def _post(self, endpoint, data=None):
        response = await self.client.post(endpoint, json=data)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error = response.json()
            raise ValueError(
                f"POST {endpoint} failed ({response.status_code}): {error}"
            ) from e

        return response.json()
    
    async def _get(self, endpoint, data=None):
        response = await self.client.get(endpoint, params=data)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error = response.json()
            raise ValueError(
                f"GET {endpoint} failed ({response.status_code}): {error}"
            ) from e
        return response.json()

    async def get_characters(self):
        return await self._get("my/characters")

    async def get_items(self, character, resources):
        return await self._post(f"my/{character.name}/action/bank/withdraw/item", resources)

    async def fetch_bank_items(self):
        data = await self._get("my/bank/items")
        bank_items = data["data"]
        page = data["page"]
        while page < data["pages"]:
            data = await self._get("my/bank/items", {"page": page+1})
            bank_items.extend(data["data"])
            page += 1

        Path("data/bank").mkdir(exist_ok=True)

        with open(f"data/bank/bank.json", "w") as f:
            json.dump(bank_items, f, indent=4)

        return bank_items


    async def find_map_tile(self, character, target):

        char_x = character.x
        char_y = character.y

        if target == "spawn_bank":
            target = "bank"

            char_x = 4
            char_y = 1

        data = {
            "content_code" : target
        }
        response = await self._get(f"maps", data)
        tiles = [
            tile for tile in response["data"]
            if tile["access"]["type"] == "standard"
        ]

        return min(
            tiles,
            key=lambda t: (t["x"] - char_x) ** 2 + (t["y"] - char_y) ** 2
        )


    async def find_closest_transition(self, x,  y, layer, target_layer):

        data = {
            "layer": layer,
            "transition": "true"
        }

        transitions = await self._get(f"maps", data)

        valid_transitions = [
            t for t in transitions["data"]
            if t["interactions"]["transition"]["layer"] == target_layer
        ]

        if not valid_transitions:
            return None

        return min(
            valid_transitions,
            key=lambda t: (t["x"] - x) ** 2 + (t["y"] - y) ** 2
        )


    async def find_resource(self, target):
        data = {
            "drop" : target
        }
        return await self._get(f"resources", data)

    async def find_craft_elements(self, target):
        return await self._get(f"items/{target}")

    async def find_category_items(self, category, type,  min=0, max=50):
        query = {
            "min_level": str(min),
            "max_level": str(max),
            "craft_skill": category,
            "type": type
        }
        return await self._get(f"items", query)

    async def find_workshop(self, target):
        data = {
            "content_type": "workshop"
        }
        workshops = await self._get(f"maps", data)

        for workshop in workshops["data"]:
            if workshop["interactions"]["content"]["code"] == target:
                return workshop

        return None

    async def find_monster(self, target):
        return await self._get(f"monsters/{target}")

    async def move(self, character, x, y):
        data = {"x": x,"y": y}
        return await self._post(f"my/{character.name}/action/move", data)

    async def transition(self, character):
        return await self._post(f"my/{character.name}/action/transition")

    async def equip_stuff(self, character, stuff):
        return await self._post(f"my/{character.name}/action/equip", stuff)

    async def fight(self, character):
        return await self._post(f"my/{character.name}/action/fight")

    async def boss_fight(self, characters):
        data = {"participants": [characters[1], characters[2]]}
        return await self._post(f"my/{characters[0]}/action/fight", data)

    async def gather(self, character):
        return await self._post(f"my/{character.name}/action/gathering")
    
    async def rest(self, character):
        return await self._post(f"my/{character.name}/action/rest")

    async def craft(self, character, craftable, quantity):
        data = {
            "code": craftable,
            "quantity": quantity
        }
        return await self._post(f"my/{character.name}/action/crafting", data)

    async def recycle(self, character, item, quantity):
        data = {
            "code": item,
            "quantity": quantity,
            "enhanced": False
        }
        return await self._post(f"my/{character.name}/action/recycling", data)

    async def deposit(self, character):
        data = []
        for item in character.inventory:
            if item["code"] != "":
                data.append({"code": item["code"], "quantity": item["quantity"]})

        if character.gold > 0:
            gold = {
                "quantity": character.gold
            }

            await self._post(f"my/{character.name}/action/bank/deposit/gold", gold)
            await asyncio.sleep(3)

        return await self._post(f"my/{character.name}/action/bank/deposit/item", data)

    async def complete_task(self, character):
        return await self._post(f"my/{character.name}/action/task/complete")

    async def accept_task(self, character):
        return await self._post(f"my/{character.name}/action/task/new")
