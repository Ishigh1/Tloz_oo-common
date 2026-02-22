import itertools

from entrance_rando import randomize_entrances
from ...Options import OracleOfSeasonsPortalShuffle
from ...data.Constants import PORTAL_CONNECTIONS, OracleOfSeasonsConnectionType
from ..data.Constants import OraclesConnectionType


def list_entrances_for_patch(world, prefix: str, vanilla_entrances: dict[str, str]):
    """
    Lists Entrances for a game.

    Parameters:
        world: The world used for the listing
        prefix (str): A prefix that is used to search for entrances.
        vanilla_entrances (dict): A list of entrances that were part of the vanilla game.

    Returns:
        object: the listed entrances
    """
    seen_entrances = set()
    connections = {}
    for entrance1 in itertools.chain(vanilla_entrances, vanilla_entrances.values()):  # Do them in order overworld then subrosia
        if entrance1 in seen_entrances:
            continue
        seen_entrances.add(entrance1)
        entrance2 = world.get_entrance(f"{prefix}{entrance1}").connected_region.name
        seen_entrances.add(entrance2)
        connections[entrance1] = entrance2
    return connections


def oo_randomize_entrances(world) -> None:
    """
    Randomizes Entrances for a game.

    Parameters:
        world: The world used for the randomization
    """
    target_group_lookup = {}

    if world.seasons:
        target_group_lookup[OracleOfSeasonsConnectionType.CONNECT_PORTAL_OVERWORLD] = [OracleOfSeasonsConnectionType.CONNECT_PORTAL_SUBROSIA]
        target_group_lookup[OracleOfSeasonsConnectionType.CONNECT_PORTAL_SUBROSIA] = [OracleOfSeasonsConnectionType.CONNECT_PORTAL_OVERWORLD]

        if world.options.shuffle_portals == OracleOfSeasonsPortalShuffle.option_shuffle:
            target_group_lookup[OracleOfSeasonsConnectionType.CONNECT_PORTAL_OVERWORLD] \
                .append(OracleOfSeasonsConnectionType.CONNECT_PORTAL_OVERWORLD)
            target_group_lookup[OracleOfSeasonsConnectionType.CONNECT_PORTAL_SUBROSIA] \
                .append(OracleOfSeasonsConnectionType.CONNECT_PORTAL_SUBROSIA)
            
    target_group_lookup[OraclesConnectionType.CONNECT_DUNGEON_OVERWORLD] = [OraclesConnectionType.CONNECT_DUNGEON_INSIDE]
    target_group_lookup[OraclesConnectionType.CONNECT_DUNGEON_INSIDE] = [OraclesConnectionType.CONNECT_DUNGEON_OVERWORLD]

    placement_state = randomize_entrances(world, True, target_group_lookup)
    if world.seasons and world.options.shuffle_portals:
        world.portal_connections = list_entrances_for_patch(world, "enter ", PORTAL_CONNECTIONS)
    if world.options.shuffle_dungeons:
        world.dungeon_entrances = list_entrances_for_patch(world, "", world.dungeon_entrances)
