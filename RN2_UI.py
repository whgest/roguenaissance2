# -*- coding: utf-8 -*-

import pygame
import pygcurse
import time
import string
import os
from time import sleep
import random
import math
from threading import Timer, Thread, Event, Lock
import logging
import RN2_animations
from RN2_initialize import ACTIVATE, CANCEL, PASS_TURN, HELP_MENU, STATUS_DISPLAY, SKILLS_MENU, LEGEND, BATTLE_OVERVIEW, MUTE_SOUND, EXIT, DOWN, LEFT, RIGHT, UP


class RN_Cursor():
    def __init__(self, UI):
        self.bgcolor = "yellow"
        self.fgcolor = "black"
        self.UI = UI
        self.x = 0
        self.y = 0
        self.tile = None #tile under cursor's position
        self.visible = 0

    @property
    def coords(self):
        return (self.x, self.y)

    def cleanup(self):
        if self.tile:
            self.UI.text(self.x, self.y,self.display_tile(self.tile)[0], fgcolor=self.display_tile(self.tile)[1], bgcolor=self.display_tile(self.tile)[2])
        return

    def move_cursor(self, x, y, tile):
        self.cleanup()
        self.x = x
        self.y = y
        self.tile = tile
        self.UI.text(x, y, self.display_tile(tile)[0], fgcolor=self.fgcolor, bgcolor=self.bgcolor)

        self.UI.screen.update()

    def display_tile(self, tile):
        to_display = {}
        for attr in ('character', 'fgcolor', 'color', 'bgcolor'):
            if getattr(tile.actor, attr, None):
                if attr == 'color':
                    to_display['fgcolor'] = "black"
                else:
                    to_display[attr] = getattr(tile.actor, attr)
            elif getattr(tile.terrainmod, attr, None):
                to_display[attr] = getattr(tile.terrainmod, attr)
            elif getattr(tile.terrain, attr, None):
                to_display[attr] = getattr(tile.terrain, attr)

        return (to_display['character'], to_display['fgcolor'], to_display['bgcolor'])

class IntervalTimer(Thread):
    def __init__(self, stopEvent, interval, func):
        Thread.__init__(self)
        self.stopped = stopEvent
        self.interval = interval
        self.func = func

    def run(self):
        while not self.stopped.wait(self.interval):
            self.func()


class RNScrollablePrompt:
    def __init__(self, UI):
        self.UI = UI
        self.coords = (1, 28, 73, 1)
        self.length = 72
        self.current_index = 0
        self.initial_delay = 1.0
        self.tick_delay = 0.2
        self.prompt_text = ''
        self.stop_timer = Event()
        self.loop_spacer = 5
        self.init = None
        self.prompt_length = 0

    def reset(self):
        self.current_index = 0
        try:
            self.init.cancel()
        except:
            pass
        self.UI.blank(self.coords)
        self.stop_timer.set()

    def slice_prompt(self):
        prompt = self.prompt_text + (self.loop_spacer * " ")
        prompt_slice = prompt[self.current_index:self.current_index + self.length]

        if len(prompt_slice) < self.length:
            #loop text
            prompt_slice2_size = (self.length - len(prompt_slice))

            prompt_slice +=prompt[0:prompt_slice2_size]

        return prompt_slice

    def start_tick(self):
        tick = IntervalTimer(self.stop_timer, self.tick_delay, self.display_tick)
        #un-stop timer
        self.stop_timer.clear()
        tick.start()

    def display_tick(self):
        self.UI.menutext(self.coords[0], self.coords[1], self.slice_prompt())

        #try pygame events/time instead i guess
        #self.UI.screen.update()
        self.current_index += 1

        if self.current_index >= self.prompt_length + self.loop_spacer:
            self.current_index = 0

    def print_skill_description(self, prompt, adjusted_mp):
        self.prompt_text = "(MP: " + str(adjusted_mp) + ") " + prompt
        self.draw_prompt()

    def print_prompt(self, text):
        if self.prompt_text != text:
            self.prompt_text = text
        self.draw_prompt()

    def draw_prompt(self):
        self.reset()

        self.prompt_length = len(self.prompt_text)
        if self.prompt_length > self.length:
            self.display_tick()
            self.init = Timer(self.initial_delay, self.start_tick)
            self.init.start()
        else:
            self.UI.menutext(self.coords[0], self.coords[1], self.prompt_text)


class RN_UI_Class():
    def __init__(self, sound):
        self.grid_size = (75, 45)
        self.screen = pygcurse.PygcurseWindow(self.grid_size[0], self.grid_size[1])
        self.cursor = RN_Cursor(self)
        self.scrolling_prompt = RNScrollablePrompt(self)
        self.screen._autoupdate = False
        self.screen.update()
        self.sound_handler = sound
        pygame.display.set_caption("ASCIIMANCER")

        print pygame.display.get_driver()

        self.cell_size = (self.screen.cellheight, self.screen.cellwidth)
        self.right_menu_coords = (51,1,23,22)
        self.narration_coords = ((1,30,73,13))
        self.battle_grid_coords = (0, 0, 50, 25)
        self.menu_base_color = (40,95,173)
        self.menu_gradient = (2,3,4)

        self.highlight_tint = (125,-120,47)
        self.highlighted_tiles = []
        self.textcolors = {
            "damage": "red2",
            "heal":  "green2",
            "skill": "magenta1",
            "death": "darkred",
            "bad_status": "yellow3",
            "good_status": "turquoise",
            "text": "snow2",
            "hit_chance": "olivedrab1",
            "mp": "dodgerblue"
        }
        self.ui_colors = {
            "move_range": 'turquoise4',
            "select_color": 'magenta',
            "target_range": "darkred",
            "aoe_range": 'yellow2',
            "overlap_range": 'darkorange2',
            "confirm_range": "green2",
            "cursor": 'white'
        }
        self.team_colors = {
            1: "green2",
            2: "red2",
            3: "yellow2"
        }

        self.select_color = self.ui_colors['select_color']
        self.screen.font = pygame.font.Font('assets/lucon.ttf', 20)


    @staticmethod
    def wait_for_keypress():
        pygcurse.waitforkeypress()
        return

    def init_animation_class(self, bmap):
        self.animations = RN2_animations.Animation(self.sound_handler, self, bmap)

    def animate(self, tiles, anim_id, active):
        self.animations.animate(tiles, anim_id, active)

    def text(self, x, y, s, fgcolor="white", bgcolor="black"):
        self.screen.write(s, x=x, y=y, fgcolor=fgcolor, bgcolor=bgcolor)
        return

    def set_map(self, bmap):
        self.bmap = bmap

    def gradient(self, y, base_color, gradient):
        r = base_color[0]
        g = base_color[1]
        b = base_color[2]
        rstep = gradient[0]
        gstep = gradient[1]
        bstep = gradient[2]
        color = [r, g, b]
        color[0] = r-(rstep*y)
        color[1] = g-(gstep*y)
        color[2] = b-(bstep*y)
        for i in range(3):
            if color[i] < 0:
                color[i] = 0
            elif color[i] > 255:
                color[i] = 255
        return pygame.Color(*color)

    def menutext(self, x, y, s, fgcolor="white", bgcolor=None):
        if bgcolor is None:
            bgcolor = self.gradient(y, self.menu_base_color, self.menu_gradient)
        length_check = x + len(s)
        if length_check > 74:
            s = s[:(length_check-74)*-1]
        self.screen.write(s, x=x, y=y, fgcolor=fgcolor, bgcolor=bgcolor)
        return

    def right_menu_text(self, x, y, s, fgcolor="white", bgcolor=None):
        if y > 22:
            return
        if bgcolor:
            self.menutext(x, y, s, fgcolor=fgcolor, bgcolor=bgcolor)
        else:
            self.menutext(x, y, s, fgcolor=fgcolor)

    def right_menu_header(self, s):
        if len(s) > 23:
            return
        spacing = int((23 - len(s))/2)
        self.menutext(51, 0, spacing * u"═" + s + spacing * u"═")

    def blank(self, area):
        for y in range (area[3]):
            self.text(area[0], y+area[1], " "*area[2], bgcolor=self.gradient(y+area[1], self.menu_base_color, self.menu_gradient))
        return

    def tint(self, r, g, b, region):
        self.screen.settint(r, g, b, region)
        return

    def clear_screen_tint(self):
        self.tint(0, 0, 0, (0, 0, self.grid_size[0], self.grid_size[1]))
        self.screen.update()

    def fade_to_black(self, speed=.05, increment=10):
        num_increments = int(math.ceil(127.5/increment))
        for i in range(num_increments):
            tint_value = -1 * int(math.floor(127.5 + (i * increment)))
            self.tint(tint_value, tint_value, tint_value, (0, 0, self.grid_size[0], self.grid_size[1]))
            self.screen.update()
            sleep(speed)

    def draw_UI(self):
        self.blank((0, 0, 74, 45))
        for y in range(24):
            self.text(50, y+1, u"║" + " "*23 + u"║", fgcolor="white", bgcolor=self.gradient(y, self.menu_base_color, self.menu_gradient))
        for y in range(17):
            self.text(0, y+26, u"║" + " "*73 + u"║", bgcolor=self.gradient(y+26, self.menu_base_color, self.menu_gradient))
        self.text(50, 0, u'╔' + u"═"*23 + u'╗', fgcolor="white", bgcolor=self.menu_base_color)
        self.text(50, 23, u'╠' + u"═"*23 + u'╣', fgcolor="white", bgcolor=self.gradient(23, self.menu_base_color, self.menu_gradient))
        self.text(0, 25, u'╔' + u"═"*49 + u'╩' + u"═"*23 + u'╣', fgcolor="white",  bgcolor=self.gradient(25, self.menu_base_color, self.menu_gradient))
        self.text(0, 27, u'╠' + u"═"*73 + u'╣', fgcolor="white", bgcolor=self.gradient(27, self.menu_base_color, self.menu_gradient))
        self.text(0, 29, u'╠' + u"═"*73 + u'╣', fgcolor="white", bgcolor=self.gradient(29, self.menu_base_color, self.menu_gradient))
        self.text(0, 43, u'╚' + u"═"*73 + u'╝', fgcolor="white", bgcolor=self.gradient(43, self.menu_base_color, self.menu_gradient))
        self.screen.update()

    def print_legend(self, unit_list, legend_list):
        self.blank(self.right_menu_coords)
        self.right_menu_header("LEGEND")
        line_count = 1
        self.menutext(51, line_count, "UNITS:")
        line_count += 1
        for u in unit_list:
             self.menutext(52, line_count, u.name + ':', fgcolor=self.team_colors[u.team_id])
             self.menutext(72, line_count, u.character, fgcolor=self.team_colors[u.team_id])
             line_count += 1
        line_count += 1
        self.menutext(51, line_count, "TERRAIN:")
        line_count += 1
        for l in legend_list:
            self.text(52, (line_count), l[0], fgcolor=l[1], bgcolor=l[2])
            self.menutext(53, (line_count), ":  " + l[3])
            line_count += 1
        self.screen.update()

    def print_stats(self, unit):
        self.blank(self.right_menu_coords)
        self.right_menu_header("CHARACTER")
        stats_list = ["attack", "defense", "magic", "resistance", "agility", "move"]
        self.menutext(51, 1, unit.name + ":")
        self.menutext(51, 3, self.fix_spacing("HP:" + str(unit.hp) + "/" + str(unit.maxhp), 23, ":"))
        self.menutext(51, 4, self.fix_spacing("MP:" + str(unit.mp) + "/" + str(unit.maxmp), 23, ":"))
        line_count = 5
        for stat in stats_list:
            if getattr(unit, stat) > getattr(unit, "base_" + stat):
                arrow = u'▲'
                color = self.textcolors["good_status"]
            elif getattr(unit, stat) < getattr(unit, "base_" + stat):
                arrow = u'▼'
                color = self.textcolors["bad_status"]
            else:
                arrow = ""
                color = "white"
            stat_name = stat[0].capitalize() + stat[1:]
            self.menutext(51, line_count, self.fix_spacing(stat_name + ":" + arrow + str(getattr(unit, stat)), 23, ":"), fgcolor=color)
            line_count += 1

        if not unit.active_status_effects:
            self.menutext(51, line_count+1, "No active effects.")
        else:
            line_count += 1
            self.menutext(51, line_count, "Active Effects:")
            line_count += 1
            colors = {
                True: self.textcolors['good_status'],
                False: self.textcolors['bad_status']
            }

            for effect in unit.active_status_effects:
                for description in effect.display:
                    self.right_menu_text(51, line_count, effect.status_effect.type + ' ' + description['text'],
                                         fgcolor=colors[description['is_beneficial']])
                    line_count += 1
        self.screen.update()
    
    def show_help(self):
        self.blank(self.right_menu_coords)
        self.right_menu_header("HELP")
        self.menutext(51, 3, "arrow keys = move")
        self.menutext(51, 4, "a = basic attack")
        self.menutext(51, 5, "s = use magic/skills")
        self.menutext(51, 6, "t = show hero stats")
        self.menutext(51, 7, "b = battle overview")
        self.menutext(51, 8, "l = show map legend")
        self.menutext(51, 9, "SPACE BAR = End turn")
        self.menutext(51, 10, "ENTER = confirm action")
        self.menutext(51, 11, "ESCAPE = cancel action")
        self.menutext(51, 13, "m = toggle music")
        self.menutext(51, 14, "q = exit")
        self.screen.update()

    def print_active(self, unit):
        self.menutext(52, 24, " " * 32)
        self.menutext(52, 24, "ACT: " + unit.name[:18], fgcolor=self.team_colors[unit.team_id])
        self.screen.update()

    def fix_spacing(self, s, length, delimiter):
        num_spaces = length - len(s) -1
        line = s.split(delimiter)
        return line[0] + ":" + " "*num_spaces + line[1]

    def draw_skills_menu(self, skills, skill_index):
        self.blank(self.right_menu_coords)
        self.right_menu_header("SKILLS")

        for i, skill in enumerate(skills):
            self.menutext(51, (1+i), 'F' + str(i+1) + ': ')
            self.menutext(55, (1+i), skill)

        self.text(55, 1+skill_index, skills[skill_index], bgcolor=self.select_color)
        self.screen.update()

    def print_skill_description(self, prompt, adjusted_mp):
        prompt_text = "(MP: " + str(adjusted_mp) + ") " + prompt
        self.menutext(1, 28, prompt_text)

    def print_turn(self, a):
        self.blank((51, 24, 23, 1))
        self.menutext(51, 24, "ACT: " + a, fgcolor='white')
        return

    def print_prompt(self, s=""):
        if s:
            self.scrolling_prompt.print_prompt(s)
        else:
            self.scrolling_prompt.reset()

    def print_error_prompt(self, text):
        self.sound_handler.play_sound('error')
        self.print_prompt(s=text)
        self.screen.update()

    def print_map(self):
        battle_map = self.bmap
        for x in range(50):
            for y in range(25):
                if battle_map[x][y].actor != None:
                    self.text(x, y, battle_map[x][y].actor.character, fgcolor=self.team_colors[battle_map[x][y].actor.team_id], bgcolor=battle_map[x][y].terrain.bgcolor)
                elif battle_map[x][y].terrainmod != None:
                    self.text(x, y, battle_map[x][y].terrainmod.character, fgcolor=battle_map[x][y].terrainmod.fgcolor, bgcolor=battle_map[x][y].terrainmod.bgcolor)
                else:
                    self.text(x, y, battle_map[x][y].terrain.character, fgcolor=battle_map[x][y].terrain.fgcolor, bgcolor=battle_map[x][y].terrain.bgcolor)
        self.screen.update()

    def display_tile(self, tile):
        to_display = {}
        for attr in ('character', 'fgcolor', 'bgcolor'):
            if getattr(tile.terrainmod, attr, None):
                to_display[attr] = getattr(tile.terrainmod, attr)
            elif getattr(tile.terrain, attr, None):
                to_display[attr] = getattr(tile.terrain, attr)

        if tile.actor:
            to_display['character'] = getattr(tile.actor, 'character')
            to_display['fgcolor'] = self.team_colors[tile.actor.team_id]

        return to_display['character'], to_display['fgcolor'], to_display['bgcolor']

    def highlight_area(self, highlight, tiles, battle_map, color=None, is_target=False):
        if not color:
            color = self.ui_colors['move_range']
        else:
            color = self.ui_colors[color]

        for t in tiles:
            x = t[0]
            y = t[1]
            tile = battle_map[x][y]
            if (not tile.terrain.movable and not is_target) or (is_target and not tile.terrain.targetable):
                pass
            if highlight:
                fgcolor = self.display_tile(tile)[1] if self.display_tile(tile)[1] != color else 'black'
                self.text(x, y, self.display_tile(tile)[0], fgcolor=fgcolor, bgcolor=color)
                self.highlighted_tiles.append((x, y))
            else:
                #clear highlight
                self.text(x, y, self.display_tile(tile)[0], self.display_tile(tile)[1], self.display_tile(tile)[2])
                if (x, y) in self.highlighted_tiles:
                    self.highlighted_tiles.remove((x, y))
        self.screen.update()

    def clear_highlight_area(self, battle_map):
        for t in self.highlighted_tiles:
            x = t[0]
            y = t[1]
            tile = battle_map[x][y]
            #clear highlight
            self.text(x, y, self.display_tile(tile)[0], self.display_tile(tile)[1], self.display_tile(tile)[2])

        self.highlighted_tiles = []
        self.screen.update()

    def move_unit(self, prev_c, new_c, actor):
        bmap = self.bmap
        self.text(prev_c[0], prev_c[1], bmap[prev_c[0]][prev_c[1]].terrain.character, fgcolor = bmap[prev_c[0]][prev_c[1]].terrain.fgcolor, bgcolor = bmap[prev_c[0]][prev_c[1]].terrain.bgcolor)
        self.text(new_c[0], new_c[1], actor.character, fgcolor=self.team_colors[actor.team_id], bgcolor=bmap[new_c[0]][new_c[1]].terrain.bgcolor)
        self.screen.update()

    def remove_unit(self, actor):
        bmap = self.bmap
        prev_c = actor.coords
        self.text(prev_c[0], prev_c[1], bmap[prev_c[0]][prev_c[1]].terrain.character,
                  fgcolor=bmap[prev_c[0]][prev_c[1]].terrain.fgcolor,
                  bgcolor=bmap[prev_c[0]][prev_c[1]].terrain.bgcolor)
        self.screen.update()

    def add_unit(self, actor):
        bmap = self.bmap
        new_c = actor.coords
        self.text(new_c[0], new_c[1], actor.character, fgcolor=self.team_colors[actor.team_id],
                  bgcolor=bmap[new_c[0]][new_c[1]].terrain.bgcolor)
        self.screen.update()

    def print_status(self, active, tile, switch=True):
        def print_x(x_pos, s, fgcolor=self.textcolors['text']):
            self.menutext(x_pos, 26, s, fgcolor=fgcolor)
            x_pos += len(s) + 1
            return x_pos

        self.blank((1, 26, 73, 1))
        if not switch:
            return
        self.menutext(1, 26, active.name, self.textcolors['text'])
        x_pos = 1 + len(active.name) + 1
        if active.hp <= 0:
            active.hp = 0

        if (1.0*active.hp/active.maxhp) >= 0.7:
            color = self.textcolors['heal']
        elif 0.3 <= (1.0*active.hp/active.maxhp) < 0.7:
            color = self.textcolors['bad_status']
        else:
            color = self.textcolors['damage']

        x_pos = print_x(x_pos, "HP:")
        x_pos = print_x(x_pos, str(active.hp) + "/" + str(active.maxhp), fgcolor=color)
        x_pos = print_x(x_pos, "MP:")
        x_pos = print_x(x_pos, str(active.mp) + "/" + str(active.maxmp), fgcolor=self.textcolors['mp'])
        x_pos = print_x(x_pos, "E:")
        status = self.get_status(active, max_length=62-x_pos)
        print_x(x_pos, status)
        self.menutext(63, 26, "terrain: ")
        self.text(72, 26, tile.character, fgcolor=tile.fgcolor, bgcolor=tile.bgcolor)
        self.screen.update()
        return

    def get_status(self, active, max_length=24):
        res = ''
        statii = {}
        if not active.active_status_effects:
            return res
        else:
            for effect in active.active_status_effects:
                statii[effect.status_effect.type] = effect.status_effect.type
            statii = statii.values()

            for effect in statii:
                res += "{}, ".format(effect)
        res = res[:-2]
        if len(res) < max_length:
            return res
        else:
            res = ''
            statii = {}
            for effect in active.active_status_effects:
                statii[effect.status_effect.type] = effect.status_effect.type
            statii = statii.values()

            for status in statii:
                res += "{}/".format(status[:3])
            res = res[:-1]
            return res[:max_length]

    def print_narration(self, narration_q):
        if narration_q:
            self.blank(self.narration_coords)
            for row, line in enumerate(narration_q):
                col = self.narration_coords[0]
                for word in line:
                    #color hack: can be either a textcolor string or team id int
                    colors = dict(self.team_colors)
                    colors.update(self.textcolors)
                    self.menutext(col, 42-row, word.string, fgcolor=colors[word.color_binding])
                    col += len(word.string) + 1
            self.screen.update()
        return

    def print_battle_menu(self, battle_menu_list, turn_count, battle_index, v_top):
        def unit_line(unit):
            line_length = 24
            def_line = '{0}*{1}/{2}'.format(unit.name, str(unit.hp), str(unit.maxhp))
            num_spaces = line_length - len(def_line)
            return def_line.replace('*', ' ' * num_spaces)

        def stretch_line(line):
            line_length = 24
            num_spaces = line_length - len(line)
            line += (" " * num_spaces)
            return line

        self.blank(self.right_menu_coords)
        num_chars = 10
        self.right_menu_header("UNIT LIST")
        self.menutext(51, 1, "Turn " + str(turn_count) + "        " + str(len(battle_menu_list)) + " units")
        visible_index = battle_index - v_top
        if visible_index >= num_chars:
            if v_top + num_chars < len(battle_menu_list):
                v_top += 1
                visible_index = num_chars - 1
            else:
                v_top = 0
                visible_index = 0
        elif visible_index < 0:
            if battle_index == 0:
                v_top = 0
                visible_index = 0
            elif v_top > 0:
                v_top -= 1
                visible_index = 0
            else:
                v_top = len(battle_menu_list) - num_chars - 1
                visible_index = num_chars - 1

        visible_menu = battle_menu_list[v_top:v_top+num_chars]
        for i, actor in enumerate(visible_menu):
            fgcolor = self.team_colors[actor.team_id]
            bgcolor = None
            if i == visible_index:
                fgcolor = self.textcolors['text']
                bgcolor = self.ui_colors['select_color']
            self.right_menu_text(51, 3 + (i * 2), unit_line(actor), fgcolor=fgcolor, bgcolor=bgcolor)
            self.right_menu_text(51, 3 + (i * 2) + 1, stretch_line(self.get_status(actor)), fgcolor=self.textcolors['text'], bgcolor=bgcolor)
        try:
            self.highlight_active(battle_menu_list[battle_index], True)
        except IndexError:
            logging.error("BATTLE MENU GLITCH: " + repr(battle_menu_list))
            print "SEE LOGS FOR ERROR."
        return v_top

    def turn_indication(self, a):
        for i in range(2):
            self.highlight_active(a, True)
            time.sleep(0.1)
            self.highlight_active(a, False)
            time.sleep(0.1)

    def highlight_active(self, a, switch):
        if switch == True:
            self.tint(self.highlight_tint[0], self.highlight_tint[1], self.highlight_tint[2], (a.coords[0], a.coords[1], 1, 1))
        if switch == False:
            self.tint(0,0,0,(a.coords[0], a.coords[1], 1, 1))
        self.screen.update()

    def print_additional_effects(self, skill, starting_line=18):
        colors = {
            True: self.textcolors['good_status'],
            False: self.textcolors['bad_status']
        }

        for effect in skill.status_effects:
            for description in effect.modifier_descriptions:
                self.right_menu_text(51, starting_line, effect.type + ' ' + description['text'], fgcolor=colors[description['is_beneficial']])
                starting_line += 1

        for effect in skill.move_effects:
            self.right_menu_text(51, starting_line, effect.description, fgcolor=self.textcolors['bad_status'])
            starting_line += 1

        return starting_line

    def print_target(self, attacker, defenders, skill):
        if (skill.targets.special_friendly_effect and len([d for d in defenders if d.is_ally_of(attacker)]) and len([d for d in defenders if d.is_hostile_to(attacker)])) or \
           (skill.targets.special_self_effect and len([d for d in defenders if attacker == d]) and len(defenders) > 1):
            self.print_complex_target(attacker, defenders, skill)
        else:
            if attacker == defenders[0]:
                self.print_simple_target(attacker, defenders, skill, skill.targets.self)
            elif attacker.is_ally_of(defenders[0]):
                self.print_simple_target(attacker, defenders, skill, skill.targets.friendly)
            else:
                self.print_simple_target(attacker, defenders, skill, skill.targets.enemy)

    def print_simple_target(self, attacker, defenders, skill, skill_effect_for_target):
        def unit_line(unit):
            line_length = 24
            def_line = '{0}*{1}/{2}'.format(unit.name, str(unit.hp), str(unit.maxhp))
            num_spaces = line_length - len(def_line)
            return def_line.replace('*', ' ' * num_spaces)

        self.blank((self.right_menu_coords))

        center_space = (20 - len(skill.name)) / 2
        self.right_menu_header("TARGET")
        self.right_menu_text(51, 2, (" "*center_space) + '--{0}--'.format(skill.name), fgcolor=self.textcolors['skill'])

        line_to_print = 4

        target_spacing = 0 if len(defenders) > 4 else 1

        if (len(defenders) > 6 and skill_effect_for_target.is_resistable) or (len(defenders) > 12 and not skill_effect_for_target.is_resistable):
            overflow_str = "+ %s more targets" % str(len(defenders) - 6)
            defenders = defenders[:6]
            self.right_menu_text(51, 16, overflow_str)

        for defender in defenders:
            self.right_menu_text(51, line_to_print, unit_line(defender), fgcolor=self.team_colors[defender.team_id])
            line_to_print += 1

            if skill_effect_for_target.is_resistable:
                hit_chance = skill_effect_for_target.get_hit_chance(attacker, defender)
                self.right_menu_text(64, line_to_print, "Hit: " + str(hit_chance) + "%", fgcolor=self.textcolors["hit_chance"])
                self.right_menu_text(51, line_to_print, self.get_status(defender, max_length=13))
                line_to_print += 1

            line_to_print += (target_spacing)

        line_to_print += 2
        if skill_effect_for_target.damage.get_average_damage(attacker):
            is_heal = (skill_effect_for_target.damage.get_average_damage(attacker) < 0)
            color = self.textcolors['heal'] if is_heal else self.textcolors['damage']
            noun = 'Healing: ' if is_heal else 'Damage: '
            dmg_range = skill_effect_for_target.damage.get_damage_range(attacker)

            if dmg_range[0] != dmg_range[1]:
                self.right_menu_text(51, line_to_print, noun + str(abs(dmg_range[0])) + " - " + str(abs(dmg_range[1])), fgcolor=color)
            else:
                self.right_menu_text(51, line_to_print, noun + str(abs(dmg_range[0])), fgcolor=color)

        line_to_print += 1
        if len(skill_effect_for_target.status_effects) or len(skill_effect_for_target.move_effects):
            self.print_additional_effects(skill_effect_for_target, starting_line=line_to_print)

        self.screen.update()

    def print_complex_target(self, attacker, defenders, skill):
        def unit_line(unit):
            line_length = 24
            def_line = '{0}*{1}/{2}'.format(unit.name, str(unit.hp), str(unit.maxhp))
            num_spaces = line_length - len(def_line)
            return def_line.replace('*', ' ' * num_spaces)

        def print_skill_effect_for_target(skill_effect_for_target, targeted_defenders, line_to_print):
            for defender in targeted_defenders:
                self.right_menu_text(51, line_to_print, unit_line(defender), fgcolor=self.team_colors[defender.team_id])
                line_to_print += 1

            if skill_effect_for_target.damage.get_average_damage(attacker):
                is_heal = (skill_effect_for_target.damage.get_average_damage(attacker) < 0)
                color = self.textcolors['heal'] if is_heal else self.textcolors['damage']
                noun = 'Healing: ' if is_heal else 'Damage: '
                dmg_range = skill_effect_for_target.damage.get_damage_range(attacker)

                if dmg_range[0] != dmg_range[1]:
                    self.right_menu_text(51, line_to_print, noun + str(abs(dmg_range[0])) + " - " + str(abs(dmg_range[1])), fgcolor=color)
                else:
                    self.right_menu_text(51, line_to_print, noun + str(abs(dmg_range[0])), fgcolor=color)

                line_to_print += 1

            if len(skill_effect_for_target.status_effects) or len(skill_effect_for_target.move_effects):
                line_to_print = self.print_additional_effects(skill_effect_for_target, starting_line=line_to_print)

            return line_to_print + 1

        self.blank(self.right_menu_coords)
        center_space = (20 - len(skill.name)) / 2
        self.right_menu_header("TARGET")
        self.menutext(51, 2, (" "*center_space) + '--{0}--'.format(skill.name), fgcolor=self.textcolors['skill'])

        line_to_print = 4

        if len([d for d in defenders if d.is_hostile_to(attacker)]):
            line_to_print = print_skill_effect_for_target(skill.targets.enemy,
                                                          [d for d in defenders if d.is_hostile_to(attacker)],
                                                          line_to_print)

        if len([d for d in defenders if d.is_ally_of(attacker) and d != attacker]):
            line_to_print = print_skill_effect_for_target(skill.targets.friendly,
                                                          [d for d in defenders if
                                                           d.is_ally_of(attacker) and d != attacker],
                                                          line_to_print)

        if len([d for d in defenders if d == attacker]):
            line_to_print = print_skill_effect_for_target(skill.targets.self,
                                                          [d for d in defenders if d == attacker],
                                                          line_to_print)

        self.screen.update()

    def draw_border(self):
        self.blank((0, 0, 74, 44))
        for y in range(44):
            self.title_text(0, y, " "*74)
            self.title_text(0, y, u"▒")
            self.title_text(74, y, u"▒")

        self.title_text(1, 0, u"▒"*73)
        self.title_text(1, 43, u"▒"*73)

    def title_screen(self, title, input, sound):
        UI = self
        self.draw_border()
        UI.title_text(14, 28, "On the \"Roguenaissance 3.0\" RPG Battle Engine")
        UI.title_text(20, 30, "by William Hardy Gest, 2013-2017")
        title_list = [("New Game", 10), ("Continue", 25), ("High Scores", 42), ("Quit", 60)]
        self.display_title(title)

        if not self.get_saved_games():
            self.title_text(25, 37, "Continue", fgcolor="gray")
            del title_list[1]

        for option in title_list:
            UI.title_text(option[1], 37, option[0])

        title_index = 0
        UI.text(title_list[title_index][1], 37, title_list[title_index][0], bgcolor=self.select_color)

        UI.screen.update()
        while 1:
                command = input()
                if command == RIGHT:
                    sound.play_sound('beep')
                    UI.title_text(title_list[title_index][1], 37, title_list[title_index][0])
                    title_index += 1
                elif command == LEFT:
                    sound.play_sound('beep')
                    UI.title_text(title_list[title_index][1], 37, title_list[title_index][0])
                    title_index -= 1
                elif command == ACTIVATE:
                    sound.play_sound('beep2')
                    selection = title_list[title_index][0]
                    break
                title_index %= len(title_list)
                UI.text(title_list[title_index][1], 37, title_list[title_index][0], bgcolor=self.select_color)
                UI.screen.update()

        if selection == "New Game":
            return True, False, False
        elif selection == "Continue":
            success, load = self.load_game(input, sound)
            if success:
                return True, True, load
            else:
                return False, False, False
        elif selection == "High Scores":
            self.high_scores(input)
            return False, False, False
        elif selection == "Quit":
            exit()
        else:
            exit()

    def title_text(self, x, y, text, fgcolor="white", bgcolor=None):
        if not bgcolor:
            bgcolor = self.gradient(y, (0,0,0), (-2, -2, -2))
        self.text(x, y, text, fgcolor=fgcolor, bgcolor=bgcolor)

    def wipe_screen(self, from_direction='left', speed=.01):
        pass

    def display_title(self, title):
        map_lines = title['layout']
        map_lines = map_lines.splitlines()
        for m in map_lines:
            list(m)
        rmap = []

        x_size = len(map_lines[0])
        y_size = len(map_lines)

        x_offset = 5
        y_offset = 8

        for x in range(x_size):
            rmap.append([])
            for y in range(y_size):
                try:
                    rmap[x].append(map_lines[y][x])
                except IndexError:
                    rmap[x].append(' ')

        for x in range(x_size):
            for y in range(y_size):
                text_color = pygame.Color(100+y*10, 0+y*7, 0+y*7)
                line_color = pygame.Color(70-x, 170-x*2, 250-x*2)
                if rmap[x][y][0] not in [" ", ".", "7", "6", "9", "8"]:
                    self.title_text(x+x_offset, y+y_offset, " ")
                elif rmap[x][y][0] in ["7"]:
                    self.title_text(x+x_offset, y+y_offset, u'∑', fgcolor=line_color)
                elif rmap[x][y][0] in ["6"]:
                    self.title_text(x+x_offset, y+y_offset, u'☼', fgcolor="yellow")
                elif rmap[x][y][0] in ["9", "8"]:
                    self.title_text(x+x_offset, y+y_offset, " ", bgcolor=text_color)
                else:
                    self.title_text(x+x_offset, y+y_offset, " ")

    def display_game_over(self, title, tips, input, sound):
        self.clear_screen_tint()
        self.draw_border()
        map_lines = title['layout']
        map_lines = map_lines.splitlines()
        for m in map_lines:
            list(m)
        rmap = []

        x_size = len(map_lines[0])
        y_size = len(map_lines)

        x_offset = 10
        y_offset = 8

        for x in range(x_size):
            rmap.append([])
            for y in range(y_size):
                rmap[x].append(map_lines[y][x])
        for x in range(x_size):
            for y in range(y_size):
                text_color = pygame.Color(85+y*12, 85+y*12, 85+y*12)

                if rmap[x][y][0] not in [" ", ".", "7", "6", "9", "8"]:
                    self.title_text(x+x_offset, y+y_offset, " ")

                elif rmap[x][y][0] in ["9", "8"]:
                    self.title_text(x+x_offset, y+y_offset, " ", bgcolor=text_color)
                else:
                    self.title_text(x+x_offset, y+y_offset, " ")
        tip_to_display = tips[random.randint(0, len(tips)-1)]
        self.text_wrapper("Tip: " + tip_to_display, 3, 24, fgcolor="yellow")

        title_list = [("Retry Battle", 17), ("Quit to Menu", 40)]
        self.title_text(title_list[0][1], 35, title_list[0][0], bgcolor=self.select_color)
        self.title_text(title_list[1][1], 35, title_list[1][0])

        title_index = 0
        self.screen.update()
        while 1:
            command = input()
            if command == RIGHT:
                sound.play_sound('beep')
                self.title_text(title_list[title_index][1], 35, title_list[title_index][0])
                title_index += 1
            elif command == LEFT:
                sound.play_sound('beep')
                self.title_text(title_list[title_index][1], 35, title_list[title_index][0])
                title_index -= 1
            elif command == ACTIVATE:
                sound.play_sound('beep2')
                selection = title_list[title_index][0]
                break

            title_index %= len(title_list)
            self.text(title_list[title_index][1], 35, title_list[title_index][0], bgcolor=self.select_color)
            self.screen.update()

        return selection == "Retry Battle"

    def display_intro(self, text):
        self.clear_screen_tint()
        self.draw_border()
        lines = 3
        for t in text.splitlines():
            if "$s" in t:
                #self.play_sound(p.split()[1])
                pass
            elif t == "$p":
                pygcurse.waitforkeypress()
            else:
                lines = self.text_wrapper(t, 2, lines)
            self.screen.update()
        return

    def text_wrapper(self, s, x, y, fgcolor="white"):  #custom text wrapper function for Console
        s = s.strip()
        s = s.split(" ")
        line = ""
        line_count = 0
        for i in range(len(s)):
            if len(line + s[i]) < 68:
                line = line + s[i] + " "
            else:
                self.title_text(x, y+line_count, line, fgcolor=fgcolor)
                line_count += 1
                line = s[i] + " "
        self.title_text(x, y+line_count, line, fgcolor=fgcolor)
        return line_count + y + 2

    def create_character(self, name_text, class_text, class_descr, input, sound):
        self.draw_border()
        self.text_wrapper(name_text, 3, 2)
        hero_name = self.get_hero_name(10)
        self.screen.update()
        self.text_wrapper(class_text, 2, 15)
        self.title_text(27, 30, "Please select a class:")
        title_list = [("Astromancer", 10), ("Pyromancer", 33), ("Terramancer", 54)]
        self.title_text(title_list[0][1], 35, title_list[0][0], bgcolor=self.select_color)
        self.title_text(title_list[1][1], 35, title_list[1][0])
        self.title_text(title_list[2][1], 35, title_list[2][0])
        title_index = 0
        self.screen.update()
        while 1:
                for y in range(5):
                    self.title_text(2, y+24, " "*72)
                self.text_wrapper(class_descr[title_list[title_index][0]], 2, 24, fgcolor="yellow")
                self.screen.update()
                command = input()
                if command == RIGHT:
                    sound.play_sound('beep')
                    self.title_text(title_list[title_index][1], 35, title_list[title_index][0])
                    title_index += 1
                elif command == LEFT:
                    sound.play_sound('beep')
                    self.title_text(title_list[title_index][1], 35, title_list[title_index][0])
                    title_index -= 1
                elif command == ACTIVATE:
                    sound.play_sound('beep2')
                    selection = title_list[title_index][0]
                    break
                title_index %= len(title_list)
                self.text(title_list[title_index][1], 35, title_list[title_index][0], bgcolor=self.select_color)
        hero_class = selection
        return hero_name, hero_class

    def get_hero_name(self, y):
        self.text(2, y, " "*19, bgcolor="white")
        self.screen.cursor = (2, y)
        done = False
        while not done:
            self.screen.cursor = (2, y)
            hero_name = self.screen.input(maxlength=17,
                                          fgcolor="black", bgcolor="white", whitelistchars=string.ascii_letters)
            if len(hero_name) > 2:
                break

        return hero_name.title()

    def get_saved_games(self):
        save_game_list = []
        t = os.listdir(os.getcwd())
        for tfile in t:
            if tfile[-4::] == ".sav" and tfile[0] != "_":
                save_game_list.append(tfile[:-4])

        return save_game_list


    def load_game(self, input, sound):
        save_game_list = self.get_saved_games()
        self.draw_border()

        if not save_game_list:
            sound.play_sound('error')
            return False, []

        title_list = save_game_list
        self.title_text(10, 4, "Saved Heroes:")
        self.title_text(10, 6, title_list[0], bgcolor=self.select_color)
        for i in range(len(save_game_list)-1):
            self.title_text(10, 7+i, title_list[i+1])
        title_index = 0
        self.screen.update()
        while 1:
            self.screen.update()
            command = input()
            if command == UP and len(save_game_list) > 1:
                sound.play_sound('beep')
                self.title_text(10, 6+title_index, title_list[title_index])
                title_index -= 1
            elif command == DOWN and len(save_game_list) > 1:
                sound.play_sound('beep')
                self.title_text(10, 6+title_index, title_list[title_index])
                title_index += 1
            elif command == ACTIVATE:
                sound.play_sound('beep2')
                selection = title_list[title_index]
                break
            elif command == CANCEL:
                sound.play_sound('error')
                return False, []
            title_index %= len(title_list)
            self.text(10, 6+title_index, title_list[title_index], bgcolor=self.select_color)
        return True, selection + ".sav"


    def display_ending(self, input, saved_data, ending_text):
        self.draw_border()
        self.clear_screen_tint()
        self.screen._autoupdate = True

        self.title_text(10, 4, "ALDEBARAN ACADEMY FINAL EXAM SCORE:")
        sleep(1)
        self.title_text(10, 8, "TURNS TAKEN:                         " + str(saved_data.score.turns_taken), fgcolor=self.textcolors['bad_status'])
        sleep(1)
        self.title_text(10, 9, "PERSONAL DAMAGE RECIEVED:            " + str(saved_data.score.damage_taken), fgcolor=self.textcolors['bad_status'])
        sleep(1)
        self.title_text(10, 10, "ENEMIES SLAIN:                       " + str(saved_data.score.enemies_killed), fgcolor=self.textcolors['good_status'])
        sleep(2)
        score = 500 - (saved_data.score.turns_taken * 3.5) - (saved_data.score.damage_taken * 1.5) + (saved_data.score.enemies_killed * 10)
        self.title_text(10, 18, "FINAL SCORE:                         " + str(score))
        sleep(2)
        grade = "F"
        if score < 200:
            grade = "D"
        if score > 200:
            grade = "C"
        if score > 300:
            grade = "B"
        if score > 400:
            grade = "A"
        if score > 450:
            grade = "S"
        self.title_text(10, 20, "GRADE:                                 " + grade, fgcolor=self.textcolors['heal'])
        try:
            fin = open("highscores.dat", "a")
        except IOError:
            fin = open("highscores.dat", "w+")

        fin.write(saved_data.saved_character.name + "|" + saved_data.saved_character.class_name + "|" + str(int(score)) + "\n")
        fin.close()

        sleep(1)
        self.text_wrapper(ending_text, 3, 30, fgcolor=self.textcolors['bad_status'])

        while 1:
            self.screen.update()
            command = input()
            if command:
                self.screen._autoupdate = False
                break

        return

    def high_scores(self, input):

        fin = open("highscores.dat", 'r+')
        highscores = fin.read()
        fin.close()

        self.draw_border()
        self.title_text(10, 4, "High Scores:")

        if not highscores:
            self.title_text(10, 8, "No high scores yet.", fgcolor=self.textcolors['bad_status'])
        else:
            highscores = highscores.splitlines()
            line_count = 0
            score_list = []
            for h in highscores:
                try:
                    score_list.append((int(h.split("|")[2]), h.split("|")[1], h.split("|")[0]))
                except:
                    continue
            score_list.sort(reverse=True)
            for s in score_list:
                self.text(10, 7+line_count, s[2] + " (" + s[1] + ")")
                self.text(60, 7+line_count, str(s[0]))
                line_count += 1
                if line_count > 40:
                    break
            self.screen.update()

        while 1:
            command = input()
            if command:
                break

        return
