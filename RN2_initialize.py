"""
Roguenaissance 2.0 Game Initializer
"""


import os
import actors
import battles
import skills
import sound as sound_class
import maps
import text
import math
import yaml

#pygame input constants, NOT ASCII CODES

UP_ARROW = 273
DOWN_ARROW = 274
LEFT_ARROW = 276
RIGHT_ARROW = 275

ENT_KEY = 271
RET_KEY = 13
ESC_KEY = 27
SPACE_KEY = 32
BACKSPACE = 8

A_KEY = 97
B_KEY = 98
H_KEY = 104
L_KEY = 108
M_KEY = 109
S_KEY = 115
T_KEY = 116
Q_KEY = 113

TWO_KEY = 258
FOUR_KEY = 260
SIX_KEY = 262
EIGHT_KEY = 264

F1 = 282
F2 = 283
F3 = 284
F4 = 285
F5 = 286
F6 = 287
F7 = 288
F8 = 289
F9 = 290
F10 = 291
F11 = 292
F12 = 293

class ModifiableAttribute(object):
    def __init__(self, name):
        self.base_stat = 0
        self.name = name
        self.attribute_modifiers = {}
        self.data = {}

    def __get__(self, instance, owner):
        return self.get_modified_value(instance)

    def __set__(self, instance, value):
        self.data[instance] = value[0]
        if not self.attribute_modifiers:
            self.attribute_modifiers = value[1]

    def get_modified_value(self, instance):
        total_modifier = 0
        try:
            base_stat = self.data[instance]
        except KeyError:
            pass
        for modifier in instance.attribute_modifiers[self.name]:
            total_modifier += modifier
        return base_stat + total_modifier


class ModifiableMoveAttribute(ModifiableAttribute):
    def __init__(self, name):
        ModifiableAttribute.__init__(self, name)

    def get_modified_value(self, instance):
        if instance.attribute_modifiers['rooted']:
            return 0
        else:
            return super(ModifiableMoveAttribute, self).get_modified_value(instance)


class Actor(object):
    MODIFIABLE_ATTRIBUTES = ["maxhp", "maxmp", "attack", "defense", "magic", "resistance", "agility", "move", "stunned",
                             "rooted"]
    attribute_modifiers = {}
    maxhp = ModifiableAttribute("maxhp")
    maxmp = ModifiableAttribute("maxmp")
    attack = ModifiableAttribute("attack")
    defense = ModifiableAttribute("defense")
    magic = ModifiableAttribute("magic")
    resistance = ModifiableAttribute("resistance")
    agility = ModifiableAttribute("agility")
    move = ModifiableMoveAttribute("move")
    stunned = ModifiableAttribute("stunned")
    rooted = ModifiableAttribute("rooted")

    def __init__(self, stats):

        self.status = []
        self.attribute_modifiers = {}

        for attribute in self.MODIFIABLE_ATTRIBUTES:
            try:
                base_value = int(getattr(stats, attribute)[0].value)
            except AttributeError:
                base_value = 0
            setattr(self, "base_" + attribute, int(base_value))
            setattr(self, attribute, (base_value, self.attribute_modifiers))
            self.attribute_modifiers[attribute] = []

        self.hp = self.maxhp
        self.set_base_mp()

        self.ai = stats.ai[0].value
        self.immunities = stats.immunities[0].value.split(",")
        self.skillset = stats.skills[0].value.split(",")
        self.character = stats.character[0].value
        self.coords = 0
        self.enemy = True
        self.descr = stats.descr[0].value
        self.color = "red"
        self.is_boss = False
        self.death_animation = 'deathanim'

    def __str__(self):
        return self.character

    def display(self):
        return self.character, self.color

    def is_hostile(self, attacker):
        return not attacker.enemy == self.enemy

    def clear_attribute_modifiers(self):
        for attr in self.MODIFIABLE_ATTRIBUTES:
            self.attribute_modifiers[attr] = []

    def clear_status(self):
        self.status = []

    def set_base_mp(self):
        self.mp = int(math.floor(self.maxmp / 2) - 1)

    def reset_actor(self):
        self.clear_attribute_modifiers()
        self.clear_status()
        self.hp = self.maxhp
        self.set_base_mp()

    def kill_actor(self):
        self.clear_attribute_modifiers()
        self.clear_status()
        self.hp = 0


class Ally(Actor):
    def __init__(self, stats):
        Actor.__init__(self, stats)
        self.enemy = False
        self.color = "lime"


class Hero(Actor):
    def __init__(self, stats, name):
        Actor.__init__(self, stats)
        self.hclass = ""
        self.enemy = False
        self.weapon = stats.weapon[0].value
        self.armor = stats.armor[0].value
        self.color = stats.color[0].value
        self.name = name
        self.ai = "player"
        self.score = {"killed": 0,
                      "turns": 0,
                      "damage": 0}
        self.current_battle = 1
        self.class_name = "Mage"
        self.death_animation = 'playerdeath'


class Boss(Actor):
    def __init__(self, stats):
        Actor.__init__(self, stats)
        self.death_animation = stats.deathanim[0].value
        self.color = stats.color[0].value
        self.is_boss = True


class Skill(object):
    def __init__(self):
        self.ident = ""
        self.target = ""
        self.stat = ""
        self.range = 0
        self.aoe = 0
        self.damage = 0
        self.effect = []
        self.mp = 0
        self.prompt = ""
        self.animation = ""

    def __str__(self):
        return self.ident

    @property
    def is_beneficial(self):
        return self.damage == 0 or self.damage[1] < 0

    def get_damage_range(self, attacker):
        """
        Damage formula for all skills is (skillStat / 3) + defined dice rolls num_dice, dice_size, (ie 2,6 is 2d6 or the
        cumulative result of 2 separate six sided dice rolls)
        """
        damage = self.damage
        print damage
        if not damage:
            return

        num_dice = damage[0]
        dice_size = abs(damage[1])
        return (getattr(attacker, self.stat)/3) + num_dice, (getattr(attacker, self.stat)/3) + (num_dice * dice_size)

    def get_hit_chance(self, attacker, defender):
        """
        To hit formula for all hostile skills is (skillStat/2) + random integer between 0 and skillStat vs. defenseStat
        The below equation gets success chance, hopefully
        """
        defending_stat = 'resistance' if self.stat == 'magic' else 'defense'

        hit_numerator = (getattr(attacker, self.stat) - getattr(defender, defending_stat)) + (getattr(attacker, self.stat) / 2.0)
        hit_denominator = getattr(attacker, self.stat)

        hit_chance = (hit_numerator / hit_denominator) * 100.0
        hit_chance = round(hit_chance, 2)

        if hit_chance == 0 or hit_chance == 100:
            hit_chance = int(hit_chance)

        return hit_chance


def open_xml(filename):
    try:
        fin = open(filename + '.xml')
    except:
        print filename + ".xml missing from working directory."
        exit()
    xml_stream = fin.read()
    fin.close()
    return xml_stream

def make_actor(xml_stream):
    actors_dict = dict()
    hero_dict = dict()
    actor_data = actors.obj_wrapper(xml_stream)[1]
    for a in actor_data.actor:
        actors_dict[a.attrs[u'ident']] = a
    for h in actor_data.heroclass:
        hero_dict[h.attrs[u'ident']] = h
    return hero_dict, actors_dict

def make_maps():
    with open('maps.yaml') as maps:
        map_data = yaml.load(maps)
        return map_data

def make_text(xml_stream):
    text_dict = dict()
    text_data = text.obj_wrapper(xml_stream)[1]
    for m in text_data.text:
        text_dict[m.attrs[u'ident']] = m
    return text_dict

def make_battle():
    with open('battles.yaml') as battles:
        battle_data = yaml.load(battles)
        return battle_data

def make_skills(xml_stream):
    skills_dict = dict()
    skills_data = skills.obj_wrapper(xml_stream)[1]
    for a in skills_data.skill:
        skill = Skill()
        skill.target = a.target[0].value
        skill.stat = a.stat[0].value
        skill.range = int(a.range[0].value)
        skill.aoe = int(a.aoe[0].value)
        skill.prompt = a.prompt[0].value
        skill.animation = a.animation[0].value
        skill.ident = a.attrs[u'ident']
        skill.name = a.attrs[u'ident']
        if a.damage[0].value == "0":
            skill.damage = 0
        else:
            skill.damage = (int(a.damage[0].value.split(",")[0]), int(a.damage[0].value.split(",")[1])) #number of "dice", size of "dice"
        skill.effects = []
        if hasattr(a, "effect"):
            for e in a.effect:
                effect_attrs = {}
                effect_attrs["magnitude"] = 1
                effect_attrs["duration"] = None
                effect_attrs["modifiers"] = []
                effect_attrs["continuous"] = None
                effect_attrs["type"] = e.type[0].value
                if e.magnitude != []:
                    #TODO: Stop using magnitude for summon spells and delete this crap
                    try:
                        effect_attrs["magnitude"] = int(e.magnitude[0].value)
                    except ValueError:
                        effect_attrs["magnitude"] = e.magnitude[0].value
                if e.duration != []:
                    effect_attrs["duration"] = int(e.duration[0].value)
                if e.continuous != []:
                    effect_attrs["continuous"] = int(e.continuous[0].value)
                if e.modifier != []:
                    for modifier in e.modifier:
                        custom_modifier = modifier.value.split(',')
                        custom_modifier[1] = int(custom_modifier[1])
                        effect_attrs["modifiers"].append(custom_modifier)
                skill.effects.append(effect_attrs)
        skill.mp = int(a.mp[0].value)
        skills_dict[a.attrs[u'ident']] = skill
    return skills_dict


def make_sound():
    with open('sound.yaml') as sound:
        sound_data = yaml.load(sound)
        return sound_data['sound'], sound_data['music']

def set_binds():
    binds = {
        RET_KEY : "activate",
        A_KEY : "activate",
        ENT_KEY : "activate",
        ESC_KEY : "cancel",
        BACKSPACE : "cancel",
        SPACE_KEY : "pass",
        H_KEY : "help",
        T_KEY : "stats",
        S_KEY : "skills",
        L_KEY : "legend",
        B_KEY : "battle",
        M_KEY : "mute",
        Q_KEY : "exit",
        DOWN_ARROW : "down",
        LEFT_ARROW : "left",
        RIGHT_ARROW : "right",
        UP_ARROW : "up",
        TWO_KEY : "down",
        FOUR_KEY : "left",
        SIX_KEY : "right",
        EIGHT_KEY : "up"
    }

    #add function keys
    for f in range(12):
        binds[281 + f] = "F" + str(f)

    return binds