"""
Project Roguenaissance 2.0 - Pygame/Pygcurses
by William Hardy Gest
"""

import RN2_battle
import RN2_battle_io
import RN2_initialize
import RN2_UI
import RN2_loadmap
import pygame.event
import pygame.mixer
import pickle
import copy

class RN_Sound():
    def __init__(self, sound, music):
        self.mute_switch = False
        self.sound = sound
        self.music = music
        self.music_to_play = ''
        pygame.mixer.init()

    def play_music(self, music_ident, queue=False):
        if music_ident == "mute":
            pygame.mixer.music.stop()
            return

        if queue:
            # self.music_to_queue = music_ident
            # print 'queueing', self.music[music_ident]
            # pygame.mixer.music.queue("sound/" + self.music[music_ident])
            return
        else:
            self.music_to_play = music_ident

        if not self.mute_switch:
            pygame.mixer.music.load("sound/" + self.music[music_ident])
            pygame.mixer.music.play(-1)

    def cut_music(self):
        pygame.mixer.music.fadeout(100)

    def deactivate_mute_switch(self):
        pygame.mixer.music.load("sound/" + self.music[self.music_to_play])
        pygame.mixer.music.play()

    def play_sound(self, sound_ident):
        sound = pygame.mixer.Sound("sound/" + self.sound[sound_ident])
        if not self.mute_switch:
            sound.play()


class Game(object):
    def __init__(self):
        self.bindings = RN2_initialize.set_binds()
        self.battles = RN2_initialize.make_battle()
        self.actors = RN2_initialize.make_actor()
        self.skills = RN2_initialize.make_skills()
        self.maps = RN2_initialize.make_maps()
        self.text = RN2_initialize.make_text()
        self.sound, self.music = RN2_initialize.make_sound()
        self.sound_handler = RN_Sound(self.sound, self.music)
        self.ui = RN2_UI.RN_UI_Class(self.sound_handler)
        self.hero = None
        self.num_battles = 3

    def init_battle(self, ident):
        battle_data = copy.deepcopy(self.battles[ident])
        map_raw = self.maps[(battle_data.get('map'))]
        bmap = RN2_loadmap.load_map(map_raw)

        io = RN2_battle_io.Battle_Controller(self.ui, self.sound_handler)
        battle_class = RN2_battle.Battle(battle_data, self.actors, self.skills, bmap, io)
        victory = battle_class.battle()

        if victory:
            return True
        else:
            return False

    # def init_hero(self, class_name, name):
    #     heroclass = self.heroclasses[class_name]
    #     self.hero = RN2_initialize.Hero(heroclass, name)
    #     self.hero.class_name = class_name

    # def load_saved_hero(self, saved_hero):
    #     heroclass = self.heroclasses[saved_hero['class_name']]
    #     self.hero = RN2_initialize.Hero(heroclass, saved_hero['name'])
    #     self.hero.class_name = saved_hero['class_name']
    #     self.hero.score = saved_hero['score']
    #     self.hero.current_battle = saved_hero['current_battle']

    def auto_save(self):
        save_data = {}

        save_data['class_name'] = self.hero.class_name
        save_data['name'] = self.hero.name
        save_data['score'] = self.hero.score
        save_data['current_battle'] = self.hero.current_battle

        fin = open(self.hero.name + ".sav", 'w')
        pickle.dump(save_data, fin)
        fin.close()
        return

    def RN_input(self):
        command = None
        while 1:
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    command = e.key
            if command is not None:
                break
            import time
            time.sleep(.01)

        if command in self.bindings:
            command = self.bindings[command]
        else:
            return "invalid"

        if command == "exit":
            exit()
        if command == "mute":
            self.RN_sound.mute_switch = not self.RN_sound.mute_switch

            if self.RN_sound.mute_switch:
                self.RN_sound.cut_music()
            else:
                self.RN_sound.deactivate_mute_switch()

        return command




def main():
    #test mode
    game = Game()
    #game.sound_handler.mute_switch = True
    game.init_battle(4)
    exit()

    while 1:
        game = Game()
        done = 0
        game.sound_handler.play_music("title")
        while not done:
            done, load, hero = game.RN_UI.title_screen(game.maps["title"], game.RN_input, game.RN_sound)
        if not load:
           game.RN_UI.display_intro(game.text["intro"])
           name, hclass = game.RN_UI.create_character(game.text["Name"], game.text["Class"],
               {"Astromancer": game.text["Astromancer"],
                "Pyromancer": game.text["Pyromancer"],
                "Terramancer": game.text["Terramancer"]}, game.RN_input, game.RN_sound)
           game.init_hero(hclass, name)
           game.auto_save()
        else:
            with open(hero) as fin:
                saved_hero = pickle.load(fin)
                game.load_saved_hero(saved_hero)

        while 1:
            game.sound_handler.play_music("trans")
            game.ui.display_intro(game.text["battle" + str(game.hero.current_battle)])
            victory = game.init_battle(game.hero.current_battle)
            if not victory:
                game.hero.reset_actor()
                retry = game.ui.display_game_over(game.maps["gameover"], game.battles[game.hero.current_battle]['tips'], game.RN_input, game.RN_sound)
                if not retry:
                    break
                else:
                    continue
            game.hero.reset_actor()
            game.hero.current_battle += 1
            if game.hero.current_battle > game.num_battles:
                game.sound_handler.play_music("ending")
                game.ui.display_ending(game.RN_input, game.hero, game.text['ending'])
                break
            game.auto_save()


if __name__ == "__main__":
    main()


