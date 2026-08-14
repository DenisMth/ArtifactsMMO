async def get_best_possible_stuff(character):

    bank = await character.api.fetch_bank_items()

    monster = (await character.api.find_monster(character.target))["data"]

    resistances = {
        "fire": monster["res_fire"],
        "earth": monster["res_earth"],
        "water": monster["res_water"],
        "air": monster["res_air"],
    }

    sorted_resistances = sorted(resistances.items(), key=lambda item: item[1])

    attacks = {
        "fire": monster["attack_fire"],
        "earth": monster["attack_earth"],
        "water": monster["attack_water"],
        "air": monster["attack_air"],
    }

    sorted_attacks = sorted(attacks.items(), key=lambda item: item[1])

    best_weapon = await get_best_possible_weapon(character, "weapon", bank, sorted_resistances)
    best_helmet = await get_best_possible_armor_piece(character,"helmet", bank, best_weapon)
    best_body_armor = await get_best_possible_armor_piece(character, "body_armor", bank, best_weapon)
    best_leg_armor = await get_best_possible_armor_piece(character, "leg_armor", bank, best_weapon)
    best_boots = await get_best_possible_armor_piece(character, "boots", bank, best_weapon)
    best_shield = await get_best_possible_shield(character, "shield", bank, sorted_attacks)

    if best_weapon["code"] == character.weapon_slot:
        best_weapon = None

    best_possible_stuff = [
        (best_weapon, "weapon"),
        (best_helmet, "helmet"),
        (best_body_armor, "body_armor"),
        (best_leg_armor, "leg_armor"),
        (best_boots, "boots"),
        (best_shield, "shield"),
    ]

    stuff = []

    for stuff_element, slot in best_possible_stuff:
        if stuff_element is not None:
            code = stuff_element["code"] if isinstance(stuff_element, dict) else stuff_element

            stuff.append({
                "code": code,
                "slot": slot,
                "quantity": 1
            })

    print(stuff)

    response = await character.equip_stuff(stuff)

async def get_best_possible_weapon(character, slot, bank, sorted_resistances):

    weapons = (await character.api.find_category_items("weaponcrafting", "weapon", character.level - 20, character.level))["data"]

    sorted_weapons = []

    seen_weapons = set()

    for element, resistance in sorted_resistances:

        wanted_weapons = [
            weapon
            for weapon in weapons
            if weapon["subtype"] == ""
            and weapon["code"] not in seen_weapons
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

            for weapon in wanted_weapons:
                seen_weapons.add(weapon["code"])

                weapon_elements = sorted(
                    [
                        (
                            effect["code"].replace("attack_", ""),
                            effect["value"],
                        )
                        for effect in weapon["effects"]
                        if effect["code"].startswith("attack_")
                           and effect["value"] > 0
                    ],
                    key=lambda x: x[1],
                    reverse=True,
                )

                sorted_weapons.append({
                    "code": weapon["code"],
                    "elements": weapon_elements,
                })

    # print(sorted_weapons)
    # print(len(sorted_weapons))

    for weapon in sorted_weapons:
        if any(item["code"] == weapon["code"] for item in bank) or weapon["code"] == getattr(character, f"{slot}_slot"):
            print(weapon)
            return weapon

    return None


async def get_best_possible_armor_piece(character, slot, bank, best_weapon):

    armor_pieces = (await character.api.find_category_items("gearcrafting", slot, character.level - 20, character.level))["data"]

    sorted_armor_pieces = []

    seen_armor_pieces = set()

    for element, value in best_weapon["elements"]:

        wanted_armor_pieces = [
            armor_piece
            for armor_piece in armor_pieces
            if armor_piece["code"] not in seen_armor_pieces
            and any(
                effect["code"] in [f"dmg_{element}", "dmg"]
                for effect in armor_piece["effects"]
            )
        ]

        wanted_armor_pieces.sort(
            key=lambda armor_piece: (
                armor_piece["level"],
                next(
                    effect["value"]
                    for effect in armor_piece["effects"]
                    if effect["code"] in [f"dmg_{element}", "dmg"]
                ),
            ),
            reverse=True,
        )

        if wanted_armor_pieces:
            for armor_piece in wanted_armor_pieces:
                seen_armor_pieces.add(armor_piece["code"])
                sorted_armor_pieces.append(armor_piece["code"])


    # print(sorted_armor_pieces)
    # print(len(sorted_armor_pieces))

    for armor_piece in sorted_armor_pieces:
        if any(item["code"] == armor_piece for item in bank) or armor_piece == getattr(character, f"{slot}_slot"):
            print(armor_piece)
            if armor_piece == getattr(character, f"{slot}_slot"):
                return None

            return armor_piece

    return None

async def get_best_possible_shield(character, slot, bank, sorted_attacks):

    shields = (await character.api.find_category_items("gearcrafting", slot, character.level - 20, character.level))["data"]

    sorted_shields = []

    seen_shields = set()

    for element, value in sorted_attacks:

        wanted_shields = [
            shield
            for shield in shields
            if shield["code"] not in seen_shields
            and any(
                effect["code"] == f"res_{element}"
                for effect in shield["effects"]
            )
        ]

        wanted_shields.sort(
            key=lambda shield: (
                shield["level"],
                next(
                    effect["value"]
                    for effect in shield["effects"]
                    if effect["code"] == f"res_{element}"
                ),
            ),
            reverse=True,
        )

        if wanted_shields:
            for shield in wanted_shields:
                seen_shields.add(shield["code"])
                sorted_shields.append(shield["code"])


    # print(sorted_shields)
    # print(len(sorted_shields))

    for shield in sorted_shields:
        if any(item["code"] == shield for item in bank) or shield == getattr(character, f"{slot}_slot"):
            print(shield)
            if shield == getattr(character, f"{slot}_slot"):
                return None

            return shield

    return None