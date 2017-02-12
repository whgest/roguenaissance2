import RN2_loadmap
import random
import time
import logging
import RN2_AI
import itertools


def add_points(coord, change):
    return tuple(sum(x) for x in zip(coord, change))


def get_neighboring_points(point):
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    return [add_points(point, n) for n in neighbors]


def calculate_affected_area(origin, caster_loc, skill, bmap):
    all_tiles = set()
    edge_tiles = [origin]

    for a in range(skill.aoe):
        all_tiles, new_tiles = skill.get_next_aoe_range(all_tiles, edge_tiles, caster_loc)
        all_tiles.update(edge_tiles)
        edge_tiles = []
        for t in new_tiles:
            if bmap.check_bounds(t) and bmap.get_tile_at(t).is_targetable():
                edge_tiles.append(t)
        if not edge_tiles:
            break

    try:
        all_tiles.update(edge_tiles)
    except TypeError:
        print all_tiles, edge_tiles
        exit()

    return list(all_tiles)


def get_adjusted_mp(mp, friendlies):
    #pending summon tracking refactor
    num_summons = len(friendlies) - 1
    return mp if mp > -1 else 1 + (num_summons * 2)