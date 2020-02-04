from RN2_AI import pathfind
from timeit import default_timer as timer

from RN2_battle_logic import get_targetable_tiles, calculate_affected_area, calculate_range, calculate_move_range, calculate_skill_range, get_distance
import dummy_ui
import copy
import random
import itertools
import importlib


class DistanceCache:
    def __init__(self):
        self.distances = None

    def make(self, units, bmap):
        cache = {}
        for unit in units:
            cache[unit.id] = {}
            for unit2 in units:
                if unit.id == unit2.id:
                    continue

                cache[unit.id][unit2.id] = {}
                if cache.get(unit2.id) and cache[unit2.id].get(unit.id):
                    cache[unit.id][unit2.id] = cache[unit2.id].get(unit.id)
                else:
                    distance, path = pathfind((unit.coords[1], unit.coords[0]),
                                              (unit2.coords[1], unit2.coords[0]), bmap)
                    cache[unit.id][unit2.id] = distance

        self.distances = cache

    def alter(self, unit, units, bmap):
        if self.distances.get(unit.id) and unit.is_dead:
            del self.distances[unit.id]

        if not self.distances.get(unit.id):
            self.distances[unit.id] = {}

        for unit2 in units:
            distance, path = pathfind((unit.coords[1], unit.coords[0]),
                                      (unit2.coords[1], unit2.coords[0]), bmap)
            self.distances[unit.id][unit2.id] = distance
            self.distances[unit2.id][unit.id] = distance

    def get(self, unit):
        return self.distances.get(unit)


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
                self.tmap[x].append(1)

    def add_threat(self, threat, bmap):
        if not threat.can_act:
            return

        skills = [self.skills[s] for s in threat.skillset]

        # determine a threat range for this unit
        skills.sort(key=lambda x: (x.range + x.aoe_size) if (threat.mp + 1 >= x.mp and x.aoe_type == "circular") else 0, reverse=True)
        threat_tiles = get_targetable_tiles(threat.coords, threat.move, skills[0], bmap, use_aoe=True)

        for t in threat_tiles:
            self.tmap[t[0]][t[1]] += 1

    def get_threat_for_tile(self, coords):
        return self.tmap[coords[0]][coords[1]]


class QuadraticWeight(object):
    def __init__(self, current_value, ideal_value, exponent):
        self.current_value = current_value
        self.ideal_value = ideal_value
        self.exponent = exponent

    def calculate(self, multiplier=1):
        result = ((max(0, self.current_value) / self.ideal_value) ** self.exponent) * multiplier
        return result


class LinearWeight(object):
    def __init__(self, current_value, ideal_value):
        self.current_value = min(current_value, ideal_value)
        self.ideal_value = ideal_value

    def calculate(self, multiplier=1):
        try:
            return (self.current_value / self.ideal_value) * multiplier
        except ZeroDivisionError:
            return 0.5


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
        self.total_damage_over_time_penalty = 0.3

        self.position_priority = 1

    def calculate(self, unit, threat_map=None, distances=None, enemies=None):
        aggression = getattr(unit, 'aggression', 0.9)

        scores = []
        for i in range(self.hp):
            modified_hp = unit.hp - (self.get_damage_over_time(unit) * self.total_damage_over_time_penalty)
            scores.append(QuadraticWeight(modified_hp, unit.maxhp, 0.33).calculate())
        for i in range(self.mp):
            scores.append(LinearWeight(unit.mp, unit.maxmp).calculate())
        for i in range(self.attack):
            scores.append(LinearWeight(unit.attack, unit.base_attack * 2).calculate())
        for i in range(self.defense):
            scores.append(LinearWeight(unit.defense, unit.base_defense * 2).calculate())
        for i in range(self.move):
            scores.append(LinearWeight(unit.move, unit.base_move * 2).calculate())
        for i in range(self.magic):
            scores.append(LinearWeight(unit.magic, unit.base_magic * 2).calculate())
        for i in range(self.resistance):
            scores.append(LinearWeight(unit.resistance, unit.base_resistance * 2).calculate())

        if threat_map:
            offense = self.calculate_offensive_utility(unit, enemies, distances)
            if threat_map:
                defense = self.calculate_defensive_utility(unit.coords, threat_map)
            else:
                defense = 0
            position_score = self.calculate_total_position_utility(offense, defense, aggression)

            for i in range(self.position_priority):
                scores.append(position_score)

        score = sum(scores) / max(1, len(scores))

        return score

    def get_damage_over_time(self, unit):
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

    def calculate_offensive_utility(self, unit, enemies, distances):
        # placeholder for a more robust priority analyzer
        priority_list = {}
        enemies = [u for u in enemies]
        enemies.sort(key=lambda x: len(x.skillset), reverse=True)

        ideal = len(enemies[0].skillset)
        for e in enemies:
            priority_list[e.id] = LinearWeight(len(e.skillset), ideal).calculate()

        scores = []
        for i, enemy in enumerate(enemies):
            distance = distances.get(unit.id)[enemy.id]
            scores.append(LinearWeight(1, distance).calculate() * priority_list[enemy.id])

        return sum(scores) / max(len(scores), 1)

    def calculate_defensive_utility(self, coords, threat_map):
        return LinearWeight(1, threat_map.get_threat_for_tile(coords)).calculate()

    def calculate_total_position_utility(self, offense, defense, aggression):
        offense_score = offense * aggression
        defense_score = defense * (1 - aggression)

        return offense_score + defense_score


class UnitScoreWeightEnemyDefaults(UnitScoreWeightDefaults):
    def __init__(self):
        UnitScoreWeightDefaults.__init__(self)
        self.hp = 10
        self.attack = 2
        self.defense = 2
        self.move = 3
        self.magic = 2
        self.resistance = 2

        self.position_priority = 1


class UnitScoreWeightAllyDefaults(UnitScoreWeightDefaults):
    def __init__(self):
        UnitScoreWeightDefaults.__init__(self)
        self.hp = 3
        self.attack = 1
        self.defense = 1
        self.move = 1
        self.magic = 1
        self.resistance = 1

        self.position_priority = 1


class UnitScoreWeightSelfDefaults(UnitScoreWeightDefaults):
    def __init__(self):
        UnitScoreWeightDefaults.__init__(self)
        self.hp = 10
        self.mp = 4
        self.attack = 2
        self.defense = 6
        self.move = 6
        self.magic = 6
        self.resistance = 6

        self.position_priority = 2


class AiWeightsDefault(object):
    def __init__(self, enemy, friendly, personal, skills):
        self.skills = skills

        # objects to score state for each type of unit
        self.enemy = enemy
        self.friendly = friendly
        self.personal = personal


class SimulationHandler(object):
    def __init__(self, unit, battle, skills):
        self.active_unit = unit
        self.unit_states = {}
        self.skills = skills

        self.stored_threat_maps = {}
        # this is a reference to the actual unit using this AI, not a cloned simulation
        self.actual_unit = unit

        self.total_time_creating_threat_maps = 0
        self.times_recreating_threat_map = 1
        self.time_spent_resetting = 0
        self.total_function_run_times = {}

        from RN2_battle import SimulatedBattle

        simulated_battle = SimulatedBattle({}, battle.actor_data, {}, copy.deepcopy(battle.bmap), {})
        simulated_battle.all_living_units = copy.deepcopy(battle.all_living_units)

        for unit in simulated_battle.all_living_units:
            unit.event = dummy_ui.DummyUi()
            self.unit_states[unit.id] = copy.deepcopy(unit.current_state())

        simulated_battle.active = [u for u in simulated_battle.all_living_units if u.id == self.active_unit.id][0]

        self.simulated_battle = simulated_battle
        enemies = [u for u in simulated_battle.all_living_units if u.is_hostile_to(simulated_battle.active)]
        self.default_threat_map = self.create_threat_map(enemies, simulated_battle.bmap)

        self.distance_cache = DistanceCache()
        self.distance_cache.make(simulated_battle.all_living_units, simulated_battle.bmap)
        self.distance_cache_orig = copy.deepcopy(self.distance_cache)

        self.reset()
        self.alter_count = 0

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

        for unit in self.simulated_battle.all_living_units:
            self.simulated_battle.bmap.remove_unit(unit)

        reset_units(self.simulated_battle.all_living_units)

        for unit in self.simulated_battle.all_living_units:
            self.simulated_battle.bmap.place_unit(unit, unit.coords)
            unit.event = dummy_ui.DummyUi()

        self.distance_cache = copy.deepcopy(self.distance_cache_orig)
        self.simulated_battle.active = [u for u in self.simulated_battle.all_living_units if u.id == self.active_unit.id][0]

    def simulate_action_with_move(self, chosen_skill, target_tile, affected_tiles, destination):
        recreate_threat_map = False
        units = self.simulated_battle.all_living_units

        if destination:
            self.simulated_battle.bmap.remove_unit(self.simulated_battle.active)
            self.simulated_battle.active.coords = destination
            self.distance_cache.alter(self.simulated_battle.active, units, self.simulated_battle.bmap)
            self.alter_count += 1

        if chosen_skill:
            self.simulated_battle.execute_skill(self.simulated_battle.active, chosen_skill, affected_tiles, target_tile)

            has_move_effects = chosen_skill and (chosen_skill.targets.enemy.move_effects or chosen_skill.targets.friendly.move_effects or chosen_skill.targets.self.move_effects) # or slow or haste or root....

            if chosen_skill.add_unit or chosen_skill.add_minion:
                recreate_threat_map = True
                for unit in units:
                    if not self.distance_cache.get(unit.id):
                        self.distance_cache.alter(unit, units, self.simulated_battle.bmap)
                        self.alter_count += 1

            #todo: remove dead units

            if chosen_skill.targets.self.has_movement_effects or chosen_skill.targets.friendly.has_movement_effects or chosen_skill.targets.enemy.has_movement_effects:
                recreate_threat_map = True
                for unit in [u for u in units if u.coords in affected_tiles]:
                    self.distance_cache.alter(unit, units, self.simulated_battle.bmap)
                    self.alter_count += 1

        return self.score_battle_state_with_map(self.simulated_battle, self.simulated_battle.active, recreate_threat_map=recreate_threat_map)

    def simulate_action(self, chosen_skill, target_tile, affected_tiles):
        if affected_tiles:
            #remove actor from simulation for this calculation
            affected_tiles_without_actor = list(affected_tiles)
            try:
                affected_tiles_without_actor.remove(self.simulated_battle.active.coords)
            except ValueError:
                affected_tiles_without_actor = affected_tiles

        if chosen_skill:
            self.simulated_battle.execute_skill(self.simulated_battle.active, chosen_skill, affected_tiles_without_actor, target_tile)

        return self.score_battle_state(self.simulated_battle, self.simulated_battle.active)

    def score_battle_state_with_map(self, simulated_battle, active, recreate_threat_map=False):
        """
        Based on passed parameters that weight criteria, score a hypothetical battle state for favorabilitiousness to the AI
        calling this function
        """

        allies = [u for u in simulated_battle.all_living_units if u.is_ally_of(simulated_battle.active) and u.id != active.id]
        enemies = [u for u in simulated_battle.all_living_units if u.is_hostile_to(simulated_battle.active)]
        enemies_of_enemies = [u for u in simulated_battle.all_living_units if not u.is_hostile_to(simulated_battle.active)]

        if recreate_threat_map:
            threat_map = self.timed_function_call(self.create_threat_map)(enemies, simulated_battle.bmap)
        else:
            threat_map = self.default_threat_map

        scores = []
        for enemy in enemies:
            scores.append(1 - self.actual_unit.ai.weights.enemy.calculate(enemy, None, self.distance_cache, enemies_of_enemies))

        for ally in allies:
            scores.append(self.actual_unit.ai.weights.friendly.calculate(ally, threat_map, self.distance_cache, enemies))

        scores.append(self.actual_unit.ai.weights.personal.calculate(active, threat_map, self.distance_cache, enemies))

        return sum(scores) / max(1, len(scores))

    def score_battle_state(self, simulated_battle, active):
        """
        Based on passed parameters that weight criteria, score a hypothetical battle state for favorabilitiousness to the AI
        calling this function
        """

        allies = [u for u in simulated_battle.all_living_units if u.is_ally_of(simulated_battle.active) and u.id != active.id]
        enemies = [u for u in simulated_battle.all_living_units if u.is_hostile_to(simulated_battle.active)]

        scores = []
        for enemy in enemies:
            scores.append(1 - self.actual_unit.ai.weights.enemy.calculate(enemy))

        for ally in allies:
            scores.append(self.actual_unit.ai.weights.friendly.calculate(ally))

        scores.append(self.actual_unit.ai.weights.personal.calculate(active))

        return sum(scores) / max(1, len(scores))

    def create_threat_map(self, enemies, bmap):
        threat_map = ThreatMap(bmap, self.skills)
        for enemy in enemies:
            threat_map.add_threat(enemy, bmap)

        return threat_map

    def timed_function_call(self, method):
        def wrapper(*args, **kwargs):
            start = timer()
            result = method(*args, **kwargs)
            end = timer()
            duration = (end-start)
            stats = self.total_function_run_times.get(method.__name__)
            if not stats:
                stats = {'count': 1, 'total_time': duration, 'avg_run_time': duration}
            else:
                stats['count'] += 1
                stats['total_time'] += duration
                stats['avg_run_time'] = stats['total_time'] / stats['count']

            self.total_function_run_times[method.__name__] = stats
            return result

        return wrapper


class RedoubtableAi(object):
    def __init__(self, battle, actor, skills):
        self.battle = battle
        self.actor = actor
        self.skills = skills
        self.bmap = battle.bmap
        self.total_function_run_times = {}

        try:
            ai_data = importlib.import_module('ai_classes.{}'.format(self.actor.ai))
            print(f'Loaded AI override: {self.actor.ai}')
            self.weights = ai_data.AiWeights(ai_data.UnitScoreWeightEnemy(), ai_data.UnitScoreWeightAlly(), ai_data.UnitScoreWeightSelf(), self.skills)
        except ImportError:
            self.weights = AiWeightsDefault(UnitScoreWeightEnemyDefaults(), UnitScoreWeightAllyDefaults(),
                                            UnitScoreWeightSelfDefaults(), self.skills)

    def timed_function_call(self, method):
        def wrapper(*args, **kwargs):
            start = timer()
            result = method(*args, **kwargs)
            end = timer()
            duration = (end-start)
            stats = self.total_function_run_times.get(method.__name__)
            if not stats:
                stats = {'count': 1, 'total_time': duration, 'avg_run_time': duration}
            else:
                stats['count'] += 1
                stats['total_time'] += duration
                stats['avg_run_time'] = stats['total_time'] / stats['count']

            self.total_function_run_times[method.__name__] = stats
            return result

        return wrapper

    def get_action(self):
        possible_moves = self.evaluate()

        top_score = possible_moves[0]['score']

        top_score_moves = list(filter(lambda x: x['score'] == top_score, possible_moves))
        chosen_action = random.choice(top_score_moves)

        possible_moves.sort(key=lambda x: str(x['skill']))
        keyfunc = lambda x: str(x['skill'])
        options_for_each = {}

        for k, g in itertools.groupby(possible_moves, keyfunc):
            options_for_each[k] = list(g)

        if chosen_action.get('destination'):
            path = pathfind((self.actor.coords[1], self.actor.coords[0]),
                            (chosen_action['destination'][1], chosen_action['destination'][0]),
                            self.battle.bmap)
        else:
            path = [0, [self.actor.coords]]

        return chosen_action['skill'], chosen_action['target'], path[1]

    def get_usable_skills(self, actor):
        usable_skills = []
        for skill in [self.skills[s] for s in actor.skillset]:
            if self.battle.get_mp_cost(skill, actor) > actor.mp:
                continue
            else:
                usable_skills.append(skill)
        return usable_skills

    def evaluate(self):
        start = timer()
        simulation = SimulationHandler(self.actor, self.battle, self.skills)

        move_range = calculate_move_range(self.actor, self.battle.bmap)

        enemies = simulation.simulated_battle.get_enemies_of_with_distance(simulation.simulated_battle.active)
        allies = simulation.simulated_battle.get_allies_of_with_distance(simulation.simulated_battle.active)
        _self = [{'unit': simulation.simulated_battle.active, 'distance': 0}]

        all_units = enemies + allies + _self

        possible_actions = []

        baseline_score = simulation.simulate_action(None, None, None)
        possible_actions.append({'score': baseline_score, 'skill': None, 'target': None})
        possible_actions_with_destinations = []
        cache = {}

        for skill in self.get_usable_skills(self.actor):
            if not skill.aoe_type == 'circular':
                continue

            max_affectable_range = self.actor.move + skill.range + skill.aoe_size

            #all target tiles reachable by this spell, using up to full movement
            valid_target_tiles = self.timed_function_call(
                get_targetable_tiles)(self.actor.coords, self.actor.move, skill, self.battle.bmap)

            # all tiles that can be affected by this skill
            affectable_tiles = self.timed_function_call(
                get_targetable_tiles)(self.actor.coords, self.actor.move, skill, self.battle.bmap, use_aoe=True)

            cache[skill.name] = {}

            if skill.add_minion or skill.add_unit:
                summon_score = None
                for t in affectable_tiles:
                    # only score once
                    summon_score = summon_score if summon_score else self.timed_function_call(
                        simulation.simulate_action)(skill, t, [t])
                    possible_actions.append(({'score': summon_score, 'skill': skill, 'target': t}))
                    self.timed_function_call(simulation.reset)()

            else:
                for unit in all_units:
                    # filter out of range units
                    if not unit['distance'] <= max_affectable_range and unit['unit'].coords in affectable_tiles:
                        continue
                    unit = unit['unit']

                    tiles_affecting_unit = self.timed_function_call(
                        calculate_range)(unit.coords, skill.aoe_size, self.battle.bmap, is_skill=True)

                    target_tiles_affecting_unit = set(tiles_affecting_unit).intersection(valid_target_tiles)
                    if not target_tiles_affecting_unit:
                        continue

                    for t in target_tiles_affecting_unit:
                        area = self.timed_function_call(calculate_affected_area)(t, (-1, -1), skill, self.battle.bmap)
                        if not cache.get(skill.name, {}).get(t):
                            score = self.timed_function_call(
                                simulation.simulate_action)(skill, t, area)
                            cache[skill.name][t] = score
                        else:
                            score = cache[skill.name][t]
                        possible_actions.append({'score': score, 'skill': skill, 'target': t})
                        self.timed_function_call(simulation.reset)()

        possible_actions.sort(key=lambda x: x['score'], reverse=True)

        for action in possible_actions[:5]:
            skill = action['skill']
            target = action['target']

            if not skill:
                for d in move_range:
                    score = self.timed_function_call(
                            simulation.simulate_action_with_move)(None, None, None, d)

                    possible_actions_with_destinations.append(
                        {'score': score, 'skill': None, 'target': None, 'destination': d})
                    self.timed_function_call(simulation.reset)()
            else:
                tiles_in_range_of_desired_target = self.timed_function_call(
                    calculate_range)(action['target'], skill.range, self.battle.bmap, is_skill=True)
                destinations_for_target_and_skill = set(move_range).intersection(tiles_in_range_of_desired_target)

                for d in destinations_for_target_and_skill:
                    area = self.timed_function_call(
                        calculate_affected_area)(action['target'], (-1, -1), action['skill'], self.battle.bmap)

                    score = self.timed_function_call(
                        simulation.simulate_action_with_move)(action['skill'], action['target'], area, d)

                    possible_actions_with_destinations.append({'score': score, 'skill': skill, 'target': target, 'destination': d})
                    self.timed_function_call(simulation.reset)()

        possible_actions_with_destinations.sort(key=lambda x: x['score'], reverse=True)
        end = timer()

        print('alters:', simulation.alter_count)
        print('evaluate run time:', (end - start), 'seconds:', len(possible_actions), 'possible actions.')
        print(self.total_function_run_times)

        return possible_actions_with_destinations
