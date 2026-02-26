def get_filler_item_name(world) -> str:
    FILLER_ITEM_NAMES = [
        "Rupees (1)", "Rupees (5)", "Rupees (10)", "Rupees (10)",
        "Rupees (20)", "Rupees (30)",
        ("Ore Chunks (10)", "Ore Chunks (10)", "Ore Chunks (25)") if world.seasons else ""
        "Random Ring", "Random Ring", "Random Ring",
        "Gasha Seed", "Gasha Seed",
        "Potion"
    ]

    item_name = world.random.choice(FILLER_ITEM_NAMES)
    if item_name == "Random Ring":
        return get_random_ring_name(world)
    return item_name

def get_random_ring_name(world) -> str:
    if len(world.random_rings_pool) > 0:
        return world.random_rings_pool.pop()
    return get_filler_item_name(world)  # It might loop but not enough to really matter