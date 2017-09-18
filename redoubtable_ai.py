from RN2_AI import pathfind
from timeit import default_timer as timer

import RN2_battle_logic
import RN2_battle
import dummy_ui
import copy
import random


class ThreatMap:
    def __init__(self, battle_map, skills):
        self.tmap = []
        self.skills = skills
        for x in range(50):
            self.tmap.append([])
            for y in range(25):
                if not battle_map[x][y].terrain.movable:
                    self.tmap[x].append(0)
                else:
                    self.tmap[x].append(1)

    def add_threat(self, threat, bmap):
        skills = [self.skills[s] for s in threat.skillset]
        skills.sort(key=lambda x: (x.range + x.aoe_size) / max(1, x.mp), reverse=True)
        threat_tiles = threat.calculate_move_range(bmap)
        for t in threat_tiles:
            if self.tmap[t[0]][t[1]] > 0:
                self.tmap[t[0]][t[1]] += 1

    def get_threat_for_tile(self, coords):
        return self.tmap[coords[0]][coords[1]]


class UnitScoreWeightDefaults(object):
    def __init__(self):
        self.hp = 1
        self.mp = 1
        self.attack = 1
        self.defense = 1
        self.agility = 1
        self.move = 1
        self.magic = 1
        self.resistance = 1

        self.total_damage_over_time = 1

        self.is_dead = 1

        self.tile_threat = 0
        self.preferred_threat_level = 10

    def calculate(self, unit, threat_map):
        score = 0
        score += self.hp * unit.hp
        score += self.mp * unit.mp
        score += self.attack * unit.attack
        score += self.defense * unit.defense
        score += self.agility * unit.agility
        score += self.move * unit.move
        score += self.magic * unit.magic
        score += self.resistance * unit.resistance

        score += self.get_damage_over_time_score(unit) * self.total_damage_over_time

        score += self.is_dead * unit.is_dead

        score += abs(self.preferred_threat_level - threat_map.get_threat_for_tile(unit.coords)) * self.tile_threat

        return score

    def get_damage_over_time_score(self, unit):
        import itertools
        result = 0
        keyfunc = lambda x: x.status_effect.type
        all_dot_effects = [e for e in unit.active_status_effects if e.status_effect.damage]

        if len(all_dot_effects):
            for key, group in itertools.groupby(all_dot_effects, keyfunc):
                effects_of_type = list(group)
                effects_of_type.sort(key=lambda x: x.status_effect.damage)
                strongest_effect_for_type = effects_of_type.pop()
                result += strongest_effect_for_type.status_effect.damage * strongest_effect_for_type.remaining_duration

        return result


class UnitScoreWeightEnemy(UnitScoreWeightDefaults):
    def __init__(self):
        UnitScoreWeightDefaults.__init__(self)
        self.hp = -10
        self.attack = -20
        self.defense = -20
        self.move = -30
        self.magic = -20
        self.resistance = -20

        self.total_damage_over_time = 8

        self.is_dead = 500

        self.tile_threat = 0
        self.preferred_threat_level = 0


class UnitScoreWeightAlly(UnitScoreWeightDefaults):
    def __init__(self):
        UnitScoreWeightDefaults.__init__(self)
        self.hp = 2
        self.attack = 4
        self.defense = 4
        self.move = 5
        self.magic = 4
        self.resistance = 4

        self.total_damage_over_time = -1

        self.is_dead = -100

        self.tile_threat = -100
        self.preferred_threat_level = 10


class UnitScoreWeightSelf(UnitScoreWeightDefaults):
    def __init__(self):
        UnitScoreWeightDefaults.__init__(self)
        self.hp = 30
        self.mp = 30
        self.attack = 60
        self.defense = 60
        self.move = 80
        self.magic = 60
        self.resistance = 60

        self.total_damage_over_time = -20

        self.is_dead = -10000

        self.tile_threat = -10
        self.preferred_threat_level = 65


class UnitScoreWeights(object):
    def __init__(self, enemy, friendly, personal):
        self.enemy = enemy
        self.friendly = friendly
        self.personal = personal


class SimulationHandler(object):
    def __init__(self, unit, battle, skills):
        self.active_unit = unit
        self.unit_states = {}
        self.skills = skills

        simulated_battle = RN2_battle.SimulatedBattle({}, battle.actor_data, {}, copy.deepcopy(battle.bmap), {})

        simulated_battle.all_living_units = copy.deepcopy(battle.all_living_units)
        for unit in simulated_battle.all_living_units:
            unit.event = dummy_ui.DummyUi()
            self.unit_states[unit.id] = copy.deepcopy(unit.current_state())

        simulated_battle.active = [u for u in simulated_battle.all_living_units if u.id == self.active_unit.id][0]

        # until destination is selected, active's position is unknown for the purpose of simulation
        simulated_battle.active.coords = [-1, -1]

        self.simulated_battle = simulated_battle
        self.reset()

    def reset(self):
        def reset_units(unit_list):
            for unit in unit_list:
                try:
                    unit.set_state(copy.deepcopy(self.unit_states[unit.id]))
                except KeyError:
                    unit_list.remove(unit)

        for unit in self.simulated_battle.all_living_units:
            self.simulated_battle.bmap.remove_unit(unit)

        reset_units(self.simulated_battle.all_living_units)

        for unit in self.simulated_battle.all_living_units:
            self.simulated_battle.bmap.place_unit(unit, unit.coords)
            unit.event = dummy_ui.DummyUi()

        self.simulated_battle.active = [u for u in self.simulated_battle.all_living_units if u.id == self.active_unit.id][0]
        self.simulated_battle.active.coords = [-1, -1]

    def simulate_move(self, chosen_skill, target_tile, affected_tiles, include_actor=False):
        if chosen_skill:
            if include_actor:
                self.simulated_battle.active.coords = random.choice(affected_tiles)
            self.simulated_battle.execute_skill(self.simulated_battle.active, chosen_skill, affected_tiles, target_tile)

        return self.score_battle_state(self.simulated_battle, self.simulated_battle.active)

    def score_battle_state(self, simulated_battle, active):
        """
        Based on passed parameters that weight criteria, score a hypothetical battle state for favorability to the AI
        calling this function
        :return: A score
        """

        score = 0
        unit_priority = 1

        allies = [u for u in simulated_battle.all_living_units if u.is_ally_of(active) and u.id != active.id]
        enemies = [u for u in simulated_battle.all_living_units if u.is_hostile_to(active)]

        threat_map = self.create_threat_map(allies, enemies)

        for enemy in enemies:
            score += active.ai.weights.enemy.calculate(enemy, threat_map) * unit_priority

        for ally in allies:
            score += active.ai.weights.friendly.calculate(ally, threat_map) * unit_priority

        score += active.ai.weights.personal.calculate(active, threat_map)

        return score

    def create_threat_map(self, allies, enemies):
        threat_map = ThreatMap(self.simulated_battle.bmap, self.skills)
        for enemy in enemies:
            threat_map.add_threat(enemy, self.simulated_battle.bmap)

        return threat_map


class Redoubtable_Ai(object):
    def __init__(self, battle, actor, skills):
        self.battle = battle
        self.actor = actor
        self.skills = skills
        self.bmap = battle.bmap

        self.weights = UnitScoreWeights(UnitScoreWeightEnemy(), UnitScoreWeightAlly(), UnitScoreWeightSelf())

    # def get_targets(self):
    #     friendly_list = []
    #     enemy_list = []
    #
    #     for enemy in self.battle.get_enemies_of(self.actor):
    #         distance, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (enemy.coords[1], enemy.coords[0]), self.bmap)
    #         enemy_list.append({"distance": distance, "unit": enemy, "path": path})
    #
    #     for ally in self.battle.get_allies_of(self.actor):
    #         distance, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (ally.coords[1], ally.coords[0]), self.bmap)
    #         friendly_list.append({"distance": distance, "unit": ally, "path": path})
    #
    #     return enemy_list, friendly_list
    #
    # def create_threat_map(self):
    #     threat_map = ThreatMap(self.battle.bmap)
    #     for enemy in self.enemy_list:
    #         threat_map.add_threat(enemy["unit"], self.battle.bmap)
    #
    #     return threat_map

    def evaluate(self):
        start = timer()
        simulation = SimulationHandler(self.actor, self.battle, self.skills)

        replace_this_value = self.actor.coords

        possible_moves = []
        baseline_score = simulation.simulate_move(None, None, None, None)
        # add wait option
        possible_moves.append({'score': baseline_score, 'skill': None, 'target': None, 'destination': None})

        for skill in [self.skills[s] for s in self.actor.skillset]:
            if self.battle.get_mp_cost(skill, self.actor) > self.actor.mp:
                continue
            # all target tiles reachable by this spell, using up to full movement
            valid_target_tiles = RN2_battle_logic.get_valid_tiles(self.actor.coords, self.actor.move, skill, self.battle.bmap)

            # spells cast on these tiles can reach at least one tile within the move range of actor
            if skill.aoe_type == 'circular':
                tiles_can_include_actor = RN2_battle_logic.get_valid_tiles(self.actor.coords, self.actor.move, skill, self.battle.bmap, use_aoe=True)
            else:
                tiles_can_include_actor = []

            for target_option in valid_target_tiles:
                # todo: can store this value for a target/range if needed
                affected_tiles = RN2_battle_logic.calculate_affected_area(target_option,
                                                                          replace_this_value,
                                                                          skill,
                                                                          simulation.simulated_battle.bmap)

                targets_in_aoe = (simulation.simulated_battle.get_targets_for_area(self.actor, affected_tiles, skill) != ([], [], []))

                if targets_in_aoe:
                    score = simulation.simulate_move(skill, target_option, affected_tiles)
                    possible_move = {'score': score, 'skill': skill, 'target': target_option, 'actor_included': False}
                    possible_moves.append(possible_move)
                    simulation.reset()

                if len(tiles_can_include_actor):
                    score = simulation.simulate_move(skill, target_option, affected_tiles, include_actor=True)
                    possible_move = {'score': score, 'skill': skill, 'target': target_option, 'actor_included': True}
                    possible_moves.append(possible_move)
                    simulation.reset()

        end = timer()
        print 'evaluate run time:', (end - start), 'seconds:', len(possible_moves), 'results.'
        return possible_moves
    #
    # def choose_safest_tile(self, skill=None, loc=None):
    #     results = []
    #     success = False
    #     for tile in self.move_range:
    #         if skill and RN2_battle_logic.grid_distance(tile, loc) > skill.range:
    #             continue
    #         else:
    #             results.append({'threat_level': self.threat_map.get_threat_for_tile(tile), 'loc': tile})
    #             success = True
    #
    #     if not success:
    #         print "No possible path to tile: ", loc
    #         exit()
    #
    #     results.sort()
    #     return results[0]
    #
    # def advance_towards_enemy(self):
    #     #todo: attack or retreat based on aggression level
    #     advance_paths = []
    #     for n in self.enemy_list:
    #         path = pathfind((self.actor.coords[1], self.actor.coords[0]), (n['unit'].coords[1], n['unit'].coords[0]), self.battle.bmap)[1]
    #         value = n['unit'].priority_value - len(path)
    #         dist = min(len(path), self.actor.move) - 1
    #
    #         if path and dist >= 0:
    #             if path[dist] == n['unit'].coords:
    #                 dist -= 1
    #
    #             advance_paths.append((value, path[dist]))
    #
    #     advance_paths.sort(reverse=True)
    #
    #     if advance_paths:
    #         return advance_paths[0]
    #     else:
    #         return (0, (self.actor.coords[1], self.actor.coords[0]))

    def get_action(self):
        possible_moves = self.evaluate()

        if possible_moves:
            possible_moves.sort(key=lambda x: x['score'], reverse=True)
            chosen_action = possible_moves[0]

            print possible_moves[:10]

            if chosen_action.get('destination'):
                path = pathfind((self.actor.coords[1], self.actor.coords[0]), (chosen_action['destination'][1],
                                                                               chosen_action['destination'][0]), self.battle.bmap)
            else:
                path = [0, [self.actor.coords]]

            return chosen_action['skill'], chosen_action['target'], path[1]
        else:
            return None, None, None
