from time import sleep
import pygame.mixer
import random

pygame.mixer.init()

def play_music(game, music_ident, queue=False):
    if music_ident == "mute":
        pygame.mixer.music.stop()
        return
    if queue:
        pygame.mixer.music.queue("sound/" + game.music[music_ident])
        return
    pygame.mixer.music.load("sound/" + game.music[music_ident])
    if not game.mute_switch:
        pygame.mixer.music.play()
        return

def check_music():
    return pygame.mixer.music.get_busy()

def play_sound(game, sound_ident):
    sound = pygame.mixer.Sound("sound/" + game.sound[sound_ident])
    if not game.mute_switch:
        sound.play()

def cleanup(game, affected_tiles):
        for t in affected_tiles:
            if game.rmap[t[0]][t[1]][0] == ("",""):
                game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1])
            else:
                game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + (game.rmap[t[0]][t[1]][1][1]-game.rmap[t[0]][t[1]][1][1]%16))
        return

def restore_tile(game, x, y):
        if game.rmap[x][y][0] == ("",""):
            game.screen.text(x, y, game.rmap[x][y][1][0], game.rmap[x][y][1][1])
        else:
            game.screen.text(x, y, game.rmap[x][y][0][0], game.rmap[x][y][0][1] + (game.rmap[x][y][1][1]-game.rmap[x][y][1][1]%16))
        return

def animation(game, a_id, origin, affected_tiles, attacker):
    if a_id == "basic":
        for a in affected_tiles:
            play_sound(game, "slash")
            game.screen.text(a[0], a[1], "/", 12)
            sleep(0.1)
            game.screen.text(a[0], a[1], "\\", 12)
            sleep(0.1)
        cleanup(game, affected_tiles)
        return

    if a_id == "bite":
        for a in affected_tiles:
            play_sound(game, "slash")
            game.screen.text(a[0], a[1], "=", 12)
            sleep(0.1)
            game.screen.text(a[0], a[1], "-", 12)
            sleep(0.1)
        cleanup(game, affected_tiles)
        return

    if a_id == "punch":
        for a in affected_tiles:
            play_sound(game, "bighit")
            game.screen.text(a[0], a[1], "*", 12)
            sleep(0.1)
            game.screen.text(a[0], a[1], "O", 12)
            sleep(0.1)
        cleanup(game, affected_tiles)
        return

    if a_id == "meteor":
        play_sound(game, "fall")
        game.screen.text(origin[0], 0, "O", 12)
        for i in range(origin[1]-1):
            restore_tile(game, origin[0], i)
            game.screen.text(origin[0], i+1, "O", 12)
            sleep(0.1)
        play_sound(game, "bigboom")
        for t in affected_tiles:
            if game.rmap[t[0]][t[1]][0] == ("",""):
                game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 64)
            else:
                game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 64)
            sleep(0.01)
        sleep(0.5)
        cleanup(game, affected_tiles)
        return

    if a_id == "tbolt":
        play_sound(game, "bigboom")
        game.screen.text(origin[0], 0, "|", 15)
        for i in range(origin[1]-1):
            game.screen.text(origin[0], i+1, "|", 15)
            sleep(0.02)
        play_sound(game, "shock")
        for i in range(origin[1]):
            restore_tile(game, origin[0], i)
        for i in range(3):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1]%16 + 255)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] - game.rmap[t[0]][t[1]][1][1]%16 + 255)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)

        sleep(0.5)
        cleanup(game, affected_tiles)
        return

    if a_id == "basic ranged":
        x_count = 0
        y_count = 0
        x_dist = attacker[0] - affected_tiles[0][0]
        y_dist = attacker[1] - affected_tiles[0][1]
        for i in range(game.grid_distance(attacker, affected_tiles[0])):
            if abs(x_dist) >= abs(y_dist) and x_dist >= 0:
                x_count -= 1
            if abs(x_dist) >= abs(y_dist) and x_dist < 0:
                x_count += 1
            if abs(x_dist) < abs(y_dist) and y_dist >= 0:
                y_count -=1
            if abs(x_dist) < abs(y_dist) and y_dist < 0:
                y_count +=1
            x_dist = attacker[0]+x_count - affected_tiles[0][0]
            y_dist = attacker[1]+y_count - affected_tiles[0][1]
            c_tile = (attacker[0]+x_count, attacker[1]+y_count)
            color = game.rmap[c_tile[0]][c_tile[1]][1][1]
            game.screen.text(c_tile[0], c_tile[1], "-", 8 + (color-color%16))
            sleep(0.1)
            restore_tile(game, attacker[0]+x_count, attacker[1]+y_count)
        play_sound(game, "arrow")
        cleanup(game, affected_tiles)
        return

    if a_id == "vine":
        x_count = 0
        y_count = 0
        x_dist = attacker[0] - affected_tiles[0][0]
        y_dist = attacker[1] - affected_tiles[0][1]
        restore_list = []
        for i in range(game.grid_distance(attacker, affected_tiles[0])):
            if abs(x_dist) >= abs(y_dist) and x_dist >= 0:
                x_count -= 1
            if abs(x_dist) >= abs(y_dist) and x_dist < 0:
                x_count += 1
            if abs(x_dist) < abs(y_dist) and y_dist >= 0:
                y_count -=1
            if abs(x_dist) < abs(y_dist) and y_dist < 0:
                y_count +=1
            x_dist = attacker[0]+x_count - affected_tiles[0][0]
            y_dist = attacker[1]+y_count - affected_tiles[0][1]
            c_tile = (attacker[0]+x_count, attacker[1]+y_count)
            color = game.rmap[c_tile[0]][c_tile[1]][1][1]
            game.screen.text(c_tile[0], c_tile[1], "|", 2 + (color-color%16))
            restore_list.append((c_tile[0], c_tile[1]))
            sleep(0.1)
        play_sound(game, "slash")
        for i in range(len(restore_list)):
            restore_tile(game, restore_list[i][0], restore_list[i][1])

        cleanup(game, affected_tiles)
        return

    if a_id == "rock toss":
        x_count = 0
        y_count = 0
        x_dist = attacker[0] - affected_tiles[0][0]
        y_dist = attacker[1] - affected_tiles[0][1]
        for i in range(game.grid_distance(attacker, affected_tiles[0])):
            if abs(x_dist) >= abs(y_dist) and x_dist >= 0:
                x_count -= 1
            if abs(x_dist) >= abs(y_dist) and x_dist < 0:
                x_count += 1
            if abs(x_dist) < abs(y_dist) and y_dist >= 0:
                y_count -=1
            if abs(x_dist) < abs(y_dist) and y_dist < 0:
                y_count +=1
            x_dist = attacker[0]+x_count - affected_tiles[0][0]
            y_dist = attacker[1]+y_count - affected_tiles[0][1]
            c_tile = (attacker[0]+x_count, attacker[1]+y_count)
            color = game.rmap[c_tile[0]][c_tile[1]][1][1]
            game.screen.text(c_tile[0], c_tile[1], "o", 0 + (color-color%16))
            sleep(0.1)
            restore_tile(game, attacker[0]+x_count, attacker[1]+y_count)
        play_sound(game, "bighit")
        cleanup(game, affected_tiles)
        return

    if a_id == "ice toss":
        play_sound(game, "ice")
        x_count = 0
        y_count = 0
        x_dist = attacker[0] - affected_tiles[0][0]
        y_dist = attacker[1] - affected_tiles[0][1]
        for i in range(game.grid_distance(attacker, affected_tiles[0])):
            if abs(x_dist) >= abs(y_dist) and x_dist >= 0:
                x_count -= 1
            if abs(x_dist) >= abs(y_dist) and x_dist < 0:
                x_count += 1
            if abs(x_dist) < abs(y_dist) and y_dist >= 0:
                y_count -=1
            if abs(x_dist) < abs(y_dist) and y_dist < 0:
                y_count +=1
            x_dist = attacker[0]+x_count - affected_tiles[0][0]
            y_dist = attacker[1]+y_count - affected_tiles[0][1]
            c_tile = (attacker[0]+x_count, attacker[1]+y_count)
            color = game.rmap[c_tile[0]][c_tile[1]][1][1]
            game.screen.text(c_tile[0], c_tile[1], "^", 0 + (color-color%16))
            sleep(0.1)
            restore_tile(game, attacker[0]+x_count, attacker[1]+y_count)
        play_sound(game, "bighit")
        cleanup(game, affected_tiles)
        return

    if a_id == "fire ball":
        play_sound(game, "arrow")
        x_count = 0
        y_count = 0
        x_dist = attacker[0] - affected_tiles[0][0]
        y_dist = attacker[1] - affected_tiles[0][1]
        for i in range(game.grid_distance(attacker, affected_tiles[0])):
            if abs(x_dist) >= abs(y_dist) and x_dist >= 0:
                x_count -= 1
            if abs(x_dist) >= abs(y_dist) and x_dist < 0:
                x_count += 1
            if abs(x_dist) < abs(y_dist) and y_dist >= 0:
                y_count -=1
            if abs(x_dist) < abs(y_dist) and y_dist < 0:
                y_count +=1
            x_dist = attacker[0]+x_count - affected_tiles[0][0]
            y_dist = attacker[1]+y_count - affected_tiles[0][1]
            c_tile = (attacker[0]+x_count, attacker[1]+y_count)
            color = game.rmap[c_tile[0]][c_tile[1]][1][1]
            game.screen.text(c_tile[0], c_tile[1], "*", 12 + (color-color%16))
            sleep(0.1)
            restore_tile(game, attacker[0]+x_count, attacker[1]+y_count)
        play_sound(game, "fire")
        for i in range(2):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 192)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 192)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        cleanup(game, affected_tiles)
        return

    if a_id == "dark ball":
        play_sound(game, "arrow")
        x_count = 0
        y_count = 0
        x_dist = attacker[0] - affected_tiles[0][0]
        y_dist = attacker[1] - affected_tiles[0][1]
        for i in range(game.grid_distance(attacker, affected_tiles[0])):
            if abs(x_dist) >= abs(y_dist) and x_dist >= 0:
                x_count -= 1
            if abs(x_dist) >= abs(y_dist) and x_dist < 0:
                x_count += 1
            if abs(x_dist) < abs(y_dist) and y_dist >= 0:
                y_count -=1
            if abs(x_dist) < abs(y_dist) and y_dist < 0:
                y_count +=1
            x_dist = attacker[0]+x_count - affected_tiles[0][0]
            y_dist = attacker[1]+y_count - affected_tiles[0][1]
            c_tile = (attacker[0]+x_count, attacker[1]+y_count)
            color = game.rmap[c_tile[0]][c_tile[1]][1][1]
            game.screen.text(c_tile[0], c_tile[1], "o", 8 + (color-color%16))
            sleep(0.1)
            restore_tile(game, attacker[0]+x_count, attacker[1]+y_count)
        play_sound(game, "shock")
        for i in range(2):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 255)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1])
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        cleanup(game, affected_tiles)
        return

    if a_id == "frostfire":
        play_sound(game, "arrow")
        x_count = 0
        y_count = 0
        x_dist = attacker[0] - affected_tiles[0][0]
        y_dist = attacker[1] - affected_tiles[0][1]
        for i in range(game.grid_distance(attacker, affected_tiles[0])):
            if abs(x_dist) >= abs(y_dist) and x_dist >= 0:
                x_count -= 1
            if abs(x_dist) >= abs(y_dist) and x_dist < 0:
                x_count += 1
            if abs(x_dist) < abs(y_dist) and y_dist >= 0:
                y_count -=1
            if abs(x_dist) < abs(y_dist) and y_dist < 0:
                y_count +=1
            x_dist = attacker[0]+x_count - affected_tiles[0][0]
            y_dist = attacker[1]+y_count - affected_tiles[0][1]
            c_tile = (attacker[0]+x_count, attacker[1]+y_count)
            color = game.rmap[c_tile[0]][c_tile[1]][1][1]
            game.screen.text(c_tile[0], c_tile[1], "+", random.randint(11,12) + (color-color%16))
            sleep(0.1)
            restore_tile(game, attacker[0]+x_count, attacker[1]+y_count)
        play_sound(game, "fire")
        play_sound(game, "ice")
        for i in range(4):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 192)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 192)
                sleep(0.1)
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 176)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 176)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        cleanup(game, affected_tiles)
        return

    if a_id == "poisonbolt":
        play_sound(game, "arrow")
        x_count = 0
        y_count = 0
        x_dist = attacker[0] - affected_tiles[0][0]
        y_dist = attacker[1] - affected_tiles[0][1]
        for i in range(game.grid_distance(attacker, affected_tiles[0])):
            if abs(x_dist) >= abs(y_dist) and x_dist >= 0:
                x_count -= 1
            if abs(x_dist) >= abs(y_dist) and x_dist < 0:
                x_count += 1
            if abs(x_dist) < abs(y_dist) and y_dist >= 0:
                y_count -=1
            if abs(x_dist) < abs(y_dist) and y_dist < 0:
                y_count +=1
            x_dist = attacker[0]+x_count - affected_tiles[0][0]
            y_dist = attacker[1]+y_count - affected_tiles[0][1]
            c_tile = (attacker[0]+x_count, attacker[1]+y_count)
            color = game.rmap[c_tile[0]][c_tile[1]][1][1]
            game.screen.text(c_tile[0], c_tile[1], "^", random.randint(10,11) + (color-color%16))
            sleep(0.1)
            restore_tile(game, attacker[0]+x_count, attacker[1]+y_count)
        play_sound(game, "gamma")
        for i in range(4):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 160)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 160)
                sleep(0.1)
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 32)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 32)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        cleanup(game, affected_tiles)
        return

    if a_id == "push":
        x_count = 0
        y_count = 0
        x_dist = attacker[0] - affected_tiles[0][0]
        y_dist = attacker[1] - affected_tiles[0][1]
        anim = ["|", "/", "-", "\\"]
        anim_count = 0
        for i in range(game.grid_distance(attacker, affected_tiles[0])):
            if anim_count > 3:
                anim_count = 0
            anim_c = anim[anim_count]
            if abs(x_dist) >= abs(y_dist) and x_dist >= 0:
                x_count -= 1
            if abs(x_dist) >= abs(y_dist) and x_dist < 0:
                x_count += 1
            if abs(x_dist) < abs(y_dist) and y_dist >= 0:
                y_count -=1
            if abs(x_dist) < abs(y_dist) and y_dist < 0:
                y_count +=1
            x_dist = attacker[0]+x_count - affected_tiles[0][0]
            y_dist = attacker[1]+y_count - affected_tiles[0][1]
            game.screen.text(attacker[0]+x_count, attacker[1]+y_count , anim_c, 11)
            anim_count += 1
            sleep(0.1)
            restore_tile(game, attacker[0]+x_count, attacker[1]+y_count)
        play_sound(game, "arrow")
        cleanup(game, affected_tiles)

        return

    if a_id == "heal":
        play_sound(game, "heal")
        for i in range(3):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 224)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] - game.rmap[t[0]][t[1]][1][1]%16 + 224)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        #cleanup(game, affected_tiles)
        return

    if a_id == "poison":
        play_sound(game, "drain")
        for i in range(3):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 160)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] - game.rmap[t[0]][t[1]][1][1]%16 + 160)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        #cleanup(game, affected_tiles)
        return

    if a_id == "armor":
        play_sound(game, "buff")
        for i in range(3):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1]%16 + 96)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] - game.rmap[t[0]][t[1]][1][1]%16 + 96)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        #cleanup(game, affected_tiles)
        return

    if a_id == "ascend":
        play_sound(game, "fall")
        game.screen.text(origin[0], 0, " ", 255)
        for i in range(origin[1]-1):
            game.screen.text(origin[0], i+1, " ", 255)
            sleep(0.03)
        game.screen.text(origin[0], origin[1], "@", 240)
        sleep(0.03)
        for i in range(origin[1]):
            restore_tile(game, origin[0], i)
            sleep(0.03)
        play_sound(game, "surge")
        anim_tiles = game.get_range(origin,2)
        for i in range(5):
            for t in anim_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1]%16 + 96+(16*i))
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] - game.rmap[t[0]][t[1]][1][1]%16 + 96+(16*i))
            sleep(0.1)
            cleanup(game, anim_tiles)
            sleep(0.1)

        return

    if a_id == "drain":
        play_sound(game, "drain")
        for i in range(5):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 64)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 64)
            game.screen.text(attacker[0], attacker[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 160)
            sleep(0.1)
            cleanup(game, affected_tiles)
            restore_tile(game, attacker[0], attacker[1])
            sleep(0.1)
        #cleanup(game, affected_tiles)
        return


    if a_id == "freeze":
        play_sound(game, "ice")
        for i in range(2):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 176)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 176)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        for t in affected_tiles:
            if game.rmap[t[0]][t[1]][0] == ("",""):
                game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 176)
            else:
                game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 176)
        sleep(1.0)
        cleanup(game, affected_tiles)
        return

    if a_id == "summon":
        play_sound(game, "summon")
        for i in range(3):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 240)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 240)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        #cleanup(game, affected_tiles)
        return

    if a_id == "gamma":
        play_sound(game, "gamma")
        for i in range(3):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + (208 + (i*16)))
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + (208 + (i*16)))
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        return

    if a_id == "skycaller":
        play_sound(game, "starstorm")
        x_list = []
        for i in range(35):
            x_list.append(random.randint(0, 48))
        for j in range(25):
            for i in range (35):
                game.screen.text(x_list[i]+1 , j, "*", random.randint(10, 15))
                sleep(0.0025)
        play_sound(game, "quake")
        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0], game.rmap[t][j][1][1] + 224)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0], game.rmap[t][j][0][1] + 224)
            sleep(0.005)
        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0], game.rmap[t][j][1][1] + 240)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0], game.rmap[t][j][0][1]+ 240)
            sleep(0.01)

        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0], game.rmap[t][j][1][1] + 208)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0], game.rmap[t][j][0][1]+ 208)
            sleep(0.01)

        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0], game.rmap[t][j][1][1] + 160)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0], game.rmap[t][j][0][1]+ 160)
            sleep(0.01)

        for j in range(25):
            for t in range (50):
                restore_tile(game,t,j)
            sleep(0.04)
        return

    if a_id == "tectonic":
        play_sound(game, "quake")
        play_sound(game, "bigboom")
        play_sound(game, "surge")
        restore_list = []
        for i in range(100):
            x = random.randint(0,49)
            y = random.randint(0,24)
            game.screen.text(x, y, "X", game.rmap[x][y][1][1] - game.rmap[x][y][1][1]%16)
            restore_list.append((x,y))
            sleep(0.02)

        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0], 128)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0], 128)
            sleep(0.01)

        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0], 96)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0], 96)
            sleep(0.01)

        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0], 128)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0], 128)
            sleep(0.01)

        for j in range(25):
            for t in range (50):
                restore_tile(game,t,j)
            sleep(0.04)

        return


    if a_id == "zero":
        play_sound(game, "zero")
        color_list = [240,176,144,48,112,128]
        for i in range(6):
                    for t in affected_tiles:
                        if game.rmap[t[0]][t[1]][0] == ("",""):
                            game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + color_list[i])
                        else:
                            game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + color_list[i])
                    sleep(0.3)
                    cleanup(game, affected_tiles)
        return

    if a_id == "splitatom":

        for i in range(25):
            if i > 0:
                restore_tile(game, i-1, 12)
                restore_tile(game, game.map_size[0]-i, 12)
            game.screen.text(i, 12, "0", 12)
            game.screen.text((game.map_size[0]-1)-i, 12, "0", 12)
            sleep(0.03)
        #play_sound(game, "bigboom")
        #for i in range (10):

        play_sound(game, "bigboom")
        play_sound(game, "burn3")
        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0],112)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0],112)
        sleep(0.25)

        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0],240)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0],240)

        sleep(0.25)

        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0], 255)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0], 255)

        sleep(1)

        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0],240)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0],240)

        sleep(0.5)

        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0],192)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0],192)

        sleep(0.5)

        for j in range(25):
            for t in range (50):
                if game.rmap[t][j][0] == ("",""):
                    game.screen.text(t, j, game.rmap[t][j][1][0],64)
                else:
                    game.screen.text(t, j, game.rmap[t][j][0][0],64)

        sleep(0.5)

        for j in range(25):
            for t in range (50):
                restore_tile(game,t,j)
            sleep(0.04)
        return

    if a_id == "surge":
        play_sound(game, "gravity")
        for i in range(3):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 255)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 255)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        #cleanup(game, affected_tiles)
        return

    if a_id == "singularity":
        play_sound(game, "singularity")
        for i in range(4):
            for t in affected_tiles:
                if game.rmap[t[0]][t[1]][0] == ("",""):
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][1][0], game.rmap[t[0]][t[1]][1][1] + 255)
                else:
                    game.screen.text(t[0], t[1], game.rmap[t[0]][t[1]][0][0], game.rmap[t[0]][t[1]][0][1] + 255)
            sleep(0.1)
            cleanup(game, affected_tiles)
            sleep(0.1)
        #cleanup(game, affected_tiles)
        return


    if a_id == "annihilate":
        play_sound(game, "annihilate")
        play_sound(game, "worldbreak")
        for i in range(3):
            for j in range(25):
                for t in range (50):
                    if game.rmap[t][j][0] == ("",""):
                        game.screen.text(t, j, game.rmap[t][j][1][0], 15)
                    else:
                        game.screen.text(t, j, game.rmap[t][j][0][0], 15)
                sleep(0.01)
            for j in range(25):
                for t in range (50):
                    if game.rmap[t][j][0] == ("",""):
                        game.screen.text(t, j, game.rmap[t][j][1][0], 240)
                    else:
                        game.screen.text(t, j, game.rmap[t][j][0][0], 240)
                sleep(0.01)

        for j in range(25):
            for t in range (50):
                restore_tile(game,t,j)
            sleep(0.04)
        return