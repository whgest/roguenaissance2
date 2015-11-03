"""

Project Roguenaissance 2.0
Battle System Controller
by William Hardy Gest

October 2013

"""
import RN2_initialize
import RN2_battle
import RN2_UI
import RN2_animations
import copy
import RN2_AI
import logging
import traceback
import time
import string as string_module
import pathfinder

logging.basicConfig(filename="logs/rn_debug.log", filemode="w+", level=logging.DEBUG)


class BattleReportLine():
    def __init__(self, string, cause_color='', effect_color='', line_color=''):
        self.string = string
        self.effect_color = effect_color
        self.cause_color = cause_color
        self.line_color = line_color

class BattleReportWord():
    def __init__(self, string, color):
        self.string = string
        self.color_binding = color

    def __str__(self):
        return "%s (%s)" % (self.string, self.color_binding)

class BattleReport():
    def __init__(self, heroes, enemies, RN_UI):
        self.RN_UI = RN_UI
        self.narration_q_length = 13
        self.strip_string = string_module.punctuation.replace("%", "")
        self.narration_q = []
        for i in range(self.narration_q_length):
            self.narration_q.append('')
        self.ally_names = []
        self.enemy_names = []
        self.turn_report = []
        self.ally_names = [h.name for h in heroes]
        self.enemy_names = [e.name for e in enemies]
        self.report_formats = {
            "use_skill": BattleReportLine("%unit: --%cause--", cause_color='skill'),
            "damage": BattleReportLine("%unit: Suffers %effect damage from %cause.", cause_color='skill', effect_color='damage'),
            "heal": BattleReportLine("%unit: Gains %effect life from %cause.", cause_color='skill', effect_color='heal'),
            "miss": BattleReportLine("%unit: Evades %cause.", cause_color='skill'),
            "resist": BattleReportLine("%unit: Resists %cause.", cause_color='skill'),
            "bad_status": BattleReportLine("%unit: Afflicted by %cause.", cause_color='bad_status'),
            "good_status": BattleReportLine("%unit: Affected by %cause.", cause_color='good_status'),
            "immunity": BattleReportLine("%unit: Immune to %cause.", cause_color='bad_status'),
            "death": BattleReportLine("%unit dies!", line_color="death"),
            "stunned": BattleReportLine("%unit is stunned and cannot act.", line_color='bad_status'),
            "status_damage": BattleReportLine("%unit: Suffers %effect damage from %cause.", cause_color='bad_status', effect_color='damage'),
            "regen": BattleReportLine("%unit: Gains %effect life from %cause.", cause_color='good_status', effect_color='heal'),
            "status_update": BattleReportLine("%unit: Afflicted by %cause: %effect!", cause_color='bad_status', effect_color='bad_status'),
            "good_status_ends": BattleReportLine("%unit: No longer affected by %cause.", cause_color='good_status'),
            "status_ends": BattleReportLine("%unit: No longer afflicted by %cause.", cause_color='bad_status'),
            "status_kill": BattleReportLine("%unit: Killed by %cause!", cause_color='bad_status'),
            "terrain_kill": BattleReportLine("%unit: Falls into %cause!", cause_color='bad_status'),
            "victory": BattleReportLine("%unit achieved victory.", line_color="ally_name")
        }

    def colorize_unit_name(self, unit):
        if isinstance(unit, RN2_initialize.Hero):
            return "hero_name"
        elif isinstance(unit, RN2_initialize.Ally):
            return "ally_name"
        elif isinstance(unit, RN2_initialize.Actor):
            return "enemy_name"
        else:
            return ""

    def add_entry(self, _format, unit, cause=None, effect=None):
        report_obj = self.report_formats[_format]
        colorized_list = []
        word_list = report_obj.string.split(" ")

        for word in word_list:
            color = ''
            if word.translate(string_module.maketrans("", ""), self.strip_string) == "%unit":
                word = word.replace("%unit", unit.name)
                color = self.colorize_unit_name(unit)
            elif word.translate(string_module.maketrans("", ""), self.strip_string) == "%cause" and report_obj.cause_color:
                word = word.replace("%cause", cause)
                color = report_obj.cause_color
            elif word.translate(string_module.maketrans("", ""), self.strip_string) == "%effect" and report_obj.effect_color:
                word = word.replace("%effect", effect)
                color = report_obj.effect_color
            if not color:
                color = "text"
            if report_obj.line_color:
                color = report_obj.line_color
            colorized_list.append(BattleReportWord(word, color))

        self.turn_report.append(colorized_list)
        self.process_report()

    def add_raw_entry(self, text, color="text"):
        colorized_list = []
        for word in text.split(" "):
            colorized_list.append(BattleReportWord(word, color))
        self.turn_report.append(colorized_list)
        self.process_report()

    def process_report(self):
        for report in self.turn_report:
            self.narration_q.insert(0, report)
            del self.narration_q[self.narration_q_length]
        self.turn_report = []
        self.RN_UI.print_narration(self.narration_q)


class Battle_Controller():
    def __init__(self, hero, battle_data, bmap, UI, RN_sound, skills, actors, input):

        self.hero = hero
        self.heroname = hero.name
        self.heroclass = hero.hclass
        self.battle_data = battle_data
        self.bmap = bmap
        self.input = input
        self.skills = skills
        self.actors = actors
        self.UI = UI
        self.RN_sound = RN_sound
        self.mute_switch = False
        self.states = {
            "move": self.movestate,
            "target": self.targetstate,
            "skills": self.skillmenu,
            "battle": self.battlemenu,
            "confirm": self.confirmstate
        }
        self.heroes = []


    def init_battle(self):
        self.battle = RN2_battle.Battle(self.hero, self.battle_data, self.add_actors(self.battle_data), self.bmap)
        self.report = BattleReport(self.battle.heroes, self.battle.enemies, self.UI)
        self.battle.report = self.report
        startpos = self.battle.startpos
        self.battle.bmap[startpos[0]][startpos[1]].actor = self.hero
        self.hero.coords = [startpos[0], startpos[1]]
        self.UI.draw_UI()
        self.UI.print_map(self.battle.bmap)
        self.UI.print_legend(self.battle.bmap.legend_list, self.battle.unit_list)
        self.init_music()

        victory = self.battle_manager(self.battle, self.UI)
        return victory

    def init_music(self):
        self.RN_sound.cut_music()

        try:
            self.RN_sound.play_music(self.battle_data['music'][0])
            # if len(self.battle_data['music']) > 1:
            #     for i, track in enumerate(self.battle_data['music']):
            #         if i > 0:
            #             self.RN_sound.play_music(track, queue=True)
        except KeyError: #no music defined
            pass

    def add_actors(self, battle):
        b_actors = []
        for e in battle["actors"]:
            e2 = e.split("/")
            stats = self.actors[e2[0]]  #pull stats from database

            if stats.ai[0].value == "boss":
                enemy = RN2_initialize.Boss(stats)
            else:
                enemy = RN2_initialize.Actor(stats)
            enemy.coords = [int(c) for c in e2[1].split(",")]
            enemy.name = e2[0]
            b_actors.append(enemy)
        return b_actors

    def battle_manager(self, battle, RN_UI):
        self.battle_events(start=True)
        battle.unit_list = self.make_unit_list(battle)
        self.battle.turn_tracker = RN2_battle.TurnTracker(battle.heroes, battle.enemies)
        self.battle.turn_tracker.roll_initiative()
        RN_UI.print_map(battle.bmap)
        while 1:
            battle.unit_list = self.make_unit_list(battle)
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            victory = self.battle_events()
            if victory:
                self.report.add_entry("victory", self.hero)
                self.RN_sound.cut_music()
                self.RN_sound.play_music('victory')
                time.sleep(1)
                self.report.add_raw_entry("")
                self.report.add_raw_entry("Total Turns Taken: " + str(self.hero.score['turns']), color="bad_status")
                time.sleep(1)
                self.report.add_raw_entry("Total Damage Taken: " + str(self.hero.score['damage']), color="bad_status")
                time.sleep(1)
                self.report.add_raw_entry("Total Enemies Killed: " + str(self.hero.score['killed']), color="good_status")
                time.sleep(1)
                RN_UI.wait_for_keypress()
                RN_UI.fade_to_black()
                return True
            player, battle.active = battle.turn_manager()
            hero = False
            if battle.active in battle.heroes:
                hero = True
            RN_UI.print_turn(battle.active.name, hero)

            terrain_ok = battle.resolve_terrain(battle.active)
            active_can_act = battle.resolve_status(battle.active)
            if not active_can_act or not terrain_ok:
                self.clear_board(battle, RN_UI)
                continue

            RN_UI.print_narration(self.report.process_report())
            if player:
                    self.RN_sound.play_sound("beep2")
                    RN_UI.turn_indication(battle.active)
                    RN_UI.print_status(battle.active, battle.bmap[battle.active.coords[0]][battle.active.coords[1]].terrain)
                    battle.state = "move"
                    battle.prevstate = "move"
                    battle.move_range = 0
                    battle.move_range = battle.get_range(tuple(battle.active.coords), battle.active.move, pathfind=True, is_move=True)
                    RN_UI.highlight_area(True, battle.move_range, battle.bmap, "teal")
                    turn = False
                    while not turn:
                        RN_UI.print_status(battle.active, battle.bmap[battle.active.coords[0]][battle.active.coords[1]].terrain)
                        command = self.input()
                        if command == "invalid":
                            RN_UI.print_prompt("Invalid command.")
                            self.RN_sound.play_sound("error")
                            continue
                        turn, newstate = self.RN_output(command, battle, RN_UI)
                        if newstate != battle.state and newstate is not False:
                            self.change_state(battle.state, newstate, battle)
                            self.prep_state(battle, RN_UI)
                    if battle.state != "confirmed":
                        pass
                    else:
                        self.report.add_entry("use_skill", battle.active, battle.selected_skill.name)
                        RN_UI.print_narration(self.report.process_report())
                        RN2_animations.RN_Animation_Class(battle.affected_tiles, self.RN_sound, RN_UI, battle.selected_skill.animation, battle.bmap, battle.active.coords)
                        battle.skill_target(battle.active, battle.selected_skill, battle.affected_tiles)
                        RN_UI.print_status(battle.active, battle.bmap[battle.active.coords[0]][battle.active.coords[1]].terrain)

            else:
                battle.bmap[battle.active.coords[0]][battle.active.coords[1]].actor = None
                RN_AI = RN2_AI.RN_AI_Class(battle, battle.active, self.skills)
                RN_UI.turn_indication(battle.active)
                skill, target, path = RN_AI.enemy_turn()

                if skill is not None:
                    self.report.add_entry("use_skill", battle.active, skill)
                    RN_UI.print_narration(self.report.process_report())
                    path, target, skill = battle.execute_ai_turn(battle.active, self.skills[skill], target, path)

                else:
                    path, target, skill = battle.execute_ai_turn(battle.active, None, target, path)
                if path:
                    battle.bmap[path[-1][0]][path[-1][1]].actor = battle.active  #update map data
                else:
                    battle.bmap[[battle.active][0]][battle.active[1]].actor = battle.active
                self.show_ai_turn(battle.active, path, target, skill, RN_UI, battle)

                if skill is not None:
                    RN2_animations.RN_Animation_Class(battle.affected_tiles, self.RN_sound, RN_UI, skill.animation, battle.bmap, battle.active.coords)
                self.check_desync(battle)
            self.update_game(battle, RN_UI)
            game_over = self.clear_board(battle, RN_UI)
            if game_over:
                self.RN_sound.cut_music()
                self.RN_sound.play_music('gameover')
                RN_UI.fade_to_black()
                return False
            RN_UI.print_narration(self.report.process_report())
            time.sleep(0.2)

    def battle_events(self, start=False):     #check for battle event conditions
        if start:
            self.activate_event(self.battle.events[0])
            return
        for e in self.battle.events:
            event_trigger = False
            condition = e.condition[0].value.split(",")
            if condition[0] == "turn" and self.battle.turn_tracker.turn_count == int(condition[1]):
                event_trigger = True
            elif condition[0] == "playeryGreater" and self.battle.hero.coords[1] >= int(condition[1]):
                event_trigger = True
            elif condition[0] == "playeryLesser" and self.battle.hero.coords[1] <= int(condition[1]):
                event_trigger = True
            elif condition[0] == "playeryIs" and self.battle.hero.coords[1] == int(condition[1]):
                event_trigger = True
            elif condition[0] == "playerxLesser" and self.battle.hero.coords[0] <= int(condition[1]):
                event_trigger = True
            elif condition[0] == "playerxGreater" and self.battle.hero.coords[0] >= int(condition[1]):
                event_trigger = True
            elif condition[0] == "playerxIs" and self.battle.hero.coords[0] == int(condition[1]):
                event_trigger = True
            elif condition[0] == "bosskill" and (not self.battle.enemies or not self.battle.enemies[0].is_boss):
                event_trigger = True

            if event_trigger:
                if self.activate_event(e):
                    return True

    def activate_event(self, event):
        effect = event.effect[0].value.split(",")
        if effect[0] == "victory":
            return True
        if effect[0] == "add_mobs":
            for f in effect:
                if f == "add_mobs":
                    continue
                e = int(f)
                enemy = self.battle.actors[e]
                self.battle.enemies.append(enemy)
                self.battle.turn_tracker.add_unit(enemy)
                self.battle.bmap[enemy.coords[0]][enemy.coords[1]].actor = enemy
                self.UI.update_map("new", enemy.coords, enemy, self.battle.bmap)
            if effect[0] == "pass":
                pass
        self.battle.events.remove(event)
        return

    def make_unit_list(self, battle):
        unit_list = []
        for h in battle.heroes:
            if (h.character, h.name) not in unit_list:
                unit_list.append((h.character, h.name, h.color))
        for e in battle.enemies:
            if (e.character, e.name) not in unit_list:
                unit_list.append((e.character, e.name, e.color))
        return unit_list

    def update_game(self, battle, RN_UI):   #death, summons, forced movement
        for change in battle.state_changes:
            if change[0] == "summon":
                self.add_summon(change, battle, RN_UI)
            elif change[0] == "forcedmove":
                path = change[1]
                for i in range(len(change[1])-1):
                    RN_UI.update_map(change[1][i], change[1][i+1], change[2], battle.bmap)
                    battle.bmap[change[1][0][0]][change[1][0][1]].actor = None
                    battle.bmap[change[1][-1][0]][change[1][-1][1]].actor = change[2]
                    #time.sleep(0.05)
            elif change[0] == "terrainmod":
                pass
            else:
                pass
        battle.state_changes = []
        return

    def clear_board(self, battle, RN_UI):
        unit_list = battle.enemies + battle.heroes
        for unit in unit_list:
            if unit.hp <= 0 or unit.status == [{"type": "Dead"}]:
                self.report.add_entry("death", unit)
                if unit.death_animation:
                    RN2_animations.RN_Animation_Class([tuple(unit.coords)], self.RN_sound, RN_UI, unit.death_animation, battle.bmap, battle.active.coords)
                battle.bmap[unit.coords[0]][unit.coords[1]].actor = None
                RN_UI.update_map(unit.coords, "dead", unit, battle.bmap)
                self.battle.turn_tracker.remove_unit(unit)
                try:
                    battle.enemies.remove(unit)
                    self.battle.hero.score['killed'] += 1
                except ValueError:
                    battle.heroes.remove(unit)
                    if unit == self.battle.hero:
                        return True #game over

    def add_summon(self, data, battle, RN_UI):
        stats = self.actors[data[1]]
        if data[3] == "enemy":
            summon = RN2_initialize.Actor(stats)
            battle.enemies.append(summon)
        else:
            summon = RN2_initialize.Ally(stats)
            battle.heroes.append(summon)

        summon.coords = data[2]
        battle.bmap[summon.coords[0]][summon.coords[1]].actor = summon
        summon.name = data[1]

        battle.turn_tracker.add_unit(summon)
        RN_UI.update_map("new", summon.coords, summon, battle.bmap)


    def check_desync(self, battle):
        for e in battle.enemies:
            if battle.bmap[e.coords[0]][e.coords[1]].actor != e:
                print repr(e.name) + " DESYNC: " + repr(e.coords)

    def RN_output(self, command, battle, RN_UI):
        if command == "exit":
            exit()
        if command == "legend":
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            return False, False
        if command == "stats":
            RN_UI.print_stats(battle.active)
            return False, False
        if command == "mute":
            self.init_music()
            return False, False

        turn, newstate = self.states[battle.state](command, battle, RN_UI)
        return turn, newstate

    def change_state(self, state, newstate, battle):
        battle.prevstate = copy.deepcopy(state)
        battle.state = newstate
        return

    def prep_state(self, battle, RN_UI):
        if battle.state == "move":
            battle.selected_skill = None
            battle.targetable_tiles = None
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            RN_UI.highlight_area(True, battle.move_range, battle.bmap, "teal")
        elif battle.state == "target":
            battle.attack_target = None
            battle.affected_tiles = None
            x = battle.active.coords[0]
            y = battle.active.coords[1]
            RN_UI.cursor.move_cursor(x, y, battle.bmap[x][y])
            RN_UI.print_prompt(battle.selected_skill.name + " --- " + "Choose target tile. (Range: " + str(battle.selected_skill.range) + ")")
            RN_UI.highlight_area(True, battle.targetable_tiles, battle.bmap, "maroon")
        elif battle.state == "confirm":
            battle.affected_tiles = battle.get_range(battle.target_tile, battle.selected_skill.aoe)
            RN_UI.highlight_area(False, battle.targetable_tiles, battle.bmap)
            RN_UI.highlight_area(True, battle.affected_tiles, battle.bmap, "lime")
            RN_UI.print_prompt("ENTER to confirm attack, ESC to cancel.")
        elif battle.state == "skills":
            RN_UI.draw_skills_menu(battle.active.skillset[1:], 0, self.skills[battle.active.skillset[1]].prompt, battle.get_adjusted_mp, self.skills)
            battle.skill_index = 0
        elif battle.state == "battle":
            battle.battle_menu_list = []
            for actor in battle.turn_tracker.initiative_list:
                battle.battle_menu_list.append((actor.name, " HP " + str(actor.hp) + "/" + str(actor.maxhp) + " (" + RN_UI.get_status(actor)[0] + ")", actor))
            battle.battle_menu_list.reverse()
            battle.battle_menu_list.insert(0, battle.battle_menu_list.pop()) #put active unit at top
            battle.v_top = RN_UI.print_battle_menu(battle.battle_menu_list, battle.turn_tracker.turn_count, battle.battle_index, battle.v_top)
            battle.battle_index = 0

    def movestate(self, command, battle, RN_UI):
        active = battle.active
        RN_UI.highlight_area(True, battle.move_range, battle.bmap)
        prev_coords = tuple(active.coords)
        if command == "activate":
            if len(active.skillset) <= 1:
                self.RN_sound.play_sound("error")
                RN_UI.print_prompt("No usable skills.")
                return False, False
            RN_UI.highlight_area(False, battle.move_range, battle.bmap)
            battle.selected_skill = self.skills[active.skillset[0]]
            battle.targetable_tiles = battle.get_range(battle.active.coords, battle.selected_skill.range)
            return False, "target"
        if command == "cancel":
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            return False, False
        elif command == "help":
            RN_UI.print_prompt()
            RN_UI.showhelp()
            return False, False
        elif command == "left":
            active.coords[0] -= 1
        elif command == "up":
            active.coords[1] -= 1
        elif command == "down":
            active.coords[1] += 1
        elif command == "right":
            active.coords[0] += 1
        elif command == "pass":
            RN_UI.highlight_area(False, battle.move_range, battle.bmap)
            return True, False
        elif command == "skills":
            RN_UI.highlight_area(False, battle.move_range, battle.bmap)
            if len(active.skillset) <= 1:
                self.RN_sound.play_sound("error")
                RN_UI.print_prompt("No usable skills.")
                return False, False
            return False, "skills"
        elif command == "battle":
            RN_UI.highlight_area(False, battle.move_range, battle.bmap)
            return False, "battle"
        else:
            return False, "invalid"
        if battle.check_bounds(active.coords) is True or battle.bmap[active.coords[0]][active.coords[1]].actor is not None or battle.bmap[active.coords[0]][active.coords[1]].terrain.movable != 1:
            active.coords[0] = prev_coords[0]
            active.coords[1] = prev_coords[1]
            self.RN_sound.play_sound("error")
            RN_UI.print_prompt("That direction is blocked.")
        if tuple(active.coords) not in battle.move_range:
            active.coords[0] = prev_coords[0]
            active.coords[1] = prev_coords[1]
            self.RN_sound.play_sound("error")
            RN_UI.print_prompt("You can't move that far.")
        battle.bmap[prev_coords[0]][prev_coords[1]].actor = None
        battle.bmap[active.coords[0]][active.coords[1]].actor = active
        RN_UI.update_map(prev_coords, active.coords, active, battle.bmap)
        RN_UI.highlight_area(True, battle.move_range, battle.bmap)
        return False, False

    def targetstate(self, command, battle, RN_UI):
        def get_shared_tiles(in_range, targeted):
            overlap_tiles = set(range_tiles).intersection(set(targeted))
            range_only = set(in_range).difference(overlap_tiles)
            aoe_only = set(targeted_aoe).difference(overlap_tiles)
            return range_only, aoe_only, overlap_tiles

        skill = battle.selected_skill
        x = RN_UI.cursor.x
        y = RN_UI.cursor.y
        prev_cursor = (x, y)

        if command == "left":
            x -= 1
        elif command == "up":
            y -= 1
        elif command == "down":
            y += 1
        elif command == "right":
            x += 1
        elif command == "activate":
            attack_target = (x, y)
            if skill.target == "empty":
                if battle.bmap[attack_target[0]][attack_target[1]].actor is None and battle.bmap[attack_target[0]][attack_target[1]].terrain.movable == 1:
                    battle.target_tile = attack_target
                    return False, "confirm"
                self.RN_sound.play_sound("error")
                RN_UI.print_prompt("That tile is occupied or inaccessible.")
                return False, False
            else:
                battle.target_tile = attack_target
                return False, "confirm"

        elif command == "cancel":
            RN_UI.cursor.move_cursor(x, y, battle.bmap[x][y])
            RN_UI.highlight_area(False, battle.targetable_tiles, battle.bmap)
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            RN_UI.print_prompt("arrows = move. a = attack. s = use skills. space = end turn. h = help")
            return False, "move"

        if battle.check_bounds((x, y)) or (x, y) not in battle.targetable_tiles or battle.bmap[x][y].terrain.targetable == 0:
            x = prev_cursor[0]
            y = prev_cursor[1]
            self.RN_sound.play_sound("error")

        RN_UI.clear_highlight_area(battle.bmap)

        RN_UI.cursor.move_cursor(x, y, battle.bmap[x][y])

        range_tiles = list(battle.targetable_tiles)
        targeted_aoe = battle.get_range((x, y), skill.aoe)
        range_only, aoe_only, overlap = get_shared_tiles(range_tiles, targeted_aoe)

        RN_UI.highlight_area(True, range_only, battle.bmap, color="maroon")
        RN_UI.highlight_area(True, aoe_only, battle.bmap, color='white')
        RN_UI.highlight_area(True, overlap, battle.bmap, color='fuchsia')

        affected_units = battle.get_targets_for_area(battle.active, battle.selected_skill, targeted_aoe)

        if len(affected_units) == 1:
            RN_UI.print_target(battle.active, affected_units[0], battle.selected_skill)
        elif len(affected_units) > 1:
            RN_UI.print_multi_target(battle.active, affected_units, battle.selected_skill)
        else:
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)

        return False, False

    def confirmstate(self, command, battle, RN_UI):
        RN_UI.highlight_area(False, battle.affected_tiles, battle.bmap)
        if command == "activate":
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            return True, "confirmed"
        else:
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            return False, "target"

    def battlemenu(self, command, battle, RN_UI):
        RN_UI.highlight_active(battle.battle_menu_list[battle.battle_index][2], False)
        if command == "up":
            battle.battle_index -= 1
        elif command == "down":
            battle.battle_index += 1
        elif command in ["cancel", "activate"]:
            return False, battle.prevstate
        battle.battle_index %= len(battle.battle_menu_list)
        battle.v_top = RN_UI.print_battle_menu(battle.battle_menu_list, battle.turn_tracker.turn_count, battle.battle_index, battle.v_top)
        return False, False

    def skillmenu(self, command, battle, RN_UI):
        selectable_skills = battle.active.skillset[1:] #remove basic attack

        if command == "up":
            battle.skill_index -= 1
        elif command == "down":
            battle.skill_index += 1
        elif command == "activate" or command[0] == "F":
            if command[0] == "F":
                f_key = int(command[1:])
                battle.skill_index = f_key - 1
            if battle.active.mp < battle.get_adjusted_mp(self.skills[selectable_skills[battle.skill_index]]):
                self.RN_sound.play_sound("error")
                RN_UI.draw_skills_menu(selectable_skills, battle.skill_index, "Insufficient MP.", battle.get_adjusted_mp, self.skills)
                return False, False
            else:
                RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
                battle.selected_skill = self.skills[selectable_skills[battle.skill_index]]
                battle.targetable_tiles = battle.get_range(battle.active.coords, battle.selected_skill.range)
                if battle.selected_skill.range != 0:  #pb-AOEs skip target state
                    return False, "target"
                else:
                    battle.target_tile = self.battle.active.coords
                    return False, "confirm"
        elif command == "cancel":
            return False, "move"


        battle.skill_index %= len(selectable_skills)
        prompt = self.skills[selectable_skills[battle.skill_index]].prompt
        RN_UI.draw_skills_menu(selectable_skills, battle.skill_index, prompt, battle.get_adjusted_mp, self.skills)
        return False, False

    def show_ai_turn(self, e, path, target, skill, RN_UI, battle):
        for i in range(len(path)-1):
            RN_UI.update_map(path[i], path[i+1], e, battle.bmap)
            time.sleep(0.02)
        return


# def main():
#     pass
#
# if __name__ == "__main__":
#     try:
#         main()
#     except:
#         exception_string = traceback.format_exc()
#         logging.error(exception_string)
#         print exception_string