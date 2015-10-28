"""
Project Roguenaissance 2.0 - Pygame/Pygcurses
by William Hardy Gest
"""

import RN2_battle_io
import RN2_initialize
import RN2_UI
import pygame.event
import pygame.mixer
import pickle

class RN_Sound():
    def __init__(self, sound, music):
        self.mute_switch = False
        self.sound = sound
        self.music = music
        pygame.mixer.init()

    def play_music(self, music_ident, queue=False):
        if music_ident == "mute":
            pygame.mixer.music.stop()
            return
        if queue:
            pygame.mixer.music.queue("sound/" + self.music[music_ident])
            return
        else:
            pygame.mixer.music.load("sound/" + self.music[music_ident])

        if not self.mute_switch:
            pygame.mixer.music.play()
            return

    def check_music(self):
        return pygame.mixer.music.get_busy()

    def cut_music(self):
        pygame.mixer.music.stop()

    def play_sound(self, sound_ident):
        sound = pygame.mixer.Sound("sound/" + self.sound[sound_ident])
        if not self.mute_switch:
            sound.play()

class Game():
    def __init__(self):
        self.bindings = RN2_initialize.set_binds()
        self.battles = RN2_initialize.make_battle(RN2_initialize.open_xml("battles"))
        self.heroclasses, self.actors = RN2_initialize.make_actor(RN2_initialize.open_xml("actors"))
        self.skills = RN2_initialize.make_skills(RN2_initialize.open_xml("skills"))
        self.maps = RN2_initialize.make_maps(RN2_initialize.open_xml("maps"))
        self.text = RN2_initialize.make_text(RN2_initialize.open_xml("text"))
        self.sound, self.music = RN2_initialize.make_sound(RN2_initialize.open_xml("sound"))
        self.RN_UI = RN2_UI.RN_UI_Class()
        self.RN_sound = RN_Sound(self.sound, self.music)
        self.hero = None
        self.num_battles = 3

    def init_battle(self, ident):
        battle = self.battles[ident]
        battle_controller = RN2_battle_io.Battle_Controller(self.hero, battle, self.maps[battle["map"]], self.RN_UI,
                                                            self.RN_sound, self.skills, self.actors, self.RN_input)
        victory = battle_controller.init_battle()
        if victory:
            return True
        else:
            return False

    def init_hero(self, heroclass, name):
        heroclass = self.heroclasses[heroclass]
        self.hero = RN2_initialize.Hero(heroclass, name)
        self.hero.hclass = heroclass

    def load_saved_hero(self, saved_hero):
        self.hero = RN2_initialize.Hero(saved_hero['hclass'], saved_hero['name'])
        self.hero.hclass = saved_hero['hclass']
        self.hero.score = saved_hero['score']
        self.hero.current_battle = saved_hero['current_battle']

    def auto_save(self):
        save_data = {}

        save_data['hclass'] = self.hero.hclass
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
                self.RN_sound.play_music("mute")
            else:
                pass
                #turn correct music on
            return self.RN_input()

        return command




def main():
    #test mode
    # game = Game()
    # game.init_hero("Astromancer", "StrongoDragonlord")
    # game.hero.mp = 99
    # game.hero.hp = 999
    # game.init_battle("1")
    # exit()

    while 1:
        game = Game()
        done = 0
        game.RN_sound.play_music("title")
        while not done:
           done, load, hero = game.RN_UI.title_screen(game.maps["title"], game.RN_input, game.RN_sound)
        if not load:
           game.RN_UI.display_intro(game.text["intro"].value)
           name, hclass = game.RN_UI.create_character(game.text["Name"].value, game.text["Class"].value,
               {"Astromancer": game.text["Astromancer"].value,
                "Pyromancer": game.text["Pyromancer"].value,
                "Terramancer": game.text["Terramancer"].value}, game.RN_input, game.RN_sound)
           game.init_hero(hclass, name)
           game.auto_save()
        else:
            with open(hero) as fin:
                saved_hero = pickle.load(fin)
                game.load_saved_hero(saved_hero)

        while 1:
            game.RN_sound.play_music("trans")
            game.RN_UI.display_intro(game.text["battle" + str(game.hero.current_battle)].value)
            victory = game.init_battle(str(game.hero.current_battle))
            if not victory:
                break
            game.hero.current_battle += 1
            if game.hero.current_battle > game.num_battles:
                game.RN_sound.play_music("ending")
                game.RN_UI.display_ending(game.RN_input, game.hero)
                break
            game.auto_save()
    exit()

if __name__ == "__main__":
    main()


