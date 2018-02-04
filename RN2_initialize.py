# -*- coding: utf-8 -*-

import math
import yaml
import random
from RN2_battle_logic import get_neighboring_points, add_points
import pyromancer_tree
from RN2_event import EventQueue, DamageOrHeal, GoodStatus, BadStatus, GoodStatusEnds, BadStatusEnds, StatusDamageOrHeal, IsDisabled, ImmuneToStatus, KillUnit
import itertools
import peerless_ai
import redoubtable_ai
import copy

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

F1 = 'F1'
F2 = 'F2'
F3 = 'F3'
F4 = 'F4'
F5 = 'F5'
F6 = 'F6'
F7 = 'F7'
F8 = 'F8'
F9 = 'F9'
F10 = 'F10'
F11 = 'F11'
F12 = 'F12'

#actions
ACTIVATE = 0
CANCEL = 1
PASS_TURN = 2
HELP_MENU = 3
STATUS_DISPLAY = 4
SKILLS_MENU = 5
LEGEND = 6
BATTLE_OVERVIEW = 7
MUTE_SOUND = 8
EXIT = 9
DOWN = 10
LEFT = 11
RIGHT = 12
UP = 13
INVALID = 99

ABBREVIATIONS = {
    'attack': 'ATK',
    'defense': 'DEF',
    'move': 'MOV',
    'magic': 'MAG',
    'resistance': "RES",
    'agility': "AGI"
}

#
# class ModifiableAttribute(object):
#     def __init__(self, name):
#         self.base_stat = 0
#         self.name = name
#         self.attribute_modifiers = {}
#         self.data = {}
#
#     def __get__(self, instance, owner):
#         return self.get_modified_value(instance)
#
#     def __set__(self, instance, value):
#         self.data[instance] = value[0]
#         if not self.attribute_modifiers:
#             self.attribute_modifiers = value[1]
#
#     def get_modified_value(self, instance):
#         base_stat = self.data[instance]
#
#         # modifiers do not stack: only the highest positive and negative ones are used
#         mods = instance.attribute_modifiers[self.name]
#
#         mods.sort(reverse=True)
#
#         try:
#             # positive and negative mods present, take strongest of each
#             if mods[0] * mods[-1] < 0:
#                 total_modifier = mods[0] + mods[-1]
#             else:
#                 # only strongest takes effect
#                 mods.sort(key=lambda x: abs(x), reverse=True)
#                 total_modifier = mods[0]
#         except IndexError:
#             total_modifier = 0
#
#         return base_stat + total_modifier
#
#
# class ModifiableMoveAttribute(ModifiableAttribute):
#     def __init__(self, name):
#         ModifiableAttribute.__init__(self, name)
#
#     def get_modified_value(self, instance):
#         if instance.attribute_modifiers['rooted']:
#             return 0
#         else:
#             return super(ModifiableMoveAttribute, self).get_modified_value(instance)





class Actor(object):
    MODIFIABLE_ATTRIBUTES = ["maxhp", "maxmp", "attack", "defense", "magic", "resistance", "agility",
                             "move", "rooted"]

    def __deepcopy__(self, memo):
        deepcopy_method = self.__deepcopy__
        event = self.event
        ai_class = self.ai_class
        ai = self.ai

        self.event = None
        self.ai_class = None
        self.ai = None

        self.__deepcopy__ = None
        cp = copy.deepcopy(self, memo)
        self.__deepcopy__ = deepcopy_method

        self.event = event
        self.ai_class = ai_class
        self.ai = ai
        return cp

    def __init__(self, data, name, event=None):
        self.id = 0
        self.character = data.get('character')
        self.immunities = data.get('immunities', [])
        self.innate_status = data.get('innate_status', [])
        self.ai = data.get('ai', 'player')
        self.skillset = data.get('skillset', [])

        self.active_status_effects = []
        self.attribute_modifiers = {}

        for attribute in self.MODIFIABLE_ATTRIBUTES:
            base_value = data.get(attribute, 0)

            setattr(self, "base_" + attribute, base_value)

            self.attribute_modifiers[attribute] = []

        self.hp = int(getattr(self, 'base_maxhp'))
        self.mp = self.set_base_mp()
        self.coords = 0
        self.death_animation = data.get('death_animation', 'deathanim')
        self.name = name
        self.team_id = 0
        self.is_dead = 0
        self.is_minion = data.get('is_minion', False)

        self.ai_class = redoubtable_ai.RedoubtableAi

        self.event = event
        self.summoned_by = data.get('summoned_by', None)

        if self.innate_status:
            for status in self.innate_status:
                self.apply_status(SkillStatusEffect(status, 'Innate'))


    @property
    def maxhp(self):
        return max(0, self.base_maxhp + self.get_modifier_for_stat("maxhp"))

    @property
    def maxmp(self):
        return max(0, self.base_maxmp + self.get_modifier_for_stat("maxmp"))

    @property
    def attack(self):
        return max(0, self.base_attack + self.get_modifier_for_stat("attack"))

    @property
    def defense(self):
        return max(0, self.base_defense + self.get_modifier_for_stat("defense"))

    @property
    def magic(self):
        return max(0, self.base_magic + self.get_modifier_for_stat("magic"))

    @property
    def resistance(self):
        return max(0, self.base_resistance + self.get_modifier_for_stat("resistance"))

    @property
    def agility(self):
        return max(0, self.base_agility + self.get_modifier_for_stat("agility"))

    @property
    def move(self):
        if self.get_modifier_for_stat("rooted"):
            return 0
        else:
            return max(0, self.base_move + self.get_modifier_for_stat("move"))

    def current_state(self):
        state = {}
        stats = list(['active_status_effects', 'attribute_modifiers', 'hp', 'mp', "coords", "is_dead"])
        for stat in stats:
            state[stat] = getattr(self, stat)

        return state

    def set_state(self, state):
        for k, v in state.items():
            setattr(self, k, v)

    def get_modifier_for_stat(self, stat):
        mods = self.attribute_modifiers[stat]
        mods.sort(reverse=True)

        try:
            # positive and negative mods present, take strongest of each
            if mods[0] * mods[-1] < 0:
                total_modifier = mods[0] + mods[-1]
            else:
                # only strongest takes effect
                mods.sort(key=lambda x: abs(x), reverse=True)
                total_modifier = mods[0]
        except IndexError:
            total_modifier = 0

        return total_modifier

    def __repr__(self):
        return self.name + "@" + hex(id(self))

    def display(self):
        return self.character

    def is_hostile_to(self, unit):
        return not unit.team_id == self.team_id

    def is_ally_of(self, unit):
        return unit.team_id == self.team_id

    @property
    def is_player_controlled(self):
        return self.ai == 'player'

    def inflict_damage_or_healing(self, raw_damage, skill_name):
        #healing is negative damage
        self.hp -= raw_damage
        if self.hp > self.maxhp:
            self.hp = self.maxhp
        if self.hp <= 0:
            self.kill_actor()

        if raw_damage:
            self.event.add_event(DamageOrHeal(self, raw_damage, skill_name))

    def clear_attribute_modifiers(self):
        for attr in self.MODIFIABLE_ATTRIBUTES:
            self.attribute_modifiers[attr] = []

    def clear_status(self):
        self.active_status_effects = []

    def set_base_mp(self):
        return max(0, int(math.floor(self.base_maxmp / 2) - 1))

    def increment_mp(self):
        if self.mp < self.maxmp:
            self.mp += 1

    def reset_actor(self):
        self.clear_attribute_modifiers()
        self.clear_status()
        self.hp = self.maxhp
        self.mp = self.set_base_mp()
        self.is_dead = False

    def kill_actor(self):
        self.clear_attribute_modifiers()
        self.clear_status()
        self.hp = 0
        self.is_dead = True

    def is_disabled(self):
        disabling_effects = [effect for effect in self.active_status_effects if effect.status_effect.lose_turn]
        is_disabled = disabling_effects[0].status_effect.type if len(disabling_effects) else False
        if is_disabled:
            self.event.add_event(IsDisabled(self, disabling_effects[0].status_effect.type))
        return is_disabled

    def initiate_turn(self):
        self.tick_continuous_status()
        self.decrement_status_durations()
        self.increment_mp()

    @property
    def can_act(self):
        return not self.is_disabled()and not self.is_dead

    def calculate_move_range(self, bmap, origin=None, modifier=0):
        if not origin:
            origin = self.coords
        origin = tuple(origin)
        all_tiles = {origin}
        edges = {origin}
        for m in range(self.move + modifier):
            edge_neighbors = set()
            for t in edges:
                edge_neighbors.update(get_neighboring_points(t))

            all_tiles.update(edges)
            new_edges = edge_neighbors.difference(all_tiles)

            edges = set()
            for t in new_edges:
                if bmap.check_bounds(t) and bmap.get_tile_at(t).is_movable:
                    edges.add(t)

        all_tiles.update(edges)
        return all_tiles

    @property
    def priority_value(self):
        try:
            return self.attack + self.magic + len(self.skillset) * (3 * (1 + (1-(self.maxhp / self.hp))))
        except ZeroDivisionError:
            return 0

    def apply_status(self, status):
        if status.type not in self.immunities:
            self.active_status_effects.append(AppliedStatusEffect(status, status.duration))

            for modifier in status.modifiers:
                if not modifier.continuous:
                    self.apply_status_modifier(modifier)

            if status.is_beneficial:
                self.event.add_event(GoodStatus(self, status.name))
            else:
                self.event.add_event(BadStatus(self, status.name))
        else:
            self.event.add_event(ImmuneToStatus(self, status.type))

    def apply_status_modifier(self, modifier):
        attribute = modifier.stat
        change = modifier.value

        if attribute in self.attribute_modifiers:
            self.attribute_modifiers.get(attribute).append(change)

    def tick_continuous_status(self):
        for active in self.active_status_effects:
            for modifier in active.status_effect.modifiers:
                if modifier.continuous:
                    self.apply_status_modifier(modifier)
                    #todo: continuous stat damage event

        #tick only the strongest damage effect for each type
        keyfunc = lambda x: x.type
        all_dot_effects = [e.status_effect for e in self.active_status_effects if e.status_effect.damage]

        #force healing effects to tick last
        all_dot_effects.sort(key=lambda x: x.damage, reverse=True)

        if len(all_dot_effects):
            for key, group in itertools.groupby(all_dot_effects, keyfunc):
                effects_of_type = list(group)
                effects_of_type.sort(key=lambda x: x.damage)
                strongest_effect_for_type = effects_of_type.pop()
                self.inflict_damage_or_healing(strongest_effect_for_type.damage, strongest_effect_for_type.type)
                self.event.overwrite_last_event(StatusDamageOrHeal(self, strongest_effect_for_type.damage, strongest_effect_for_type.type))

        if self.hp <= 0:
            self.kill_actor()

    def decrement_status_durations(self):
        for active in self.active_status_effects:
            if active.status_effect.expires:
                active.remaining_duration -= 1

        for active in self.active_status_effects:
            if active.remaining_duration <= 0:
                self.remove_status(active)

    def remove_status(self, applied_status):
        status = applied_status.status_effect
        for modifier in status.modifiers:
            if modifier.expires:
                attribute = modifier.stat
                change = modifier.value

                self.attribute_modifiers[attribute].remove(change)

        self.active_status_effects.remove(applied_status)

        # only display the 'status ends' event if this was the last active effect of this type
        if not len([s for s in self.active_status_effects if s.status_effect.type == status.type]):
            if applied_status.status_effect.is_beneficial:
                self.event.add_event(GoodStatusEnds(self, applied_status.status_effect.name))
            else:
                self.event.add_event(BadStatusEnds(self, applied_status.status_effect.name))


class StandardDamage:
    def __init__(self, data, ident, attack_stat, defense_stat):

        self.attack_stat = attack_stat
        self.defense_stat = defense_stat
        self.no_damage = True if not data else False
        self.type = "Damage"

        if data:
            self.fixed_damage = data.get('fixed_damage', 0)
            self.num_dice = data.get('num_dice', 0)
            self.dice_size = data.get('dice_size', 0)
            self.stat_modify = data.get('stat_modify', True)

            if (self.num_dice and not self.dice_size) or (self.dice_size and not self.num_dice):
                print "Skill {0} must have both num_dice and dice_size to use randomized damage.".format(ident)
                raise ValueError

            if self.fixed_damage and (self.num_dice or self.dice_size):
                print "Skill {0} can not have both fixed and randomized damage.".format(ident)
                raise ValueError

    def get_damage_range(self, attacker):
        """
        Return tuple represented minimum and maximum damage

        Damage formula for all skills is (skillStat / 3) + defined dice rolls num_dice, dice_size, (ie 2,6 is 2d6 or the
        cumulative result of 2 separate six sided dice rolls)
        """
        if self.no_damage:
            return 0, 0

        negative_multiplier = -1 if self.dice_size < 0 or self.fixed_damage < 0 else 1
        stat_modifier = negative_multiplier * (getattr(attacker, self.attack_stat)/3) if self.attack_stat and self.stat_modify else 0

        if self.fixed_damage:
            return self.fixed_damage, self.fixed_damage
        else:
            return negative_multiplier * (stat_modifier + self.num_dice), negative_multiplier * (self.dice_size * self.num_dice + stat_modifier)

    def get_minimum_damage(self, attacker):
        return self.get_damage_range(attacker)[0]

    def get_maximum_damage(self, attacker):
        return self.get_damage_range(attacker)[1]

    def get_average_damage(self, attacker):
        return sum(self.get_damage_range(attacker)) / 2

    def roll_damage(self, attacker, defender, use_random=True):
        if use_random:
            damage_range = self.get_damage_range(attacker)
            return random.choice(range(damage_range[0], damage_range[1] + 1))
        else:
            return self.get_average_damage(attacker)


class DrainDamage(StandardDamage):
    def __init__(self, data, ident, attack_stat, defense_stat):
        StandardDamage.__init__(self, data, ident, attack_stat, defense_stat)
        self.name = ident
        self.type = "Drain"

    def roll_damage(self, attacker, defender, use_random=True):
        if use_random:
            inflicted_damage = min(StandardDamage.roll_damage(self, attacker, defender), defender.hp)
        else:
            inflicted_damage = min(StandardDamage.get_average_damage(self, attacker), defender.hp)

        attacker.inflict_damage_or_healing(inflicted_damage * -1, self.name)

        return inflicted_damage


class SelfDestructDamage(StandardDamage):
    def __init__(self, data, ident, attack_stat, defense_stat):
        StandardDamage.__init__(self, data, ident, attack_stat, defense_stat)
        self.name = ident
        self.type = "Self Destruct"

    def roll_damage(self, attacker, defender, use_random=True):
        if use_random:
            inflicted_damage = min(StandardDamage.roll_damage(self, attacker, defender), defender.hp)
        else:
            inflicted_damage = min(StandardDamage.get_average_damage(self, attacker), defender.hp)

        attacker.kill_actor()

        return inflicted_damage

class LineAttack():
    def get_next_aoe_range(self, all_tiles, edges, caster_loc):
        def negative_coords(coords):
            return coords[0] * -1, coords[1] * -1

        if edges:
            last_line_tile = list(edges)[-1]
        else:
            return all_tiles, []

        #Subtract caster loc from last_line_tile to determine direction
        point_diff = add_points(last_line_tile, negative_coords(caster_loc))
        if point_diff[0]:
            direction = (point_diff[0] / abs(point_diff[0]), 0)
        elif point_diff[1]:
            direction = (0, point_diff[1] / abs(point_diff[1]))
        else:
            direction = (0, 0)

        next_point = add_points(last_line_tile, direction)

        new_edges = [next_point]
        return all_tiles, new_edges


class CircularAttack():
    def get_next_aoe_range(self, all_tiles, edges, _):
        edge_neighbors = set()
        for t in edges:
            edge_neighbors.update(get_neighboring_points(t))

        all_tiles.update(edges)
        new_edges = edge_neighbors.difference(all_tiles)
        return all_tiles, new_edges


class ConeAttack():
    def get_next_aoe_range(self, all_tiles, edges, caster_loc):
        def negative_coords(coords):
            return coords[0] * -1, coords[1] * -1

        if edges:
            last_line_tile = list(list(edges)[-1])
        else:
            return all_tiles, []

        #Subtract caster loc from last_line_tile to determine direction
        point_diff = add_points(last_line_tile, negative_coords(caster_loc))
        if point_diff[0]:
            direction = (point_diff[0] / abs(point_diff[0]), 0)
        elif point_diff[1]:
            direction = (0, point_diff[1] / abs(point_diff[1]))
        else:
            direction = (0, 0)

        next_points = []
        step = max(1, int((len(edges)/2.0) + 0.5))

        for i in range(step):
            along_x = (direction[0])
            along_y = (direction[1])
            if along_y:
                next_points.append(add_points(last_line_tile, add_points(direction, (i+1, 0))))
                next_points.append(add_points(last_line_tile, add_points(direction, (-i-1, 0))))
            if along_x:
                next_points.append(add_points(last_line_tile, add_points(direction, (0, i + 1))))
                next_points.append(add_points(last_line_tile, add_points(direction, (0, -i - 1))))

        next_points.append(add_points(last_line_tile, direction))
        new_edges = next_points
        return all_tiles, new_edges

AOE_TYPES = {
    'line': LineAttack,
    'circular': CircularAttack,
    'cone': ConeAttack
}

DAMAGE_TYPES = {
    'standard': StandardDamage,
    'drain': DrainDamage,
    'self_destruct': SelfDestructDamage
}

DEFAULT_DEFENSE_STATS = {
    'attack': 'defense',
    'magic': 'resistance'
}


class SkillMoveEffect:
    def __init__(self, data):
        self.type = data.get('type', 'push')
        self.origin = data.get('origin', 'user')
        self.distance = data.get('distance')
        self.instant = data.get('instant', False)

    @property
    def description(self):
        preposition = 'from' if self.type is 'push' else 'to'
        return '{0} {1} {2} {3}'.format(self.type.capitalize(), self.distance, preposition, self.origin)


class SkillStatusEffectModifier:
    def __init__(self, data):
        self.stat = data['stat']
        self.value = data['value']
        self.expires = data.get('expires', True)
        self.continuous = data.get('continuous', False)

    @property
    def description(self):
        if self.value > 0:
            arrow = u'▲'
        else:
            arrow = u'▼'
        return u'({0} {1} {2})'.format(ABBREVIATIONS[self.stat], arrow, abs(self.value))

    @property
    def is_beneficial(self):
        return True if self.value > 0 else False


class AppliedStatusEffect:
    def __init__(self, status, duration):
        self.status_effect = status
        self.remaining_duration = duration

    @property
    def display(self):
        descriptions = []

        for d in self.status_effect.modifier_descriptions:
            r = {}
            r['text'] = d['text'][:-3] + u' {}t'.format(self.remaining_duration)
            r['is_beneficial'] = d['is_beneficial']
            descriptions.append(r)
        return descriptions

    def __repr__(self):
        return self.status_effect.type + ' ' + str(self.remaining_duration)


class SkillStatusEffect:
    def __init__(self, data, skill_ident):
        self.type = data.get('type')
        self.name = data.get('name', self.type)
        if not self.name:
            self.name = skill_ident

        self.duration = data.get('duration', 1)
        self.lose_turn = data.get('lose_turn', False)
        self.damage = data.get('damage', 0)
        self.expires = data.get('expires', True)

        self.modifiers = []
        for m in data.get('modifiers', []):
            self.modifiers.append(SkillStatusEffectModifier(m))

    @property
    def modifier_descriptions(self):
        descriptions = []
        if self.lose_turn:
            descriptions.append(
                {'text': 'for {}t'.format(self.duration), 'is_beneficial': False})
        if self.damage:
            descriptions.append({'text': 'for {0} HP {1}t'.format(abs(self.damage), self.duration), 'is_beneficial': (self.damage < 0)})
        for modifier in self.modifiers:
            descriptions.append({'text': u'{0} {1}t'.format(modifier.description, self.duration), 'is_beneficial': modifier.is_beneficial})

        return descriptions

    def __str__(self):
        return self.type

    @property
    def is_beneficial(self):
        count = 0
        for m in self.modifiers:
            count += m.value

        return True if count >= 0 and not self.lose_turn and self.damage <= 0 else False


class SkillEffectForTargetType:
    def __init__(self, target_type_data, ident):
        self.ignored = target_type_data.get('ignored', False)
        self.damage_type = target_type_data.get('damage_type', 'standard')
        self.is_resistable = target_type_data.get('is_resistable', True)
        self.attack_stat = target_type_data.get('attack_stat')
        self.defense_stat = target_type_data.get('defense_stat')
        if self.attack_stat and not self.defense_stat:
            self.defense_stat = DEFAULT_DEFENSE_STATS[self.attack_stat]

        self.damage = DAMAGE_TYPES[self.damage_type](target_type_data.get('damage'), ident, self.attack_stat, self.defense_stat)

        self.status_effects = []
        for s in target_type_data.get('status_effects', []):
            self.status_effects.append(SkillStatusEffect(s, ident))

        self.move_effects = []
        for m in target_type_data.get('move_effects', []):
            self.move_effects.append(SkillMoveEffect(m))

        self.add_units = []

    def get_hit_chance(self, attacker, defender):
        """
        To hit formula for all hostile skills is (skillStat/2) + (random integer between 0 and skillStat) vs. defenseStat
        The below equation gets success chance, hopefully
        """
        if not self.attack_stat:
            return 100

        defending_stat = self.defense_stat

        hit_numerator = (getattr(attacker, self.attack_stat) - getattr(defender, defending_stat)) + (getattr(attacker, self.attack_stat) / 2.0)
        hit_denominator = getattr(attacker, self.attack_stat)

        hit_chance = (hit_numerator / hit_denominator) * 100.0
        hit_chance = min(100, round(hit_chance, 1))

        if hit_chance == 0 or hit_chance == 100:
            hit_chance = int(hit_chance)

        return max(0, hit_chance)

    def attack_roll(self, attacker, defender):
        stat = getattr(attacker, self.attack_stat)
        defense = getattr(defender, self.defense_stat)
        random_roll = random.randint(0, stat)
        attack_roll = (stat / 2) + random_roll
        if attack_roll >= defense:
            return True
        else:
            return False

    @property
    def is_harmful(self):
        """
        A method for AI to determine whether a skill effect is totally harmful and can be skipped for eval on friendly targets
        """
        healing = self.damage and (getattr(self.damage, 'dice_size', 0) < 0 or getattr(self.damage, 'fixed_damage', 0) < 0)
        healing_over_time = len([s for s in self.status_effects if s.damage and s.damage < 0])
        stat_boosts = len([s for s in self.status_effects if s.modifiers and len([m for m in s.modifiers if m.value > 0])])

        return not healing and not healing_over_time and not stat_boosts


class TargetTypes:
    def __init__(self, targets, data, ident):
        enemy_data = dict(data) #copy default data
        enemy_data.update(targets.get('enemy', {}))
        self.enemy = SkillEffectForTargetType(enemy_data, ident)

        friendly_data = dict(data)
        friendly_data.update(targets.get('friendly', enemy_data))
        self.friendly = SkillEffectForTargetType(friendly_data, ident)

        self_data = dict(data)
        self_data.update(targets.get('self', friendly_data))
        self.self = SkillEffectForTargetType(self_data, ident)

        self.special_friendly_effect = bool(targets.get('friendly', False))
        self.special_self_effect = bool(targets.get('self', False))


class Skill:
    def __init__(self, ident, data):
        self.ident = ident
        self.name = data.get('name', self.ident)

        self.range = data.get('range', 0)
        self.aoe_size = data.get('aoe_size', 0)
        self.aoe_type = data.get('aoe_type', 'circular')
        self.aoe = AOE_TYPES[self.aoe_type]()
        self.add_unit = data.get('add_unit', [])
        self.add_minion = data.get('add_minion', [])
        self.mp = data.get('mp', 0)
        self.mp_cost_type = data.get('mp_cost_type')
        self.prompt = data.get('prompt')
        self.animation = data.get('animation')
        self.targets = TargetTypes(data.get('targets', {}), data, self.ident)
        self.targets_empty = data.get('targets_empty', False)

    def __str__(self):
        return self.name if self.name else self.ident

    def __repr__(self):
        return self.name if self.name else self.ident

    @property
    def affects_enemies(self):
        return not self.targets.enemy.ignored and not self.targets_empty

    @property
    def affects_friendlies(self):
        return not self.targets.friendly.ignored and not self.targets_empty

    @property
    def affects_self(self):
        return not self.targets.self.ignored and not self.targets_empty

    @property
    def skill_prompt(self):
        prompt = self.prompt
        prompt += " Range: %s" % str(self.range)
        if self.aoe > 1:
            prompt += " Area: %s" % str(self.aoe_size).capitalize()

        return prompt


def make_actor():
    with open('actors.yaml') as actors:
        actors_data = yaml.load(actors)

    return actors_data['actors']

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
        skill_data = skills_data[skill_key]

        skill_object = Skill(skill_key, skill_data)

        skills_dict[skill_key] = skill_object
    return skills_dict


def make_sound():
    with open('sound.yaml') as sound:
        sound_data = yaml.load(sound)
        return sound_data['sound'], sound_data['music']

def set_binds():
    binds = {
        RET_KEY: ACTIVATE,
        A_KEY: ACTIVATE,
        ENT_KEY: ACTIVATE,
        ESC_KEY: CANCEL,
        BACKSPACE: CANCEL,
        SPACE_KEY: PASS_TURN,
        H_KEY: HELP_MENU,
        T_KEY: STATUS_DISPLAY,
        S_KEY: SKILLS_MENU,
        L_KEY: LEGEND,
        B_KEY: BATTLE_OVERVIEW,
        M_KEY: MUTE_SOUND,
        Q_KEY: EXIT,
        DOWN_ARROW: DOWN,
        LEFT_ARROW: LEFT,
        RIGHT_ARROW: RIGHT,
        UP_ARROW: UP,
        TWO_KEY: DOWN,
        FOUR_KEY: LEFT,
        SIX_KEY: RIGHT,
        EIGHT_KEY: UP
    }

    #add function keys
    for f in range(12):
        binds[281 + f] = "F" + str(f)

    return binds


