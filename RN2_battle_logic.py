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

    # if skill.name == "Meteor":
    #     ui.highlight_area(True, all_tiles, bmap, color="red")
    #     time.sleep(1)


    for a in range(skill.aoe_size):
        all_tiles, new_tiles = skill.aoe.get_next_aoe_range(all_tiles, edge_tiles, caster_loc)
        all_tiles.update(edge_tiles)
        edge_tiles = []
        for t in new_tiles:
            if bmap.check_bounds(t) and bmap.get_tile_at(t).is_targetable():
                edge_tiles.append(t)
        if not edge_tiles:
            break

    try:
        all_tiles.update(edge_tiles)
        # if skill.name == "Meteor":
        #     ui.highlight_area(True, all_tiles, bmap, color="red")
        #     time.sleep(1)
    except TypeError:
        print all_tiles, edge_tiles
        exit()

    #ui.highlight_area(False, all_tiles, bmap)
    return list(all_tiles)


# def calculate_move_range(unit, bmap):
#     move_range = unit.move
#     origin = tuple(unit.coords)
#     all_tiles = {origin}
#     edges = [origin]
#     for m in range(move_range):
#         edge_neighbors = set()
#         for t in edges:
#             edge_neighbors.update(get_neighboring_points(t))
#
#         all_tiles.update(edges)
#         new_edges = edge_neighbors.difference(all_tiles)
#
#         for t in new_edges:
#             if bmap.check_bounds(t) and bmap.get_tile_at(t).is_movable():
#                 edges.append(t)
#
#     all_tiles.update(edges)
#     return all_tiles

def calculate_move_range(unit, bmap):
    return calculate_range(unit.coords, unit.move, bmap)

def calculate_skill_range(unit, skill, bmap):
    return calculate_range(unit.coords, skill.range, bmap, is_skill=True)

def calculate_range(origin, _range, bmap, is_skill=False):
    origin = tuple(origin)
    all_tiles = {origin}
    edges = [origin]
    for m in range(_range):
        edge_neighbors = set()
        for t in edges:
            edge_neighbors.update(get_neighboring_points(t))

        all_tiles.update(edges)
        new_edges = edge_neighbors.difference(all_tiles)

        for t in new_edges:
            tile_is_valid = bmap.get_tile_at(t).is_targetable() if is_skill else  bmap.get_tile_at(t).is_movable()
            if bmap.check_bounds(t) and tile_is_valid:
                edges.append(t)

    all_tiles.update(edges)
    return all_tiles



def get_adjusted_mp(mp, friendlies):
    #pending summon tracking refactor
    num_summons = len(friendlies) - 1
    return mp if mp > -1 else 1 + (num_summons * 2)


def grid_distance(actor1, actor2):
    return abs(actor1[0] - actor2[0]) + abs(actor1[1] - actor2[1])

