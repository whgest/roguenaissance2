"""

Project Roguenaissance 2.0
Battle System Logic
by William Hardy Gest

October 2013

"""

import RN2_loadmap
import RN2_initialize
import random
import time
import RN2_battle_io
import RN2_battle_logic
import RN2_event

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
    def __init__(self, battle_data, actor_data, skills, bmap, io):
        #todo: color data should not be in here

        self.io = io
        self.units = battle_data.get('units', [])
        self.actor_data = actor_data
        self.skills = skills
        self.events = battle_data.get('events', [])
        self.event = RN2_event.EventQueue()
        self.active = None
        self.selected_skill = None
        self.skill_index = 0
        self.battle_index = 0
        self.battle_menu_list = []
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
        self.unit_list = []

        self.all_living_units = []

        self.turn_tracker = TurnTracker(self.all_living_units)

    def check_victory_conditions(self):
        #only 1 team alive
        return len(set([u.team_id for u in self.all_living_units])) == 1

    def check_loss_condition(self):
        return False

    def update_display(self):
        self.io.update(self.event.queue)
        self.event.clear()

    def state_check(self):
        for unit in self.all_living_units:
            if self.bmap.get_tile_at(unit.coords).actor != unit:
                print unit, unit.coords, self.bmap.get_tile_at(unit.coords).actor
                raise AssertionError

    def battle(self):
        #self.battle_events(start=True)
        self.place_units(self.units)
        self.turn_tracker.roll_initiative()
        self.io.draw_battle_ui(self)

        while 1:
            if self.check_victory_conditions():
                return True

            #battle events
            #todo: update legend
            self.active = self.turn_manager()

            self.active.initiate_turn()
            if not self.active.can_act:
                continue

            self.state_check()
            if self.active.is_player_controlled:
                pass

            else:
                #get ai move and validate
                ai = self.active.ai_class(self, self.active, self.skills)
                skill_name, target_tile, move_path = ai.get_action(self.io.ui)
                chosen_skill = self.skills.get(skill_name)
                is_valid = self.validate_ai_turn(self.active, chosen_skill, target_tile, move_path[1:])
                if not is_valid:
                    continue

                #resolve turn
                if move_path:
                    self.move_unit(self.active, move_path[-1])
                    self.event.add_event(RN2_event.MoveUnit(self.active, move_path))
                if chosen_skill:
                    affected_tiles = RN2_battle_logic.calculate_affected_area(target_tile, self.active.coords, chosen_skill, self.bmap, self.io.ui)
                    self.event.add_event(RN2_event.UseSkill(self.active, chosen_skill, affected_tiles))
                    self.execute_skill(self.active, chosen_skill, affected_tiles, target_tile)

                self.update_state()
                self.update_display()

            game_over = self.check_loss_condition()
            if game_over:
                self.io.game_over()
                return False

            #RN_UI.print_narration(self.report.process_report())
            time.sleep(DELAY_BETWEEN_TURNS)

    def update_state(self):
        to_remove = []
        for unit in self.all_living_units:
            if unit.hp <= 0 or unit.is_dead:
                self.remove_unit(unit)
                self.event.add_event(RN2_event.KillUnit(unit))
                to_remove.append(unit)

        for unit in to_remove:
            self.all_living_units.remove(unit)

    def turn_manager(self):
        while 1:
            active_actor = self.turn_tracker.get_next_unit()
            if active_actor.hp > 0:
                break

        return active_actor

    def move_unit(self, unit, destination):
        self.bmap.remove_unit(unit)
        unit.coords = destination
        self.bmap.place_unit(unit, destination)

    def remove_unit(self, unit):
        self.bmap.remove_unit(unit)

    def place_units(self, units):
        for unit in units:
            name = unit['ident']
            stats = self.actor_data[name]

            actor = RN2_initialize.Actor(stats, name)
            actor.coords = tuple([int(c) for c in unit['loc'].split(",")])
            actor.team_id = unit['team_id']

            self.all_living_units.append(actor)
            self.turn_tracker.add_unit(actor)
            self.bmap.place_unit(actor, actor.coords)

    # def battle_events(self, start=False):  # check for battle event conditions
    #     if start:
    #         self.activate_event(self.battle.events[0])
    #         return
    #     for e in self.battle.events:
    #         event_trigger = False
    #         trigger_type = e['condition']['trigger_type']
    #         condition = e['condition'].get('trigger_condition')
    #         if trigger_type == "turn" and self.battle.turn_tracker.turn_count == condition:
    #             event_trigger = True
    #         elif trigger_type == "playeryGreater" and self.battle.hero.coords[1] >= condition:
    #             event_trigger = True
    #         elif trigger_type == "playeryLesser" and self.battle.hero.coords[1] <= condition:
    #             event_trigger = True
    #         elif trigger_type == "playeryIs" and self.battle.hero.coords[1] == condition:
    #             event_trigger = True
    #         elif trigger_type == "playerxLesser" and self.battle.hero.coords[0] <= condition:
    #             event_trigger = True
    #         elif trigger_type == "playerxGreater" and self.battle.hero.coords[0] >= condition:
    #             event_trigger = True
    #         elif trigger_type == "playerxIs" and self.battle.hero.coords[0] == condition:
    #             event_trigger = True
    #         elif trigger_type == "bosskill" and not [u for u in self.battle.all_living_units if u.is_boss]:
    #             event_trigger = True
    #         elif trigger_type == "kill_team_2" and not [u for u in self.battle.all_living_units if u.team_id == 2]:
    #             event_trigger = True
    #
    #         if event_trigger:
    #             if self.activate_event(e):
    #                 return True

    # def activate_event(self, event):
    #     effect_type = event['effect']['type']
    #     if effect_type == "victory":
    #         return True
    #     elif effect_type == "add_mobs":
    #         for mob_id in event['effect']['ids']:
    #             enemy = self.actors[mob_id]
    #             self.all_living_units.append(enemy)
    #             self.turn_tracker.add_unit(enemy)
    #             self.bmap[enemy.coords[0]][enemy.coords[1]].actor = enemy
    #             self.UI.update_map("new", enemy.coords, enemy, self.battle.bmap)
    #     elif effect_type == "pass":
    #         pass
    #     self.events.remove(event)
    #     return

    def add_unit(self, name, loc, team_id):
        stats = self.actor_data[name]
        summon = RN2_initialize.Actor(stats, name)

        summon.team_id = team_id
        summon.coords = loc
        self.bmap[summon.coords[0]][summon.coords[1]].actor = summon
        summon.name = name

        self.turn_tracker.add_unit(summon)
        self.all_living_units.append(summon)
        self.event.add_event(RN2_event.AddUnit(summon))


    @property
    def unit_list(self):
        unit_list = []
        for unit in self.all_living_units:
            if (unit.character, unit.name, "white") not in unit_list:
                unit_list.append((unit.character, unit.name, "white"))
        return unit_list

    def get_allies_of(self, actor):
        return list([x for x in self.all_living_units if x.team_id == actor.team_id and x != actor])

    def get_enemies_of(self, actor):
        return list([x for x in self.all_living_units if x.team_id != actor.team_id])

    def get_targets_for_area(self, attacker, affected_tiles):
        enemy_units_affected = []
        friendly_units_affected = []
        self_unit_affected = []
        for unit in self.all_living_units:
            if unit.coords in affected_tiles:
                if unit in self.get_allies_of(attacker):
                    friendly_units_affected.append(unit)

                if unit in self.get_enemies_of(attacker):
                    enemy_units_affected.append(unit)

                if unit == attacker:
                    self_unit_affected.append(unit)

        return enemy_units_affected, friendly_units_affected, self_unit_affected

    def execute_skill(self, attacker, skill, affected_tiles, origin):
        attacker.mp = attacker.mp - skill.mp

        #todo: sort by distance, resolve furthest (or closest for pull) first to reduce move collisions
        enemy_units_affected, friendly_units_affected, self_unit_affected = self.get_targets_for_area(attacker, affected_tiles)

        if not skill.targets.enemy.ignored:
            for unit in enemy_units_affected:
                self.skill_effect_on_unit(attacker, skill.targets.enemy, unit, skill.name, origin)

        if not skill.targets.friendly.ignored:
            for unit in friendly_units_affected:
                self.skill_effect_on_unit(attacker, skill.targets.friendly, unit, skill.name, origin)

        if not skill.targets.self.ignored:
            for unit in self_unit_affected:
                self.skill_effect_on_unit(attacker, skill.targets.self, unit, skill.name, origin)

        for new_unit in skill.add_unit:
            empty_tiles = self.bmap.get_empty_tiles(affected_tiles)
            if empty_tiles:
                self.add_unit(new_unit, random.choice(empty_tiles), attacker.team_id)

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
        def max_abs(coords):
            x = coords[0]
            y = coords[1]
            return x if abs(x) > abs(y) else y

        origin = attacker.coords if effect.origin == "user" else origin
        distance = effect.distance
        modifier = -1 if effect.move_type == "push" else 1
        difference = [float(unit.coords[0] - origin[0]), float(unit.coords[1] - origin[1])]

        direction = [0, 0] if not any(difference) else [difference[0]/max_abs(difference), difference[1]/max_abs(difference)]

        move_step = [int(round(c)) * modifier for c in direction]

        for d in range(distance):
            new_coords = RN2_battle_logic.add_points(unit.coords, move_step)
            if self.bmap.get_tile_at(new_coords).is_movable():
                self.event.add_event(RN2_event.MoveUnit(unit, [unit.coords, new_coords]))
                self.move_unit(unit, new_coords)

    def check_bounds(self, coords):
        if 0 > coords[0] or coords[0] > self.map_size[0] or 0 > coords[1] or coords[1] > self.map_size[1]:
            return True
        return False

    def validate_ai_turn(self, e, skill_name, target, path):
        destination = path[-1] if len(path) else e.coords
        print '{0} with HP {5} at {1} moves to tile {4} and chooses skill {2} targeting tile {3}.'.format(e, e.coords, skill_name, target, destination, e.hp)
        skill = self.skills.get(skill_name)
        if target:
            target_tile = self.bmap[target[0]][target[1]]

        def move_is_legal():
            for tile in path:
                if self.bmap[tile[0]][tile[1]].is_movable():
                    continue
                else:
                    print "Actor '{0}' returned illegal move. Tile ({1}, {2}) is blocked by {3}.".format(e.name, tile[0], tile[1], self.bmap.get_tile_at(tile).actor)
                    exit()
                    return False
            return True

        def skill_is_legal():
            if e.mp >= skill.mp:
                return True
            else:
                print "Actor '{0}' does not have the MP to cast {1}. MP: {2} Needed: {3}".format(e.name, skill.name, e.mp, skill.mp)
                return False

        def target_is_legal():
            # if skill and skill.target == "empty" and not target_tile.is_movable():
            #     print "Actor {0} can not use skill {1} on tile ({2}, {3}): Blocked".format(e.name, skill.name, target[0], target[1])
            #     return
            # else:
            #     return True
            # #todo: check skill range, emptiness for summon skills, etc.
            return True

        if skill and not skill_is_legal():
            return False

        if path and not move_is_legal():
            return False

        if target and not target_is_legal():
            return False

        return True

    def grid_distance(self, actor1, actor2):
        return abs(actor1[0] - actor2[0]) + abs(actor1[1] - actor2[1])
