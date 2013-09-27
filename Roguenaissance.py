"""

Project Roguenaissance
by William Hardy Gest

September 2013

"""


#savegames need to store battle id, hero, and score stats. no in battle saving. iron man.


import os
from time import sleep
from msvcrt import getch
from msvcrt import getche
import pickle

def title_screen(game):
    try:
        #self.display_art('title')    #if there are art or music files labelled "title", they will be used here.
        game.play_music('title')
    except:
        pass
    for y in range(40):
        game.screen.text(0, y, "|")
        game.screen.text(74, y, "|")
    for x in range(75):
        game.screen.text(x, 0, "-")
        game.screen.text(x, 39, "-")
    game.screen.text(6, 30, "A game made for the \"Project Roguenaissance\" RPG Battle Engine", 15)
    game.screen.text(22, 31, "by William Hardy Gest, 2013", 15)
    title_list = [("New Game", 10), ("Continue", 25), ("High Scores", 42), ("Quit", 60)]
    game.screen.text(title_list[0][1], 35, title_list[0][0], 223)
    game.screen.text(title_list[1][1], 35, title_list[1][0])
    game.screen.text(title_list[2][1], 35, title_list[2][0])
    game.screen.text(title_list[3][1], 35, title_list[3][0])
    title_index = 0
    while 1:
            command = ord(getch())
            if command == 224:
                command = ord(getch())
                command = game.convert_arrows(command)
            if command == 54: #6
                game.screen.text(title_list[title_index][1], 35, title_list[title_index][0])
                title_index += 1
            elif command == 52: #4
                game.screen.text(title_list[title_index][1], 35, title_list[title_index][0])
                title_index -= 1
            elif command in [13, 32]:  #RETURN, #SPACE
                selection = title_list[title_index][0]
                break
            title_index %= len(title_list)
            game.screen.text(title_list[title_index][1], 35, title_list[title_index][0], 223)

    if selection == "New Game":
        display_intro(game, "intro")
        create_character(game)
        #return game, "new"
    elif selection == "Load Game":
        #return load_game(), "load"
        pass
    elif selection == "High Scores":
        pass
    elif selection == "Quit":
        exit()
    else:
        exit()

def load_game(self):
    t = os.listdir(os.getcwd())
    for tfile in t:
        if tfile[-4::] == ".sav":
            print tfile
    filename = raw_input("Load which file? >>>>")
    if filename in ["quit,cancel,exit"]:
        exit()
    if filename[-4::] == ".sav":
        filename = filename.replace(".sav", "")
    if filename+".sav" in t:
        filename = filename +".sav"
        fin = open(filename)
        loaded_game = pickle.load(fin)
        fin.close()
        print
        return loaded_game
    else:
        print "Invalid save file."
        return


def create_character(game):
    game.screen.rectangle((1,30,73,38))
    text_wrapper(game, game.text["Name"].value, 2, 3)
    while 1:
        game.screen.pos(2,10)
        game.screen.cursor(1)
        hero_name = get_hero_name(game, 10)
        if len(hero_name) > 18:
            game.screen.text(2, 12, game.text["NameInvalid"].value)
            game.screen.rectangle((2,10,73,13))
        else:
            game.screen.cursor(0)
            game.heroname = hero_name
            break

    text_wrapper(game, game.text["Class"].value, 2, 15)
    game.screen.text(27, 30, "Please select a class:", 15)
    title_list = [("Astromancer", 10), ("Pyromancer", 33), ("Terramancer", 54)]
    game.screen.text(title_list[0][1], 35, title_list[0][0], 223)
    game.screen.text(title_list[1][1], 35, title_list[1][0])
    game.screen.text(title_list[2][1], 35, title_list[2][0])
    title_index = 0
    while 1:
            text_wrapper(game, game.text[title_list[title_index][0]].value, 2, 24)
            command = ord(getch())
            if command == 224:
                command = ord(getch())
                command = game.convert_arrows(command)
            if command == 54: #6
                game.screen.text(title_list[title_index][1], 35, title_list[title_index][0])
                title_index += 1
            elif command == 52: #4
                game.screen.text(title_list[title_index][1], 35, title_list[title_index][0])
                title_index -= 1
            elif command in [13, 32]:  #RETURN, #SPACE
                selection = title_list[title_index][0]
                break
            title_index %= len(title_list)
            game.screen.rectangle((2,24,73,29))
            game.screen.text(title_list[title_index][1], 35, title_list[title_index][0], 223)

    game.heroclass = selection
    game.screen.rectangle((1,1,73,38))
    return


def text_wrapper(game, s, x, y):  #custom text wrapper function for Console
    s = s.strip()
    s = s.split(" ")
    line = ""
    line_count = 0
    for i in range(len(s)):
        if len(line + s[i]) < 68:
            line = line + s[i] + " "
        else:
            game.screen.text(x, y+line_count, line)
            line_count += 1
            line = s[i] + " "
    game.screen.text(x, y+line_count, line)
    return line_count + y + 2

def get_hero_name(game, y):  #turns out you can't type to Console very easily
    c_count = 0
    hero_name = ""
    while 1:
        input = getch()
        if 97 <= ord(input) <= 122 or 65 <= ord(input) <= 90:
            hero_name = hero_name + input
            game.screen.text(2 + c_count,y, input)
            c_count += 1
            game.screen.pos(2 + c_count, y)
        elif ord(input) == 13 and len(hero_name) > 2:
            return hero_name
        elif ord(input) == 8 and len(hero_name) > 0:
            hero_name = hero_name[:-1]
            game.screen.text(2 + c_count-1,y, " ")
            c_count -= 1
            game.screen.pos(2 + c_count, y)
        else:
            pass

def display_intro(game, text):
    game.screen.rectangle((1,1,73,38))
    text = game.text[text].value
    lines = 1
    for t in text.splitlines():
        if "$s" in t:                         #the intros are stored as text in xml. these codes allow it to contain
            #self.play_sound(p.split()[1])     #more interesting things. $s = play sound. $m = play music.
            pass
        elif t == "$p":
            getch()
        else:
            lines = text_wrapper(game, t, 2, lines)
    game.screen.rectangle((1,1,73,38))
    return

