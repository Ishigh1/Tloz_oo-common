def fill_slot_data(world, user_slot_data) -> dict:
    slot_data = {
        "version": f"{world.version()}",
        "old_man_rupee_values": world.old_man_rupee_values,
        "dungeon_entrances": {a.replace(" entrance", ""): b.replace("enter ", "") for a, b in world.dungeon_entrances.items()},
        "essences_in_game": world.essences_in_game,
        "shop_rupee_requirements": world.shop_rupee_requirements,
        "shop_costs": world.shop_prices,
    }
    for property, value in user_slot_data.items():
        slot_data[property] = value

    world.made_hints.wait()
    # The structure is made to make it easy to call CreateHints
    slot_data_item_hints = []
    for item_hint in world.item_hints:
        if item_hint is None:
            # Joke hint
            slot_data_item_hints.append(None)
            continue
        location = item_hint.location
        slot_data_item_hints.append((location.address, location.player))
    slot_data["item_hints"] = slot_data_item_hints

    return slot_data