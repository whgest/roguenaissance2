import pygame.time


class EventQueue(object):

    queue = []

    def add_event(self, event):
        EventQueue.queue.append(event)

    def clear(self):
        del EventQueue.queue[:]

    def overwrite_last_event(self, event):
        EventQueue.queue.pop()
        self.add_event(event)

    def __deepcopy__(self, memodict={}):
        pass


class BattleEvent(object):
    def report_entry(self):
        pass

    def display(self, ui):
        pass

    def animate(self, ui):
        pass


class MoveUnit(BattleEvent):
    def __init__(self, actor, path):
        BattleEvent.__init__(self)
        self.path = path
        self.actor = actor

    def display(self, ui):
        prev_coords = self.path[0]
        for move in self.path[1:]:
            ui.move_unit(prev_coords, move, self.actor)
            prev_coords = move
            pygame.time.wait(30)


class UseSkill(BattleEvent):
    def __init__(self, user, skill, affected_tiles):
        BattleEvent.__init__(self)
        self.skill = skill
        self.affected_tiles = affected_tiles
        self.user = user

    def report_entry(self):
        return {'_format': 'use_skill', 'unit': self.user, 'cause': self.skill.name}

    def animate(self, ui):
        ui.print_skill_announce(self.skill.name)
        ui.animate(self.affected_tiles, self.skill.animation, self.user)


class RemoveSkillAnnounce(BattleEvent):
    def __init__(self, skill):
        self.skill = skill
        BattleEvent.__init__(self)

    def animate(self, ui):
        ui.remove_skill_announce(self.skill.name)


class UpdateMap(BattleEvent):
    def __init__(self, battle_map):
        BattleEvent.__init__(self)
        self.battle_map = battle_map

    def display(self, ui):
        ui.update_map(self.battle_map)


class KillUnit(BattleEvent):
    def __init__(self, actor):
        BattleEvent.__init__(self)
        self.actor = actor

    def display(self, ui):
        ui.remove_unit(self.actor)

    def report_entry(self):
        return {'_format': 'death', 'unit': self.actor}

    def animate(self, ui):
        ui.animate([self.actor.coords], self.actor.death_animation, self.actor)


class KillUnitTerrain(KillUnit):
    def __init__(self, actor, terrain_name):
        KillUnit.__init__(self, actor)
        self.terrain_name = terrain_name

    def report_entry(self):
        return {'_format': 'terrain_kill', 'unit': self.actor, 'cause': self.terrain_name}

    def animate(self, ui):
        pass


class AddUnit(BattleEvent):
    def __init__(self, actor):
        BattleEvent.__init__(self)
        self.actor = actor

    def display(self, ui):
        ui.add_unit(self.actor)


class Miss(BattleEvent):
    def __init__(self, unit, cause_name):
        BattleEvent.__init__(self)
        self.unit = unit
        self.cause_name = cause_name

    def display(self, ui):
        ui.sound_handler.play_sound('miss')
        ui.show_result_on_map(self.unit, 'MISS')

    def report_entry(self):
        return {'_format': 'miss', 'unit': self.unit, 'cause': self.cause_name}


class StartTurn(BattleEvent):
    def __init__(self, unit):
        BattleEvent.__init__(self)
        self.unit = unit

    def display(self, ui):
        ui.print_active(self.unit)


class DamageOrHeal(BattleEvent):
    def __init__(self, unit, amount, cause_name):
        BattleEvent.__init__(self)
        self.unit = unit
        self.amount = amount
        self.cause_name = cause_name

    def display(self, ui):
        if self.amount >= 0:
            ui.animations.flash_damaged(self.unit.coords[0], self.unit.coords[1])
        ui.show_result_on_map(self.unit, self.amount)

    def report_entry(self):
        if self.amount >= 0:
            return {'_format': 'damage', 'unit': self.unit, 'cause': self.cause_name, 'effect': self.amount}
        else:
            return {'_format': 'heal', 'unit': self.unit, 'cause': self.cause_name, 'effect': abs(self.amount)}


class StatusDamageOrHeal(DamageOrHeal):
    def __init__(self, unit, amount, cause_name):
        DamageOrHeal.__init__(self, unit, amount, cause_name)

    def report_entry(self):
        if self.amount >= 0:
            return {'_format': 'status_damage', 'unit': self.unit, 'cause': self.cause_name, 'effect': self.amount}
        else:
            return {'_format': 'status_heal', 'unit': self.unit, 'cause': self.cause_name, 'effect': abs(self.amount)}


class BadStatus(BattleEvent):
    def __init__(self, unit, cause_name):
        BattleEvent.__init__(self)
        self.unit = unit
        self.cause_name = cause_name

    def display(self, ui):
        ui.show_result_on_map(self.unit, '+{}'.format(self.cause_name), color=ui.textcolors['bad_status'])

    def report_entry(self):
            return {'_format': 'bad_status', 'unit': self.unit, 'cause': self.cause_name}


class GoodStatus(BadStatus):
    def __init__(self, unit, cause_name):
        BadStatus.__init__(self, unit, cause_name)

    def display(self, ui):
        ui.show_result_on_map(self.unit, '+{}'.format(self.cause_name), color=ui.textcolors['good_status'])

    def report_entry(self):
            return {'_format': 'good_status', 'unit': self.unit, 'cause': self.cause_name}


class BadStatusEnds(BadStatus):
    def __init__(self, unit, cause_name):
        BadStatus.__init__(self, unit, cause_name)

    def display(self, ui):
        ui.show_result_on_map(self.unit, '-{}'.format(self.cause_name), color=ui.textcolors['bad_status'])

    def report_entry(self):
            return {'_format': 'bad_status_ends', 'unit': self.unit, 'cause': self.cause_name}


class GoodStatusEnds(BadStatus):
    def __init__(self, unit, cause_name):
        BadStatus.__init__(self, unit, cause_name)

    def display(self, ui):
        ui.show_result_on_map(self.unit, '-{}'.format(self.cause_name), color=ui.textcolors['good_status'])

    def report_entry(self):
            return {'_format': 'good_status_ends', 'unit': self.unit, 'cause': self.cause_name}


class IsDisabled(BadStatus):
    def __init__(self, unit, cause_name):
        BadStatus.__init__(self, unit, cause_name)

    def report_entry(self):
        return {'_format': 'disabled', 'unit': self.unit, 'cause': self.cause_name}

    def display(self, ui):
        ui.show_result_on_map(self.unit, '{}'.format(self.cause_name), color=ui.textcolors['text'])


class ImmuneToStatus(BadStatus):
    def __init__(self, unit, cause_name):
        BadStatus.__init__(self, unit, cause_name)

    def report_entry(self):
        return {'_format': 'immune', 'unit': self.unit, 'cause': self.cause_name}

    def display(self, ui):
        ui.show_result_on_map(self.unit, 'IMMUNE')


class ImmuneToTerrain(BadStatus):
    def __init__(self, unit, cause_name):
        BadStatus.__init__(self, unit, cause_name)

    def report_entry(self):
        return {'_format': 'immune_terrain', 'unit': self.unit, 'cause': self.cause_name}

    def display(self, ui):
        ui.show_result_on_map(self.unit, 'IMMUNE')
