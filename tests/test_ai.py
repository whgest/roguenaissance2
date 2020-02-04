import yaml
import copy

from redoubtable_ai import RedoubtableAi
from RN2_initialize import make_skills
from RN2_battle import Battle
from RN2_loadmap import load_map
from RN2_battle_logic import calculate_area_of_effect
from dummy_ui import DummyUi


SKILLS = make_skills()

with open('tests/test_actors.yaml') as actors:
    test_actors = yaml.load(actors, Loader=yaml.FullLoader)

with open('tests/test_battles.yaml') as battles:
    test_battles = yaml.load(battles, Loader=yaml.FullLoader)

with open('maps.yaml') as battles:
    maps = yaml.load(battles, Loader=yaml.FullLoader)


def init_battle(battle_id):
    battle_data = copy.deepcopy(test_battles[battle_id])
    map_raw = maps[battle_data['map']]
    bmap = load_map(map_raw)

    io = DummyUi()
    battle = Battle(battle_data, test_actors, SKILLS, bmap, io)
    for unit in battle_data['units']:
        loc = tuple(int(c) for c in unit['loc'].split(','))
        battle.add_unit(unit['ident'], loc, unit['team_id'])

    return battle


def init_ai(battle):
    battle = init_battle(battle)
    ai = RedoubtableAi(battle, battle.all_living_units[0], SKILLS)
    return ai, battle


def test_evaluate_does_not_error():
    ai, battle = init_ai('basic_attack')
    assert ai.evaluate()


def test_evaluate_returns_basic_attack_action():
    ai, battle = init_ai('basic_attack')
    result = ai.evaluate()[0]
    assert result['skill'] and result['skill'].name == "Bite"
    assert result['target'] == (1, 3)


def test_evaluate_returns_basic_attack_action_with_move():
    ai, battle = init_ai('basic_attack_with_move')
    result = ai.evaluate()[0]
    assert result['skill'] and result['skill'].name == "Bite"
    assert result['target'] == (1, 8)
    assert result['destination'] == (1, 7)


def test_evaluate_returns_aoe_attack_action_at_max_total_range():
    ai, battle = init_ai('aoe_attack_at_max_range')
    result = ai.evaluate()[0]
    assert result['skill'] and result['skill'].name == "Meteor"
    assert result['target'] == (1, 12)
    assert result['destination'] == (1, 7)


def test_evaluate_returns_aoe_attack_on_multiple_enemies():
    ai, battle = init_ai('aoe_attack')
    result = ai.evaluate()[0]
    assert result['skill'] and result['skill'].name == "Meteor"
    assert result['target'] == (5, 4)


def test_evaluate_returns_aoe_attack_action_with_avoidance():
    ai, battle = init_ai('aoe_attack_with_avoidance')
    result = ai.evaluate()[0]
    assert result['skill'] and result['skill'].name == "Meteor"
    assert result['target'] == (5, 4)
    assert result['destination'] not in calculate_area_of_effect(result['target'], result['skill'], battle.bmap)


def test_evaluate_returns_heal_on_ally():
    ai, battle = init_ai('heal_ally')
    result = ai.evaluate()[0]
    assert result['skill'] and result['skill'].name == "Soothing Breeze"
    assert result['target'] == (5, 7)


def test_evaluate_returns_heal_on_self():
    ai, battle = init_ai('heal_self')
    result = ai.evaluate()[0]
    assert result['skill'] and result['skill'].name == "Soothing Breeze"
    assert result['target'] == result['destination']


def test_evaluate_returns_advancement_towards_distant_enemy():
    ai, battle = init_ai('distant_enemy')
    result = ai.evaluate()[0]
    assert not result['skill']
    assert not result['target']
    assert result['destination'] == (6, 1)


def test_rooted_enemy_can_attack():
    ai, battle = init_ai('rooted')
    result = ai.evaluate()[0]
    assert result['skill']


def test_summons_are_placed_intentionally():
    ai, battle = init_ai('summon_placement')
    result = ai.evaluate()[0]
    assert result['target'][1] > 5


def test_evaluate_doesnt_take_forever():
    ai, battle = init_ai('complex_time_check')
    from timeit import default_timer as timer
    start = timer()
    result = ai.evaluate()[0]
    end = timer()
    assert result
    assert (end-start) < 5


def test_distance_cache():
    ai, battle = init_ai('complex_time_check')
    from redoubtable_ai import DistanceCache

    cache = DistanceCache()
    cache.make(battle.all_living_units, battle.bmap)
    assert cache.distances
