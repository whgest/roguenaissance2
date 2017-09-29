# -*- coding: utf-8 -*-

from  pygame.time import wait as sleep
import math
import random

class Animation():
    def __init__(self, game, RN_UI, bmap):
        self.UI = RN_UI
        self.bmap = bmap
        self.game = game

    def animate(self, affected_tiles, anim_id, attacker):
        self.attacker = attacker.coords
        self.anim_id = anim_id
        self.tiles = affected_tiles
        self.UI.screen._autoupdate = True
        self.animation()
        self.UI.screen._autoupdate = False

    def cleanup(self, tiles, clean_tint=True, tint=(0, 0, 0)):
        if type(tiles) is not list:
            tiles = [tiles]
        for t in tiles:
            if clean_tint is True:
                self.UI.tint(tint[0], tint[1], tint[2], (t[0], t[1], 1, 1))
            display = self.UI.display_tile(self.bmap[t[0]][t[1]])
            self.UI.text(t[0], t[1], display[0], fgcolor=display[1], bgcolor=display[2])
        return

    def flash_tiles(self, tiles, flash_list, reps=1, delay=150, fast_update=True, cleanup=True):
        if fast_update is True:
            self.UI.screen._autoupdate = False
        for i in range(reps):
            for f in flash_list:
                for t in tiles:
                    self.UI.tint(f[0], f[1], f[2], (t[0], t[1], 1, 1))
                if fast_update is True:
                    self.UI.screen.update()
                sleep(delay)
        if cleanup is True:
            self.cleanup(self.tiles)
        if fast_update is True:
            self.UI.screen._autoupdate = True
        return

    def flash_screen(self, color=(255, 255, 255), delay=15, reps=1):
        self.UI.screen._autoupdate = False
        for r in range(reps):
            self.UI.tint(color[0], color[1], color[2], self.UI.battle_grid_coords)
            sleep(delay)
            self.UI.screen.update()
            self.UI.tint(0, 0, 0, self.UI.battle_grid_coords)
            sleep(delay)
            self.UI.screen.update()

        self.UI.screen._autoupdate = True
        return

    def tint_screen(self, tint, speed=5, increments=3):
        r = tint[0]
        g = tint[1]
        b = tint[2]

        for i in range(increments):
            red_tint_value = int(math.floor(r/(increments-i)))
            green_tint_value = int(math.floor(g/(increments-i)))
            blue_tint_value = int(math.floor(b/(increments-i)))
            self.UI.tint(red_tint_value, green_tint_value, blue_tint_value, self.UI.battle_grid_coords)
            self.UI.screen.update()
            sleep(speed)


    def projectile(self, start, end, character_list, color_list, delay=5, clear=True):
            if type(end) is list:
                end = end[0]
            clean_list = []
            x_count = 0
            y_count = 0
            color_index = 0
            char_index = 0
            x_dist = start[0] - end[0]
            y_dist = start[1] - end[1]
            for i in range(self.grid_distance(start, end)):
                if abs(x_dist) >= abs(y_dist) and x_dist >= 0:
                    x_count -= 1
                if abs(x_dist) >= abs(y_dist) and x_dist < 0:
                    x_count += 1
                if abs(x_dist) < abs(y_dist) and y_dist >= 0:
                    y_count -=1
                if abs(x_dist) < abs(y_dist) and y_dist < 0:
                    y_count +=1
                x_dist = start[0]+x_count - end[0]
                y_dist = start[1]+y_count - end[1]
                c_tile = (start[0]+x_count, start[1]+y_count)
                color = color_list[color_index]                  #color/character cycling
                character = character_list[char_index]
                color_index += 1
                char_index += 1
                color_index %= len(color_list)
                char_index %= len(character_list)
                self.UI.text(c_tile[0], c_tile[1], character, fgcolor = color, bgcolor = self.bmap[c_tile[0]][c_tile[1]].terrain.bgcolor)
                sleep(delay)
                if clear is True:
                    self.cleanup((c_tile[0], c_tile[1]))
                else:
                    clean_list.append((c_tile[0], c_tile[1]))
            if clear is False:
                self.cleanup(clean_list)
            return

    def hit(self, tiles, character_list, color_list, reps=1, delay=100):
        if type(tiles) is not list:
            tiles = [tiles]
        color_index = 0
        for i in range(reps):
            for j in range(len(character_list)):
                color = color_list[color_index]
                color_index += 1
                color_index %= len(color_list)
                for t in tiles:
                    self.UI.text(t[0], t[1], character_list[j], fgcolor=color, bgcolor="black")
                sleep(delay)
        self.cleanup(tiles)
        return

    def firework(self, origin, size, character, color, delay=20, reverse=False, clean_wait=True, cleanup=True):
        self.UI.screen._autoupdate = False
        cleanup_list = []
        x = origin[0]
        y = origin[1]
        if reverse is True:
            i = size-1
        else:
            i = 0
        tint = (self.UI.screen._screenRdelta[x][y], self.UI.screen._screenGdelta[x][y], self.UI.screen._screenBdelta[x][y])
        while i < size and i > -2:
            for drow in (-1-i, 0, 1+i):
                for dcol in (-1-i, 0, 1+i):
                    if drow == 0 and dcol == 0:
                        continue
                    if origin[0]+drow > 49 or origin[0]+drow < 0 or origin[1]+dcol > 24 or origin[1]+dcol < 0:
                        continue

                    self.UI.tint(0, 0, 0, (origin[0]+drow, origin[1]+dcol,1,1))
                    self.UI.text(origin[0]+drow, origin[1]+dcol, character, fgcolor=color, bgcolor="black")#bgcolor=self.bmap[x][y].terrain.bgcolor)
                    cleanup_list.append((origin[0]+drow, origin[1]+dcol))
                self.UI.screen.update()

            if reverse is True:
                i -= 1
            else:
                i += 1
            sleep(delay)
            if clean_wait is False:
                self.cleanup(cleanup_list, tint = tint)
                cleanup_list = []

        if cleanup:
            self.cleanup(cleanup_list, tint = tint)

        self.UI.screen._autoupdate = True

    def grid_distance(self, actor1, actor2):
        return abs(actor1[0] - actor2[0]) + abs(actor1[1] - actor2[1])

    def animation(self):
        if self.anim_id == "meteor":
            self.game.play_sound("fall")
            self.tint_screen((-25, -25, -25))
            self.projectile((self.tiles[0][0], 0), (self.tiles[0][0], self.tiles[0][1]), ["O"], ["red", "maroon"])
            self.game.play_sound("bigboom")
            self.flash_tiles(self.tiles, [(50,-50,-50), (150,-50,-50)], 3)
            self.tint_screen((0, 0, 0))
            return

        elif self.anim_id == "basic":
            self.game.play_sound("slash")
            self.hit(self.tiles, ["\\", "/"], ["red"])
            return

        elif self.anim_id == "bite":
            self.game.play_sound("slash")
            self.hit(self.tiles, [u"Ξ", "=", "-"], ["red"])
            return

        elif self.anim_id == "punch":
            self.game.play_sound("bighit")
            self.hit(self.tiles, ["*", "o", "O"], ["red"])
            return

        elif self.anim_id == "basic ranged":
            self.projectile(self.attacker, self.tiles, [u"¤"], ["white"])
            self.game.play_sound("arrow")
            return

        elif self.anim_id == "tbolt":
            self.game.play_sound("bigboom")
            self.projectile((self.tiles[0][0], 0), (self.tiles[0][0], self.tiles[0][1]), ["\\", "/"], ["white"], clear=False)
            self.game.play_sound("shock")
            self.flash_tiles(self.tiles, [(150,150,150), (100,100,100)], 3)
            return

        elif self.anim_id == "vine":
            self.projectile(self.attacker, self.tiles, [u"ζ"], ["green"], clear=False)
            self.game.play_sound("slash")
            return

        elif self.anim_id == "rock toss":
            self.projectile(self.attacker, self.tiles, [u"■"], ["olivedrab1"])
            self.game.play_sound("bighit")
            self.hit(self.tiles, ["*", "o", "O"], ["olivedrab1"])
            return

        elif self.anim_id == "venom":
            self.game.play_sound("slash")
            self.hit(self.tiles, ["\\", "/", "X", u"♦"], ["green2"])
            self.game.play_sound("dark")
            return

        elif self.anim_id == "ice toss":
            self.game.play_sound("ice")
            self.projectile(self.attacker, self.tiles, [u"♦"], ["deepskyblue"])
            self.game.play_sound("bighit")
            self.hit(self.tiles, ["*", "o", "O"], ["deepskyblue"])
            return

        elif self.anim_id == "fire ball":
            self.game.play_sound("fireball")
            self.projectile(self.attacker, self.tiles, [u"☼"], ["red", "maroon"])
            self.game.play_sound("fire")
            self.flash_tiles(self.tiles, [(150,-50,-50), (-50,-125,-125)], 3)
            return

        elif self.anim_id == "dark ball":
            self.game.play_sound("fireball")
            self.projectile(self.attacker, self.tiles, [u"☼"], ["magenta", "green2"])
            self.game.play_sound("dark")
            self.flash_tiles(self.tiles, [(-125,-125,-125), (-205,-205,-205)], 3)
            return

        elif self.anim_id == "poisonbolt":
            self.projectile(self.attacker, self.tiles, [u"Θ", "O"], ["green", "green2"])
            self.game.play_sound("gamma")
            self.flash_tiles(self.tiles, [(-50,50,-50), (-50,150,-50)], 3)

        elif self.anim_id == "frostfire":
            self.game.play_sound("fireball")
            self.projectile(self.attacker, self.tiles, [u"┼", u"╬"], ["red", "deepskyblue"])
            self.game.play_sound("ice")
            self.game.play_sound("fire")
            self.flash_tiles(self.tiles, [(-50,-50,125), (125,-50,-50)], 4)

        elif self.anim_id == "push":
            self.projectile(self.attacker, self.tiles, ["-", "\\", "|", "/"], ["white"])
            self.game.play_sound("bighit")
            self.hit(self.tiles, ["*", "o", "O"], ["white"])
            return

        elif self.anim_id == "heal":
            self.game.play_sound("holy2")
            self.flash_tiles(self.tiles, [(200, 200, -25), (200, 200, 200)], 3)

        elif self.anim_id == "time":
            self.game.play_sound("slowdown")
            self.flash_tiles(self.tiles, [(200, 200, 200), (-200, -200, -200)], 3)

        elif self.anim_id == "poison":
            self.game.play_sound("drain")
            self.flash_tiles(self.tiles, [(-50,50,-50), (-50,150,-50)], 3)

        elif self.anim_id == "armor":
            self.game.play_sound("buff")
            self.flash_tiles(self.tiles, [(190, 180, 100), (160, 80, 45)], 3)

        elif self.anim_id == "drain":
            self.game.play_sound("drain")
            self.flash_tiles(self.tiles, [(200, 200, 200), (200, -50, -50)], 3)

        elif self.anim_id == "freeze":
            self.game.play_sound("ice")
            self.flash_tiles(self.tiles, [(0, 200, 200), (-50, 200, 200)], 3)

        elif self.anim_id == "summon":
            self.game.play_sound("summon")
            self.flash_tiles(self.tiles, [(100, 100, 100), (200, 200, 200)], 3)

        elif self.anim_id == "gamma":
            self.game.play_sound("gamma")
            self.flash_tiles(self.tiles, [(200, 200, -25), (200, 200, 200), (200, 0, 150)], 3)

        elif self.anim_id == "surge":
            self.game.play_sound("gravity")
            self.flash_tiles(self.tiles, [(-50, -50, 150), (70, -35, 150)], 3)

        elif self.anim_id == "singularity":
            self.game.play_sound("singularity")
            self.flash_tiles(self.tiles, [(-50, -50, 150), (70, -35, 150), (-200, -200, -200)], 4)

        elif self.anim_id == "zero":
            self.tint_screen((50, 50, 200))
            self.game.play_sound("zero")
            self.flash_tiles(self.tiles, [(-50, 150, 200), (-100, -150, 200), (200, 200, 200)], 4)
            self.tint_screen((0, 0, 0))

        elif self.anim_id == "skycaller":
            self.game.play_sound("starstorm")
            self.flash_tiles(self.tiles, [(-40, -40, -40)], 1, fast_update=True, cleanup=False)
            colors = ["yellow", "magenta", "green2", "white"]
            for i in range(6):
                self.firework((random.randint(6,43), (random.randint(6,18))), 6, "*", random.choice(colors))
            self.game.play_sound("quake")
            self.flash_tiles(self.tiles, [(200, 200, -25), (200, 200, 200), (200, 0, 150)], 4, fast_update=True)

        elif self.anim_id == "tectonic":
            self.tint_screen((139, 69, 19))
            self.game.play_sound("quake")
            self.game.play_sound("bigboom")
            self.firework(self.attacker, 40, u"Ж", "olivedrab1")
            self.game.play_sound("surge")
            self.flash_tiles(self.tiles, [(0, -50, -100), (-100, -100, -100)], 4, fast_update=True)
            self.tint_screen((0, 0, 0))

        elif self.anim_id == "splitatom":
            self.flash_tiles(self.tiles, [(-30, -30, -30), (-60, -60, -60), (-100, -100, -100)], 1, fast_update=True, cleanup=False)
            self.firework((25, 13), 25, u"∙", "red", reverse=True, clean_wait=False)
            self.game.play_sound("burn3")
            self.game.play_sound("bigboom")
            self.flash_tiles(self.tiles, [(255,255,255), (255,255,255), (255,-200,-200), (255,-100,-100), (200,-50,-50), (100,0,0), (50,0,0)], 1, fast_update=True, cleanup=True, delay=300)

        elif self.anim_id == "avalanche":
            self.game.play_sound("buff")
            self.flash_tiles([self.attacker], [(100, 100, 100), (0, 0, 0)], 4)
            self.game.play_sound("fall")
            self.hit(self.tiles, ['/', '\\', '|', 'X'], ['white'])
            self.game.play_sound("bighit")
            self.flash_screen((139, 69, 19))
            self.game.play_sound('impact')

        elif self.anim_id == "ascend":
            self.game.play_sound("fall")
            self.projectile((self.tiles[0][0], 0), (self.tiles[0][0], self.tiles[0][1]), [u"█"], ["white"], clear=False)
            self.game.play_sound("surge")
            self.flash_tiles(self.tiles, [(0, -50, -100), (-50, 200, -50), (-50, -50, 200)], 3)

        elif self.anim_id == "annihilate":
            self.game.play_sound("annihilate")
            self.game.play_sound("worldbreak")
            self.flash_tiles(self.tiles, [(200,200,200), (-200, -200, -200)], 4, fast_update=True, cleanup=True, delay=300)

        elif self.anim_id == "playerdeath":
            self.game.play_sound("zero")
            self.flash_tiles(self.tiles, [(200, -50, -50), (100, 0, 0)], 6, cleanup=False)
            self.game.play_sound("bigboom")
            self.firework(self.tiles[0], 5, "X", (0, 0, 0), cleanup=False)

        elif self.anim_id == "deathanim":
            self.game.play_sound("death")
            self.flash_tiles(self.tiles, [(200, -50, -50), (200, 0, 0), (-50, -100, -100), (-100, -200, -200), (-255, -255, -255)], 1)

        elif self.anim_id == "beldeath":
            self.flash_screen(color=(150, 150, 150), reps=2)
            self.game.play_sound("annihilate")
            self.flash_tiles(self.tiles, [(-50, -50, -50), (-150, -150, -150)], 8, cleanup=False)
            self.game.play_sound("bigboom")
            self.firework(self.tiles[0], 15, "X", (0, 0, 0), cleanup=False)

        elif self.anim_id == "none":
            pass

        else:
            return