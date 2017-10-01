# -*- coding: utf-8 -*-
import random
import copy


class Terrain(object):
    def __init__(self):
        self.name = "Nothing"
        self.fgcolor = ""
        self.bgcolor = ""
        self.character = " "
        self.movecost = 1
        self.aquatic = 0
        self.targetable = 0
        self.blocking = 0
        self.movable = 1
        self.fatal = 0
        self.flammable = 1

    @property
    # stops forced movement AFTER landing on this tile
    def ends_forced_movement(self):
        return self.aquatic or self.fatal

#Terrain types:

class Grass(Terrain):
    def __init__(self):
        Terrain.__init__(self)
        self.name = "Grass"
        self.fgcolor = "forestgreen"
        self.bgcolor = "gray50"
        self.character = u'√'
        self.movecost = 1
        self.aquatic = 0
        self.targetable = 1
        self.movable = 1

    def terrain_effect(self):
        pass   #something like taking extra fire damage

class Stone(Terrain):
    def __init__(self):
        Terrain.__init__(self)
        self.name = "Stone"
        self.fgcolor = "gray70"
        self.bgcolor = "gray50"
        self.character = u'.'
        self.movecost = 1
        self.aquatic = 0
        self.targetable = 1
        self.movable = 1

    def terrain_effect(self):
        pass   #nothing?

class Lava(Terrain):
    def __init__(self):
        Terrain.__init__(self)
        self.name = "Lava"
        self.fgcolor = "black"
        self.bgcolor = "darkred"
        self.character = u'Ξ'
        self.movecost = 1
        self.aquatic = 0
        self.targetable = 1
        self.movable = 0
        self.fatal = 1

class Pit(Terrain):
    def __init__(self):
        Terrain.__init__(self)
        self.name = "Pit"
        self.fgcolor = "black"
        self.bgcolor = "black"
        self.character = " "
        self.movecost = 0
        self.aquatic = 0
        self.targetable = 0
        self.movable = 0
        self.fatal = 1

class Water(Terrain):
    def __init__(self):
        Terrain.__init__(self)
        self.name = "Water"
        self.fgcolor = "deepskyblue"
        self.bgcolor = "blue"
        self.character = u'≈'
        self.movecost = 3
        self.aquatic = 1
        self.targetable = 1
        self.movable = 0
        self.blocking = 1

    def terrain_effect(self):
        pass   #no skills, no mana regen, immune to burning, etc.

class Wall(Terrain):
    def __init__(self):
        Terrain.__init__(self)
        self.name = "Wall"
        self.fgcolor = "gray70"
        self.bgcolor = "gray70"
        self.character = " "
        self.movecost = 0
        self.aquatic = 0
        self.targetable = 0
        self.movable = 0
        self.blocking = 1

    def terrain_effect(self):
        pass   #bounce back

class Goal(Terrain):
    def __init__(self):
        Terrain.__init__(self)
        self.name = "Goal"
        self.fgcolor = "gold"
        self.bgcolor = "gray50"
        self.character = "G"
        self.movecost = 1
        self.aquatic = 0
        self.targetable = 1
        self.movable = 1

    def terrain_effect(self):
        pass   #victory

class Wood(Terrain):
    def __init__(self):
        Terrain.__init__(self)
        self.name = "Wood"
        self.fgcolor = "black"
        self.bgcolor = "burlywood4"
        self.character = u"≡"
        self.movecost = 1
        self.aquatic = 0
        self.targetable = 1
        self.movable = 1

    def terrain_effect(self):
        pass   #death

class Bridge(Terrain):
    def __init__(self):
        Terrain.__init__(self)
        self.name = "Bridge"
        self.fgcolor = "black"
        self.bgcolor = "gray50"
        self.character = u"+"
        self.movecost = 1
        self.aquatic = 0
        self.targetable = 1
        self.movable = 1

    def terrain_effect(self):
        pass   #death


class TerrainMod:
    def __init__(self):
        self.name = ""
        self.fgcolor = None
        self.bgcolor = None
        self.character = None
        self.movecost = 0
        self.damage = 0
        self.total_duration = 0
        self.current_duration = self.total_duration
        self.removed = False
        self.priority = 0
        self.movable = 1

    def apply(self, tile, apply_chance=100):
        tile.terrainmod = self

    def tick_duration(self):
        self.current_duration -= 1
        if self.current_duration == 0:
            self.remove_mod()

    def remove_mod(self):
        self.removed = True


class Flaming(TerrainMod):
    def __init__(self):
        TerrainMod.__init__(self)
        self.name = 'flaming'
        self.fgcolor = 'orange'
        self.bgcolor = None
        self.character = u'ψ'
        self.movecost = 0
        self.damage = 5
        self.total_duration = 3
        self.current_duration = self.total_duration
        self.removed = False
        self.priority = 7

    def apply(self, tile, apply_chance=100):
        if tile.flammable:
            rand = random.randint(0, 100)
            if rand > apply_chance:
                tile.terrainmod = Flaming()

    def remove_mod(self):
        self.removed = True
        #change mod to "burned"


class Burned(TerrainMod):
    def __init__(self):
        TerrainMod.__init__(self)
        self.name = 'burned'
        self.fgcolor = 'gray'
        self.bgcolor = None
        self.character = None
        self.movecost = 0
        self.damage = 0
        self.total_duration = 0
        self.current_duration = self.total_duration
        self.removed = False
        self.priority = 1


class BMap(object):
    # def __deepcopy__(self, memo):
    #     import timeit as timer
    #     start = timer.default_timer()
    #     deepcopy_method = self.__deepcopy__
    #
    #     self.__deepcopy__ = None
    #     cp = copy.deepcopy(self, memo)
    #     self.__deepcopy__ = deepcopy_method
    #     end = timer.default_timer()
    #     print "copy map time:", end-start
    #
    #     return cp

    def __init__(self):
        self.contents = []
        self.legend_list = []

        self.map_size = (49, 24)

    def __getitem__(self, item):
        try:
            return self.contents[item]
        except:
            print item
            raise IndexError

    def append(self, obj):
        self.contents.append(obj)

    def get_tile_at(self, coords):
        try:
            return self.contents[coords[0]][coords[1]]
        except IndexError:
            print "Invalid coords", coords
            raise ValueError

    def get_empty_tiles(self, tiles):
        res = []
        for tile in tiles:
            if self.get_tile_at(tile).is_movable:
                res.append(tile)

        return res

    def find_goal_tiles(self):
        pass

    def place_unit(self, unit, coords):
        tile = self.get_tile_at(coords)
        if tile.actor:
            print "'Cant place {0}: Tile {1} is occupied by {2}".format(unit, coords, tile.actor)
            raise KeyError

        tile.actor = unit

    def remove_unit(self, unit):
        tile = self.get_tile_at(unit.coords)
        tile.actor = None

    def check_bounds(self, coords):
        if 0 > coords[0] or coords[0] > self.map_size[0] or 0 > coords[1] or coords[1] > self.map_size[1]:
            return False
        return True

    def all_targetable_tiles(self):
        all_targetable_tiles = []
        for x in range(self.map_size[0]):
            for y in range(self.map_size[1]):
                all_targetable_tiles.append((x, y))


class Tile(object):
    # def __deepcopy__(self, memo):
    #     import timeit as timer
    #     start = timer.default_timer()
    #     deepcopy_method = self.__deepcopy__
    #
    #     self.__deepcopy__ = None
    #     cp = copy.deepcopy(self, memo)
    #     self.__deepcopy__ = deepcopy_method
    #     end = timer.default_timer()
    #     print "copy tile time:", end-start
    #
    #     return cp

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.actor = None
        self.terrain = None
        self.terrainmod = None

    def __getattr__(self, name):
        if self.terrainmod and getattr(self.terrainmod, name):
            return getattr(self.terrainmod, name)
        elif self.terrain and getattr(self.terrain, name):
            return getattr(self.terrain, name)
        else:
            return getattr(self, name)

    @property
    def is_movable(self):
        return self.terrain.movable and not self.actor

    @property
    def is_targetable(self):
        return self.terrain.targetable and not self.terrain.blocking


def load_map(map_data):
    map_lines = map_data['layout']
    map_lines = map_lines.splitlines()
    for m in map_lines:
        list(m)
    battle_map = BMap()
    for x in range(50):
        battle_map.append([])
        for y in range(25):
            tile = Tile(x, y)
            tile, map_list = analyze_data(map_lines[y][x], battle_map, tile)
            battle_map[x].append(tile)
    return battle_map


def analyze_data(character, battle_map, tile):
    terrain_types = [(".", Grass()), (",", Stone()), ("~", Water()), ("L", Lava()), ("X", Pit()), ("G", Goal()),
                     ("*", Wall()), ("|", Wood()), ("+", Bridge())]
    for m in terrain_types:
        if character == m[0]:
            tile.terrain = m[1]
    if tile.terrain is None:
        raise TypeError
    if (tile.terrain.character, tile.terrain.fgcolor, tile.terrain.bgcolor, tile.terrain.name) not in battle_map.legend_list and tile.terrain.character != " ":  #add to the legend
        battle_map.legend_list.append((tile.terrain.character, tile.terrain.fgcolor, tile.terrain.bgcolor, tile.terrain.name))
    return tile, battle_map