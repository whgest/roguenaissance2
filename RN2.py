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
        self.saved_data = None
        self.persistent_actor = None
        self.num_battles = 3

    def init_battle(self, ident):
        battle_data = copy.deepcopy(self.battles[ident])
        map_raw = self.maps[(battle_data.get('map'))]
        bmap = RN2_loadmap.load_map(map_raw)

        io = RN2_battle_io.BattleController(self.ui, self.sound_handler, self.input)
        battle_class = RN2_battle.Battle(battle_data, self.actors, self.skills, bmap, io, persistent_actor=self.persistent_actor)
        victory = battle_class.battle()

        if victory:
            return True
        else:
            return False

    def new_game(self, class_name, name):
        self.saved_data = SaveGame({'saved_character': {'class_name': class_name, 'name': name}})
        self.persistent_actor = self.saved_data.saved_character

    def load_saved_game(self, saved_data):
        self.saved_data = SaveGame(saved_data)
        self.persistent_actor = self.saved_data.saved_character

    def auto_save(self):
        fin = open(self.saved_data.saved_character.name + ".sav", 'w')
        pickle.dump(self.saved_data.dehydrate(), fin)
        fin.close()

    def input(self):
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
            return 99

        if command == "exit":
            exit()
        if command == "mute":
            self.sound_handler.mute_switch = not self.sound_handler.mute_switch

            if self.sound_handler.mute_switch:
                self.sound_handler.cut_music()
            else:
                self.sound_handler.deactivate_mute_switch()

        return command


class SaveData(object):
    def __init__(self, data):
        for k in data.keys():
            setattr(self, k, data.get(k))

    def dehydrate(self):
        #copy attrs and create a pickleable dictionary, recursively
        dehydrated = dict(self.__dict__)
        for k in dehydrated.keys():
            if hasattr(dehydrated[k], 'dehydrate'):
                dehydrated[k] = dehydrated[k].dehydrate()

        return dehydrated


class SavedCharacter(SaveData):
    def __init__(self, data):
        self.name = None
        self.class_name = None
        SaveData.__init__(self, data)


class SavedScore(SaveData):
    def __init__(self, data):
        self.turns_taken = 0
        self.damage_taken = 0
        self.enemies_killed = 0
        SaveData.__init__(self, data)


class SaveGame(SaveData):
    def __init__(self, data):
        self.current_battle = 1
        SaveData.__init__(self, data)
        self.saved_character = SavedCharacter(data.get('saved_character'))
        self.score = SavedScore(data.get('score', {}))


def main():
    #test mode
    game = Game()
    game.sound_handler.mute_switch = True
    game.new_game('Terramancer', "Flayk")
    game.init_battle(1)
    exit()

    while 1:
        game = Game()
        done = False
        game.sound_handler.mute_switch = True
        game.sound_handler.play_music("title")
        load = False
        hero = None

        while not done:
            done, load, hero = game.ui.title_screen(game.maps["title"], game.input, game.sound_handler)

        if not load:
            game.ui.display_intro(game.text["intro"])
            name, hclass = game.ui.create_character(game.text["Name"], game.text["Class"],
               {"Astromancer": game.text["Astromancer"],
                "Pyromancer": game.text["Pyromancer"],
                "Terramancer": game.text["Terramancer"]}, game.input, game.sound_handler)
            game.new_game(hclass, name)
            game.auto_save()
        else:
            with open(hero) as fin:
                saved_hero = pickle.load(fin)
                game.load_saved_game(saved_hero)

        while 1:
            game.sound_handler.play_music("trans")
            game.ui.display_intro(game.text["battle" + str(game.saved_data.current_battle)])
            victory = game.init_battle(game.saved_data.current_battle)
            if not victory:
                retry = game.ui.display_game_over(game.maps["gameover"], game.battles[game.saved_data.current_battle]['tips'], game.input, game.sound_handler)
                if not retry:
                    break
                else:
                    continue
            game.saved_data.current_battle += 1
            if game.saved_data.current_battle > game.num_battles:
                game.sound_handler.play_music("ending")
                game.ui.display_ending(game.input, game.saved_data, game.text['ending'])
                break
            game.auto_save()


if __name__ == "__main__":
    main()


