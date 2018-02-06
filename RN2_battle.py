import RN2_initialize
import random
import pygame
import RN2_battle_logic
import RN2_event
import RN2_battle_triggers

PLAYER_AI = "player"
DELAY_BETWEEN_TURNS = 50
TURN_MARKER = 'turn_marker'


class TurnTracker:
    def __init__(self, units):
        self.initiative_list = []
        self.turn_count = 1
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


class Battle(object):
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
        self.skill_index = 0
        self.battle_index = 0
        self.v_top = 0
        self.report = None
        self.targetable_tiles = None
        self.kills = 0
        self.bmap = bmap
        self.map_size = (49, 24)
        self.persistent_actor = persistent_actor
        self.avatar = None

        self.all_living_units = []

        self.turn_tracker = TurnTracker(self.all_living_units)

        for trigger in self.trigger_data:
            self.triggers.append(RN2_battle_triggers.BattleTrigger(trigger, self))

        if self.victory_condition_data:
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
                print(self.all_living_units, unit, unit.coords, self.bmap.get_tile_at(unit.coords).actor)
                raise AssertionError

    @property
    def battle_menu_list(self):
        unit_list = []
        for unit in self.turn_tracker.initiative_list:
            if unit in self.all_living_units:
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
                if self.persistent_actor:
                    self.persistent_actor.score.turns_taken += self.turn_tracker.turn_count
                return True
            self.active = self.turn_manager()

            self.active.initiate_turn()
            if not self.active.can_act:
                continue

            self.event.add_event(RN2_event.StartTurn(self.active))
            self.update_display()

            self.state_check() #sanity check for agreement of unit coords and map pos

            if self.active.is_player_controlled:
                chosen_skill, target_tile, destination = self.io.player_turn(self)
                self.validate_ai_turn(self.active, chosen_skill, target_tile, [destination])

            else:
                #ai controlled
                skill_name, target_tile, move_path = self.active.ai.get_action()
                chosen_skill = self.skills.get(skill_name) if type(skill_name) is str else skill_name
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

            self.update_display()
            self.clear_killed()

            game_over = self.check_loss_condition()
            if game_over:
                return False

            if not self.active.is_player_controlled:
                pygame.time.wait(DELAY_BETWEEN_TURNS)

    def resolve_battle_triggers(self):
        for trigger in self.triggers:
            if trigger.resolve():
                self.triggers.remove(trigger)

    def clear_killed(self):
        to_remove = []

        for unit in self.all_living_units:
            if unit.hp <= 0 or unit.is_dead:
                for summon in [u for u in self.all_living_units if u.summoned_by == unit]:
                    to_remove.append(summon)
                to_remove.append(unit)

                if self.persistent_actor and unit.team_id != 1:
                    self.persistent_actor.score.enemies_killed += 1

        for unit in to_remove:
            unit.kill_actor()
            self.event.add_event(RN2_event.KillUnit(unit))
            self.update_display()
            try:
                self.all_living_units.remove(unit)
            except ValueError:
                print("{} attempted removal but was not present in list".format(unit.name))
            self.remove_unit(unit)
            self.update_display()

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

            actor = RN2_initialize.Actor(stats, name, event=self.event)
            actor.coords = tuple([int(c) for c in unit['loc'].split(",")])
            actor.team_id = unit['team_id']
            actor.id = 1
            actor.ai = "player"

            self.all_living_units.append(actor)
            self.turn_tracker.add_unit(actor)
            self.bmap.place_unit(actor, actor.coords)
            self.avatar = actor

    def add_unit(self, name, loc, team_id, summoner=None):
        if self.bmap.get_tile_at(loc).is_movable:
            stats = self.actor_data[name]
            stats['summoned_by'] = summoner
            unit = RN2_initialize.Actor(stats, name, event=self.event)

            unit.team_id = team_id

            try:
                unit.id = max([u.id for u in self.all_living_units]) + 1
            except ValueError:
                unit.id = 1

            unit.coords = loc
            self.bmap[unit.coords[0]][unit.coords[1]].actor = unit
            unit.name = name

            self.initialize_unit_ai(unit)

            self.turn_tracker.add_unit(unit)
            self.all_living_units.append(unit)
            self.event.add_event(RN2_event.AddUnit(unit))

    def initialize_unit_ai(self, unit):
        if unit.summoned_by and unit.summoned_by.ai == "player":
            unit.ai = "player"
        else:
            unit.ai = unit.ai_class(self, unit, self.skills)

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
        #print("{} is charged {} MP for {} and now has {}".format(attacker.name, self.get_mp_cost(skill, attacker), skill.name, attacker.mp))

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

        for new_unit in skill.add_minion:
            empty_tiles = self.bmap.get_empty_tiles(affected_tiles)
            if empty_tiles:
                self.add_unit(new_unit, random.choice(empty_tiles), attacker.team_id)

    def skill_effect_on_unit(self, attacker, skill_target_type_effect, target, skill_name, origin):
        requires_attack_roll = skill_target_type_effect.is_resistable
        if requires_attack_roll and not skill_target_type_effect.attack_roll(attacker, target):
            self.event.add_event(RN2_event.Miss(target, skill_name))
            return

        inflicted_damage = skill_target_type_effect.damage.roll_damage(attacker, target)

        target.inflict_damage_or_healing(inflicted_damage, skill_name)

        if self.persistent_actor and target.id == 1 and inflicted_damage > 0:
            self.persistent_actor.score.damage_taken += inflicted_damage

        for status_effect in skill_target_type_effect.status_effects:
            target.apply_status(status_effect)

        for move_effect in skill_target_type_effect.move_effects:
            self.move_effect_on_unit(attacker, move_effect, target, origin)

    def move_effect_on_unit(self, attacker, effect, unit, origin):
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

        # todo: bug-- diagonal pushes push twice as far
        last_valid_tile = tuple(unit.coords)
        for d in range(distance):
            new_coords = RN2_battle_logic.add_points(last_valid_tile, move_step)
            if not self.bmap.check_bounds(new_coords):
                break
            elif self.bmap.get_tile_at(new_coords).terrain.blocking:
                break
            elif not self.bmap.get_tile_at(new_coords).actor:
                last_valid_tile = new_coords

            if last_valid_tile == origin or self.bmap.get_tile_at(last_valid_tile).terrain.ends_forced_movement:
                break

        if last_valid_tile != unit.coords:
            self.event.add_event(RN2_event.MoveUnit(unit, [unit.coords, last_valid_tile]))
            self.move_unit(unit, last_valid_tile)
            self.resolve_terrain(unit)

    def check_bounds(self, coords):
        if 0 > coords[0] or coords[0] > self.map_size[0] or 0 > coords[1] or coords[1] > self.map_size[1]:
            return True
        return False

    def validate_ai_turn(self, e, skill, target, path):
        destination = path[-1] if len(path) else e.coords
        print('{0} with HP {5}, MP {6}, at {1} moves to tile {4} and chooses skill {2} targeting tile {3}.\n'.format(e, e.coords, skill, target, destination, e.hp, e.mp))

        if target:
            target_tile = self.bmap[target[0]][target[1]]
        else:
            target_tile = None

        for tile in path:
            if self.bmap.get_tile_at(tile).actor == e or self.bmap.get_tile_at(tile).is_movable:
                continue
            else:
                print("Actor '{0}' returned illegal move. Tile ({1}, {2}) is blocked by {3}.".format(e.name, tile[0], tile[1], self.bmap.get_tile_at(tile).actor))
                raise AssertionError

        if skill and not e.mp >= self.get_mp_cost(skill, e):
            print("Actor '{0}' does not have the MP to cast {1}. MP: {2} Needed: {3}".format(e.name, skill.name, e.mp, self.get_mp_cost(skill, e)))
            raise AssertionError

        #todo: check skill range, emptiness for summon skills, etc.
        if skill and target and destination and RN2_battle_logic.grid_distance(destination, target) > skill.range:
            print("Actor '{0}' cannot reach target {1} with skill {2}. Range: {3}, Distance: {4}".format(e.name, target, skill.name, skill.range, RN2_battle_logic.grid_distance(destination, target)))
            raise AssertionError

    def get_mp_cost(self, skill, unit):
        if skill.mp == -1:
            num_summons = len([u for u in self.all_living_units if u.summoned_by == unit])
            return 1 + (num_summons * 2)
        else:
            return skill.mp

    def resolve_terrain(self, unit):
        tile = self.bmap.get_tile_at(unit.coords)
        if tile.terrain.fatal:
            if tile.terrain.name not in unit.immunities:
                unit.kill_actor()
                self.event.overwrite_last_event(RN2_event.KillUnitTerrain(unit, tile.terrain.name))
            else:
                self.event.add_event(RN2_event.ImmuneToTerrain(unit, tile.terrain.name))


# todo: move this to ai file
class SimulatedBattle(Battle):
    def __init__(self, *args, **kwargs):
        Battle.__init__(self, *args, **kwargs)
        import dummy_ui
        self.io = dummy_ui.DummyUi()
        self.event = dummy_ui.DummyUi()
        self.turn_tracker = dummy_ui.DummyUi()

    def skill_effect_on_unit(self, attacker, skill_target_type_effect, target, skill_name, origin):
        inflicted_damage = skill_target_type_effect.damage.roll_damage(attacker, target, use_random=False)

        target.inflict_damage_or_healing(inflicted_damage, skill_name)

        for status_effect in skill_target_type_effect.status_effects:
            target.apply_status(status_effect)

        for move_effect in skill_target_type_effect.move_effects:
            self.move_effect_on_unit(attacker, move_effect, target, origin)

    def add_unit(self, name, loc, team_id, summoner=None):
        import dummy_ui
        Battle.add_unit(self, name, loc, team_id, summoner)
        self.all_living_units[-1].event = dummy_ui.DummyUi()

    def initialize_unit_ai(self, unit):
        pass
