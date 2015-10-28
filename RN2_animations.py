# -*- coding: utf-8 -*-

from time import sleep
import pygame.mixer
import random

class RN_Animation_Class():
    def __init__(self, affected_tiles, game, RN_UI, anim_id, bmap, attacker):
        self.tiles = affected_tiles
        self.UI = RN_UI
        self.bmap = bmap
        self.anim_id = anim_id
        self.game = game
        self.attacker = attacker
        self.UI.screen._autoupdate = True
        self.animation()
        self.UI.screen._autoupdate = False

    def cleanup(self, tiles, clean_tint=True, tint = (0,0,0)):
        if type(tiles) is not list:
            tiles = [tiles]
        for t in tiles:
            if clean_tint is True:
                self.UI.tint(tint[0], tint[1], tint[2], (t[0],t[1],1,1))
            display = self.bmap[t[0]][t[1]].display()
            self.UI.text(t[0], t[1], display[0], fgcolor = display[1], bgcolor = display[2])
        return

    def flash_tiles(self, tiles, flash_list, reps=1, delay=0.15, fast_update=True, cleanup=True):
        if fast_update is True:
            self.UI.screen._autoupdate = False
        for i in range(reps):
            for f in flash_list:
                for t in tiles:
                    self.UI.tint(f[0], f[1], f[2], (t[0],t[1],1,1))
                if fast_update is True:
                    self.UI.screen.update()
                sleep(delay)
        if cleanup is True:
            self.cleanup(self.tiles)
        if fast_update is True:
            self.UI.screen._autoupdate = True
        return

    # def recolor_tiles(self, tiles, flash_list, reps=1, delay=0.15, fast_update=False, cleanup=True):
    #     if fast_update is True:
    #         self.UI.screen._autoupdate = False
    #     for i in range(reps):
    #         for f in flash_list:
    #             for t in tiles:
    #                 self.UI.text(f[0], f[1], f[2], (t[0],t[1],1,1))
    #             if fast_update is True:
    #                 self.UI.screen.update()
    #             sleep(delay)
    #     if cleanup is True:
    #         self.cleanup(self.tiles)
    #     if fast_update is True:
    #         self.UI.screen._autoupdate = True
    #     return

    def projectile(self, start, end, character_list, color_list, delay=0.05, clear=True):
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

    def hit(self, tiles, character_list, color_list, reps=1, delay=0.1):
        if type(tiles) is not list:
            tiles = [tiles]
        color_index = 0
        for i in range(reps):
            for j in range(len(character_list)):
                color = color_list[color_index]
                color_index += 1
                color_index %= len(color_list)
                for t in tiles:
                    self.UI.text(t[0], t[1], character_list[j], fgcolor = color, bgcolor = "black")
                sleep(delay)
        self.cleanup(tiles)
        return

    def firework(self, origin, size, character, color, delay = 0.005, reverse=False, clean_wait=True):
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
        self.cleanup(cleanup_list, tint = tint)
        self.UI.screen._autoupdate = True


    def grid_distance(self, actor1, actor2):
        return abs(actor1[0] - actor2[0]) + abs(actor1[1] - actor2[1])

    def animation(self):

        if self.anim_id == "meteor":
           self.game.play_sound("fall")
           self.projectile((self.tiles[0][0], 0), (self.tiles[0][0], self.tiles[0][1]), ["O"], ["red", "maroon"])
           self.game.play_sound("bigboom")
           self.flash_tiles(self.tiles, [(50,-50,-50), (150,-50,-50)], 3)
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
            print self.attacker, self.tiles
            self.projectile(self.attacker, self.tiles, [u"■"], ["olive"])
            self.game.play_sound("bighit")
            self.hit(self.tiles, ["*", "o", "O"], ["olive"])
            return

        elif self.anim_id == "ice toss":
            self.game.play_sound("ice")
            self.projectile(self.attacker, self.tiles, [u"♦"], ["aqua"])
            self.game.play_sound("bighit")
            self.hit(self.tiles, ["*", "o", "O"], ["aqua"])
            return

        elif self.anim_id == "fire ball":
            self.game.play_sound("fireball")
            self.projectile(self.attacker, self.tiles, [u"☼"], ["red", "maroon"])
            self.game.play_sound("fire")
            self.flash_tiles(self.tiles, [(150,-50,-50), (-50,-125,-125)], 3)
            return

        elif self.anim_id == "dark ball":
            self.game.play_sound("fireball")
            self.projectile(self.attacker, self.tiles, [u"☼"], ["fuchsia", "lime"])
            self.game.play_sound("dark")
            self.flash_tiles(self.tiles, [(-125,-125,-125), (-205,-205,-205)], 3)
            return

        elif self.anim_id == "poisonbolt":
            self.projectile(self.attacker, self.tiles, [u"Θ", "O"], ["green", "lime"])
            self.game.play_sound("gamma")
            self.flash_tiles(self.tiles, [(-50,50,-50), (-50,150,-50)], 3)

        elif self.anim_id == "frostfire":
            self.game.play_sound("fireball")
            self.projectile(self.attacker, self.tiles, [u"┼", u"╬"], ["red", "aqua"])
            self.game.play_sound("ice")
            self.game.play_sound("fire")
            self.flash_tiles(self.tiles, [(-50,-50,125), (125,-50,-50)], 4)

        elif self.anim_id == "push":
            self.projectile(self.attacker, self.tiles, ["-", "\\", "|", "/" ], ["white"])
            self.game.play_sound("bighit")
            self.hit(self.tiles, ["*", "o", "O"], ["white"])
            return

        elif self.anim_id == "heal":
            self.game.play_sound("heal")
            self.flash_tiles(self.tiles, [(200, 200, -25), (200, 200, 200)], 3)

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
            self.game.play_sound("zero")
            self.flash_tiles(self.tiles, [(-50, 150, 200), (-100, -150, 200), (200, 200, 200)], 4, delay=0.075)

        elif self.anim_id == "skycaller":
            self.game.play_sound("starstorm")
            self.flash_tiles(self.tiles, [(-40, -40, -40)], 1, fast_update=True, cleanup=False)
            colors = ["yellow", "fuchsia", "lime", "white"]
            for i in range(6):
                self.firework((random.randint(6,43), (random.randint(6,18))), 6, "*", random.choice(colors))
            self.game.play_sound("quake")
            self.flash_tiles(self.tiles, [(200, 200, -25), (200, 200, 200), (200, 0, 150)], 4, fast_update=True)

        elif self.anim_id == "tectonic":
            self.game.play_sound("quake")
            self.game.play_sound("bigboom")
            self.firework(self.attacker, 50, u"Ж", "olive", delay = 0.025)
            self.game.play_sound("surge")
            self.flash_tiles(self.tiles, [(0, -50, -100), (-100, -100, -100)], 4, fast_update=True)

        elif self.anim_id == "splitatom":
            self.flash_tiles(self.tiles, [(-30, -30, -30), (-60, -60, -60), (-100, -100, -100)], 1, fast_update=True, cleanup=False)
            self.firework((25,13), 25, u"∙", "red", reverse=True, clean_wait=False)
            self.game.play_sound("burn3")
            self.game.play_sound("bigboom")
            self.flash_tiles(self.tiles, [(255,255,255), (255,255,255), (255,-200,-200), (255,-100,-100), (200,-50,-50), (100,0,0), (50,0,0)], 1, fast_update=True, cleanup=True, delay=0.3)

        elif self.anim_id == "ascend":
            self.game.play_sound("fall")
            self.projectile((self.tiles[0][0], 0), (self.tiles[0][0], self.tiles[0][1]), [u"█"], ["white"], clear = False)
            self.game.play_sound("surge")
            self.flash_tiles(self.tiles, [(0, -50, -100), (-50, 200, -50), (-50, -50, 200)], 3)

        elif self.anim_id == "annihilate":
            self.game.play_sound("annihilate")
            self.game.play_sound("worldbreak")
            self.flash_tiles(self.tiles, [(200,200,200), (-200, -200, -200)], 4, fast_update=True, cleanup=True, delay=0.3)

        else:
            return





        #
        # if a_id == "ascend":
        #     play_sound(game, "fall")
        #     game.screen.text(origin[0], 0, " ", 255)
        #     for i in range(origin[1]-1):
        #         game.screen.text(origin[0], i+1, " ", 255)
        #         sleep(0.03)
        #     game.screen.text(origin[0], origin[1], "@", 240)
        #     sleep(0.03)
        #     for i in range(origin[1]):
        #         restore_tile(game, origin[0], i)
        #         sleep(0.03)
        #     play_sound(game, "surge")
        #     anim_tiles = game.get_range(origin,2)
        #     for i in range(5):
        #         for t in anim_tiles:
        #             if game.rmap[t[0]][t[1]][0] == ("",""):
        #                 game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1]%16 + 96+(16*i))
        #             else:
        #                 game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] - game.rmap[t[0]][t[1]][1][1]%16 + 96+(16*i))
        #         sleep(0.1)
        #         cleanup(game, anim_tiles)
        #         sleep(0.1)
        #
        #     return



        #

        #
        # if a_id == "annihilate":
        #     play_sound(game, "annihilate")
        #     play_sound(game, "worldbreak")
        #     for i in range(3):
        #         for j in range(25):
        #             for t in range (50):
        #                 if game.rmap[t][j][0] == ("",""):
        #                     game.screen.text(t, j, game.rmap[t][j][1][0], 15)
        #                 else:
        #                     game.screen.text(t, j, game.rmap[t][j][0][0], 15)
        #             sleep(0.01)
        #         for j in range(25):
        #             for t in range (50):
        #                 if game.rmap[t][j][0] == ("",""):
        #                     game.screen.text(t, j, game.rmap[t][j][1][0], 240)
        #                 else:
        #                     game.screen.text(t, j, game.rmap[t][j][0][0], 240)
        #             sleep(0.01)
        #
        #     for j in range(25):
        #         for t in range (50):
        #             restore_tile(game,t,j)
        #         sleep(0.04)
        #     return