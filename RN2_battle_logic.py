import RN2_loadmap
import random
import time
import logging
import RN2_AI
import itertools


def get_range(bmap, map_size, origin, arange, pathfind=False, is_move=False):
    targetable_tiles = []


    if arange == 'global':  # global attack
        for x in range(map_size[0] + 1):
            for y in range(map_size[1] + 1):
                targetable_tiles.append((x, y))

    else:
        targetable_tiles = [tuple(origin)]  # list of tuple coordinates of tiles that are in attack range
        new_tiles = [tuple(origin)]
        for i in range(arange):
            for t in targetable_tiles:
                if (t[0] + 1, t[1]) not in targetable_tiles:
                    new_tiles.append((t[0] + 1, t[1]))
                if (t[0] - 1, t[1]) not in targetable_tiles:
                    new_tiles.append((t[0] - 1, t[1]))
                if (t[0], t[1] - 1) not in targetable_tiles:
                    new_tiles.append((t[0], t[1] - 1))
                if (t[0], t[1] + 1) not in targetable_tiles:
                    new_tiles.append((t[0], t[1] + 1))
            for t in new_tiles:
                if t not in targetable_tiles and 0 <= t[0] <= 49 and 0 <= t[1] <= 24:
                    targetable_tiles.append(t)
    remove_list = []

    for t in targetable_tiles:
        if (is_move and bmap[t[0]][t[1]].terrain.movable == 0) or (
            not is_move and bmap[t[0]][t[1]].terrain.targetable == 0):
            remove_list.append(t)

    if pathfind:
        for t in targetable_tiles:
            path = RN2_AI.pathfind(tuple(origin)[::-1], t[::-1], bmap)
            if path[0] > arange + 1:
                remove_list.append(t)

    for r in remove_list:
        targetable_tiles.remove(r)
    return targetable_tiles
