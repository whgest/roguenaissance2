from RN2_AI import RN_AI_Class, pathfind
import random
import logging
import RN2_battle_logic
import time
import math
#todo: summons are not considered here

#weight placed on each consideration in action selection. these will serve as "genes" for the first few simple learning AIs
#needs situational weighting equations based on battle factors (strategic considerations)

#skills refactor to further generalize?



class SimpleCheck:
    def __init__(self, multiplier):
        self.multiplier = multiplier


class InflictDamage(SimpleCheck):
    def __init__(self, multiplier):
        SimpleCheck.__init__(self, multiplier)

    def calculate(self, damage):
        return damage * self.multiplier


class ChanceToKill(SimpleCheck):
    def __init__(self, multiplier):
        SimpleCheck.__init__(self, multiplier)

    def calculate(self, min_damage, max_damage, target):
        #chance to kill is the required damage to kill, divided by the number of possible damage roll results
        numerator = max(0, (max_damage - target.hp) + 1)
        denominator = (max_damage - min_damage) + 1
        chance_to_kill = numerator / denominator

        return self.multiplier * chance_to_kill


class HealDamage(SimpleCheck):
    def __init__(self, multiplier):
        SimpleCheck.__init__(self, multiplier)

    def calculate(self, healing, target):
        healing = abs(healing)
        percentage_health = float(target.hp)/float(target.maxhp)

        res = self.multiplier * ((1 - percentage_health) * healing)
        return res


class SummonCheck(SimpleCheck):
    def calculate(self):
        return 1 * self.multiplier


DAMAGE_ENEMY = InflictDamage(10)
DAMAGE_FRIENDLY = InflictDamage(-5)
DAMAGE_SELF = InflictDamage(-100)

ENEMY_KILLED = ChanceToKill(30)
FRIENDLY_KILLED = ChanceToKill(-10)
SELF_KILLED = ChanceToKill(-10000)

HEAL_ENEMY = HealDamage(-10)
HEAL_FRIENDLY = HealDamage(5)
HEAL_SELF = HealDamage(100)

ADDITIONAL_ALLY = SummonCheck(30)

DAMAGE_OVER_TIME_MODIFIER = 0.5
HEALING_OVER_TIME_MODIFIER = 0.5

MP_COST = -12

INFLICT_DISABLE = 100
INFLICT_PUSH = 10

HIT_RATE_MODIFIER = 1

INCREASE_SELF_ATTACK = 1
INCREASE_SELF_DEFENSE = 1
INCREASE_SELF_MAGIC = 1
INCREASE_SELF_RESISTANCE = 1
INCREASE_SELF_MOVE = 1

INCREASE_FRIENDLY_ATTACK = 1
INCREASE_FRIENDLY_DEFENSE = 1
INCREASE_FRIENDLY_MAGIC = 1
INCREASE_FRIENDLY_RESISTANCE = 1
INCREASE_FRIENDLY_MOVE = 1

INCREASE_ENEMY_ATTACK = -1
INCREASE_ENEMY_DEFENSE = -1
INCREASE_ENEMY_MAGIC = -1
INCREASE_ENEMY_RESISTANCE = -1
INCREASE_ENEMY_MOVE = -1

DECREASE_SELF_ATTACK = -1
DECREASE_SELF_DEFENSE = -1
DECREASE_SELF_MAGIC = -1
DECREASE_SELF_RESISTANCE = -1
DECREASE_SELF_MOVE = -1

DECREASE_FRIENDLY_ATTACK = -1
DECREASE_FRIENDLY_DEFENSE = -1
DECREASE_FRIENDLY_MAGIC = -1
DECREASE_FRIENDLY_RESISTANCE = -1
DECREASE_FRIENDLY_MOVE = -1

DECREASE_ENEMY_ATTACK = -1
DECREASE_ENEMY_DEFENSE = -1
DECREASE_ENEMY_MAGIC = -1
DECREASE_ENEMY_RESISTANCE = -1
DECREASE_ENEMY_MOVE = -1

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
        threat_tiles = threat.calculate_move_range(bmap, modifier=1)
        for t in threat_tiles:
            if self.tmap[t[0]][t[1]] > 0:
                self.tmap[t[0]][t[1]] += 1

    def get_threat_for_tile(self, coords):
        return self.tmap[coords[0]][coords[1]]


class PyromancerDecisionTree(object):
    count = 0
    def __init__(self, battle, actor, skills):
        self.battle = battle
        self.actor = actor
        self.skills = skills
        self.bmap = battle.bmap
        self.enemy_list, self.friendly_list = self.get_targets()
        self.threat_map = self.create_threat_map()
        self.move_range = self.actor.calculate_move_range(self.battle.bmap)
        self.aggression = 1 if self.actor.ai == "pyromancer" else 10

    def get_targets(self):
        friendly_list = []
        enemy_list = []

        for enemy in self.battle.get_enemies_of(self.actor):
            distance, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (enemy.coords[1], enemy.coords[0]), self.bmap)
            enemy_list.append({"distance": distance, "unit": enemy, "path": path})

        for ally in self.battle.get_allies_of(self.actor):
            distance, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (ally.coords[1], ally.coords[0]), self.bmap)
            friendly_list.append({"distance": distance, "unit": ally, "path": path})

        return enemy_list, friendly_list

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

    def get_valid_tiles(self, origin, move_range, skill, bmap):
        origin = tuple(origin)
        all_tiles = {origin}
        edges = [origin]
        for m in range(move_range):
            edge_neighbors = set()
            for t in edges:
                edge_neighbors.update(self.get_neighboring_points(t))

            all_tiles.update(edges)
            new_edges = edge_neighbors.difference(all_tiles)

            for t in new_edges:
                if self.check_bounds(t) and bmap.get_tile_at(t).is_movable():
                    edges.append(t)

        for s in range(skill.range):
            all_tiles, new_edges = skill.aoe.get_next_aoe_range(all_tiles, edges, self.actor.coords)

            edges = set()
            for t in new_edges:
                if self.check_bounds(t) and bmap.get_tile_at(t).is_targetable():
                    edges.add(t)

        all_tiles.update(edges)
        # self.ui.highlight_area(True, all_tiles, self.battle.bmap, color="red")
        # time.sleep(1)
        # self.ui.highlight_area(False, all_tiles, self.battle.bmap)

        return all_tiles

    def determine_best_target_for_skill(self, skill, user, user_threat):
        enemy_locations = [{'loc': e['unit'].coords, 'actor': e['unit']} for e in self.enemy_list]
        friendly_locations = [{'loc': a['unit'].coords, 'actor': a['unit']} for a in self.friendly_list]
        valid_target_tiles = self.get_valid_tiles(self.actor.coords, self.actor.move, skill, self.battle.bmap)
        target_tile_options = {}

        for tile in valid_target_tiles:
            target_tile_options[tile] = 0
            affected_area = RN2_battle_logic.calculate_affected_area(tile, self.actor.coords, skill, self.battle.bmap)

            # if skill.effects and skill.effects[0]['type'] == "Summon" and self.battle.bmap[tile[0]][tile[1]].is_movable():
            #     target_tile_options[tile] += ADDITIONAL_ALLY.calculate()

            if skill.affects_enemies:
                for loc in enemy_locations:
                    avg_damage = skill.targets.enemy.damage.get_average_damage(user)
                    min_damage = skill.targets.enemy.damage.get_minimum_damage(user)
                    max_damage = skill.targets.enemy.damage.get_maximum_damage(user)
                    if tuple(loc['loc']) in affected_area:
                        if avg_damage > 0:
                            target_tile_options[tile] += DAMAGE_ENEMY.calculate(avg_damage)
                            target_tile_options[tile] += ENEMY_KILLED.calculate(min_damage, max_damage, loc['actor'])
                        elif avg_damage < 0:
                            target_tile_options[tile] += HEAL_ENEMY.calculate(avg_damage, loc['actor'])

            if skill.affects_friendlies:
                avg_damage = skill.targets.friendly.damage.get_average_damage(user)
                min_damage = skill.targets.friendly.damage.get_minimum_damage(user)
                max_damage = skill.targets.friendly.damage.get_maximum_damage(user)
                for loc in friendly_locations:
                    if tuple(loc['loc']) in affected_area:
                        if avg_damage > 0:
                            target_tile_options[tile] += DAMAGE_FRIENDLY.calculate(avg_damage)
                            target_tile_options[tile] += FRIENDLY_KILLED.calculate(min_damage, max_damage, loc['actor'])
                        elif avg_damage < 0:
                            target_tile_options[tile] += HEAL_FRIENDLY.calculate(avg_damage, loc['actor'])

            if tuple(self.actor.coords) in affected_area and skill.affects_self:
                avg_damage = skill.targets.self.damage.get_average_damage(user)
                min_damage = skill.targets.self.damage.get_minimum_damage(user)
                max_damage = skill.targets.self.damage.get_maximum_damage(user)
                if avg_damage > 0:
                    target_tile_options[tile] += DAMAGE_SELF.calculate(avg_damage)
                    target_tile_options[tile] += SELF_KILLED.calculate(min_damage, max_damage, self.actor)
                elif avg_damage < 0:
                    target_tile_options[tile] += HEAL_SELF.calculate(avg_damage, self.actor)


        results = []
        for k, v in target_tile_options.items():
            results.append((v, k))

        results.sort(reverse=True)




        return results[0] if results else (None, None)

    def choose_safest_tile(self, skill=None, loc=None):
        results = []
        success = False
        for tile in self.move_range:
            if skill and RN2_battle_logic.grid_distance(tile, loc) > skill.range:
                continue
            else:
                results.append({'threat_level': self.threat_map.get_threat_for_tile(tile), 'loc': tile})
                success = True

        if not success:
            print "No possible path to tile: ", loc
            exit()

        results.sort()
        return results[0]

    def advance_towards_enemy(self):
        #todo: attack or retreat based on aggression level
        advance_paths = []
        for n in self.enemy_list:
            path = pathfind((self.actor.coords[1], self.actor.coords[0]), (n['unit'].coords[1], n['unit'].coords[0]), self.battle.bmap)[1]
            value = n['unit'].priority_value - len(path)
            dist = min(len(path), self.actor.move) - 1

            if path and dist >= 0:
                if path[dist] == n['unit'].coords:
                    dist -= 1

                advance_paths.append((value, path[dist]))

        advance_paths.sort(reverse=True)

        if advance_paths:
            return advance_paths[0]
        else:
            return (0, (self.actor.coords[1], self.actor.coords[0]))

    def get_action(self, ui):

        results = []
        best_retreat = self.choose_safest_tile()
        self.ui = ui


        #calculate the value of the "do nothing" option
        no_action_value = 0
        no_action_value += best_retreat['threat_level']

        results.append((no_action_value, None, None, best_retreat['loc']))

        advance = self.advance_towards_enemy()
        results.append((self.aggression, None, None, advance[1]))

        for s in self.actor.skillset:
            skill_data = self.skills[s]
            if skill_data.mp > self.actor.mp:
                continue

            skill_value, target_tile = self.determine_best_target_for_skill(skill_data, self.actor, self.threat_map.get_threat_for_tile(self.actor.coords))
            if target_tile is None:
                continue

            safest_tile = self.choose_safest_tile(skill=skill_data, loc=target_tile)

            skill_value += safest_tile['threat_level'] * -0.1 #todo: aggression
            skill_value += RN2_battle_logic.get_adjusted_mp(skill_data.mp, self.friendly_list) * MP_COST
            results.append((skill_value, skill_data.name, target_tile, safest_tile['loc']))

        results.sort(reverse=True)
        print results

        chosen_action = results[0]
        path = pathfind((self.actor.coords[1], self.actor.coords[0]), (chosen_action[3][1], chosen_action[3][0]), self.battle.bmap)
        return chosen_action[1], chosen_action[2], path[1]
