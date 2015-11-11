# -*- coding: utf-8 -*-
import logging
import time

#logging.basicConfig(filename="logs/rn_debug(" + time.asctime() + ").log", filemode="w", level=logging.DEBUG)

class Terrain():
    def __init__(self):
        self.name = "Nothing"
        self.fgcolor = ""
        self.bgcolor = ""
        self.character = " "
        self.movecost = 1
        self.aquatic = 0
        self.targetable = 0
        self.blocking = 0
        self.moveable = 1
        self.fatal = 0

#Terrain types:

class Grass(Terrain):
    def __init__(self):
        Terrain.__init__(self)
        self.name = "Grass"
        self.fgcolor = "green"
        self.bgcolor = "gray"
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
        self.fgcolor = "silver"
        self.bgcolor = "gray"
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
        self.fgcolor = "red"
        self.bgcolor = "maroon"
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
        self.fgcolor = "teal"
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
        self.fgcolor = "silver"
        self.bgcolor = "silver"
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
        self.fgcolor = "yellow"
        self.bgcolor = "gray"
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
        self.bgcolor = "olive"
        self.character = u"≡"
        self.movecost = 1
        self.aquatic = 0
        self.targetable = 1
        self.movable = 1

    def terrain_effect(self):
        pass   #death

class TerrainMod():
    def __init__(self):
        self.name = ""
        self.fgcolor = ""
        self.bgcolor = ""
        self.character = ""
        self.movecost = ""

class BMap():
    def __init__(self):
        self.contents = []
        self.legend_list = []
        self.terrain_types = [(".", Grass()), (",", Stone()), ("~", Water()), ("L", Lava()), ("X", Pit()), ("G", Goal()), ("*", Wall()), ("|", Wood())]

    def __getitem__(self, item):
        return self.contents[item]

    def append(self, obj):
        self.contents.append(obj)

class Tile():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.actor = None
        self.terrain = None
        self.terrainmod = None

    def display(self):
        if self.actor != None:
            return [self.actor.character, self.actor.color, self.terrain.bgcolor]
        elif self.terrainmod != None:
            return [self.terrainmod.character, self.terrainmod.color, self.terrain.bgcolor]
        elif self.terrain != None:
            return [self.terrain.character, self.terrain.fgcolor, self.terrain.bgcolor]
        else:
            raise ValueError


def load_map(map_data):
    startpos = []
    map_lines = map_data['layout']
    for c in map_data['start'].split(","):
        startpos.append(int(c))
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
    return battle_map, startpos


def analyze_data(character, battle_map, tile):
    for m in battle_map.terrain_types:     #m is tuple(character, terrain class)
        if character == m[0]:
            tile.terrain = m[1]
    if tile.terrain is None:
        logging.debug("Tile" + repr(tile.x) + repr(tile.y) + "invalid or not found.")
        raise TypeError
    if (tile.terrain.character, tile.terrain.fgcolor, tile.terrain.bgcolor, tile.terrain.name) not in battle_map.legend_list and tile.terrain.character != " ":  #add to the legend
        battle_map.legend_list.append((tile.terrain.character, tile.terrain.fgcolor, tile.terrain.bgcolor, tile.terrain.name))
    return tile, battle_map