"""

Project Roguenaissance 2.0
Battle System Controller
by William Hardy Gest

October 2013

"""
import logging
import time
import string as string_module
import RN2_battle_logic
from RN2_initialize import ACTIVATE, CANCEL, PASS_TURN, HELP_MENU, STATUS_MENU, SKILLS_MENU, LEGEND, BATTLE_OVERVIEW, MUTE_SOUND, EXIT, DOWN, LEFT, RIGHT, UP

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



MOVE_CHARACTER = 1
TARGET_SKILL = 2
CONFIRM_SKILL = 3
IN_SKILLS_MENU = 4
IN_BATTLE_OVERVIEW = 5
END_TURN = 6

DIR_LEFT = [-1, 0]
DIR_RIGHT = [1, 0]
DIR_UP = [0, -1]
DIR_DOWN = [0, 1]


class PlayerTurnState(object):
    def __init__(self, ui, unit, bmap, player_selections):
        self.ui = ui
        self.unit = unit
        self.bmap = bmap
        self.player_selections = player_selections
        self.selected_skill = None
        self.targetable_tiles = []
        self.function_bindings = {
            ACTIVATE: self.activate,
            CANCEL: self.cancel,
            PASS_TURN: self.pass_turn,
            HELP_MENU: self.help_menu,
            SKILLS_MENU: self.skills_menu,
            BATTLE_OVERVIEW: self.battle_overview,
            #LEGEND: self.legend,
            DOWN: self.down,
            LEFT: self.left,
            RIGHT: self.right,
            UP: self.up
        }

    def input_error(self, text):
        self.ui.print_error_prompt(text)

    def process_input(self, command):
        return self.function_bindings[command]()

    def activate_state(self):
        pass

    def deactivate_state(self):
        pass

    def activate(self):
        raise NotImplementedError

    def cancel(self):
        raise NotImplementedError

    def pass_turn(self):
        return END_TURN

    def help_menu(self):
        self.ui.show_help()

    def skills_menu(self):
        return IN_SKILLS_MENU

    def battle_overview(self):
        return IN_BATTLE_OVERVIEW

    def left(self):
        pass

    def right(self):
        pass

    def up(self):
        pass

    def down(self):
        pass


class MoveCharacter(PlayerTurnState):
    def __init__(self, ui, unit, bmap, player_selections):
        PlayerTurnState.__init__(self, ui, unit, bmap, player_selections)
        self.destination = []
        self.initial_position = self.unit.coords

        self.move_range = RN2_battle_logic.calculate_move_range(self.unit, self.bmap)

    def move_is_valid(self, destination):
        tile_is_movable = self.bmap.check_bounds(destination) and self.bmap.get_tile_at(destination).is_movable()
        in_range = destination in self.move_range

        return tile_is_movable and in_range

    def activate_state(self):
        self.player_selections.target_tile = self.unit.coords

    def deactivate_state(self):
        self.ui.highlight_area(False, self.move_range, self.bmap, "teal")

    def draw_state_ui(self):
        self.ui.print_legend()
        self.ui.print_prompt("arrows = move. a = attack. s = use skills. space = end turn. h = help")
        self.ui.highlight_area(True, self.move_range, self.bmap, "teal")

    def activate(self):
        if not self.unit.skillset:
            self.input_error("No usable skills.")
        else:
            self.ui.highlight_area(False, self.move_range, self.bmap)
            self.player_selections.selected_skill = self.unit.skillset[0]
            return TARGET_SKILL

    def cancel(self):
        self.ui.print_legend()

    def handle_movement(self, direction):
        destination = RN2_battle_logic.add_points(self.unit.coords, direction)
        if self.move_is_valid(destination):

            self.player_selections.destination = destination

            self.ui.move_unit(self.unit.coords, destination, self.unit)
            self.bmap.remove_unit(self.unit)
            self.unit.coords = destination
            self.bmap.place_unit(self.unit, destination)
        else:
            self.input_error("Cannot move there.")

    def left(self):
        self.handle_movement(DIR_LEFT)

    def right(self):
        self.handle_movement(DIR_RIGHT)

    def up(self):
        self.handle_movement(DIR_UP)

    def down(self):
        self.handle_movement(DIR_DOWN)


class InSkillsMenu(PlayerTurnState):
    def __init__(self, ui, unit, bmap, player_selections, skills):
        PlayerTurnState.__init__(self, ui, unit, bmap, player_selections)
        self.skills = skills
        self.skill_menu_index = 0

    def draw_state_ui(self):
        self.skill_menu_index %= len(self.unit.skillset[1:])
        skill_to_display = self.skills[self.unit.skillset[1:][self.skill_menu_index]]
        prompt = skill_to_display.skill_prompt
        self.ui.draw_skills_menu(self.unit.skillset[1:], self.skill_menu_index, prompt)

    def activate(self):
        skill_name = self.unit.skillset[1:][self.skill_menu_index]
        self.player_selections.chosen_skill = self.skills[skill_name]
        return TARGET_SKILL

    def cancel(self):
        return MOVE_CHARACTER

    def up(self):
        self.skill_menu_index -= 1

    def down(self):
        self.skill_menu_index += 1


class InBattleOverview(PlayerTurnState):
    def __init__(self, ui, unit, bmap, player_selections, battle):
        PlayerTurnState.__init__(self, ui, unit, bmap, player_selections)
        self.index = 0
        self.v_top = 0
        self.battle = battle
        self.list = battle.battle_menu_list
        print battle.battle_menu_list

    def draw_state_ui(self):
        self.index %= len(self.list)
        self.v_top = self.ui.print_battle_menu(self.list, self.battle.turn_tracker.turn_count, self.index, self.v_top)
        self.ui.highlight_active(self.list[self.index][2], False)

    def activate(self):
        return MOVE_CHARACTER

    def cancel(self):
        return MOVE_CHARACTER

    def up(self):
        self.index -= 1

    def down(self):
        self.index += 1


class TargetSkill(PlayerTurnState):
    def __init__(self, ui, unit, bmap, player_selections, all_units, battle):
        PlayerTurnState.__init__(self, ui, unit, bmap, player_selections)
        self.all_units = all_units
        self.battle = battle
        self.player_selections.target_tile = self.unit.coords

    def activate_state(self):
        self.ui.cursor.visible = True
        self.ui.cursor.move_cursor(self.player_selections.target_tile[0], self.player_selections.target_tile[1], self.bmap.get_tile_at(self.unit.coords))
        self.targetable_tiles = RN2_battle_logic.calculate_skill_range(self.unit, self.player_selections.chosen_skill, self.bmap)

    def deactivate_state(self):
        self.ui.clear_highlight_area(self.bmap)

    def target_is_valid(self, tile):
        tile_is_targetable = self.bmap.check_bounds(tile) and self.bmap.get_tile_at(tile).is_targetable()
        in_range = tile in self.targetable_tiles

        return tile_is_targetable and in_range

    def highlight_targetable_area(self, targeted_aoe, cursor_pos):
        def get_shared_tiles(in_range, targeted):
            overlap_tiles = set(range_tiles).intersection(set(targeted))
            range_only_tiles = set(in_range).difference(overlap_tiles)
            aoe_only_tiles = set(targeted_aoe).difference(overlap_tiles)
            return range_only_tiles, aoe_only_tiles, overlap_tiles

        range_tiles = self.targetable_tiles
        range_only, aoe_only, overlap = get_shared_tiles(range_tiles, targeted_aoe)

        self.ui.highlight_area(True, range_only, self.bmap, color='maroon')
        self.ui.highlight_area(True, aoe_only, self.bmap, color='yellow')
        self.ui.highlight_area(True, overlap, self.bmap, color='orange')
        self.ui.highlight_area(True, [cursor_pos], self.bmap, color='white')

    def print_target_display(self, targeted_aoe):
        #todo: this and the UI functions have to be completely refactored for the new skill target type system
        enemy_units_affected, friendly_units_affected, self_unit_affected = self.battle.get_targets_for_area(self.unit, targeted_aoe)
        affected_units = []
        affected_units.extend(enemy_units_affected)
        affected_units.extend(friendly_units_affected)
        affected_units.extend(self_unit_affected)

        if len(affected_units) == 1:
            self.ui.print_target(self.unit, affected_units[0], self.player_selections.chosen_skill)
        elif len(affected_units) > 1:
            self.ui.print_multi_target(self.unit, affected_units, self.player_selections.chosen_skill)
        else:
            self.ui.print_legend()

    def draw_state_ui(self):
        #self.ui.print_legend()
        self.ui.print_prompt(self.player_selections.chosen_skill.name + " --- " + "Select target area.")
        targeted_aoe = RN2_battle_logic.calculate_affected_area(self.ui.cursor.coords, self.unit.coords, self.player_selections.chosen_skill, self.bmap)
        self.ui.clear_highlight_area(self.bmap)
        self.highlight_targetable_area(targeted_aoe, self.ui.cursor.coords)
        self.print_target_display(targeted_aoe)

    def activate(self):
        return CONFIRM_SKILL

    def cancel(self):
        return MOVE_CHARACTER

    def handle_movement(self, direction):
        target_tile = RN2_battle_logic.add_points(self.player_selections.target_tile, direction)
        if self.target_is_valid(target_tile):
            self.player_selections.target_tile = target_tile
            self.ui.cursor.move_cursor(target_tile[0], target_tile[1], self.bmap.get_tile_at(target_tile))
        else:
            self.input_error("Invalid target.")

    def left(self):
        self.handle_movement(DIR_LEFT)

    def right(self):
        self.handle_movement(DIR_RIGHT)

    def up(self):
        self.handle_movement(DIR_UP)

    def down(self):
        self.handle_movement(DIR_DOWN)


class ConfirmSkill(PlayerTurnState):
    def __init__(self, ui, unit, bmap, player_selections):
        PlayerTurnState.__init__(self, ui, unit, bmap, player_selections)

    def activate_state(self):
        self.affected_tiles = RN2_battle_logic.calculate_affected_area(self.player_selections.target_tile, self.unit.coords, self.player_selections.chosen_skill, self.bmap)

    def deactivate_state(self):
        self.ui.highlight_area(False, self.affected_tiles, self.bmap)

    def draw_state_ui(self):
        self.ui.highlight_area(True, self.affected_tiles, self.bmap, "lime")
        self.ui.print_prompt("ENTER to confirm attack, ESC to cancel.")

    def activate(self):
        return END_TURN

    def cancel(self):
        return TARGET_SKILL


class PlayerTurn(object):
    class PlayerSelections:
        def __init__(self, position):
            self.destination = position
            self.target_tile = None
            self.chosen_skill = None

    def __init__(self, ui, input, battle):
        self.unit = battle.active
        self.bmap = battle.bmap
        self.battle = battle
        self.ui = ui
        self.input = input
        self.current_state = MOVE_CHARACTER
        self.player_selections = self.PlayerSelections(self.unit.coords)
        self.states = {
            MOVE_CHARACTER: MoveCharacter(self.ui, self.unit, self.bmap, self.player_selections),
            TARGET_SKILL: TargetSkill(self.ui, self.unit, self.bmap, self.player_selections, self.battle.all_living_units, self.battle),
            IN_SKILLS_MENU: InSkillsMenu(self.ui, self.unit, self.bmap, self.player_selections, self.battle.skills),
            CONFIRM_SKILL: ConfirmSkill(self.ui, self.unit, self.bmap, self.player_selections),
            IN_BATTLE_OVERVIEW: InBattleOverview(self.ui, self.unit, self.bmap, self.player_selections, self.battle)
        }

    def get_action(self):
        self.states[self.current_state].activate_state()
        while self.current_state is not END_TURN:
            self.states[self.current_state].draw_state_ui()
            command = self.input()
            new_state = self.states[self.current_state].process_input(command)
            if new_state:
                self.states[self.current_state].deactivate_state()
                self.current_state = new_state
                try:
                    self.states[self.current_state].activate_state()
                except KeyError:
                    continue

        print self.player_selections.destination
        return self.player_selections.chosen_skill, self.player_selections.target_tile, self.player_selections.destination


class BattleController(object):
    def __init__(self, ui, sound_handler, input):
        self.report = BattleReport(ui)
        self.ui = ui
        self.input = input
        self.sound_handler = sound_handler
        self.mute_switch = False

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
        #self.ui.print_legend(self.battle.bmap.legend_list, self.battle.unit_list)
        #self.init_music()

    def update(self, state_changes):
        for change in state_changes:
            if change.report_entry():
                self.report.add_entry(change.report_entry())
            change.animate(self.ui)
            change.display(self.ui)

    def player_turn(self, battle):
        turn = PlayerTurn(self.ui, self.input, battle)
        return turn.get_action()




