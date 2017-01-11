from RN2_battle_logic import get_range
from RN2_AI import RN_AI_Class, pathfind
import random
import logging

#todo: summons are not considered here

#weight placed on each consideration in action selection. these will serve as "genes" for the first few simple learning AIs
#needs situational weighting equations based on battle factors (strategic considerations)

#skills refactor to further generalize?


INFLICT_SLOW = 1 #(if move >= distance and move - slow < distance), threat
INFLICT_STUN = 1 #threat level, health
INFLICT_ROOT = 1 #threat_level, health, distance > 1, nonranged
INFLICT_PUSH = 1 #(if move >= distance and move - push < distance), threat

DAMAGE_TO_ENEMY = 10
DAMAGE_OVER_TIME_TO_ENEMY = 5
ENEMY_KILLED = 50
HIT_RATE = 1
DAMAGE_TO_SELF = -100
DAMAGE_TO_FRIENDLY = -1
FRIENDLY_KILLED = -5
SELF_KILLED = -10000
TILE_THREAT_LEVEL = -10
ENEMY_HEALED = -1
FRIENDLY_HEALED = 1 #health
FRIENDLY_HEALED_OVER_TIME = 1 #health
SELF_HEALED = 1 #health
SELF_HEALED_OVER_TIME = 1 #health
MP_COST = -8
ADDITIONAL_ALLY = -10000 #allies on board, threat

class ThreatMap:
    def __init__(self, battle_map):
        self.tmap = []
        for x in range(50):
            self.tmap.append([])
            for y in range(25):
                if not battle_map[x][y].terrain.movable:
                    self.tmap[x].append(0)
                else:
                    self.tmap[x].append(1)

    def add_threat(self, threat, bmap):
        threat_range = threat.move + 1
        threat_tiles = get_range(bmap, (50, 25), threat.coords, threat_range*2, pathfind=False, is_move=True)
        for t in threat_tiles:
            if self.tmap[t[0]][t[1]] > 0:
                self.tmap[t[0]][t[1]] += 1

        threat_tiles = get_range(bmap, (50, 25), threat.coords, threat_range, pathfind=False, is_move=True)
        for t in threat_tiles:
            if self.tmap[t[0]][t[1]] > 0:
                self.tmap[t[0]][t[1]] += 1

    def get_threat_for_tile(self, coords):
        return self.tmap[coords[0]][coords[1]]


class PyromancerDecisionTree(RN_AI_Class):
    def __init__(self, battle, actor, skills):
        RN_AI_Class.__init__(self, battle, actor, skills)
        self.threat_map = self.create_threat_map()
        self.move_range = get_range(self.battle.bmap, (50, 25), (self.actor.coords), self.actor.move, pathfind=True, is_move=True)

    #assign each tile a threat rating based on enemies that can reach it
    def create_threat_map(self):
        threat_map = ThreatMap(self.battle.bmap)
        for enemy in self.enemy_list:
            threat_map.add_threat(enemy["unit"], self.battle.bmap)

        return threat_map

    def check_bounds(self, coords):
        if 0 > coords[0] or coords[0] > self.battle.bmap.map_size[0] or 0 > coords[1] or coords[1] > self.battle.bmap.map_size[1]:
            return False
        return True

    def add_points(self, coord, change):
        return tuple(sum(x) for x in zip(coord, change))

    def get_neighboring_points(self, point):
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        return [self.add_points(point, n) for n in neighbors]

    def get_valid_tiles(self, origin, move_range, skill_range, bmap):
        origin = tuple(origin)
        all_tiles = {origin}
        edges = {origin}
        for m in range(move_range):
            edge_neighbors = set()
            for t in edges:
                edge_neighbors.update(self.get_neighboring_points(t))

            all_tiles.update(edges)
            new_edges = edge_neighbors.difference(all_tiles)

            edges = set()
            for t in new_edges:
                if self.check_bounds(t) and bmap.get_tile_at(t).is_movable():
                    edges.add(t)

        for s in range(skill_range):
            edge_neighbors = set()
            for t in edges:
                edge_neighbors.update(self.get_neighboring_points(t))

            all_tiles.update(edges)
            new_edges = edge_neighbors.difference(all_tiles)

            edges = set()
            for t in new_edges:
                if self.check_bounds(t) and bmap.get_tile_at(t).is_targetable():
                    edges.add(t)

        all_tiles.update(edges)
        return all_tiles


    def determine_best_target_for_skill(self, skill, damage):
        enemy_locations = [{'loc': e['unit'].coords, 'actor': e['unit']} for e in self.enemy_list]
        friendly_locations = [{'loc': a['unit'].coords, 'actor': a['unit']} for a in self.friendly_list]
        target_tile_options = {}

        #calculate expected results for each possible tile

        for tile in self.get_valid_tiles(self.actor.coords, self.actor.move, skill.range, self.battle.bmap):
            if skill.effects and skill.effects[0]['type'] == "Summon" and self.battle.bmap[tile[0]][tile[1]].is_movable():
                try:
                    target_tile_options[tile] += ADDITIONAL_ALLY
                except KeyError:
                    target_tile_options[tile] = ADDITIONAL_ALLY

            if skill.affects_enemies:
                for loc in enemy_locations:
                    if self.grid_distance(loc['loc'], tile) <= skill.aoe:
                        try:
                            target_tile_options[tile] += damage * DAMAGE_TO_ENEMY
                        except KeyError:
                            target_tile_options[tile] = damage * DAMAGE_TO_ENEMY

                        if loc['actor'].hp < damage:
                            target_tile_options[tile] += 1 * ENEMY_KILLED

            if skill.affects_friendlies:
                for loc in friendly_locations:
                    if self.grid_distance(loc['loc'], tile) <= skill.aoe:
                        try:
                            target_tile_options[tile] += damage * DAMAGE_TO_FRIENDLY
                        except KeyError:
                            target_tile_options[tile] = damage * DAMAGE_TO_FRIENDLY

                        if loc['actor'].hp < damage:
                            target_tile_options[tile] += 1 * FRIENDLY_KILLED

                if self.grid_distance(self.actor.coords, tile) <= skill.aoe:
                    try:
                        target_tile_options[tile] += damage * DAMAGE_TO_SELF
                    except KeyError:
                        target_tile_options[tile] = damage * DAMAGE_TO_SELF

                    if self.actor.hp < damage:
                        target_tile_options[tile] += 1 * SELF_KILLED

        results = []
        for k, v in target_tile_options.items():
            results.append((v, k))

        results.sort(reverse=True)

        return results[0] if results else (None, None)

    def choose_safest_tile(self, skill=None, loc=None):
        results = []
        success = False
        for tile in self.move_range:
            if skill and self.grid_distance(tile, loc) > skill.range:
                continue
            else:
                results.append({'threat_level': self.threat_map.get_threat_for_tile(tile), 'loc': tile})
                success = True

        if not success:
            print "No possible path to tile: ", loc
            exit()

        results.sort()
        return results[0]

    def get_action(self):
        results = []
        best_retreat = self.choose_safest_tile()

        #calculate the value of the "do nothing" option
        no_action_value = 0
        no_action_value += best_retreat['threat_level'] * TILE_THREAT_LEVEL
        results.append((0, None, None, best_retreat['loc']))

        for s in self.actor.skillset:
            skill_data = self.skills[s]
            if skill_data.mp > self.actor.mp:
                continue

            average_damage_per_target = skill_data.get_average_damage(self.actor)

            skill_value, target_tile = self.determine_best_target_for_skill(skill_data, average_damage_per_target)
            if target_tile is None:
                continue

            safest_tile = self.choose_safest_tile(skill=skill_data, loc=target_tile)

            skill_value += safest_tile['threat_level'] * TILE_THREAT_LEVEL
            skill_value += skill_data.mp * MP_COST
            results.append((skill_value, skill_data.name, target_tile, safest_tile['loc']))

        results.sort(reverse=True)
        print results

        chosen_action = results[0]
        print chosen_action
        path = pathfind((self.actor.coords[1], self.actor.coords[0]), (chosen_action[3][1], chosen_action[3][0]), self.battle.bmap)
        return chosen_action[1], chosen_action[2], path[1]
