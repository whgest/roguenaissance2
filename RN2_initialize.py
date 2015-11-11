"""
Roguenaissance 2.0 Game Initializer
"""
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

    def __init__(self, stats, name):
        self.character = ''
        self.immunities = []
        self.always = []

        for key in stats:
            if key not in self.MODIFIABLE_ATTRIBUTES:
                setattr(self, key, stats[key])

        self.status = []
        self.attribute_modifiers = {}

        for attribute in self.MODIFIABLE_ATTRIBUTES:
            try:
                base_value = stats[attribute]
            except KeyError:
                base_value = 0
            setattr(self, "base_" + attribute, base_value)
            setattr(self, attribute, (base_value, self.attribute_modifiers))
            self.attribute_modifiers[attribute] = []

        self.hp = self.maxhp
        self.set_base_mp()
        self.coords = 0
        self.enemy = True
        self.color = "red"
        self.is_boss = False
        self.death_animation = 'deathanim'
        self.name = name

    def __str__(self):
        return self.name

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
    def __init__(self, stats, name):
        Actor.__init__(self, stats, name)
        self.enemy = False
        self.color = "lime"


class Hero(Actor):
    def __init__(self, stats, name):
        Actor.__init__(self, stats, name)
        self.hclass = ''
        self.enemy = False
        self.ai = "player"
        self.score = {"killed": 0,
                      "turns": 0,
                      "damage": 0}
        self.current_battle = 1
        self.class_name = "Mage"
        self.death_animation = 'playerdeath'
        self.color = stats['color']


class Boss(Actor):
    def __init__(self, stats, name):
        Actor.__init__(self, stats, name)
        self.death_animation = stats['deathanim']
        self.is_boss = True
        self.color = stats['color']


class Skill(object):
    AFFECTS_TEXT = {
        "enemy": "Enemies",
        "friendly": "Allies",
        "tile": "All",
        "empty": "",
        "self": "Self"
    }


    def __init__(self):
        self.ident = ""
        self.target = ""
        self.stat = ""
        self.range = 0
        self.aoe = 0
        self.damage = 0
        self.effects = []
        self.mp = 0
        self.prompt = ""
        self.animation = ""
        self.is_beneficial = 0

    def __str__(self):
        return self.ident

    def get_damage_range(self, attacker):
        """
        Damage formula for all skills is (skillStat / 3) + defined dice rolls num_dice, dice_size, (ie 2,6 is 2d6 or the
        cumulative result of 2 separate six sided dice rolls)
        """
        damage = self.damage
        if not damage:
            return

        if damage.get('fixed_damage'):
            return abs(damage.get('fixed_damage')), abs(damage.get('fixed_damage'))

        num_dice = damage['num_dice']
        dice_size = abs(damage['dice_size'])
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

    def get_average_damage(self, attacker):
        """
        For use in AI attack evaluation
        """
        attacker_stat = getattr(attacker, self.stat)
        return (attacker_stat/3) + (self.damage['num_dice'] * (self.damage['dice_size']/2))

    def get_skill_prompt(self):
        prompt = self.prompt
        prompt += " Range: %s" % str(self.range)
        if self.aoe > 1:
            prompt += " Area: %s" % str(self.aoe).capitalize()
        if self.AFFECTS_TEXT.get(self.target):
            prompt += " Affects: %s" % self.AFFECTS_TEXT.get(self.target)

        return prompt

def make_actor():
    with open('actors.yaml') as actors:
        actors_data = yaml.load(actors)

    return actors_data['classes'], actors_data['actors']

def make_maps():
    with open('maps.yaml') as maps:
        map_data = yaml.load(maps)
        return map_data

def make_text():
    with open('text.yaml') as text:
        text_data = yaml.load(text)
        return text_data

def make_battle():
    with open('battles.yaml') as battles:
        battle_data = yaml.load(battles)
        return battle_data

def make_skills():
    skills_dict = {}
    with open('skills.yaml') as skills:
        skills_data = yaml.load(skills)

    for skill_key in skills_data:
        skill_raw = skills_data[skill_key]
        skill_object = Skill()
        for key in skill_raw:
            setattr(skill_object, key, skill_raw[key])

        skill_object.name = skill_key
        for effect in skill_object.effects:
            if not effect.get('duration'):
                effect['duration'] = 0
            if not effect.get('magnitude'):
                effect['magnitude'] = 0
        skills_dict[skill_object.name] = skill_object
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