# -*- coding: utf-8 -*-
"""

Project Roguenaissance 2.0 UI
by William Hardy Gest

October 2013

"""

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
from RN2_initialize import ACTIVATE, CANCEL, PASS_TURN, HELP_MENU, STATUS_MENU, SKILLS_MENU, LEGEND, BATTLE_OVERVIEW, MUTE_SOUND, EXIT, DOWN, LEFT, RIGHT, UP


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
        self.cell_size = (self.screen.cellheight, self.screen.cellwidth)
        self.right_menu_coords = (51,1,23,22)
        self.narration_coords = ((1,30,73,13))
        self.battle_grid_coords = (0, 0, 50, 25)
        self.menu_base_color = (40,95,173)
        self.menu_gradient = (2,3,4)
        self.select_color = "fuchsia"
        self.highlight_tint = (125,-120,47)
        self.highlighted_tiles = []
        self.textcolors = {
            "damage": "darkred",
            "heal":  "lime",
            "skill": "fuchsia",
            "death": "red",
            "bad_status": "yellow",
            "good_status": "aqua",
            "hero_name": "white",
            "ally_name": "green",
            "enemy_name": "red",
            "text": "silver"
        }
        self.team_colors = {
            1: "lime",
            2: "red",
            3: "yellow"
        }
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
            self.text(50, y+1, u"║" + " "*23 + u"║", fgcolor= "white", bgcolor = self.gradient(y, self.menu_base_color, self.menu_gradient))
        for y in range(17):
            self.text(0, y+26, u"║" + " "*73 + u"║", bgcolor= self.gradient(y+26, self.menu_base_color, self.menu_gradient))
        self.text(50, 0, u'╔' + u"═"*23 + u'╗', fgcolor= "white", bgcolor=self.menu_base_color)
        self.text(50, 23, u'╠' + u"═"*23 + u'╣', fgcolor= "white", bgcolor= self.gradient(23, self.menu_base_color, self.menu_gradient))
        self.text(0, 25, u'╔' + u"═"*49 + u'╩' + u"═"*23 + u'╣', fgcolor= "white",  bgcolor= self.gradient(25, self.menu_base_color, self.menu_gradient))
        self.text(0, 27, u'╠' + u"═"*73 + u'╣', fgcolor= "white",  bgcolor = self.gradient(27, self.menu_base_color, self.menu_gradient))
        self.text(0, 29, u'╠' + u"═"*73 + u'╣', fgcolor= "white",  bgcolor = self.gradient(29, self.menu_base_color, self.menu_gradient))
        self.text(0, 43, u'╚' + u"═"*73 + u'╝', fgcolor= "white",  bgcolor = self.gradient(43, self.menu_base_color, self.menu_gradient))
        self.screen.update()

    def print_legend(self):
        self.blank(self.right_menu_coords)
        self.menutext(51, 1, "     BATTLE LEGEND:")
        self.menutext(51, 3, " UNITS:")
        # line_count = 1
        # for u in unit_list:
        #      self.menutext(52, (4+line_count), u[0] + ": " + u[1], fgcolor=u[2])
        #      line_count += 1
        # line_count += 1
        # self.menutext(51, (4+line_count), " TERRAIN:")
        # line_count += 2
        # for l in legend_list:
        #     self.text(52, (4+line_count), l[0], fgcolor=l[1], bgcolor=l[2])
        #     self.menutext(53, (4+line_count), ":    " + l[3])
        #     line_count += 1
        self.screen.update()

    def print_stats(self, hero):
        self.blank(self.right_menu_coords)
        stats_list = ["attack", "defense", "magic", "resistance", "agility", "move"]
        self.menutext(51, 1, hero.name + ":", hero.color)
        self.menutext(51, 3, self.fix_spacing("HP:" + str(hero.hp) + "/" + str(hero.maxhp), 23, ":"))
        self.menutext(51, 4, self.fix_spacing("MP:" + str(hero.mp) + "/" + str(hero.maxmp), 23, ":"))
        line_count = 5
        for stat in stats_list:
            if getattr(hero, stat) > getattr(hero, "base_" + stat):
                color = "lime"
            elif getattr(hero, stat) < getattr(hero, "base_" + stat):
                color = "darkred"
            else:
                color = "white"
            stat_name = stat[0].capitalize() + stat[1:]
            self.menutext(51, line_count, self.fix_spacing(stat_name + ":" + str(getattr(hero, stat)), 23, ":"), fgcolor=color)
            line_count += 1
        line_count += 1
        if hasattr(hero, "weapon"):
            self.menutext(51, line_count, self.fix_spacing("Weapon:" + hero.weapon, 23, ":"))
            self.menutext(51, line_count+1, self.fix_spacing("Armor:" + hero.armor, 23, ":"))
        if hero.status == []:
            self.menutext(51, line_count+3, self.fix_spacing("Status:" + "Normal", 23, ":"))
        else:
            line_count2 = 0
            self.menutext(51, 15, "Status:")
            for s in hero.status:
                self.menutext(63, line_count+3+line_count2, s.name, fgcolor=self.textcolors[s.display_color])
                line_count += 1
        return
    
    def show_help(self):
        self.blank(self.right_menu_coords)
        self.menutext(51, 1, "HELP:")
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
        return    

    def fix_spacing(self, s, length, delimiter):
        num_spaces = length - len(s) -1
        line = s.split(delimiter)
        return line[0] + ":" + " "*num_spaces + line[1]

    def draw_skills_menu(self, skills, skill_index, prompt):
        self.blank(self.right_menu_coords)
        self.menutext(51, 1, "SKILLS:")

        for i, skill in enumerate(skills):
            self.menutext(51, (3+i), 'F' + str(i+1) + ': ')
            self.menutext(55, (3+i), skill)

        self.text(55, 3+skill_index, skills[skill_index], bgcolor=self.select_color)
        self.scrolling_prompt.print_skill_description(prompt, "?")
        self.screen.update()

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
        for attr in ('character', 'fgcolor', 'team_id', 'bgcolor'):
            if getattr(tile.actor, attr, None):
                if attr == 'character':
                    to_display[attr] = getattr(tile.actor, attr)
                else:
                    to_display['fgcolor'] = self.team_colors[tile.actor.team_id]

            elif getattr(tile.terrainmod, attr, None):
                to_display[attr] = getattr(tile.terrainmod, attr)
            elif getattr(tile.terrain, attr, None):
                to_display[attr] = getattr(tile.terrain, attr)

        return (to_display['character'], to_display['fgcolor'], to_display['bgcolor'])

    def highlight_area(self, highlight, tiles, battle_map, color="teal", is_target=False):
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
        self.blank((1,26,73,1))
        if not switch:
            return
        self.menutext(1, 26, active.name, "white")
        if active.hp <= 0:
            active.hp = 0
        if (1.0*active.hp/active.maxhp) >= 0.7: color = "lime"
        elif 0.3 <= (1.0*active.hp/active.maxhp) < 0.7: color = "yellow"
        else: color = "darkred"
        self.menutext(19, 26, "HP: ")
        self.menutext(23, 26, str(active.hp) +"/" + str(active.maxhp), fgcolor = color)
        self.menutext(31, 26, "MP: ")
        self.menutext(35, 26, str(active.mp) + "/" +str(active.maxmp), fgcolor = "aqua")
        self.menutext(42, 26, "condition: ")
        status, color = self.get_status(active)
        self.menutext(53, 26, status, color)
        self.menutext(63, 26, "terrain: ")
        self.text(72, 26, tile.character, fgcolor= tile.fgcolor, bgcolor=tile.bgcolor)
        self.screen.update()
        return

    def get_status(self, active):
        if not active.active_status_effects:
            return "Normal", "lime"
        if len(active.active_status_effects) == 1:
            try:
                return active.active_status_effects[0].status_effect.name, "yellow"
            except TypeError:
                print "ERROR INVALID STATUS", active.active_status_effects
        else:
            res = ""
            for s in active.active_status_effects:
                res = res + s.status_effect.name[0] + "/"
            return res[:-1], "yellow"

    def print_narration(self, narration_q):
        if narration_q:
            self.blank(self.narration_coords)
            for row, line in enumerate(narration_q):
                col = self.narration_coords[0]
                for word in line:
                    self.menutext(col, 42-row, word.string, fgcolor=self.textcolors[word.color_binding])
                    col += len(word.string) + 1
            self.screen.update()
        return

    def print_battle_menu(self, battle_menu_list, turn_count, battle_index, v_top):
        self.blank((self.right_menu_coords))
        num_chars = 10
        self.menutext(51, 1, "OVERVIEW: (Turn " + str(turn_count) +")")
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
            fgcolor = "white"
            bgcolor = None
            if i == visible_index:
                bgcolor = "fuchsia"
            self.menutext(51, 3+(i*2), actor[0], fgcolor=fgcolor, bgcolor=bgcolor)
            self.menutext(51, 4+(i*2), actor[1], fgcolor=fgcolor, bgcolor=bgcolor)
        try:
            self.highlight_active(battle_menu_list[battle_index][2], True)
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
        pass
        # for i, effect in enumerate(skill.effects):
        #     self.menutext(51, starting_line, "Additional Effects: ", fgcolor="yellow")
        #     if '|' in effect['type']:
        #         double_effect = effect['type'].split('|')
        #         self.menutext(51, starting_line + i + 1, "Allies: " + double_effect[0], fgcolor="lime")
        #         self.menutext(51, starting_line + i + 2, "Enemies: " + double_effect[1], fgcolor="red")
        #         self.menutext(51, starting_line + i + 3, '(' + str(effect["magnitude"]) + " for " + str(effect["duration"]) + " turns)")
        #     elif effect["duration"] and effect["magnitude"]:
        #         self.menutext(51, starting_line + i + 1, effect["type"] + " " + str(effect["magnitude"]) + " for " + str(effect["duration"]) + " turns.", fgcolor="white")
        #     elif effect["duration"]:
        #         self.menutext(51, starting_line + i + 1, effect["type"] + " for " + str(effect["duration"]) + " turns.", fgcolor="white")
        #     elif effect["magnitude"]:
        #         self.menutext(51, starting_line + i + 1, effect["type"] + " " + str(effect["magnitude"]) + " spaces.", fgcolor="white")


    def print_target(self, attacker, defender, skill):
        self.blank((self.right_menu_coords))
        center_space = (22 - len(attacker.name))/2
        self.menutext(51, 2, (" "*center_space) + attacker.name, fgcolor="lime")
        self.menutext(51, 3, " HP " + str(attacker.hp) + "/" + str(attacker.maxhp) + " (" + self.get_status(attacker)[0] + ")", fgcolor="lime")
        center_space = (22 - len(skill.name))/2
        self.menutext(51, 4, (" "*10) + u"▼")
        self.menutext(51, 5, (" "*10) + u"▼")
        self.menutext(51, 6, (" "*10) + u"▼")
        self.menutext(51, 7, (" "*center_space) + skill.name, fgcolor='white')
        self.menutext(51, 8, (" "*10) + u"▼")
        self.menutext(51, 9, (" "*10) + u"▼")
        self.menutext(51, 10,(" "*10) + u"▼")
        center_space = (22 - len(defender.name))/2
        color = 'red' if defender.is_hostile_to(attacker) else 'lime'
        self.menutext(51, 11, (" "*center_space) +defender.name, fgcolor=color)
        self.menutext(51, 12, " HP " + str(defender.hp) + "/" + str(defender.maxhp) + " (" + self.get_status(defender)[0] + ")", fgcolor=color)

        # if not skill.is_beneficial:
        #     hit_chance = skill.get_hit_chance(attacker, defender)
        #     self.menutext(51, 15, "Hit Chance: " + str(hit_chance) + "%", fgcolor="yellow")

        # if skill.damage != 0:
        #     color = 'lime' if skill.is_beneficial else 'darkred'
        #     noun = 'Healing: ' if skill.is_beneficial else 'Damage: '
        #     dmg_range = skill.get_damage_range(attacker)
        #
        #     if dmg_range[0] != dmg_range[1]:
        #         self.menutext(51, 16, noun + str(dmg_range[0]) + " - " + str(dmg_range[1]), fgcolor=color)
        #     else:
        #         self.menutext(51, 16, noun + str(dmg_range[0]), fgcolor=color)

        self.print_additional_effects(skill, starting_line=18)
        self.screen.update()
        return

    def print_multi_target(self, attacker, defenders, skill):
        self.blank(self.right_menu_coords)
        center_space = (22 - len(attacker.name))/2
        self.menutext(51, 1, (" "*center_space) + attacker.name, fgcolor="lime")
        self.menutext(51, 2, " HP " + str(attacker.hp) + "/" + str(attacker.maxhp) + " (" + self.get_status(attacker)[0] + ")", fgcolor="lime")
        center_space = (22 - len(skill.name))/2

        self.menutext(51, 3, (" "*10) + u"▼")
        self.menutext(51, 4, (" "*center_space) + skill.name, fgcolor='white')
        self.menutext(51, 5, (" "*10) + u"▼")

        current_line = 7

        if len(defenders) > 5:
            overflow_str = "+ %s more targets." % str(len(defenders) - 5)
            defenders = defenders[:4]
            self.menutext(51, 15, overflow_str, fgcolor="yellow")

        for defender in defenders:
            hit_chance_string = ''
            # if not skill.is_beneficial:
            #     hit_chance = skill.get_hit_chance(attacker, defender)
            #     hit_chance_string = "Hit: " + str(hit_chance) + "%"

            center_space = (22 - len(defender.name))/2
            color = 'red' if defender.is_hostile_to(attacker) else 'lime'
            self.menutext(51, current_line, (" " * center_space) + defender.name, fgcolor=color)
            self.menutext(51, current_line + 1, " HP " + str(defender.hp) + "/" + str(defender.maxhp) + '  ' + hit_chance_string, fgcolor=color)
            current_line += 2

        # if skill.damage != 0:
        #     color = 'lime' if skill.is_beneficial else 'darkred'
        #     noun = 'Healing: ' if skill.is_beneficial else 'Damage: '
        #     dmg_range = skill.get_damage_range(attacker)
        #     if dmg_range[0] != dmg_range[1]:
        #         self.menutext(51, 16, noun + str(dmg_range[0]) + " - " + str(dmg_range[1]), fgcolor=color)
        #     else:
        #         self.menutext(51, 16, noun + str(dmg_range[0]), fgcolor=color)

        self.print_additional_effects(skill, starting_line=19)

        self.screen.update()
        return

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
        UI.title_text(14, 28, "On the \"Roguenaissance 2.0\" RPG Battle Engine")
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
        hero_name = self.screen.input(maxlength=17, minlength=3,
                                      fgcolor="black", bgcolor="white", whitelistchars=string.ascii_letters)
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
        self.title_text(10, 8, "TURNS TAKEN:                         " + str(saved_data.score['turns_taken']), fgcolor='yellow')
        sleep(1)
        self.title_text(10, 9, "PERSONAL DAMAGE RECIEVED:            " + str(saved_data.score['damage_taken']), fgcolor='yellow')
        sleep(1)
        self.title_text(10, 10, "ENEMIES SLAIN:                       " + str(saved_data.score['enemies_killed']), fgcolor='aqua')
        sleep(3)
        score = 500 - (saved_data.score['turns_taken'] * 4.5) - (saved_data.score['damage_taken'] * 2) + (saved_data.score['enemies_killed'] * 10)
        self.title_text(10, 18, "FINAL SCORE:                         " + str(score))
        sleep(3)
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
        self.title_text(10, 20, "GRADE:                                 " + grade, fgcolor="lime")
        try:
            fin = open("highscores.dat", "a")
        except IOError:
            fin = open("highscores.dat", "w+")

        fin.write(saved_data.saved_character.name + "|" + saved_data.saved_character.class_name + "|" + str(int(score)) + "\n")
        fin.close()

        sleep(1)
        self.text_wrapper(ending_text, 3, 30, fgcolor="yellow")

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
            self.title_text(10, 8, "No high scores yet.", fgcolor="yellow")
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

        while 1:
            self.screen.update()
            command = input()
            if command:
                break

        return

def main():
    RN_UI = RN_UI_Class()
    RN_UI.draw_UI()
    RN_UI.print_legend([[".", "red", "grass"]], [["@", "white", "hero"]])
    pygcurse.waitforkeypress()

if __name__ == "__main__":
    main()