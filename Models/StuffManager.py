async def get_best_possible_stuff(character, skill=None):

    await character.rest()

    async with character.api.bank_lock:
        bank = await character.api.fetch_bank_items()

        if not skill:
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

            best_rings = await get_best_possible_rings(character, bank, best_weapon)
            best_artifacts = await get_best_possible_artifacts(character, bank, "fight")
            best_amulet = await get_best_possible_amulet(character, bank, best_weapon)

            if best_weapon["code"] == character.weapon_slot:
                best_weapon = None

        else:

            if skill in ["mining","woodcutting","fishing","alchemy"]:
                max_stat = "prospecting"
            else:
                max_stat = "wisdom"

            best_weapon = await get_best_possible_tool(character, "weapon", bank, skill)
            best_helmet = await get_best_possible_skill_armor_piece(character, "helmet", bank, max_stat)
            best_body_armor = await get_best_possible_skill_armor_piece(character, "body_armor", bank, max_stat)
            best_leg_armor = await get_best_possible_skill_armor_piece(character, "leg_armor", bank, max_stat)
            best_boots = await get_best_possible_skill_armor_piece(character, "boots", bank, max_stat)
            best_shield = None

            best_rings = await get_best_possible_skill_rings(character, bank, max_stat)
            best_artifacts = await get_best_possible_artifacts(character, bank, max_stat)
            best_amulet = await get_best_possible_skill_amulet(character, bank, max_stat)

        bank_withdraw_stuff = [
            (best_weapon, 1),
            (best_helmet, 1),
            (best_body_armor, 1),
            (best_leg_armor, 1),
            (best_boots, 1),
            (best_shield, 1),
            (best_rings[0], 2),
            (best_artifacts[0], 1),
            (best_artifacts[1], 1),
            (best_artifacts[2], 1),
            (best_amulet, 1)
        ]

        bank_withdraw = []

        for item, quantity in bank_withdraw_stuff:
            if item is not None:
                code = item["code"] if isinstance(item, dict) else item

                bank_withdraw.append({
                    "code": code,
                    "quantity": quantity
                })

        print(bank_withdraw)

        if len(bank_withdraw) > 0:
            await character.go_to_target("bank")
            if character.inventory[0]["code"] != "":
                await character.deposit()

            response = await character.api.get_items(character, bank_withdraw)
            await character._handle_response(response)

            best_possible_stuff = [
                (best_weapon, "weapon"),
                (best_helmet, "helmet"),
                (best_body_armor, "body_armor"),
                (best_leg_armor, "leg_armor"),
                (best_boots, "boots"),
                (best_shield, "shield"),
                (best_rings[0], "ring1"),
                (best_rings[1], "ring2"),
                (best_artifacts[0], "artifact1"),
                (best_artifacts[1], "artifact2"),
                (best_artifacts[2], "artifact3"),
                (best_amulet, "amulet")
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

            await character.equip_stuff(stuff)
            if character.inventory[0]["code"] != "":
                await character.deposit()

async def get_best_possible_tool(character, slot, bank, skill):

    if skill != "craft":

        tools = [
            item
            for item in character.api.items
            if item["type"] == "weapon"
               and item.get("subtype", "") == "tool"
               and item["level"] <= getattr(character, f"{skill}_level")
               and any(
                effect["code"] == skill
                for effect in item["effects"]
            )
        ]

        tools.sort(
            key=lambda tool: next(
                effect["value"]
                for effect in tool["effects"]
                if effect["code"] == skill
            )
        )
    else:
        tools = [
            item
            for item in character.api.items
            if item["type"] == "weapon"
               and item.get("code") == character.weapon_slot
        ]

    for tool in tools:
        if any(item["code"] == tool["code"] for item in bank) or tool["code"] == getattr(character, f"{slot}_slot"):
            print(tool)
            if tool["code"] == getattr(character, f"{slot}_slot"):
                return None
            return tool

    return None

async def get_best_possible_weapon(character, slot, bank, sorted_resistances):

    weapons = [
        item
        for item in character.api.items
        if item["type"] == "weapon"
           and item.get("subtype", "") == ""
           and item["level"] <= character.level
    ]

    wanted_weapons = []
    equipped_weapon = None

    for weapon in weapons:

        score = 0
        elements = []

        for effect in weapon["effects"]:
            if effect["code"].startswith("attack_"):

                for element, value in sorted_resistances:
                    if effect["code"] == f"attack_{element}":
                        score += effect["value"] * (100 - value) / 100
                        elements.append((element, effect["value"]))

            elif effect["code"] == "critical_strike":
                score += effect["value"]

        weapon_data = {
            "code": weapon["code"],
            "score": score,
            "elements": elements
        }

        wanted_weapons.append(weapon_data)

        if weapon["code"] == getattr(character, f"{slot}_slot"):
            equipped_weapon = weapon_data

    wanted_weapons.sort(
        key=lambda weapon: weapon["score"],
        reverse=True,
    )

    # print(sorted_weapons)
    # print(len(sorted_weapons))

    for weapon in wanted_weapons:
        if any(item["code"] == weapon["code"] for item in bank) or weapon["code"] == getattr(character, f"{slot}_slot"):
            print(f"Weapon code: {weapon}")
            return weapon

    return None


async def get_best_possible_armor_piece(character, slot, bank, best_weapon):

    armor_pieces = [
        item
        for item in character.api.items
        if item["type"] == slot
           and item.get("subtype", "") == ""
           and item["level"] <= character.level
    ]

    wanted_armor_pieces = []
    equipped_armor_piece = None

    for armor_piece in armor_pieces:

        score = 0

        for effect in armor_piece["effects"]:
            if effect["code"] == "hp":
                score += effect["value"]

            elif effect["code"].startswith("dmg"):

                for element, value in best_weapon["elements"]:
                    if effect["code"] in [f"dmg_{element}", "dmg"]:
                        score += effect["value"] * value/100

            elif effect["code"] == "critical_strike":
                score += effect["value"]


        armor_data = {
            "code": armor_piece["code"],
            "score": score,
        }

        wanted_armor_pieces.append(armor_data)

        if armor_piece["code"] == getattr(character, f"{slot}_slot"):
            equipped_armor_piece = armor_data

    wanted_armor_pieces.sort(
        key=lambda armor_piece: armor_piece["score"],
        reverse=True,
    )

    # print(sorted_armor_pieces)
    # print(len(sorted_armor_pieces))

    for armor_piece in wanted_armor_pieces:
        if any(item["code"] == armor_piece["code"] for item in bank) or armor_piece["code"] == equipped_armor_piece["code"]:
            print(armor_piece)
            if armor_piece["score"] == equipped_armor_piece["score"]:
                return None

            return armor_piece

    return None

async def get_best_possible_skill_armor_piece(character, slot, bank, max_stat):

    armor_pieces = [
        item
        for item in character.api.items
        if item["type"] == slot
           and item.get("subtype", "") == ""
           and item["level"] <= character.level
    ]

    wanted_armor_pieces = []
    equipped_armor_piece = None

    for armor_piece in armor_pieces:

        score = 0

        for effect in armor_piece["effects"]:
            if effect["code"] == max_stat:
                score += effect["value"]

        armor_data = {
            "code": armor_piece["code"],
            "score": score,
        }

        wanted_armor_pieces.append(armor_data)

        if armor_piece["code"] == getattr(character, f"{slot}_slot"):
            equipped_armor_piece = armor_data

    wanted_armor_pieces.sort(
        key=lambda armor_piece: armor_piece["score"],
        reverse=True,
    )

    # print(sorted_armor_pieces)
    # print(len(sorted_armor_pieces))

    for armor_piece in wanted_armor_pieces:
        if any(item["code"] == armor_piece["code"] for item in bank) or armor_piece["code"] == equipped_armor_piece["code"]:
            print(armor_piece)
            if armor_piece["score"] == equipped_armor_piece["score"]:
                return None

            return armor_piece

    return None


async def get_best_possible_shield(character, slot, bank, sorted_attacks):

    shields = [
        item
        for item in character.api.items
        if item["type"] == slot
           and item.get("subtype", "") == ""
           and item["level"] <= character.level
    ]

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
            # print(shield)
            if shield == getattr(character, f"{slot}_slot"):
                return None

            return shield

    return None

async def get_best_possible_rings(character, bank, best_weapon):

    rings = [
        item
        for item in character.api.items
        if item["type"] == "ring"
           and item.get("subtype", "") == ""
           and item["level"] <= character.level
    ]

    wanted_rings = []

    equipped_rings = []

    for ring in rings:

        score = 0

        for effect in ring["effects"]:
            if effect["code"] == "hp":
                score += effect["value"]

            elif effect["code"].startswith("dmg"):

                for element, value in best_weapon["elements"]:
                    if effect["code"] in [f"dmg_{element}", "dmg"]:
                        score += effect["value"] * value / 100

            elif effect["code"] == "critical_strike":
                score += effect["value"]

        ring_data = {
            "code": ring["code"],
            "score": score,
        }

        wanted_rings.append(ring_data)

        if ring["code"] == character.ring1_slot:
            equipped_rings.append(ring_data)

        if ring["code"] == character.ring2_slot:
            equipped_rings.append(ring_data)

    wanted_rings.sort(
        key=lambda ring: ring["score"],
        reverse=True,
    )

    # print(wanted_rings)
    # print(len(wanted_rings))

    for ring in wanted_rings:
        if any(item["code"] == ring["code"] for item in bank) or ring["code"] == character.ring1_slot:
            print(ring)
            if ring["score"] == equipped_rings[0]["score"]:
                return [None, None]

            return [ring, ring]

    return [None, None]

async def get_best_possible_skill_rings(character, bank, max_stat):

    rings = [
        item
        for item in character.api.items
        if item["type"] == "ring"
           and item.get("subtype", "") == ""
           and item["level"] <= character.level
    ]

    wanted_rings = []

    equipped_rings = []

    for ring in rings:

        score = 0

        for effect in ring["effects"]:
            if effect["code"] == max_stat:
                score += effect["value"]

        ring_data = {
            "code": ring["code"],
            "score": score,
        }

        wanted_rings.append(ring_data)

        if ring["code"] == character.ring1_slot:
            equipped_rings.append(ring_data)

        if ring["code"] == character.ring2_slot:
            equipped_rings.append(ring_data)

    wanted_rings.sort(
        key=lambda ring: ring["score"],
        reverse=True,
    )

    # print(wanted_rings)
    # print(len(wanted_rings))

    for ring in wanted_rings:
        if any(item["code"] == ring["code"] for item in bank) or ring["code"] == character.ring1_slot:
            print(ring)
            if ring["score"] == equipped_rings[0]["score"]:
                return [None, None]

            return [ring, ring]

    return [None, None]

async def get_best_possible_artifacts(character, bank, max_stat):

    artifacts = [
        item
        for item in character.api.items
        if item["type"] == "artifact"
           and item.get("subtype", "") == ""
           and item["level"] <= character.level
    ]

    wanted_artifacts = []

    for artifact in artifacts:

        score = 0

        if max_stat == "fight":

            for effect in artifact["effects"]:
                if effect["code"] == "hp":
                    score += effect["value"]

                elif effect["code"] == "dmg":
                    score += effect["value"] * 6

                elif effect["code"] == "critical_strike":
                    score += effect["value"]

        else:

            for effect in artifact["effects"]:
                if effect["code"] == max_stat:
                    score += effect["value"]

        wanted_artifacts.append({
            "code": artifact["code"],
            "score": score,
        })

    wanted_artifacts.sort(
        key=lambda ring: ring["score"],
        reverse=True,
    )

    # print(wanted_artifacts)
    # print(len(wanted_artifacts))

    results = ["empty", "empty", "empty"]

    equipped_artifacts = [
        character.artifact1_slot,
        character.artifact2_slot,
        character.artifact3_slot
    ]

    found_candidates = []

    for artifact in wanted_artifacts:
        if any(item["code"] == artifact["code"] for item in bank) or artifact["code"] in equipped_artifacts:
            found_candidates.append(artifact["code"])
        if len(found_candidates) >= 3:
            break

    print(f"Candidates: {found_candidates}")

    for i, artifact in enumerate(equipped_artifacts):
        if artifact in found_candidates:
            found_candidates.remove(artifact)
            results[i] = None

    for i, result in enumerate(results):
        if result == "empty":
            for artifact in found_candidates:
                found_candidates.remove(artifact)
                results[i] = artifact

    print(results)
    return results

async def get_best_possible_amulet(character, bank, best_weapon):

    amulets = [
        item
        for item in character.api.items
        if item["type"] == "amulet"
           and item.get("subtype", "") == ""
           and item["level"] <= character.level
    ]

    wanted_amulets = []
    equipped_amulet = None

    for amulet in amulets:

        score = 0

        for effect in amulet["effects"]:
            if effect["code"] == "hp":
                score += effect["value"]

            elif effect["code"].startswith("dmg"):

                for element, value in best_weapon["elements"]:
                    if effect["code"] in [f"dmg_{element}", "dmg"]:
                        score += effect["value"] * value / 100

            elif effect["code"] == "critical_strike":
                score += effect["value"]

        amulet_data = {
            "code": amulet["code"],
            "score": score,
        }

        wanted_amulets.append(amulet_data)

        if amulet["code"] == getattr(character,"amulet_slot"):
            equipped_amulet = amulet_data

    wanted_amulets.sort(
        key=lambda amulet: amulet["score"],
        reverse=True,
    )

    # print(wanted_amulets)
    # print(len(wanted_amulets))

    for amulet in wanted_amulets:
        if any(item["code"] == amulet["code"] for item in bank) or amulet["code"] == equipped_amulet["code"]:
            print(amulet)
            if amulet["score"] == equipped_amulet["score"]:
                return None

            return amulet

    return None


async def get_best_possible_skill_amulet(character, bank, max_stat):

    amulets = [
        item
        for item in character.api.items
        if item["type"] == "amulet"
           and item.get("subtype", "") == ""
           and item["level"] <= character.level
    ]

    wanted_amulets = []
    equipped_amulet = None

    for amulet in amulets:

        score = 0

        for effect in amulet["effects"]:
            if effect["code"] == max_stat:
                score += effect["value"]

        amulet_data = {
            "code": amulet["code"],
            "score": score,
        }

        wanted_amulets.append(amulet_data)

        if amulet["code"] == getattr(character, "amulet_slot"):
            equipped_amulet = amulet_data

    wanted_amulets.sort(
        key=lambda amulet: amulet["score"],
        reverse=True,
    )

    # print(wanted_amulets)
    # print(len(wanted_amulets))

    for amulet in wanted_amulets:
        if any(item["code"] == amulet["code"] for item in bank) or amulet["code"] == equipped_amulet["code"]:
            print(amulet)
            if amulet["score"] == equipped_amulet["score"]:
                return None

            return amulet

    return None