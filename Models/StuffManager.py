async def get_best_possible_stuff(self):
    await get_best_possible_weapon(self)

async def get_best_possible_weapon(self):
    monster = (await self.api.find_monster(self.target))["data"]

    resistances = {
        "fire": monster["res_fire"],
        "earth": monster["res_earth"],
        "water": monster["res_water"],
        "air": monster["res_air"],
    }

    sorted_resistances = sorted(resistances.items(), key=lambda item: item[1])

    weapons = (await self.api.find_category_items("weaponcrafting", self.level - 20, self.level))["data"]

    sorted_weapons = []

    for element, resistance in sorted_resistances:

        wanted_weapons = [
            weapon
            for weapon in weapons
            if weapon["subtype"] == ""
               and any(
                effect["code"] == f"attack_{element}"
                for effect in weapon["effects"]
            )
        ]

        wanted_weapons.sort(
            key=lambda weapon: (
                weapon["level"],
                next(
                    effect["value"]
                    for effect in weapon["effects"]
                    if effect["code"] == f"attack_{element}"
                ),
            ),
            reverse=True,
        )

        if wanted_weapons:
            sorted_weapons.extend(weapon["code"] for weapon in wanted_weapons)

    print(sorted_weapons)
    print(len(sorted_weapons))