from BaseClasses import MultiWorld, Item, EntranceType
from rule_builder.rules import True_
from Options import Accessibility
from ..data.Constants import OraclesConnectionType
from ...data.Constants import *


def create_randomizable_connections(world, prefix: str,
                                    vanilla_connections: dict[str, str], outer_group: int, inner_group: int):
    """
    Creates randomizable conections for a game.

    Parameters:
        world: The world used for the listing
        prefix (str): A prefix that is used to create the connections.
        vanilla_connections (dict): A list of connections that were part of the vanilla game.
        outer_group (int): A group number for the outside connection entrance.
        inner_group (int): A group number for the inside connection exit.
    """
    for reg1, reg2 in vanilla_connections.items():
        region_1 = world.get_region(reg1)
        region_2 = world.get_region(reg2)

        entrance = region_1.create_exit(f"{prefix}{reg1}")
        entrance.randomization_group = outer_group
        entrance.randomization_type = EntranceType.TWO_WAY
        world.set_rule(entrance, True_())

        entrance = region_1.create_er_target(f"{prefix}{reg1}")
        entrance.randomization_group = outer_group
        entrance.randomization_type = EntranceType.TWO_WAY

        entrance = region_2.create_exit(f"{prefix}{reg2}")
        entrance.randomization_group = inner_group
        entrance.randomization_type = EntranceType.TWO_WAY
        world.set_rule(entrance, True_())

        entrance = region_2.create_er_target(f"{prefix}{reg2}")
        entrance.randomization_group = inner_group
        entrance.randomization_type = EntranceType.TWO_WAY


def create_connections(world, all_logic: list):
    """
    Creates connections for a game.

    Parameters:
        world: The world used for the listing
        all_logic (list): Logic that is taken into account for during game randomization.

    Returns:
        object: the listed entrances
    """

    if world.options.shuffle_dungeons:
        create_randomizable_connections(world, "", world.dungeon_entrances,
                                        OraclesConnectionType.CONNECT_DUNGEON_OVERWORLD,
                                        OraclesConnectionType.CONNECT_DUNGEON_INSIDE)
    else:
        dungeon_entrances = []
        for reg1, reg2 in world.dungeon_entrances.items():
            dungeon_entrances.append([reg1, reg2, True, None])
        all_logic.append(dungeon_entrances)

    if world.seasons:
        from ...data.Constants import OracleOfSeasonsConnectionType, PORTAL_CONNECTIONS
        if world.options.shuffle_portals:
            create_randomizable_connections(world, "enter ", PORTAL_CONNECTIONS,
                                        OracleOfSeasonsConnectionType.CONNECT_PORTAL_OVERWORLD,
                                        OracleOfSeasonsConnectionType.CONNECT_PORTAL_SUBROSIA)
        else:
            portal_connections = []
            for reg1, reg2 in PORTAL_CONNECTIONS.items():
                portal_connections.append([reg1, reg2, True, None])
            all_logic.append(portal_connections)

    true_rule = True_()
    # Create connections
    for logic_array in all_logic:
        for entrance_desc in logic_array:
            region_1 = world.get_region(entrance_desc[0])
            region_2 = world.get_region(entrance_desc[1])
            is_two_way = entrance_desc[2]
            rule = entrance_desc[3]
            if rule is None:
                rule = true_rule

            entrance = region_1.connect(region_2, None)
            world.set_rule(entrance, rule)
            if is_two_way:
                entrance = region_2.connect(region_1, None)
                world.set_rule(entrance, rule)


def apply_self_locking_rules(multiworld: MultiWorld, player: int, rules):
    """
    Applies self locking rules to a game if accessibility requirements are not set to full.

    Parameters:
        multiworld (Multiworld): A multiworld used to apply the rules.
        player (int): The player number.
        rules: Rules to follow. Example format is { "keys": {"Hero's Cave: Final Chest": lambda state, item: any([
            is_small_key(item, self.player, 0),
            is_item(item, self.player, f"Master Key ({DUNGEON_NAMES[0]})")
        ]) }, "OTHER_SELF_LOCKING_ITEMS": { "North Horon: Malon Trade": "Cuccodex" } 
    """
    world = multiworld.worlds[player]
    if world.options.accessibility == Accessibility.option_full:
        return

    # Process self-locking keys first
    for location_name, key_rule in rules["keys"].items():
        location = multiworld.get_location(location_name, player)
        location.always_allow = key_rule

    # Process other self-locking items
    OTHER_SELF_LOCKING_ITEMS = rules["OTHER_SELF_LOCKING_ITEMS"]
    if world.seasons and not world.options.secret_locations:
        OTHER_SELF_LOCKING_ITEMS["Goron Mountain: Biggoron Trade"] = "Lava Soup"

    for loc_name, item_name in OTHER_SELF_LOCKING_ITEMS.items():
        location = multiworld.get_location(loc_name, player)
        location.always_allow = make_self_locking_item_lambda(player, item_name)

    # Great Furnace special case
    if world.seasons:
        location = multiworld.get_location("Subrosia: Item Smelted in Great Furnace", player)
        location.always_allow = lambda state, item: (item.player == player and item.name in ["Red Ore", "Blue Ore"])


def is_small_key(item: Item, player: int, dungeon: int):
    """
    Does a checkup to ensure an item is a small key.

    Parameters:
        item (Item): A item to checkup on.
        player (int): The player number.
        dungeon (int): The number of a dungeon

    Returns:
        boolean: True if an item is a small key. False otherwise
    """
    return is_item(item, player, f"Small Key ({DUNGEON_NAMES[dungeon]})")


def is_item(item: Item, player: int, item_name: str):
    """
    Does a checkup to ensure an item is actually an item.

    Parameters:
        item (Item): A item to checkup on.
        player (int): The player number.
        item_name (str): The name of the item to checkup on.

    Returns:
        boolean: True if an item is an item. False otherwise
    """
    return item.player == player and item.name == item_name


def make_self_locking_item_lambda(player: int, item_name: str, required_count: int = 0):
    """
    Creates a self locking item using lambda.

    Parameters:
        player (int): The player number.
        item_name (str): The name of the item to create.
        required_count (int): The required count of items to create. Default is 0.

    Returns:
        lambda: Returns the created item using the lambda module
    """
    if required_count == 0:
        return lambda state, item: (item.player == player and item.name == item_name)

    return lambda state, item: (item.player == player
                                and item.name == item_name
                                and state.has(item_name, player, required_count))
