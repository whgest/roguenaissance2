"""

Project Roguenaissance 2.0
Battle System Logic
by William Hardy Gest

October 2013

"""

import RN2_initialize
import random
import time
import RN2_battle_logic
import RN2_event
import RN2_battle_triggers

PLAYER_AI = "player"
DELAY_BETWEEN_TURNS = 0.2



TURN_MARKER = 'turn_marker'
class TurnTracker:
    def __init__(self, units):
        self.initiative_list = []
        self.turn_count = 0
        self.units = units
        self.top_of_the_order = None
        self.has_rolled_initiative = False

    def roll_initiative(self):
        initiative_list = []
        for actor in self.units:
            initiative = (actor.agility*2 + random.randint(1, 20))
            initiative_list.append((initiative, actor))

        initiative_list.sort()
        self.initiative_list = [x[1] for x in initiative_list]
        self.initiative_list.insert(0, TURN_MARKER)

        self.has_rolled_initiative = True

    def add_unit(self, unit):
        if self.has_rolled_initiative:
            self.initiative_list.insert(0, unit)

    def get_next_unit(self):
        active_actor = self.initiative_list.pop()
        if active_actor == TURN_MARKER:
            self.initiative_list.insert(0, TURN_MARKER)
            self.turn_count += 1
            return self.get_next_unit()
        if active_actor.hp > 0:
            self.initiative_list.insert(0, active_actor)
            return active_actor
        else:
            return self.get_next_unit()



class Battle:
    def __init__(self, battle_data, actor_data, skills, bmap, io, persistent_actor=None):
        self.io = io
        self.units = battle_data.get('units', [])
        self.music = battle_data.get('music', [])
        self.player_start = battle_data.get('player_start', None)
        self.actor_data = actor_data
        self.skills = skills
        self.trigger_data = battle_data.get('triggers', [])
        self.victory_condition_data = battle_data.get('victory_condition', {})
        self.victory_condition = []
        self.triggers = []
        self.event = RN2_event.EventQueue()
        self.active = None
        self.selected_skill = None
        self.skill_index = 0
        self.battle_index = 0
        self.v_top = 0
        self.move_range = None
        self.report = None
        self.state_changes = []
        self.targetable_tiles = None
        self.target_tile = None
        self.state = ""
        self.kills = 0
        self.bmap = bmap
        self.map_size = (49, 24)
        self.persistent_actor = persistent_actor
        self.avatar = None

        self.all_living_units = []

        self.turn_tracker = TurnTracker(self.all_living_units)

        for trigger in self.trigger_data:
            self.triggers.append(RN2_battle_triggers.BattleTrigger(trigger, self))

        self.victory_condition = (RN2_battle_triggers.BattleTrigger(self.victory_condition_data, self))

    def check_victory_conditions(self):
        if self.victory_condition:
            return self.victory_condition.resolve()
        else:
            #only 1 team alive
            return len(set([u.team_id for u in self.all_living_units])) == 1

    def check_loss_condition(self):
        if self.avatar and self.avatar.is_dead:
            return True
        return False

    def update_display(self):
        self.io.update(self.event.queue)
        self.event.clear()

    def state_check(self):
        for unit in self.all_living_units:
            if self.bmap.get_tile_at(unit.coords).actor != unit:
                print self.all_living_units, unit, unit.coords, self.bmap.get_tile_at(unit.coords).actor
                raise AssertionError

    @property
    def battle_menu_list(self):
        unit_list = []
        for unit in self.all_living_units:
            unit_list.append(unit)
        unit_list.reverse()
        unit_list.insert(0, unit_list.pop())  # put active unit at top

        return unit_list

    @property
    def legend_unit_list(self):
        res = {}
        for unit in self.battle_menu_list:
            res[unit.character] = unit
        return res.values()

    def battle(self):
        self.place_avatar()
        self.turn_tracker.roll_initiative()
        self.io.draw_battle_ui(self)

        while 1:
            self.resolve_battle_triggers()

            if self.check_victory_conditions():
                return True
            self.active = self.turn_manager()

            self.active.initiate_turn()
            if not self.active.can_act:
                continue

            self.update_display()

            self.state_check() #sanity check for agreement of unit coords and map pos

            if self.active.is_player_controlled:
                chosen_skill, target_tile, destination = self.io.player_turn(self)
                self.validate_ai_turn(self.active, chosen_skill, target_tile, [destination])

            else:
                #ai controlled
                ai = self.active.ai_class(self, self.active, self.skills)
                skill_name, target_tile, move_path = ai.get_action(self.io.ui)
                chosen_skill = self.skills.get(skill_name)
                destination = move_path[-1] if move_path else None

                self.validate_ai_turn(self.active, chosen_skill, target_tile, move_path[1:])
                if destination:
                    self.event.add_event(RN2_event.MoveUnit(self.active, move_path))

            #resolve turn
            if destination:
                self.move_unit(self.active, destination)
            if chosen_skill:
                affected_tiles = RN2_battle_logic.calculate_affected_area(target_tile, self.active.coords, chosen_skill, self.bmap)
                self.event.add_event(RN2_event.UseSkill(self.active, chosen_skill, affected_tiles))
                self.execute_skill(self.active, chosen_skill, affected_tiles, target_tile)

            self.clear_killed()
            self.update_display()

            game_over = self.check_loss_condition()
            if game_over:
                return False

            time.sleep(DELAY_BETWEEN_TURNS)

    def resolve_battle_triggers(self):
        for trigger in self.triggers:
            if trigger.resolve():
                self.triggers.remove(trigger)

    def clear_killed(self):
        to_remove = []
        for unit in self.all_living_units:
            if unit.hp <= 0 or unit.is_dead:
                self.event.add_event(RN2_event.KillUnit(unit))
                self.remove_unit(unit)
                to_remove.append(unit)

        for unit in to_remove:
            self.all_living_units.remove(unit)

    def turn_manager(self):
        while 1:
            active_actor = self.turn_tracker.get_next_unit()
            if active_actor.hp > 0:
                break

        #todo: handle edge case where no units survive
        return active_actor

    def move_unit(self, unit, destination):
        self.bmap.remove_unit(unit)
        unit.coords = destination
        self.bmap.place_unit(unit, destination)

    def remove_unit(self, unit):
        self.bmap.remove_unit(unit)

    # for placing the avatar unit in a campaign
    def place_avatar(self):
        units = []
        if self.persistent_actor and self.player_start:
            units.append({'ident': self.persistent_actor.class_name, 'loc': self.player_start, 'team_id': 1, 'name': self.persistent_actor.name})

        for unit in units:
            ident = unit['ident']
            stats = self.actor_data[ident]

            name = ident if not unit.get('name') else unit.get('name')

            actor = RN2_initialize.Actor(stats, name)
            actor.coords = tuple([int(c) for c in unit['loc'].split(",")])
            actor.team_id = unit['team_id']

            self.all_living_units.append(actor)
            self.turn_tracker.add_unit(actor)
            self.bmap.place_unit(actor, actor.coords)
            self.avatar = actor

    def add_unit(self, name, loc, team_id, summoner=None):
        if self.bmap.get_tile_at(loc).is_movable:
            stats = self.actor_data[name]
            stats['summoned_by'] = summoner
            unit = RN2_initialize.Actor(stats, name)

            unit.team_id = team_id

            unit.coords = loc
            self.bmap[unit.coords[0]][unit.coords[1]].actor = unit
            unit.name = name

            self.turn_tracker.add_unit(unit)
            self.all_living_units.append(unit)
            self.event.add_event(RN2_event.AddUnit(unit))

    def get_allies_of(self, actor):
        return list([x for x in self.all_living_units if x.team_id == actor.team_id and x != actor])

    def get_enemies_of(self, actor):
        return list([x for x in self.all_living_units if x.team_id != actor.team_id])

    def get_targets_for_area(self, attacker, affected_tiles, skill):
        enemy_units_affected = []
        friendly_units_affected = []
        self_unit_affected = []
        for unit in self.all_living_units:
            if unit.coords in affected_tiles:
                if unit in self.get_allies_of(attacker) and skill.affects_friendlies:
                    friendly_units_affected.append(unit)

                if unit in self.get_enemies_of(attacker) and skill.affects_enemies:
                    enemy_units_affected.append(unit)

                if unit == attacker and skill.affects_self:
                    self_unit_affected.append(unit)

        return enemy_units_affected, friendly_units_affected, self_unit_affected

    def execute_skill(self, attacker, skill, affected_tiles, origin):

        attacker.mp = attacker.mp - self.get_mp_cost(skill, attacker)
        #print "{} is charged {} MP for {} and now has {}".format(attacker.name, self.get_mp_cost(skill, attacker), skill.name, attacker.mp)

        enemy_units_affected, friendly_units_affected, self_unit_affected = self.get_targets_for_area(attacker, affected_tiles, skill)

        for unit in enemy_units_affected:
            self.skill_effect_on_unit(attacker, skill.targets.enemy, unit, skill.name, origin)

        for unit in friendly_units_affected:
            self.skill_effect_on_unit(attacker, skill.targets.friendly, unit, skill.name, origin)

        for unit in self_unit_affected:
            self.skill_effect_on_unit(attacker, skill.targets.self, unit, skill.name, origin)

        for new_unit in skill.add_unit:
            empty_tiles = self.bmap.get_empty_tiles(affected_tiles)
            if empty_tiles:
                self.add_unit(new_unit, random.choice(empty_tiles), attacker.team_id, summoner=attacker)

    def skill_effect_on_unit(self, attacker, skill_target_type_effect, target, skill_name, origin):
        requires_attack_roll = skill_target_type_effect.is_resistable
        if requires_attack_roll and not skill_target_type_effect.attack_roll(attacker, target):
            self.event.add_event(RN2_event.Miss(target, skill_name))
            return

        inflicted_damage = skill_target_type_effect.damage.roll_damage(attacker)

        target.inflict_damage_or_healing(inflicted_damage, skill_name)

        for status_effect in skill_target_type_effect.status_effects:
            target.apply_status(status_effect)

        for move_effect in skill_target_type_effect.move_effects:
            self.move_effect_on_unit(attacker, move_effect, target, origin)

    def move_effect_on_unit(self, attacker, effect, unit, origin):
        #todo: somehow reduce move collisions

        def max_abs(coords):
            x = coords[0]
            y = coords[1]
            return abs(x) if abs(x) > abs(y) else abs(y)

        origin = attacker.coords if effect.origin == "user" else origin
        distance = effect.distance
        modifier = 1 if effect.type == "push" else -1
        difference = [float(unit.coords[0] - origin[0]), float(unit.coords[1] - origin[1])]

        direction = [0, 0] if not any(difference) else [difference[0]/max_abs(difference), difference[1]/max_abs(difference)]

        move_step = [int(round(c)) * modifier for c in direction]

        for d in range(distance):
            new_coords = RN2_battle_logic.add_points(unit.coords, move_step)
            if self.bmap.check_bounds(new_coords) and self.bmap.get_tile_at(new_coords).is_movable:
                self.event.add_event(RN2_event.MoveUnit(unit, [unit.coords, new_coords]))
                self.move_unit(unit, new_coords)
                if new_coords == origin:
                    break

    def check_bounds(self, coords):
        if 0 > coords[0] or coords[0] > self.map_size[0] or 0 > coords[1] or coords[1] > self.map_size[1]:
            return True
        return False

    def validate_ai_turn(self, e, skill, target, path):
        destination = path[-1] if len(path) else e.coords
        print '{0} with HP {5}, MP {6}, at {1} moves to tile {4} and chooses skill {2} targeting tile {3}.'.format(e, e.coords, skill, target, destination, e.hp, e.mp)

        if target:
            target_tile = self.bmap[target[0]][target[1]]

        for tile in path:
            if self.bmap.get_tile_at(tile).actor == e or self.bmap.get_tile_at(tile).is_movable:
                continue
            else:
                print "Actor '{0}' returned illegal move. Tile ({1}, {2}) is blocked by {3}.".format(e.name, tile[0], tile[1], self.bmap.get_tile_at(tile).actor)
                raise AssertionError

        if skill and not e.mp >= self.get_mp_cost(skill, e):
            print "Actor '{0}' does not have the MP to cast {1}. MP: {2} Needed: {3}".format(e.name, skill.name, e.mp, self.get_mp_cost(skill, e))
            raise AssertionError

        #todo: ensure unit has skill


        #todo: check skill range, emptiness for summon skills, etc.


    def grid_distance(self, actor1, actor2):
        return abs(actor1[0] - actor2[0]) + abs(actor1[1] - actor2[1])

    def get_mp_cost(self, skill, unit):
        if skill.mp == -1:
            num_summons = len([u for u in self.all_living_units if u.summoned_by == unit])
            return 1 + (num_summons * 2)
        else:
            return skill.mp

