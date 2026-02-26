from BaseClasses import MultiWorld, Item


def order_pool(multiworld: MultiWorld, progitempool: list[Item], game: str):
    """
    Creates an ordering pool for a game.

    Parameters:
        multiworld (MultiWorld): A mutiworld that is used for creating the pool.
        progitempool (list[Item]): A progressive item pool
        game (str): The name of the game
    """
    players = multiworld.get_game_players(game)
    if not players:
        return
    weight_dict = {}
    for player in players:
        possible_items = [["Flippers", "Bush Breaker"], ["Power Bracelet"]]
        bush_breakers = [["Progressive Sword"], ["Biggoron's Sword"]]
        world = multiworld.worlds[player]

        if world.seasons:
            from ...data.Constants import SEASON_WINTER
            portal_connections = {world.portal_connections[key]: key for key in world.portal_connections}
            portal_connections.update(world.portal_connections)

            bad_portals = {"spool swamp portal", "horon village portal", "eyeglass lake portal", "temple remains lower portal", "d8 entrance portal"}
            if portal_connections["temple remains lower portal"] in bad_portals:
                bad_portals.add("temple remains upper portal")

            if multiworld.random.random() < 0.5:
                if portal_connections["horon village portal"] not in bad_portals:
                    possible_items.append(["Progressive Boomerang", "Progressive Boomerang"])
                else:
                    bush_breakers.append(["Progressive Boomerang", "Progressive Boomerang"])

            if portal_connections["eyeglass lake portal"] not in bad_portals and world.options.default_seed == "pegasus":
                items = ["Progressive Feather", "Progressive Feather", "Seed Satchel", "Bush Breaker"]
                if world.default_seasons["EYEGLASS_LAKE"] != SEASON_WINTER:
                    items.append("Rod of Seasons (Winter)")
                possible_items.append(items)

        seed_shooter = "Progressive Slingshot" if world.seasons else "Seed Shooter"
        seed_shooter_cross_items = "Progressive Slingshot" if world.ages else "Seed Shooter"

        if world.options.default_seed == "ember":
            possible_items.append(["Seed Satchel"])
            possible_items.append([seed_shooter])
            if world.options.cross_items:
                possible_items.append([seed_shooter_cross_items])

        if world.options.animal_companion == "dimitri":
            possible_items.append(["Dimitri's Flute"])
        elif world.options.animal_companion == "ricky":
            bush_breakers.append(["Ricky's Flute"])
        else:
            bush_breakers.append(["Moosh's Flute"])

        if world.seasons:
            if not world.options.remove_d0_alt_entrance:
                if world.dungeon_entrances["d2 entrance"] == "enter d0" \
                        or world.dungeon_entrances["d5 entrance"] == "enter d0" \
                        or world.dungeon_entrances["d7 entrance"] == "enter d0" \
                        or (world.dungeon_entrances["d8 entrance"] == "enter d0" and portal_connections["d8 entrance portal"] not in bad_portals):
                    possible_items.append(["Bush Breaker"])

        if world.options.logic_difficulty > 0:
            if multiworld.random.random() < 0.5:
                bush_breakers.append(["Bombs (10)", "Bombs (10)"])
            if world.options.default_seed == "gale":
                bush_breakers.append([seed_shooter])
                if world.options.cross_items:
                    bush_breakers.append([seed_shooter_cross_items])

        if world.ages or (world.options.cross_items and world.seasons):
            bush_breakers.append(["Switch Hook"])

        items = multiworld.random.choice(possible_items)
        if "Bush Breaker" in items:
            items.remove("Bush Breaker")
            items.extend(multiworld.random.choice(bush_breakers))
        for item in multiworld.precollected_items[player]:
            if item.name in items:
                items.remove(item.name)
        weight_dict[player] = items

    indexes = {player: [] for player in players}
    for i in range(len(progitempool)):
        item = progitempool[i]
        player = item.player
        if player not in players:
            continue

        if len(indexes[player]) < len(weight_dict[player]):
            indexes[player].append(i)
        if item.name not in weight_dict[player]:
            continue
        other_index = indexes[player].pop()
        progitempool[i], progitempool[other_index] = progitempool[other_index], progitempool[i]
        weight_dict[player].remove(item.name)
        for player in players:
            if len(weight_dict[player]) > 0:
                break
        else:
            break