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

PLAYER_AI = "player"
DELAY_BETWEEN_TURNS = 0.2

class BattleStateChange(object):
    def __init__(self):
        self.reports = []

    @property
    def report_entry(self):
        return self.reports

    def display(self, ui):
        pass

    def animate(self, ui):
        pass


class MoveUnit(BattleStateChange):
    def __init__(self, actor, path):
        BattleStateChange.__init__(self)
        self.path = path
        self.actor = actor

    def display(self, ui):
        prev_coords = self.path[0]
        for move in self.path[1:]:
            ui.move_unit(prev_coords, move, self.actor)


class UpdateMap(BattleStateChange):
    def __init__(self, battle_map):
        BattleStateChange.__init__(self)
        self.battle_map = battle_map

    def display(self, ui):
        ui.update_map(self.battle_map)


class KillUnit(BattleStateChange):
    def __init__(self, change):
        BattleStateChange.__init__(self, change)
        self.actor = change.actor

    def display(self, ui):
        ui.kill_unit(self.actor)


class AddUnit(BattleStateChange):
    def __init__(self, change):
        BattleStateChange.__init__(self, change)
        self.actor = change.actor

    def display(self, ui):
        ui.add_unit(self.actor)

    def update_game_state(self, state_changes):
        #todo: update displays relating to unit states and map state
        for change in state_changes:
            change.animate(self.RN_UI)
            self.report.add_entry(change.report_entry)
            change.display(self.RN_UI)

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
    def __init__(self, battle_data):
        #todo: color data should not be in here

        self.actors = battle_data.get('actors', [])
        self.events = battle_data.get('events', [])
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
        self.bmap = RN2_loadmap.load_map(battle_data.get('map'))
        self.map_size = (49, 24)
        self.unit_list = []
        self.io = RN2_battle_io.Battle_Controller()

        self.all_living_units = []

        self.turn_tracker = TurnTracker(self.all_living_units)

    def battle(self):
        self.battle_events(start=True)
        self.unit_list = self.make_unit_list()
        self.turn_tracker.roll_initiative()

        while 1:
            if self.check_victory_conditions():
                #todo: victory display
                return True
            else:
                unit_list = self.make_unit_list()
                self.io.update_unit_list(unit_list)
                #todo: update legend
                player, self.active = self.turn_manager()

                self.active.initiate_turn()
                active_can_act = self.active.can_act

                if not active_can_act:
                    continue

                if self.active.is_player_controlled():
                    pass

                else:
                    #get ai move and validate
                    chosen_skill, target_tile, move_path = self.active.ai_class.get_action()
                    is_valid = self.validate_ai_turn(self.active, chosen_skill, target_tile, move_path)
                    if not is_valid:
                        continue

                    #resolve turn
                    if move_path:
                        self.move_unit(self.active.coords, move_path, self.bmap)

                    if chosen_skill:
                        self.execute_skill(self.active, chosen_skill, affected_tiles, target_tile):




                    #update display




                game_over = self.check_loss_condition()
                if game_over:
                #     self.RN_sound.cut_music()
                #     self.RN_sound.play_music('gameover')
                #     RN_UI.fade_to_black()
                     return False
                #RN_UI.print_narration(self.report.process_report())
                time.sleep(DELAY_BETWEEN_TURNS)

    def get_allies_of(self, actor):
        return list([x for x in self.all_living_units if x.team_id == actor.team_id])

    def get_enemies_of(self, actor):
        return list([x for x in self.all_living_units if x.team_id != actor.team_id])

    def turn_manager(self):
        while 1:
            active_actor = self.turn_tracker.get_next_unit()
            if active_actor.hp > 0:
                break

        if active_actor.ai == PLAYER_AI:
            return True, active_actor
        else:
            return False, active_actor

    def add_actors(self, battle):
        b_actors = []
        for actor_data in battle["actors"]:
            name = actor_data['ident']
            stats = self.actors[name]  # pull stats from database

            actor = RN2_initialize.Actor(stats, name)
            actor.coords = [int(c) for c in actor_data['loc'].split(",")]
            actor.team_id = actor_data['team_id']
            b_actors.append(actor_data)
        return b_actors

    def battle_manager(self, battle, RN_UI):
            battle.unit_list = self.make_unit_list()
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            victory = self.battle_events()
            if victory:
                pass
                # self.report.add_entry("victory", self.hero)
                # self.RN_sound.cut_music()
                # self.RN_sound.play_music('victory')
                # time.sleep(1)
                # self.report.add_raw_entry("")
                # self.report.add_raw_entry("Total Turns Taken: " + str(self.hero.score['turns']), color="bad_status")
                # time.sleep(1)
                # self.report.add_raw_entry("Total Damage Taken: " + str(self.hero.score['damage']), color="bad_status")
                # time.sleep(1)
                # self.report.add_raw_entry("Total Enemies Killed: " + str(self.hero.score['killed']),
                #                           color="good_status")
                # time.sleep(1)
                # RN_UI.wait_for_keypress()
                # RN_UI.fade_to_black()
                # return True


            # control logic to be split out vvvv




            import pyromancer_tree
            RN_AI = pyromancer_tree.PyromancerDecisionTree(battle, battle.active, self.skills)
            skill, target, path = RN_AI.get_action()

            RN_UI.turn_indication(battle.active)

            if skill is not None:
                self.report.add_entry("use_skill", battle.active, skill)
                RN_UI.print_narration(self.report.process_report())
                path, target, skill = battle.execute_ai_turn(battle.active, self.skills[skill], target, path)
            else:
                path, target, skill = battle.execute_ai_turn(battle.active, None, target, path)

            if path:
                battle.bmap[path[-1][0]][path[-1][1]].actor = battle.active  # update map data
                battle.active.coords = (path[-1][0], path[-1][1])
            else:
                battle.bmap[battle.active.coords[0]][battle.active.coords[1]].actor = battle.active

            self.show_ai_turn(battle.active, path, target, skill, RN_UI, battle)

            if skill is not None:
                # RN2_animations.RN_Animation_Class(battle.affected_tiles, self.RN_sound, RN_UI, skill.animation,
                #                                   battle.bmap, battle.active.coords)

            self.update_game(battle, RN_UI)
            game_over = self.clear_board(battle, RN_UI)
            if game_over:
                self.RN_sound.cut_music()
                self.RN_sound.play_music('gameover')
                RN_UI.fade_to_black()
                return False
            RN_UI.print_narration(self.report.process_report())
            time.sleep(0.2)

    def battle_events(self, start=False):  # check for battle event conditions
        if start:
            self.activate_event(self.battle.events[0])
            return
        for e in self.battle.events:
            event_trigger = False
            trigger_type = e['condition']['trigger_type']
            condition = e['condition'].get('trigger_condition')
            if trigger_type == "turn" and self.battle.turn_tracker.turn_count == condition:
                event_trigger = True
            elif trigger_type == "playeryGreater" and self.battle.hero.coords[1] >= condition:
                event_trigger = True
            elif trigger_type == "playeryLesser" and self.battle.hero.coords[1] <= condition:
                event_trigger = True
            elif trigger_type == "playeryIs" and self.battle.hero.coords[1] == condition:
                event_trigger = True
            elif trigger_type == "playerxLesser" and self.battle.hero.coords[0] <= condition:
                event_trigger = True
            elif trigger_type == "playerxGreater" and self.battle.hero.coords[0] >= condition:
                event_trigger = True
            elif trigger_type == "playerxIs" and self.battle.hero.coords[0] == condition:
                event_trigger = True
            elif trigger_type == "bosskill" and not [u for u in self.battle.all_living_units if u.is_boss]:
                event_trigger = True
            elif trigger_type == "kill_team_2" and not [u for u in self.battle.all_living_units if u.team_id == 2]:
                event_trigger = True

            if event_trigger:
                if self.activate_event(e):
                    return True

    def activate_event(self, event):
        effect_type = event['effect']['type']
        if effect_type == "victory":
            return True
        elif effect_type == "add_mobs":
            for mob_id in event['effect']['ids']:
                enemy = self.actors[mob_id]
                self.all_living_units.append(enemy)
                self.turn_tracker.add_unit(enemy)
                self.bmap[enemy.coords[0]][enemy.coords[1]].actor = enemy
                self.UI.update_map("new", enemy.coords, enemy, self.battle.bmap)
        elif effect_type == "pass":
            pass
        self.events.remove(event)
        return

    def make_unit_list(self):
        unit_list = []
        for unit in self.all_living_units:
            if (unit.character, unit.name, "white") not in unit_list:
                unit_list.append((unit.character, unit.name, "white"))
        return unit_list

    # def get_range(self, origin, arange, pathfind=False, is_move=False):
    #
    #     LINE_ATTACK_RANGE = 12
    #     targetable_tiles = []
    #
    #     if arange == 'line': #line attack
    #         line_dir = []
    #         for i in range(2):
    #             diff = origin[i] - self.hero.coords[i]
    #             line_dir.append(0 if not diff else diff / abs(diff))
    #
    #         for i in range(LINE_ATTACK_RANGE):
    #             next_tile_coords = (origin[0] + (i * line_dir[0]), origin[1] + (i * line_dir[1]))
    #             if self.bmap.get_tile_at(next_tile_coords) and self.bmap.get_tile_at(next_tile_coords).terrain.targetable:
    #                 targetable_tiles.append(next_tile_coords)
    #             else:
    #                 break
    #
    #     elif arange == 'global': #global attack
    #         for x in range(self.map_size[0]+1):
    #             for y in range(self.map_size[1]+1):
    #                targetable_tiles.append((x, y))
    #
    #     else:
    #         targetable_tiles = [tuple(origin)]       #list of tuple coordinates of tiles that are in attack range
    #         new_tiles = [tuple(origin)]
    #         for i in range(arange):
    #             for t in targetable_tiles:
    #                 if (t[0]+1, t[1]) not in targetable_tiles:
    #                     new_tiles.append((t[0]+1, t[1]))
    #                 if (t[0]-1, t[1]) not in targetable_tiles:
    #                     new_tiles.append((t[0]-1, t[1]))
    #                 if (t[0], t[1]-1) not in targetable_tiles:
    #                     new_tiles.append((t[0], t[1]-1))
    #                 if (t[0], t[1]+1) not in targetable_tiles:
    #                     new_tiles.append((t[0], t[1]+1))
    #             for t in new_tiles:
    #                 if t not in targetable_tiles and 0 <= t[0] <= 49 and 0 <= t[1] <= 24:
    #                     targetable_tiles.append(t)
    #     remove_list = []
    #
    #
    #
    #
    #     for t in targetable_tiles:
    #         if (is_move and self.bmap[t[0]][t[1]].terrain.movable == 0) or (not is_move and self.bmap[t[0]][t[1]].terrain.targetable == 0):
    #             remove_list.append(t)
    #
    #     if pathfind:
    #         for t in targetable_tiles:
    #             path = RN2_AI.pathfind(tuple(origin)[::-1], t[::-1], self.bmap)
    #             if path[0] > arange + 1:
    #                 remove_list.append(t)
    #
    #     for r in remove_list:
    #         targetable_tiles.remove(r)
    #     return targetable_tiles

    def check_bounds(self, coords):
        if 0 > coords[0] or coords[0] > self.map_size[0] or 0 > coords[1] or coords[1] > self.map_size[1]:
            return True
        return False

    def get_adjusted_mp(self, skill, actor): #each summon costs an additional mp for each existing summon
        if skill.mp != -1:
            return skill.mp
        else:
            return 1 + (len(self.get_allies_of(actor)) - 1) * 2

    def get_targets_for_area(self, attacker, skill, affected_tiles):
        targets = []
        friendlies = self.get_allies_of(attacker)
        enemies = self.get_enemies_of(attacker)

        if skill.target == "enemy":
            for e in enemies:
                if tuple(e.coords) in affected_tiles:
                    targets.append(e)
        if skill.target == "friendly":
            for f in friendlies:
                if tuple(f.coords) in affected_tiles:
                    targets.append(f)

        if skill.target == "empty":
            #empty is for summons and skills that do NOT target an actor
            targets.append(affected_tiles[0])

        if skill.target in ["all", "tile"]:
            for e in enemies:
                if tuple(e.coords) in affected_tiles:
                    targets.append(e)
            for f in friendlies:
                if tuple(f.coords) in affected_tiles:
                    targets.append(f)

        return targets

    def skill_target(self, attacker, skill, affected_tiles):
        attacker.mp = attacker.mp - self.get_adjusted_mp(skill, attacker)
        potential_targets = self.get_targets_for_area(attacker, skill, affected_tiles)
        affected_targets = []
        for target in potential_targets:
            if skill.is_beneficial or skill.target == 'empty' or self.attack_roll(attacker, target, skill):
                affected_targets.append(target)

        if affected_targets:
            self.skill_effect(attacker, skill, affected_targets, affected_tiles)
    #
    # def skill_effect(self, attacker, skill, targets, affected_tiles):
    #     for t in targets:
    #         if skill.damage != 0:
    #             damage = self.damage_roll(attacker, t, skill)
    #         else:
    #             damage = 0
    #
    #         for effect in skill.effects:
    #             if effect["type"] in ["Drain"]:
    #                 attacker.hp += damage
    #                 if attacker.hp > attacker.maxhp:
    #                     attacker.hp = attacker.maxhp
    #             elif effect["type"] in ["Pull", "Push"]:
    #                 self.forced_move(attacker, t, effect["type"], effect["magnitude"])
    #             elif effect["type"] in ["Capture", "Pushto"]:
    #                 self.forced_move(attacker, t, effect["type"], effect["magnitude"], affected_tiles[0])
    #             elif effect["type"] == "Summon":
    #                 self.summon(attacker, effect["to_summon"], targets[0])
    #             else:  # status effect
    #                 if t.hp <= 0:   #check if target is dead first
    #                     continue
    #
    #                 effect_type = effect['type']
    #                 #resolve dual status skills
    #                 if "|" in effect["type"]:
    #                     if t in self.get_allies_of(attacker):
    #                         effect_type = effect["type"].split("|")[0]
    #                     else:
    #                         effect_type = effect["type"].split("|")[1]
    #
    #                 # if same status already exists, refresh duration
    #                 break_flag = False
    #                 for status in t.status:
    #                     if status.name == effect_type:
    #                         status.duration = effect["duration"]
    #                         if status.magnitude < effect['magnitude']:
    #                             status.magnitude = effect["magnitude"]
    #                         break_flag = True
    #                         break
    #                 if break_flag:
    #                     continue
    #                 if effect_type in t.immunities:
    #                     self.report.add_entry("immunity", t, cause=effect_type)
    #                     continue
    #
    #                 if effect_type in DEFAULT_STATUS_EFFECTS:
    #                     modifiers = DEFAULT_STATUS_EFFECTS[effect_type].effects
    #                     continuous = DEFAULT_STATUS_EFFECTS[effect_type].continuous
    #                     impairing = DEFAULT_STATUS_EFFECTS[effect_type].impairing
    #                 else:  # custom status effects defined in xml
    #                     modifiers = effect["modifiers"]
    #                     continuous = effect["continuous"]
    #                     #add impairing if needed
    #                     impairing = False
    #
    #                 status_to_apply = AppliedStatusEffect(effect_type, modifiers, effect["duration"], self.report,
    #                                                       magnitude=effect["magnitude"], continuous=continuous,
    #                                                       impairing=impairing)
    #                 t.status.append(status_to_apply)
    #                 status_to_apply.apply_status(t)
    #
    #     return

    def summon(self, caster, monster, tile):
        tile = [tile[0], tile[1]]
        self.state_changes.append(("summon", monster, tile, caster.team_id))
        return

    # def attack_roll(self, attacker, defender, skill):
    #     if skill.aoe == 'global':
    #         return True
    #     if skill.stat == "attack":
    #         random_roll = random.randint(0, attacker.attack)
    #         attack_roll = (attacker.attack/2) + random_roll
    #         if attack_roll >= defender.defense:
    #             return True
    #         else:
    #             self.report.add_entry("miss", defender, cause=skill.name)
    #             return False
    #     elif skill.stat == "magic":
    #         attack_roll = (attacker.magic/2) + random.randint(0, attacker.magic)
    #         if attack_roll >= defender.resistance:
    #             return True
    #         else:
    #             self.report.add_entry("resist", defender, cause=skill.name)
    #             return False
    #     return
    #
    # def damage_roll(self, attacker, defender, skill):
    #     inflicted_damage = 0
    #
    #     if skill.damage.get('fixed_damage'):
    #         inflicted_damage = skill.damage['fixed_damage']
    #     else:
    #         num_dice = skill.damage['num_dice']
    #         dice_size = skill.damage['dice_size']
    #         roll = 0
    #         for i in range(num_dice):
    #             randoms = [1*(dice_size/abs(dice_size)), dice_size]  #1 or - 1
    #             randoms.sort()
    #             roll = roll + random.randint(*randoms)
    #             inflicted_damage = roll + (getattr(attacker, skill.stat)/3)*(roll/abs(roll))
    #
    #     defender.hp -= inflicted_damage
    #     if defender.hp > defender.maxhp:
    #         defender.hp = defender.maxhp
    #     if inflicted_damage < 0:
    #         self.report.add_entry("heal", defender, cause=skill.name, effect=str(abs(inflicted_damage)))
    #     else:
    #         self.report.add_entry("damage", defender, cause=skill.name, effect=str(abs(inflicted_damage)))
    #
    #     if defender == self.hero and inflicted_damage > 0:
    #         self.hero.score['damage'] += inflicted_damage
    #     return inflicted_damage

    def validate_ai_turn(self, e, skill, target, path):
        print e, skill, target, path
        if target:
            target_tile = self.bmap[target[0]][target[1]]

        def move_is_legal():
            for tile in path:
                if self.bmap[tile[0]][tile[1]].is_movable():
                    continue
                else:
                    print "Actor {0} returned illegal move. Tile ({1}, {2}) is blocked.".format(e.name, tile[0], tile[1])
                    return False
            return True

        def skill_is_legal():
            if e.mp >= skill.mp:
                return True
            else:
                print "Actor {0} does not have the MP to cast {1}. MP: {2} Needed: {3}".format(e.name, skill.name, e.mp, skill.mp)
                return False

        def target_is_legal():
            if skill and skill.target == "empty" and not target_tile.is_movable():
                print "Actor {0} can not use skill {1} on tile ({2}, {3}): Blocked".format(e.name, skill.name, target[0], target[1])
                return
            else:
                return True
            #todo: check skill range

        if skill and not skill_is_legal():
            return False

        if path and not move_is_legal():
            return False

        if target and not target_is_legal():
            return False

        return True

    def grid_distance(self, actor1, actor2):
        return abs(actor1[0] - actor2[0]) + abs(actor1[1] - actor2[1])

    def enemy_skill(self, e, skill, target):
        affected_tiles = RN2_battle_logic.calculate_affected_area(target, self.active.coords, skill, self.bmap)
        self.affected_tiles = affected_tiles
        self.skill_target(e, skill, affected_tiles)

    def resolve_status(self, actor):
        can_act = True
        if not actor.active_status_effects:
            return can_act

        actor.tick_continuous_status()
        if actor.stunned:
            self.report.add_entry('stunned', actor)
            can_act = False

        if actor.hp <= 0:
            can_act = False

        actor.decrement_status_durations()

        return can_act

    def stat_modifiers(self, a):
        stats_list = ["attack", "defense", "magic", "resistance", "agility", "move"]
        for stat in stats_list:
            stat_mod = getattr(a, stat) + a.statmods[stat]
            setattr(a, stat, stat_mod)

    def resolve_terrain(self, actor):
        is_okay = True
        is_terrain_immune = 'Terrain' in actor.immunities
        actor_on_tile = self.bmap[actor.coords[0]][actor.coords[1]]

        if actor_on_tile.terrain.fatal and not is_terrain_immune:
            actor.kill_actor()
            self.report.add_entry('terrain_kill', actor, cause=actor_on_tile.terrain.name)
            is_okay = False

        return is_okay

    def forced_move(self, attacker, defender, direction, magnitude, origin=False):  #returns a path for later animation
        if "Push" in defender.immunities:
            self.report.add_entry("immunity", defender, cause="Push/Pull")
            return
        if origin:
            nexus = origin
        else:
            nexus = attacker.coords
        magnitude = int(magnitude)
        if direction in ["Push", "Pushto"]:
            direction = 1
        elif direction in ["Pull", "Capture"]:
            direction = -1
        x_dist = nexus[0] - defender.coords[0]
        y_dist = nexus[1] - defender.coords[1]
        path = [defender.coords]
        for i in range(magnitude):
            prev_coords = tuple(defender.coords)
            if abs(x_dist) >= abs(y_dist) and nexus[0] > defender.coords[0]:
                path.append([defender.coords[0]-(1*direction), defender.coords[1]])
            elif abs(x_dist) >= abs(y_dist) and nexus[0] <= defender.coords[0]:
                path.append([defender.coords[0]+(1*direction), defender.coords[1]])
            elif abs(x_dist) < abs(y_dist) and nexus[1] > defender.coords[1]:
                path.append([defender.coords[0], defender.coords[1]-(1*direction)])
            elif abs(x_dist) < abs(y_dist) and nexus[1] < defender.coords[1]:
                path.append([defender.coords[0], defender.coords[1]+(1*direction)])
            defender.coords = path[-1]

            #TODO: CRASHES ON FORCED MOVE OUT OF BOUNDS
            defender_on_tile = self.bmap[defender.coords[0]][defender.coords[1]]

            if self.check_bounds(defender.coords) == True or defender_on_tile.actor is not None or defender_on_tile.terrain.blocking == 1:
                defender.coords[0] = prev_coords[0]
                defender.coords[1] = prev_coords[1]
                break

            if defender_on_tile.terrain.fatal == 1:
                if 'Terrain' in defender.immunities:
                    self.report.add_entry("immunity", defender, cause="fatal terrain")
                    defender.coords[0] = prev_coords[0]
                    defender.coords[1] = prev_coords[1]
                break


            time.sleep(0.1)
        self.state_changes.append(("forcedmove", path, defender))
        return