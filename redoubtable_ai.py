from RN2_AI import pathfind
from timeit import default_timer as timer

import RN2_battle_logic
import RN2_battle
import dummy_ui
import copy
import random
import itertools
import importlib


class ThreatMap:
    def __init__(self, battle_map, skills):
        self.tmap = []
        self.skills = skills
        self.battle_map = battle_map

        self.stored_values = {}

        self.reset()

        self.dynamic_c = 0

    def reset(self):
        self.tmap = []
        for x in range(50):
            self.tmap.append([])
            for y in range(25):
                self.tmap[x].append(0)

    def add_threat(self, threat, bmap):
        threat_x = threat.coords[0]
        threat_y = threat.coords[1]

        for x in range(50):
            for y in range(25):
                self.tmap[x][y] += 75 - (abs(threat_x - x) + abs(threat_y - y))
    #
    # def add_threat(self, threat, bmap):
    #     skills = [self.skills[s] for s in threat.skillset]
    #     skills.sort(key=lambda x: min(12, (x.range + x.aoe_size)) / max(1, x.mp), reverse=True)
    #
    #     if 0:
    #         pass
    #     if self.stored_values.get(threat.coords) and self.stored_values[threat.coords].get(threat.move) and self.stored_values[threat.coords][threat.move].get(skills[0].range):
    #         threat_tiles = self.stored_values[threat.coords][threat.move][skills[0].range]
    #         self.dynamic_c += 1
    #     else:
    #         threat_tiles = RN2_battle_logic.get_valid_tiles(threat.coords, threat.move, skills[0], bmap, use_aoe=True)
    #
    #         if not self.stored_values.get(threat.coords):
    #             self.stored_values[threat.coords] = {}
    #             self.stored_values[threat.coords][threat.move] = {}
    #
    #         elif not self.stored_values[threat.coords].get(threat.move):
    #             self.stored_values[threat.coords][threat.move] = {}
    #
    #         self.stored_values[threat.coords][threat.move][skills[0].range] = threat_tiles
    #
    #     for t in threat_tiles:
    #         if self.tmap[t[0]][t[1]] > 0:
    #             self.tmap[t[0]][t[1]] += 1

    def get_threat_for_tile(self, coords):
        return self.tmap[coords[0]][coords[1]]


class QuadraticWeight(object):
    def __init__(self, current_value, ideal_value, exponent):
        self.current_value = current_value
        self.ideal_value = ideal_value
        self.exponent = exponent

    def calculate(self):
        return (self.current_value / self.ideal_value) ** self.exponent


class LinearWeight(object):
    def __init__(self, current_value, ideal_value):
        self.current_value = min(current_value, ideal_value)
        self.ideal_value = ideal_value

    def calculate(self):
        return self.current_value / self.ideal_value


class UnitScoreWeightDefaults(object):
    def __init__(self):
        self.hp = 0
        self.mp = 0
        self.attack = 0
        self.defense = 0
        self.agility = 0
        self.move = 0
        self.magic = 0
        self.resistance = 0

        self.total_damage_over_time = 0

        self.is_low_hp = 0
        self.low_hp_threshold = 0

        self.tile_threat = 0
        self.preferred_threat_level = 0

    def calculate(self, unit, threat_map):
        score = 0
        score += self.hp * max(0, unit.hp)
        score += self.mp * unit.mp
        score += self.attack * max(0, unit.attack)
        score += self.defense * max(0, unit.defense)
        score += self.agility * max(0, unit.agility)
        score += self.move * max(0, unit.move)
        score += self.magic * max(0, unit.magic)
        score += self.resistance * max(0, unit.resistance)

        score += self.get_damage_over_time_score(unit) * self.total_damage_over_time

        score += self.is_low_hp if (unit.hp / unit.maxhp) * 100 < self.low_hp_threshold else 0

        score += max(0, 750 - abs(self.preferred_threat_level - threat_map.get_threat_for_tile(unit.coords))) * self.tile_threat

        return score

    def calculate_location_score(self, threat_on_tile):
        return abs(self.preferred_threat_level - threat_on_tile) * self.tile_threat

    def get_damage_over_time_score(self, unit):
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


class UnitScoreWeightEnemyDefaults(UnitScoreWeightDefaults):
    def __init__(self):
        UnitScoreWeightDefaults.__init__(self)
        self.hp = -10
        self.attack = -20
        self.defense = -20
        self.move = -30
        self.magic = -20
        self.resistance = -20

        self.total_damage_over_time = 8

        self.is_low_hp = 100
        self.low_hp_threshold = 30

        # todo: these plusses can acutally make leaving an enemy alive score higher than killing it. rethink how this works to be less confusing and opaque and buggy

        self.tile_threat = 0.01
        self.preferred_threat_level = 750


class UnitScoreWeightAllyDefaults(UnitScoreWeightDefaults):
    def __init__(self):
        UnitScoreWeightDefaults.__init__(self)
        self.hp = 2
        self.attack = 15
        self.defense = 15
        self.move = 15
        self.magic = 15
        self.resistance = 15

        self.total_damage_over_time = -1

        self.is_low_hp = -10
        self.low_hp_threshold = 30

        self.tile_threat = 0.01
        self.preferred_threat_level = 550


class UnitScoreWeightSelfDefaults(UnitScoreWeightDefaults):
    def __init__(self):
        UnitScoreWeightDefaults.__init__(self)
        self.hp = 25
        self.mp = 40
        self.attack = 60
        self.defense = 60
        self.move = 80
        self.magic = 60
        self.resistance = 60

        self.total_damage_over_time = -20

        self.is_low_hp = -100
        self.low_hp_threshold = 30

        self.tile_threat = 0.02
        self.preferred_threat_level = 100


class AiWeightsDefault(object):
    def __init__(self, enemy, friendly, personal, skills):
        self.skills = skills

        # objects to score state for each type of unit
        self.enemy = enemy
        self.friendly = friendly
        self.personal = personal

        self.randomness_percentage = 5

        # scores to prioritize units within above categories
        self.is_summon = 0.5
        self.is_minion = 0.3
        self.can_heal = 1.5
        self.can_summon = 1.2
        # todo: for summons: summon already exists

    def get_priority_for_unit(self, unit):
        priority_modifier = 1
        priority_modifier *= self.is_summon if unit.summoned_by else 1
        priority_modifier *= self.can_heal if [self.skills[s] for s in unit.skillset if self.skills[s].targets.friendly.damage.get_average_damage(unit) < 1] else 1
        priority_modifier *= self.can_summon if [self.skills[s] for s in unit.skillset if self.skills[s].add_unit] else 1
        priority_modifier *= self.is_minion if unit.is_minion else 1

        return priority_modifier


class SimulationHandler(object):
    def __init__(self, unit, battle, skills):
        self.active_unit = unit
        self.unit_states = {}
        self.skills = skills
        self.threat_map = None
        # this is a reference to the actual unit using this AI, not a cloned simulation
        self.actual_unit = unit

        self.total_time_creating_threat_maps = 0
        self.times_recreating_threat_map = 0
        self.time_spent_resetting = 0

        # start1 = timer()
        simulated_battle = RN2_battle.SimulatedBattle({}, battle.actor_data, {}, copy.deepcopy(battle.bmap), {})
        # end1 = timer()
        # print "Initiating battle class time:", end1-start1

        simulated_battle.all_living_units = copy.deepcopy(battle.all_living_units)

        for unit in simulated_battle.all_living_units:
            unit.event = dummy_ui.DummyUi()
            self.unit_states[unit.id] = copy.deepcopy(unit.current_state())

        simulated_battle.active = [u for u in simulated_battle.all_living_units if u.id == self.active_unit.id][0]

        self.simulated_battle = simulated_battle
        self.reset()

    def reset(self):
        def reset_units(unit_list):
            remove_list = []
            for r_unit in unit_list:
                try:
                    r_unit.set_state(copy.deepcopy(self.unit_states[r_unit.id]))
                except KeyError:
                    remove_list.append(r_unit)

            for r_unit in remove_list:
                unit_list.remove(r_unit)

        start = timer()
        for unit in self.simulated_battle.all_living_units:
            self.simulated_battle.bmap.remove_unit(unit)

        reset_units(self.simulated_battle.all_living_units)

        for unit in self.simulated_battle.all_living_units:
            self.simulated_battle.bmap.place_unit(unit, unit.coords)
            unit.event = dummy_ui.DummyUi()

        self.simulated_battle.active = [u for u in self.simulated_battle.all_living_units if u.id == self.active_unit.id][0]

        self.simulated_battle.bmap.remove_unit(self.simulated_battle.active)
        self.simulated_battle.active.coords = (-1, -1)
        end = timer()
        self.time_spent_resetting += (end - start)

    def simulate_move(self, chosen_skill, target_tile, affected_tiles, include_actor=False):
        if chosen_skill:
            if include_actor:
                self.simulated_battle.bmap.remove_unit(self.simulated_battle.active)
                self.simulated_battle.active.coords = random.choice([affected_tiles])[0]

            self.simulated_battle.execute_skill(self.simulated_battle.active, chosen_skill, affected_tiles, target_tile)

        has_move_effects = chosen_skill and (chosen_skill.targets.enemy.move_effects or chosen_skill.targets.friendly.move_effects or chosen_skill.targets.self.move_effects)
        recreate_threat_map = chosen_skill and (has_move_effects or chosen_skill.add_unit or chosen_skill.add_minion)

        return self.score_battle_state(self.simulated_battle, self.simulated_battle.active, recreate_threat_map)

    def score_battle_state(self, simulated_battle, active, recreate_threat_map=False):
        """
        Based on passed parameters that weight criteria, score a hypothetical battle state for favorabilitiousness to the AI
        calling this function
        """

        score = 0

        allies = [u for u in simulated_battle.all_living_units if u.is_ally_of(simulated_battle.active) and u.id != active.id]
        enemies = [u for u in simulated_battle.all_living_units if u.is_hostile_to(simulated_battle.active)]

        if recreate_threat_map or not self.threat_map:
            start = timer()
            self.create_threat_map(enemies)
            end = timer()
            self.total_time_creating_threat_maps += (end-start)
            self.times_recreating_threat_map += 1

        for enemy in enemies:
            score += min(-1, self.actual_unit.ai.weights.enemy.calculate(enemy, self.threat_map) * self.actual_unit.ai.weights.get_priority_for_unit(enemy))

        for ally in allies:
            score += max(1, self.actual_unit.ai.weights.friendly.calculate(ally, self.threat_map) * self.actual_unit.ai.weights.get_priority_for_unit(ally))

        score += max(1, self.actual_unit.ai.weights.personal.calculate(active, self.threat_map))

        return score

    def create_threat_map(self, enemies):
        if not self.threat_map:
            self.threat_map = ThreatMap(self.simulated_battle.bmap, self.skills)
        else:
            self.threat_map.reset()

        for enemy in enemies:
            self.threat_map.add_threat(enemy, self.simulated_battle.bmap)


class RedoubtableAi(object):
    def __init__(self, battle, actor, skills):
        self.battle = battle
        self.actor = actor
        self.skills = skills
        self.bmap = battle.bmap

        try:
            ai_data = importlib.import_module('ai_classes.{}'.format(self.actor.ai))
            self.weights = ai_data.AiWeights(ai_data.UnitScoreWeightEnemy(), ai_data.UnitScoreWeightAlly(), ai_data.UnitScoreWeightSelf(), self.skills)
        except ImportError:
            self.weights = AiWeightsDefault(UnitScoreWeightEnemyDefaults(), UnitScoreWeightAllyDefaults(),
                                            UnitScoreWeightSelfDefaults(), self.skills)

    def evaluate(self):
        start = timer()
        simulation = SimulationHandler(self.actor, self.battle, self.skills)
        end2 = timer()

        move_range = RN2_battle_logic.calculate_move_range(self.actor, self.battle.bmap)

        possible_moves = []
        baseline_score = simulation.simulate_move(None, None, None, None)
        # add wait option
        possible_moves.append({'score': baseline_score, 'skill': None, 'target': None, 'destination': None})

        # add advance option
        enemy_list = []
        for enemy in simulation.simulated_battle.get_enemies_of(simulation.simulated_battle.active):
            distance, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (enemy.coords[1], enemy.coords[0]), simulation.simulated_battle.bmap)
            enemy_list.append({"distance": distance, "unit": enemy, "path": path})

        advance_to = sorted(enemy_list, key=lambda x: self.weights.get_priority_for_unit(x['unit']), reverse=True)[0]

        advance_path = advance_to['path'][:self.actor.move+1]

        try:
            advance_path.remove(advance_to['unit'].coords)
        except ValueError:
            pass

        if advance_path:
            eval_move = self.evaluate_move(advance_path, self.actor,
                                           simulation.threat_map)
            advance_score = baseline_score + max(1, self.actor.ai.weights.personal.calculate_location_score(eval_move['threat']))

            possible_moves.append({'score': advance_score, 'skill': None, 'target': None, 'destination': eval_move['destination']})

        for skill in [self.skills[s] for s in self.actor.skillset]:
            if self.battle.get_mp_cost(skill, self.actor) > self.actor.mp:
                continue

            # all target tiles reachable by this spell, using up to full movement
            valid_target_tiles = RN2_battle_logic.get_valid_tiles(self.actor.coords, self.actor.move, skill, self.battle.bmap)

            # For non standard aoes dependant on caster position. In all other cases, the position should not be
            # considered in simulation but is required by the calculation, hence the assignment of position to (-1, -1)
            valid_target_tiles_with_position = []
            for t in valid_target_tiles:
                if skill.aoe_type == 'circular':
                    valid_target_tiles_with_position.append((t, (-1, -1)))
                else:
                    # todo: only works on non standard aoe skills of range 1
                    positions = RN2_battle_logic.get_neighboring_points(t)
                    valid_target_tiles_with_position.extend([(t, p) for p in positions if p in move_range])

            if skill.add_unit or skill.add_minion:
                # for skills intended for use on an empty tile (summons only, for now)
                for target_option in [t for t in valid_target_tiles if simulation.simulated_battle.bmap.get_tile_at(t).is_movable]:
                    move_options_for_target_and_skill = []

                    # todo: dry up
                    for tile in move_range:
                        if (skill and RN2_battle_logic.grid_distance(tile, target_option) > skill.range) or tile==target_option:
                            continue
                        else:
                            move_options_for_target_and_skill.append(tile)

                    affected_tiles = RN2_battle_logic.calculate_affected_area(target_option,
                                                                              (-1, -1),
                                                                              skill,
                                                                              simulation.simulated_battle.bmap)

                    score = simulation.simulate_move(skill, target_option, affected_tiles)

                    eval_move = self.evaluate_move(move_options_for_target_and_skill, self.actor,
                                                   simulation.threat_map)
                    score += self.actor.ai.weights.personal.calculate_location_score(eval_move['threat'])

                    possible_moves.append({'score': score, 'skill': skill, 'target': target_option, 'destination': eval_move['destination']})

                    simulation.reset()

            else:
                # for skills intended for use on a unit
                for target_option, position in valid_target_tiles_with_position:

                    # all tiles within range of this target for this skill
                    move_options_for_target_and_skill = []

                    if position == (-1, -1):
                        for tile in move_range:
                            if skill and RN2_battle_logic.grid_distance(tile, target_option) > skill.range:
                                continue
                            else:
                                move_options_for_target_and_skill.append(tile)
                    else:
                        move_options_for_target_and_skill = [position]

                    affected_tiles = RN2_battle_logic.calculate_affected_area(target_option,
                                                                              position,
                                                                              skill,
                                                                              simulation.simulated_battle.bmap)

                    targets_in_aoe = (simulation.simulated_battle.get_targets_for_area(self.actor, affected_tiles, skill) != ([], [], []))

                    # simulate action without actor in aoe, if such an action is possible
                    move_options_for_target_and_skill_not_in_aoe = set(move_options_for_target_and_skill) - set(affected_tiles)

                    if targets_in_aoe and len(move_options_for_target_and_skill_not_in_aoe):
                        score = simulation.simulate_move(skill, target_option, affected_tiles)

                        if position == (-1, -1):
                            eval_move = self.evaluate_move(move_options_for_target_and_skill_not_in_aoe, self.actor, simulation.threat_map)
                            score += self.actor.ai.weights.personal.calculate_location_score(eval_move['threat'])
                            destination = eval_move['destination']

                        else:
                            score += self.actor.ai.weights.personal.calculate_location_score(simulation.threat_map.get_threat_for_tile(position))
                            destination = position

                        possible_move = {'score': score, 'skill': skill,
                                         'target': target_option, 'destination': destination}

                        possible_moves.append(possible_move)
                        simulation.reset()

                    # simulate action with actor in aoe, if such an action is possible
                    move_options_for_target_and_skill_inside_aoe = set(move_options_for_target_and_skill) & set(affected_tiles)

                    if len(move_options_for_target_and_skill_inside_aoe) and not skill.targets.self.ignored and not skill.targets_empty and not (skill.targets.self.is_harmful and not targets_in_aoe):
                        score = simulation.simulate_move(skill, target_option, affected_tiles, include_actor=True)

                        eval_move = self.evaluate_move(move_options_for_target_and_skill_inside_aoe, self.actor, simulation.threat_map)
                        score += self.actor.ai.weights.personal.calculate_location_score(eval_move['threat'])

                        # print 'score after move (in) to ', eval_move['destination'], score, '\n'

                        possible_move = {'score': score, 'skill': skill, 'target': target_option,
                                         'actor_included': True, 'destination': eval_move['destination']}

                        possible_moves.append(possible_move)
                        simulation.reset()

        end = timer()
        print 'evaluate run time:', (end - start), 'seconds:', len(possible_moves), 'results.'

        print 'total_time_creating_threat_maps', simulation.total_time_creating_threat_maps, simulation.times_recreating_threat_map, 'times', simulation.total_time_creating_threat_maps/simulation.times_recreating_threat_map, 'per run'
        #
        # print 'stored values used {} times.'.format(simulation.threat_map.dynamic_c)
        # print 'total time resetting: {}\n'.format(simulation.time_spent_resetting)
        print "simulation handler initiation time:", end2 - start, int((end2-start)/(end-start) * 100), '% of total runtime :('
        # for possible_move in possible_moves:
        #     possible_move['score'] *= (random.randint(100 - self.weights.randomness_percentage, 100 + self.weights.randomness_percentage) / 100.0)

        return possible_moves

    def evaluate_move(self, tiles_to_evaluate, actor, threat_map):
        keyfunc = lambda x: abs(threat_map.get_threat_for_tile(x) - actor.ai.weights.personal.preferred_threat_level)
        tiles_to_evaluate = sorted(tiles_to_evaluate, key=keyfunc)

        eval_tiles = {}
        for k, g in itertools.groupby(tiles_to_evaluate, keyfunc):
            eval_tiles[k] = list(g)

        best = min(eval_tiles.keys())

        return {'threat': best, 'destination': eval_tiles[best][-1]}

    def get_action(self):
        possible_moves = self.evaluate()

        if possible_moves:
            possible_moves.sort(key=lambda x: x['score'], reverse=True)
            top_score = possible_moves[0]['score']

            top_score_moves = list(filter(lambda x: x['score'] == top_score, possible_moves))

            chosen_action = random.choice(top_score_moves)

            possible_moves.sort(key=lambda x: x['skill'])
            keyfunc = lambda x: x['skill']
            options_for_each = {}
            for k, g in itertools.groupby(possible_moves, keyfunc):
                options_for_each[k] = list(g)

            for k in options_for_each.keys():
                if len(options_for_each[k]):
                    print k, len(options_for_each[k]), 'best:', options_for_each[k]

            if chosen_action.get('destination'):
                path = pathfind((self.actor.coords[1], self.actor.coords[0]),
                                (chosen_action['destination'][1], chosen_action['destination'][0]),
                                self.battle.bmap)
            else:
                path = [0, [self.actor.coords]]

            return chosen_action['skill'], chosen_action['target'], path[1]
        else:
            return None, None, None
