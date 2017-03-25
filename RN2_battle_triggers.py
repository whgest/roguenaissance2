
class BattleTriggerEffect(object):
    def __init__(self, data, battle):
        self.value = data.get('effect_value', None)
        self.battle = battle

    def resolve(self):
        raise NotImplementedError


class AddUnits(BattleTriggerEffect):
    def resolve(self):
        for val in self.value:
            unit_data = self.battle.units[val]
            loc = tuple([int(c) for c in unit_data['loc'].split(",")])
            self.battle.add_unit(unit_data['ident'], loc, int(unit_data['team_id']))


class BattleTriggerCondition(object):
    def __init__(self, data, battle):
        self.condition = data.get('condition_value', None)
        self.battle = battle

    def check(self):
        raise NotImplementedError


class IsTurn(BattleTriggerCondition):
    def check(self):
        return self.battle.turn_tracker.turn_count == int(self.condition)


class OnGoalTile(BattleTriggerCondition):
    def check(self):
        return self.battle.bmap.get_tile_at(self.battle.avatar.coords).terrain.name == "Goal"


class BattleTrigger(object):
    def __init__(self, data, battle):
        self.conditions = []
        self.effects = []
        for condition in data.get('conditions'):
            condition_class_to_instantiate = CLASS_MAPPINGS[condition['condition_type']]
            self.conditions.append(condition_class_to_instantiate(condition, battle))

        for effect in data.get('effects', []):
            effect_class_to_instantiate = CLASS_MAPPINGS[effect['effect_type']]
            self.effects.append(effect_class_to_instantiate(effect, battle))

    def resolve(self):
        for condition in self.conditions:
            if not condition.check():
                break
        else:
            for effect in self.effects:
                effect.resolve()
            return True

        return False




CLASS_MAPPINGS = {
    'on_goal_tile': OnGoalTile,
    'is_turn': IsTurn,
    'add_units': AddUnits
}
