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
import RN2_battle_logic

logging.basicConfig(filename="logs/rn_debug.log", filemode="w+", level=logging.DEBUG)


class BattleReportLine:
    def __init__(self, string, cause_color='', effect_color='', line_color=''):
        self.string = string
        self.effect_color = effect_color
        self.cause_color = cause_color
        self.line_color = line_color


class BattleReportWord:
    def __init__(self, string, color):
        self.string = string
        self.color_binding = color

    def __str__(self):
        return "%s (%s)" % (self.string, self.color_binding)


class BattleReport:
    def __init__(self, RN_UI):
        self.RN_UI = RN_UI
        self.narration_q_length = 13
        self.strip_string = string_module.punctuation.replace("%", "")
        self.narration_q = []
        for i in range(self.narration_q_length):
            self.narration_q.append('')
        self.turn_report = []
        self.report_formats = {
            "use_skill": BattleReportLine("%unit: --%cause--", cause_color='skill'),
            "damage": BattleReportLine("%unit: Suffers %effect damage from %cause.", cause_color='skill', effect_color='damage'),
            "heal": BattleReportLine("%unit: Gains %effect HP from %cause.", cause_color='skill', effect_color='heal'),
            "miss": BattleReportLine("%unit: Evades %cause.", cause_color='skill'),
            "resist": BattleReportLine("%unit: Resists %cause.", cause_color='skill'),
            "bad_status": BattleReportLine("%unit: Afflicted by %cause.", cause_color='bad_status'),
            "good_status": BattleReportLine("%unit: Affected by %cause.", cause_color='good_status'),
            "immunity": BattleReportLine("%unit: Immune to %cause.", cause_color='bad_status'),
            "death": BattleReportLine("%unit dies!", line_color="death"),
            "disabled": BattleReportLine("%unit is disabled by %cause and cannot act.", line_color='bad_status'),
            "status_damage": BattleReportLine("%unit: Suffers %effect damage from %cause.", cause_color='bad_status', effect_color='damage'),
            "status_heal": BattleReportLine("%unit: Gains %effect life from %cause.", cause_color='good_status', effect_color='heal'),
            "status_update": BattleReportLine("%unit: Afflicted by %cause: %effect!", cause_color='bad_status', effect_color='bad_status'),
            "good_status_ends": BattleReportLine("%unit: No longer affected by %cause.", cause_color='good_status'),
            "bad_status_ends": BattleReportLine("%unit: No longer afflicted by %cause.", cause_color='bad_status'),
            "status_kill": BattleReportLine("%unit: Killed by %cause!", cause_color='bad_status'),
            "terrain_kill": BattleReportLine("%unit: Falls into %cause!", cause_color='bad_status'),
            "victory": BattleReportLine("%unit achieved victory.", line_color="ally_name")
        }

    def colorize_unit_name(self, unit):
        #todo: show team color
        return "hero_name"

    def add_entry(self, entry):
        _format = entry.get('_format', '')
        unit = entry.get('unit', '')
        cause = entry.get('cause', '')
        effect = str(entry.get('effect', ''))


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


class Battle_Controller(object):
    def __init__(self, ui, sound_handler):

        self.report = BattleReport(ui)
        self.ui = ui
        self.sound_handler = sound_handler
        self.mute_switch = False
        self.states = {
            "move": self.movestate,
            "target": self.targetstate,
            "skills": self.skillmenu,
            "battle": self.battlemenu,
            "confirm": self.confirmstate
        }

    def init_music(self, music_ident):
        self.sound_handler.cut_music()

        try:
            self.sound_handler.play_music(music_ident)
        except KeyError:
            print "Track id {0} not found.".format(music_ident)
            raise KeyError

    def draw_battle_ui(self, battle):
        self.ui.init_animation_class(battle.bmap)
        self.ui.draw_UI()
        self.ui.set_map(battle.bmap)
        self.ui.print_map()

    def update(self, state_changes):
        # todo: update displays relating to unit states and map state
        for change in state_changes:
            if change.report_entry():
                self.report.add_entry(change.report_entry())
            change.animate(self.ui)
            change.display(self.ui)




    # def init_battle(self):
    #     #self.battle = RN2_battle.Battle(self.hero, self.battle_data, self.add_actors(self.battle_data), self.bmap)
    #     self.report = BattleReport(self.UI)
    #     self.battle.report = self.report
    #     self.UI.draw_UI()
    #     self.UI.print_map(self.battle.bmap)
    #     self.UI.print_legend(self.battle.bmap.legend_list, self.battle.unit_list)
    #     self.init_music()

        # victory = self.battle_manager(self.battle, self.UI)
        # return victory
    #
    #
    # def player_turn(self):
    #     if player:
    #         self.RN_sound.play_sound("beep2")
    #         RN_UI.turn_indication(battle.active)
    #         battle.state = "move"
    #         battle.prevstate = "move"
    #         battle.move_range = 0
    #         battle.move_range = battle.get_range(tuple(battle.active.coords), battle.active.move, pathfind=True,
    #                                              is_move=True)
    #         RN_UI.highlight_area(True, battle.move_range, battle.bmap, "teal")
    #         RN_UI.print_prompt("arrows = move. a = attack. s = use skills. space = end turn. h = help")
    #         turn_ended = False
    #         while not turn_ended:
    #             RN_UI.print_status(battle.active,
    #                                battle.bmap[battle.active.coords[0]][battle.active.coords[1]].terrain)
    #             command = self.input()
    #             if command == "invalid":
    #                 RN_UI.print_prompt("Invalid command.")
    #                 self.RN_sound.play_sound("error")
    #                 continue
    #             turn_ended, newstate = self.RN_output(command, battle, RN_UI)
    #             if newstate != battle.state and newstate is not False:
    #                 self.change_state(battle.state, newstate, battle)
    #                 self.prep_state(battle, RN_UI)
    #
    #         if battle.state == "confirmed":
    #             RN_UI.print_prompt()
    #             self.report.add_entry("use_skill", battle.active, battle.selected_skill.name)
    #             RN_UI.print_narration(self.report.process_report())
    #             RN2_animations.RN_Animation_Class(battle.affected_tiles, self.RN_sound, RN_UI,
    #                                               battle.selected_skill.animation, battle.bmap,
    #                                               battle.active.coords)
    #             battle.skill_target(battle.active, battle.selected_skill, battle.affected_tiles)
    #             RN_UI.print_status(battle.active,
    #                                battle.bmap[battle.active.coords[0]][battle.active.coords[1]].terrain)
    #


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
            RN_UI.print_prompt("arrows = move. a = attack. s = use skills. space = end turn. h = help")
        elif battle.state == "target":
            battle.attack_target = None
            battle.affected_tiles = None
            x = battle.active.coords[0]
            y = battle.active.coords[1]
            RN_UI.cursor.move_cursor(x, y, battle.bmap[x][y])
            noun = "tile" if battle.selected_skill.aoe == 0 else "area"
            RN_UI.print_prompt(battle.selected_skill.name + " --- " + "Choose target %s." % noun)
            targeted_aoe = RN2_battle_logic.calculate_affected_area((x, y), battle.active.coords, battle.selected_skill, battle.bmap)
            self.highlight_targetable_area(battle, targeted_aoe, (x, y), RN_UI)
            self.print_target_display(targeted_aoe, RN_UI)
        elif battle.state == "confirm":
            battle.affected_tiles = RN2_battle_logic.calculate_affected_area(battle.target_tile, battle.active.coords, battle.selected_skill, battle.bmap)
            RN_UI.highlight_area(False, battle.targetable_tiles, battle.bmap)
            RN_UI.highlight_area(True, battle.affected_tiles, battle.bmap, "lime")
            self.print_target_display(battle.affected_tiles, RN_UI)
            RN_UI.print_prompt("ENTER to confirm attack, ESC to cancel.")
        elif battle.state == "skills":
            RN_UI.draw_skills_menu(battle.active.skillset[1:], 0, self.skills[battle.active.skillset[1]].prompt, battle.get_adjusted_mp, self.skills)
            battle.skill_index = 0
        elif battle.state == "battle":
            battle.battle_menu_list = []
            for actor in battle.turn_tracker.initiative_list:
                if type(actor) is not str:
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

    def highlight_targetable_area(self, battle, targeted_aoe, cursor_pos, RN_UI):
        def get_shared_tiles(in_range, targeted):
            overlap_tiles = set(range_tiles).intersection(set(targeted))
            range_only_tiles = set(in_range).difference(overlap_tiles)
            aoe_only_tiles = set(targeted_aoe).difference(overlap_tiles)
            return range_only_tiles, aoe_only_tiles, overlap_tiles

        range_tiles = list(battle.targetable_tiles)
        range_only, aoe_only, overlap = get_shared_tiles(range_tiles, targeted_aoe)

        RN_UI.highlight_area(True, range_only, battle.bmap, color='maroon')
        RN_UI.highlight_area(True, aoe_only, battle.bmap, color='yellow')
        RN_UI.highlight_area(True, overlap, battle.bmap, color='orange')
        RN_UI.highlight_area(True, [cursor_pos], battle.bmap, color='white')

    def print_target_display(self, targeted_aoe, RN_UI):
        battle = self.battle
        affected_units = battle.get_targets_for_area(battle.active, battle.selected_skill, targeted_aoe)

        if len(affected_units) == 1:
            RN_UI.print_target(battle.active, affected_units[0], battle.selected_skill)
        elif len(affected_units) > 1:
            RN_UI.print_multi_target(battle.active, affected_units, battle.selected_skill)
        else:
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)

    def targetstate(self, command, battle, RN_UI):
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
            RN_UI.clear_highlight_area(battle.bmap)
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            RN_UI.print_prompt("arrows = move. a = attack. s = use skills. space = end turn. h = help")
            return False, "move"

        if battle.check_bounds((x, y)) \
                or (x, y) not in battle.targetable_tiles \
                or battle.bmap[x][y].terrain.targetable == 0:
            x = prev_cursor[0]
            y = prev_cursor[1]
            self.RN_sound.play_sound("error")

        RN_UI.clear_highlight_area(battle.bmap)
        RN_UI.cursor.move_cursor(x, y, battle.bmap[x][y])

        affected_tiles = RN2_battle_logic.calculate_affected_area((x, y), battle.active.coords, skill, battle.bmap)

        self.highlight_targetable_area(battle, affected_tiles, (x, y), RN_UI)
        self.print_target_display(affected_tiles, RN_UI)

        return False, False

    def confirmstate(self, command, battle, RN_UI):
        RN_UI.highlight_area(False, battle.affected_tiles, battle.bmap)
        if command == "activate":
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            return True, "confirmed"
        else:
            RN_UI.print_legend(battle.bmap.legend_list, battle.unit_list)
            if battle.target_tile == battle.hero.coords:
                return False, "move"
            else:
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
            if battle.active.mp < battle.get_adjusted_mp(self.skills[selectable_skills[battle.skill_index]], battle.active):
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
        if path:
            prev_coords = e.coords
            for tile in path:
                RN_UI.update_map(prev_coords, tile, e, battle.bmap)
                prev_coords = tile
                #time.sleep(0.02)
            return
