import asyncio
import json
from pathlib import Path
from tkinter.constants import ROUND

from api import API


class Character:
    def __init__(self, api, data) -> None:
        self.api = api
        self.update(data)

        self.action = "idle"
        self.target = None
        self.target_coords = None
        self.on_target = False
        self.min_hp_needed = self.max_hp

    def set_action(self, action, target, characters = None):
        print(f"{self.name}: action changed from {self.action} {self.target} to {action} {target}")
        self.action = action
        self.target = target
        self.characters = characters
        self.target_coords = None
        self.on_target = False

    async def _handle_response(self, response):
        await asyncio.sleep(response["data"]["cooldown"]["total_seconds"])
        if "character" in response["data"]:
            self.update(response["data"]["character"])
        elif "characters" in response["data"]:
            self.update(response["data"]["characters"][0])

    def is_on_map_tile(self, response):
        if response["x"] == self.x and response["y"] == self.y and response["layer"] == self.layer:
           return True
        else:
            return False

    async def fight_hp_needed(self):
        monster = (await self.api.find_monster(self.target))["data"]

        char_fire = round(round(self.attack_fire * (1 + (self.dmg + self.dmg_fire)/100)) * (1 - monster["res_fire"]/100))
        char_earth = round(round(self.attack_earth * (1 + (self.dmg + self.dmg_earth)/100)) * (1 - monster["res_earth"]/100))
        char_water = round(round(self.attack_water * (1 + (self.dmg + self.dmg_water) / 100)) * (1 - monster["res_water"]/100))
        char_air = round(round(self.attack_air * (1 + (self.dmg + self.dmg_air) / 100)) * (1 - monster["res_air"]/100))

        char_dmg = char_fire + char_earth + char_water + char_air

        monster_fire = round(round(monster["attack_fire"]) * (1 - self.res_fire/100))
        monster_earth = round(round(monster["attack_earth"]) * (1- self.res_earth/100))
        monster_water = round(round(monster["attack_water"]) * (1 - self.res_water/100))
        monster_air = round(round(monster["attack_air"]) * (1 - self.res_air/100))

        monster_dmg = monster_fire + monster_earth + monster_water + monster_air

        rounds = 0
        char_health = self.max_hp
        monster_health = monster["hp"]
        burn_dot = 0

        for effect in self.effects:
            if effect["code"] == "burn":
                burn_dot = (effect["value"] * char_dmg) //100

        while rounds < 100 and char_health > 1:
            rounds += 1
            monster_health -= round(char_dmg * (1 + (0.5 * (self.critical_strike/100)) )) + burn_dot
            char_health -= round(monster_dmg * (1 + (0.5 * (monster["critical_strike"]/100))))

            burn_dot -= max(burn_dot//10, 1)

            if monster_health <= 0:
                return self.max_hp - char_health

        return -1

    async def get_best_possible_stuff(self):

        monster = (await self.api.find_monster(self.target))["data"]

        resistances = {
            "fire": monster["res_fire"],
            "earth": monster["res_earth"],
            "water": monster["res_water"],
            "air": monster["res_air"],
        }

        sorted_resistances = sorted(resistances.items(), key=lambda item: item[1])

        weapons = (await self.api.find_category_items("weaponcrafting", 1, self.level))["data"]

        sorted_weapons = []

        for best_element, _ in sorted_resistances:

            wanted_weapons = [
                weapon
                for weapon in weapons
                if weapon["subtype"] == ""
                   and any(
                    effect["code"] == f"attack_{best_element}"
                    for effect in weapon["effects"]
                )
            ]

            wanted_weapons.sort(
                key=lambda weapon: (
                    next(
                        effect["value"]
                        for effect in weapon["effects"]
                        if effect["code"] == f"attack_{best_element}"
                    ),
                    weapon["level"],
                ),
                reverse=True,
            )

            sorted_weapons.extend(weapon["code"] for weapon in wanted_weapons)

        print(sorted_weapons)



    async def go_to_target(self, target=None):

        if not target:
            target = self.target

        corresponding_tile = await self.api.find_map_tile(self, target)

        if self.is_on_map_tile(corresponding_tile):
            self.on_target = True
            self.target_coords = [self.x, self.y]
        else:

            if corresponding_tile["layer"] != self.layer:

                if self.layer in ["interior", "underground"]:
                    transition_x = self.x
                    transition_y = self.y
                else:
                    transition_x = corresponding_tile["x"]
                    transition_y = corresponding_tile["y"]

                closest_transition = await self.api.find_closest_transition(transition_x, transition_y, self.layer, corresponding_tile["layer"])
                if self.x != closest_transition["x"] or self.y != closest_transition["y"]:
                    await self.move(closest_transition["x"], closest_transition["y"])
                await self.transition()

            self.target_coords = [corresponding_tile["x"], corresponding_tile["y"]]
            if self.is_on_map_tile(corresponding_tile):
                self.on_target = True
            else:
                await self.move(self.target_coords[0], self.target_coords[1])

    async def boss_fight(self, characters):

        if self.hp < 200:
            await self.rest()

        response = await self.api.boss_fight(characters)
        await self._handle_response(response)


    async def fight(self):

        if self.target_coords is not None:
            if self.x != self.target_coords[0] or self.y != self.target_coords[1]:
                self.on_target = False

        if not self.on_target:
            if self.target == "task" and self.task_type == "monsters":
                self.target = self.task

            # await self.get_best_possible_stuff()

            self.min_hp_needed = await self.fight_hp_needed()
            if self.min_hp_needed < 0:
                self.set_action("fight", "chicken")

            await self.go_to_target()

        if self.hp < self.min_hp_needed:
            await self.rest()

        response = await self.api.fight(self)
        await self._handle_response(response)

        if self.task_type == "monsters":
            if self.task_progress == self.task_total:
                await self.move(1, 2)
                await self.complete_task()
                await self.accept_task()
                self.set_action("fight", "task")

    async def rest(self):
        response = await self.api.rest(self)
        await self._handle_response(response)

    async def gather(self):

        if not self.on_target:
            await self.go_to_target()

        response = await self.api.gather(self)
        await self._handle_response(response)

    async def gatheraft(self):

        main_target = self.target
        craft_elements = await self.api.find_craft_elements(self.target)

        nb_items_needed = 0

        for craft_element in craft_elements["data"]["craft"]["items"]:
            nb_items_needed += craft_element["quantity"]

        craftable_items = (self.inventory_max_items - 30) // nb_items_needed

        for craft_element in craft_elements["data"]["craft"]["items"]:
            resource = await self.api.find_resource(craft_element["code"])
            self.target = resource["data"][0]["code"]
            self.on_target = False
            amount = 0

            while amount < (craft_element["quantity"] * craftable_items):
                await self.gather()

                for item in self.inventory:
                    if item["code"] == craft_element["code"]:
                        amount = item["quantity"]

        workshop = await self.api.find_workshop(craft_elements["data"]["craft"]["skill"])
        await self.go_to_target(workshop["interactions"]["content"]["code"])
        await self.craft(craft_elements["data"]["code"], craftable_items - 1)
        self.target = main_target

    async def craft_from_bank(self, quantity=-1):
        # main_target = self.target
        craft_elements = await self.api.find_craft_elements(self.target)

        nb_items_needed = 0

        for craft_element in craft_elements["data"]["craft"]["items"]:
            nb_items_needed += craft_element["quantity"]

        if quantity == -1:
            craftable_items = (self.inventory_max_items) // nb_items_needed
        else :
            craftable_items = quantity

        await self.go_to_target("bank")
        if self.inventory[0]["code"] != "":
            await self.deposit()

        resources = []

        for craft_element in craft_elements["data"]["craft"]["items"]:

            withdraw_item = {
                "code": craft_element["code"],
                "quantity": craft_element["quantity"] * craftable_items,
            }
            resources.append(withdraw_item)

        response = await self.api.get_items(self, resources)
        await self._handle_response(response)
        workshop = await self.api.find_workshop(craft_elements["data"]["craft"]["skill"])
        await self.go_to_target(workshop["interactions"]["content"]["code"])
        await self.craft(craft_elements["data"]["code"], craftable_items)
        return craftable_items


    async def craftcyle(self):
        crafted_items = await self.craft_from_bank()
        await self.recycle(self.target, crafted_items)
        await self.go_to_target("bank")
        await self.deposit()

    async def craftstock(self, quantity=-1):
        crafted_items = await self.craft_from_bank(quantity)
        await self.go_to_target("bank")
        await self.deposit()

    async def move(self, x, y):
        response = await self.api.move(self, x, y)
        await self._handle_response(response)

    async def transition(self):
        response = await self.api.transition(self)
        await self._handle_response(response)

    async def craft(self, craftable, quantity=-1):
        response = await self.api.craft(self, craftable, quantity)
        await self._handle_response(response)

    async def recycle(self, item, quantity):
        response = await self.api.recycle(self, item, quantity)
        await self._handle_response(response)

    async def deposit(self):
        response = await self.api.deposit(self)
        await self._handle_response(response)

    async def complete_task(self):
        response = await self.api.complete_task(self)
        await self._handle_response(response)

    async def accept_task(self):
        response = await self.api.accept_task(self)
        await self._handle_response(response)

    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)

        self.save()

    def save(self):
        data = {
            key: value
            for key, value in self.__dict__.items()
            if key not in {"api", "action", "target"}
        }

        Path("data/characters").mkdir(exist_ok=True)

        with open(f"data/characters/{self.name}.json", "w") as f:
            json.dump(data, f, indent=4)

    async def run(self):

        while True:

            try:

                if self.action in ["idle", "i"]:
                    await asyncio.sleep(1)

                elif self.action in ["fight", "f"]:
                    await self.fight()

                elif self.action in ["bossfight", "bf"]:
                    await self.boss_fight(self.characters)

                elif self.action in ["gather", "g"]:
                    await self.gather()

                elif self.action in ["gatheraft", "gc"]:

                    if self.inventory[0]["code"] != "":
                        if self.x != 4 or self.y != 1:
                            await self.go_to_target("bank")
                        await self.deposit()
                    await self.gatheraft()

                elif self.action in ["craft", "c"]:
                    await self.craftstock(1)
                    self.set_action("idle", "test")

                elif self.action in ["craftmass", "cm"]:
                    await self.craftstock()

                elif self.action in ["craftcycle", "cc"]:
                    await self.craftcyle()

                elif self.action in ["assemble", "a"]:
                    if self.x != 4 or self.y != 1:
                        await self.go_to_target("spawn_bank")
                    await self.deposit()

                items_count = 0
                for item in self.inventory:
                    items_count += item["quantity"]

                if items_count == self.inventory_max_items:
                    await self.go_to_target("bank")
                    await self.deposit()
                    self.on_target = False

            except Exception as e:
                import traceback
                traceback.print_exc()
                await asyncio.sleep(2)