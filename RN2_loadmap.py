# -*- coding: utf-8 -*-
import logging
import random

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
        self.flammable = 1

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


class BMap:
    def __init__(self):
        self.contents = []
        self.legend_list = []
        self.terrain_types = [(".", Grass()), (",", Stone()), ("~", Water()), ("L", Lava()), ("X", Pit()), ("G", Goal()), ("*", Wall()), ("|", Wood())]

    def __getitem__(self, item):
        return self.contents[item]

    def append(self, obj):
        self.contents.append(obj)

    def get_tile_at(self, coords):
        try:
            return self.contents[coords[0]][coords[1]]
        except IndexError:
            return False


class Tile:
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

    def display(self):
        to_display = {}
        for attr in ('character', 'fgcolor', 'color', 'bgcolor'):
            if getattr(self.actor, attr, None):
                if attr == 'color':
                    to_display['fgcolor'] = self.actor.color
                else:
                    to_display[attr] = getattr(self.actor, attr)
            elif getattr(self.terrainmod, attr, None):
                to_display[attr] = getattr(self.terrainmod, attr)
            elif getattr(self.terrain, attr, None):
                to_display[attr] = getattr(self.terrain, attr)

        return [to_display['character'], to_display['fgcolor'], to_display['bgcolor']]


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