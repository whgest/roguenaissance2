from RN2_AI import pathfind
import RN2_battle_logic
import dummy_ui
import copy
import RN2_battle
from timeit import default_timer as timer


class ThreatMap:
    def __init__(self, battle_map):
        tmap = []
        for x in range(50):
            tmap.append([])
            for y in range(25):
                tmap[x].append(1)

        self.tmap = tmap

    def add_threat(self, threat, bmap):
        threat_x = threat.coords[0]
        threat_y = threat.coords[1]

        for x in range(50):
            for y in range(25):
                self.tmap[x][y] = 75 - (abs(threat_x - x) + abs(threat_y - y))

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
        #print unit, unit.coords, abs(self.preferred_threat_level - threat_map.get_threat_for_tile(unit.coords)) * self.tile_threat

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
    def __init__(self, enemy, friendly, personal, preferred_threat_level=2):
        self.enemy = enemy
        self.friendly = friendly
        self.personal = personal


class SimulationHandler(object):
    def __init__(self, unit, battle):
        self.active_unit = unit
        self.unit_states = {}

        simulated_battle = RN2_battle.SimulatedBattle({}, battle.actor_data, {}, copy.deepcopy(battle.bmap), {})

        simulated_battle.all_living_units = copy.deepcopy(battle.all_living_units)
        for unit in simulated_battle.all_living_units:
            unit.event = dummy_ui.DummyUi()
            self.unit_states[unit.id] = copy.deepcopy(unit.current_state())

        simulated_battle.active = [u for u in simulated_battle.all_living_units if u.id == self.active_unit.id][0]

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

        # start = timer()
        reset_units(self.simulated_battle.all_living_units)
        # end = timer()
        # print 'reset units time:', (end - start)

        for unit in self.simulated_battle.all_living_units:
            self.simulated_battle.bmap.place_unit(unit, unit.coords)
            unit.event = dummy_ui.DummyUi()

        self.simulated_battle.active = [u for u in self.simulated_battle.all_living_units if u.id == self.active_unit.id][0]

    def simulate_move(self, chosen_skill, target_tile, destination, affected_tiles):
        if destination and destination != self.simulated_battle.active.coords:
            self.simulated_battle.move_unit(self.simulated_battle.active, destination)

        if chosen_skill:
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

        start = timer()
        threat_map = self.create_threat_map(allies, enemies)
        end = timer()
        #print end-start

        for enemy in enemies:
            score += active.ai.weights.enemy.calculate(enemy, threat_map) * unit_priority

        for ally in allies:
            score += active.ai.weights.friendly.calculate(ally, threat_map) * unit_priority

        score += active.ai.weights.personal.calculate(active, threat_map)

        return score

    def create_threat_map(self, allies, enemies):
        threat_map = ThreatMap(self.simulated_battle.bmap)
        for enemy in enemies:
            threat_map.add_threat(enemy, self.simulated_battle.bmap)

        return threat_map


class PeerlessAi(object):
    """
    AI class for a unit
    """
    def __init__(self, battle, actor, skills):
        self.battle = battle
        self.actor = actor
        self.skills = skills
        self.bmap = battle.bmap

        self.weights = UnitScoreWeights(UnitScoreWeightEnemy(), UnitScoreWeightAlly(), UnitScoreWeightSelf())

    def evaluate(self):
        start = timer()
        simulation = SimulationHandler(self.actor, self.battle)

        possible_moves = []
        ranges = {}
        baseline_score = simulation.simulate_move(None, None, None, None)
        # add wait option
        possible_moves.append({'score': baseline_score, 'skill': None, 'target': None, 'destination': None})

        move_range = self.actor.calculate_move_range(self.bmap)

        for move_option in move_range:
            # add option to move and take no action
            score = simulation.simulate_move(None, None, move_option, None)
            possible_moves.append({'score': score, 'skill': None, 'target': None, 'destination': move_option})
            simulation.reset()
            for skill in [self.skills[s] for s in self.actor.skillset]:
                if ranges.get(move_option, {}).get(skill.range):
                    skill_range = ranges.get(move_option, {}).get(skill.range)
                else:
                    skill_range = RN2_battle_logic.calculate_skill_range(self.actor, skill, self.bmap)
                    if not ranges.get(move_option):
                        ranges[move_option] = {}
                    ranges[move_option].update({skill.range: skill_range})
                for target_option in skill_range:
                    #todo: doesnt account for move_option, possibly missing affect self
                    affected_tiles = RN2_battle_logic.calculate_affected_area(target_option,
                                                                              move_option,
                                                                              skill,
                                                                              simulation.simulated_battle.bmap)

                    if simulation.simulated_battle.get_targets_for_area(self.actor, affected_tiles, skill) != ([], [], []):
                        sstart = timer()
                        score = simulation.simulate_move(skill, target_option, move_option, affected_tiles)
                        send = timer()
                        #print "Time to score:", (send - sstart)
                        possible_move = {'score': score, 'skill': skill, 'target': target_option, 'destination': move_option}
                        possible_moves.append(possible_move)
                        tstart = timer()
                        simulation.reset()
                        tend = timer()
                        #print "Time to reset:", (tend - tstart)

        end = timer()
        print 'evaluate run time:', (end - start), 'seconds:', len(possible_moves), 'results.'
        return possible_moves

    def get_action(self):
        possible_moves = self.evaluate()

        if possible_moves:
            possible_moves.sort(key=lambda x: x['score'], reverse=True)
            chosen_action = possible_moves[0]

            print possible_moves[:10]

            if chosen_action['destination']:
                path = pathfind((self.actor.coords[1], self.actor.coords[0]), (chosen_action['destination'][1],
                                                                               chosen_action['destination'][0]), self.battle.bmap)
            else:
                path = [0, [self.actor.coords]]

            return chosen_action['skill'], chosen_action['target'], path[1]
        else:
            return None, None, None
