import logging

from BaseClasses import Item, ItemClassification
from ..Options import OraclesShopPrices, OraclesMasterKeys, OraclesLogicDifficulty
from ...data import LOCATIONS_DATA, ITEMS_DATA
from ...data.Constants import ITEM_GROUPS, DUNGEON_NAMES
from ..data.Constants import VALID_RUPEE_ITEM_VALUES, SEED_ITEMS


def create_item(world, name) -> Item:
    """
    Creates an item for game using logic and Archipelago's Item function.

    Parameters:
        world: The world that is being used for Item Creation.
        name (str): The name of the item that is being created.

    Returns:
        Item: Archipelago's Item Function that returns it's details about an item.
    """
    # If item name has a "!PROG" suffix, force it to be progression. This is typically used to create the right
    # amount of progression rupees while keeping them a filler item as default
    if name.endswith("!PROG"):
        name = name.removesuffix("!PROG")
        classification = ItemClassification.progression_deprioritized_skip_balancing
    elif name.endswith("!USEFUL"):
        # Same for above but with useful. This is typically used for Required Rings,
        # as we don't want those locked in a barren dungeon
        name = name.removesuffix("!USEFUL")
        classification = ITEMS_DATA[name]["classification"]
        if classification == ItemClassification.filler:
            classification = ItemClassification.useful
    elif name.endswith("!FILLER"):
        name = name.removesuffix("!FILLER")
        classification = ItemClassification.filler
    else:
        classification = ITEMS_DATA[name]["classification"]
    ap_code = world.item_name_to_id[name]

    # A few items become progression only in hard logic
    progression_items_in_medium_logic = ["Expert's Ring", "Fist Ring", "Swimmer's Ring", "Energy Ring", "Heart Ring L-2"]
    if world.options.logic_difficulty >= OraclesLogicDifficulty.option_medium and name in progression_items_in_medium_logic:
        classification = ItemClassification.progression
    if world.options.logic_difficulty >= OraclesLogicDifficulty.option_hard and name == "Heart Ring L-1":
        classification = ItemClassification.progression
    # As many Gasha Seeds become progression as the number of deterministic Gasha Nuts
    if world.remaining_progressive_gasha_seeds > 0 and name == "Gasha Seed":
        world.remaining_progressive_gasha_seeds -= 1
        classification = ItemClassification.progression_deprioritized

    # Players in Medium+ are expected to know the default paths through Lost Woods, Phonograph becomes filler
    if world.seasons and world.options.logic_difficulty >= OraclesLogicDifficulty.option_medium and not world.options.randomize_lost_woods_item_sequence and name == "Phonograph":
        classification = ItemClassification.filler

    # UT doesn't let us know if the item is progression or not, so it is always progression
    if hasattr(world.multiworld, "generation_is_fake"):
        classification = ItemClassification.progression

    return Item(name, classification, ap_code, world.player)


def build_rupee_item_dict(world, rupee_item_count: int, filler_item_count: int) -> tuple[dict[str, int], int]:
    """
    Builds a rupee pool for a game

    Parameters:
        world: The world that is being used for the building.
        rupee_item_count (int): The amount of rupees that are being filled.
        filler_item_count (int): Junk items being added to the mix

    Returns:
        dict: The fully built rupee pool using the build_currency_item_dict function.
    """
    sorted_shop_values = sorted(world.shop_rupee_requirements.values())
    total_cost = sorted_shop_values[-1]

    # Count the old man's contribution, it's especially important as it may be negative
    # (We ignore dungeons here because we don't want to worry about whether they'll be available)
    # TODO : With GER that note will be obsolete
    environment_rupee = 0
    for name in world.old_man_rupee_values:
        environment_rupee += world.old_man_rupee_values[name]

    target = total_cost / 2 - environment_rupee
    total_cost = max(total_cost - environment_rupee, sorted_shop_values[-3])  # Ensure it doesn't drop too low due to the old men
    return build_currency_item_dict(world, rupee_item_count, filler_item_count, target, total_cost, "Rupees", VALID_RUPEE_ITEM_VALUES)


def build_ore_item_dict(world, ore_item_count: int, filler_item_count: int) -> tuple[dict[str, int], int]:
    """
    Builds an ore pool for a seasons based game

    Parameters:
        world: The world that is being used for the building.
        ore_item_count (int): The amount of ore chunks that are being filled.
        filler_item_count (int): Junk items being added to the mix

    Returns:
        dict: The fully built ore pool using the build_currency_item_dict function.
    """
    from ...data.Constants import MARKET_LOCATIONS, VALID_ORE_ITEM_VALUES
    total_cost = sum([world.shop_prices[loc] for loc in MARKET_LOCATIONS])
    target = total_cost / 2

    return build_currency_item_dict(world, ore_item_count, filler_item_count, target, total_cost, "Ore Chunks", VALID_ORE_ITEM_VALUES)


def build_currency_item_dict(world, currency_item_count: int, filler_item_count: int, initial_target,
                             total_cost: int, currency_name: str, valid_currency_item_values: list[int]) -> tuple[dict[str, int], int]:
    """
    Builds a currency pool for a game

    Parameters:
        world: The world that is being used for Item Creation.
        currency_item_count (str): Money that is being added to the pool
        filler_item_count (int): Junk items being added to the mix
        initial_target (int): The target that the builder is heading for.
        total_cost (int): The cost of the build.
        currency_name (str): The name of the currency that is being built.
        valid_currency_item_values (list[int]): Vaslues that are being used for the build.

    Returns:
        Dict: The fully built currency pool.
    """
    average_value = total_cost / currency_item_count
    deviation = average_value / 2.5
    currency_item_dict = {}
    target = initial_target
    for i in range(0, currency_item_count):
        value = world.random.gauss(average_value, deviation)
        value = min(valid_currency_item_values, key=lambda x: abs(x - value))
        if value > average_value / 3:
            # Put a "!PROG" suffix to force them to be created as progression items (see `create_item`)
            item_name = f"{currency_name} ({value})!PROG"
            target -= value
        else:
            # Don't count little packs as progression since they are likely irrelevant
            item_name = f"{currency_name} ({value})"
        currency_item_dict[item_name] = currency_item_dict.get(item_name, 0) + 1
    # If the target is positive, it means there aren't enough rupees, so we'll steal a filler from the pool and reroll
    if target > 0:
        return build_currency_item_dict(world, currency_item_count + 1, filler_item_count - 1, initial_target,
                                        total_cost, currency_name, valid_currency_item_values)
    return currency_item_dict, filler_item_count


def filter_confined_dungeon_items_from_pool(world, items: list[Item]) -> None:
    """
    Filters confined dungeon items for a game.

    Parameters:
        world: The world that is being used for the filtering.
        items (list[Item]): Items that are being filtered.
    """
    confined_dungeon_items = []
    excluded_dungeons = []
    if world.options.exclude_dungeons_without_essence and not world.options.shuffle_essences:
        for i, essence_name in enumerate(ITEM_GROUPS["Essences"]):
            if essence_name not in world.essences_in_game:
                excluded_dungeons.append(i + 1)

    # Put Small Keys / Master Keys unless keysanity is enabled for those
    if world.options.master_keys != OraclesMasterKeys.option_disabled:
        small_keys_name = "Master Key"
    else:
        small_keys_name = "Small Key"
    if not world.options.keysanity_small_keys:
        confined_dungeon_items.extend([item for item in items if item.name.startswith(small_keys_name)])
    else:
        for i in excluded_dungeons:
            confined_dungeon_items.extend([item for item in items if item.name == f"{small_keys_name} ({DUNGEON_NAMES[i]})"])

    # Put Boss Keys unless keysanity is enabled for those
    if not world.options.keysanity_boss_keys:
        confined_dungeon_items.extend([item for item in items if item.name.startswith("Boss Key")])
    else:
        for i in excluded_dungeons:
            confined_dungeon_items.extend([item for item in items if item.name == f"Boss Key ({DUNGEON_NAMES[i]})"])

    # Put Maps & Compasses unless keysanity is enabled for those
    if not world.options.keysanity_maps_compasses:
        confined_dungeon_items.extend([item for item in items if item.name.startswith("Dungeon Map")
                                       or item.name.startswith("Compass")])

    for item in confined_dungeon_items:
        items.remove(item)
    world.pre_fill_items.extend(confined_dungeon_items)
