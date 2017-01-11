import gridmap
import pathfinder
import random
import logging



def check_bounds(coords):
    if coords[1] > 49 or coords[0] > 24 or coords[0] < 0 or coords[1] < 0:
        return True


def pathfind(start, end, map):   #return true distance, path
    pfmap = gridmap.GridMap(25,50)
    pf = pathfinder.PathFinder(pfmap.successors, pfmap.move_cost, pfmap.move_cost)
    if check_bounds(start) or check_bounds(end):
        logging.debug("Check bounds failed.")
        return 0, []

    if map[end[1]][end[0]].terrain.movable == 0:
        return 0, []

    for x in range(50):
        for y in range(25):
            if map[x][y].actor is not None or map[x][y].terrain.movable == 0:
                pfmap.set_blocked((y, x))

    pfmap.set_blocked((start[0], start[1]), False)
    pfmap.set_blocked((end[0], end[1]), False)

    path = list(pf.compute_path(start, end))
    adjusted_path = []
    for p in path:
        adjusted_path.append((p[1], p[0]))
    return len(adjusted_path), adjusted_path




class RN_AI_Class():
    def __init__(self, battle, actor, skills):
        self.skills = skills
        self.battle = battle
        self.map = self.battle.bmap
        self.actor = actor
        self.enemy_list, self.friendly_list = self.get_targets()

    def get_action(self):
        logging.debug("AI turn: {0} using script '{1}'".format(self.actor.name, self.actor.ai))

        if not self.enemy_list:
            skill, target, path = None, None, None
        elif self.actor.ai == "damage":
            possible_moves = self.possible_attacks()
            if not possible_moves:
                logging.debug(self.actor.name + ": No possible attacks. Advancing.")
                return self.advance()
            else:
                return self.prioritize_targets(possible_moves)
        elif self.actor.ai == "weakest":
            possible_moves = self.possible_attacks()
            if not possible_moves:
                logging.debug(self.actor.name + ": No possible attacks. Advancing.")
                skill, target, path = self.advance()
            else:
                skill, target, path = self.prioritize_targets(possible_moves)
        elif self.actor.ai == "support":
            skill, target, path = self.heal_allies()

        elif self.actor.ai == "boss":
            skill, target, path = self.boss_logic()
        else:
            logging.debug(self.actor.ai + ": invalid AI.")
            return None, None, []

        logging.debug("Function: get_action returns: " + str([self.actor.name, skill, target, path]) + " MP:" + repr(self.actor.mp))
        if target is None:
            return skill, None, path
        elif type(target) is tuple:
            return skill, target, path
        else:
            return skill, target.coords, path

    def get_targets(self):
        friendly_list = []
        enemy_list = []

        for enemy in self.battle.get_enemies_of(self.actor):
            distance, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (enemy.coords[1], enemy.coords[0]), self.map)
            enemy_list.append({"distance": distance, "unit": enemy, "path": path})

        for ally in self.battle.get_allies_of(self.actor):
            distance, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (ally.coords[1], ally.coords[0]), self.map)
            friendly_list.append({"distance": distance, "unit": ally, "path": path})

        return enemy_list, friendly_list

    def heal_allies(self):
        heal_skill = ""
        for s in self.actor.skillset:
            if self.skills[s].damage['dice_size'] < 0:
                heal_skill = self.skills[s]
                if heal_skill.mp > self.actor.mp:
                    logging.debug(self.actor.name + ": Not enough MP for heal. MP:" + repr(self.actor.mp))
                    return self.possible_attacks()
        if heal_skill == "":
            return self.possible_attacks()
        for f in self.friendly_list:
            if f[1].hp < f[1].maxhp/3:
                if self.grid_distance(self.actor.coords, f[1].coords) <= heal_skill.range:
                    logging.debug(self.actor.name + ": Heal target " + f[1].name + "in range. Healing with skill" + repr(heal_skill.name))
                    return heal_skill.name, f[1], f[2]
                else:
                    count = 0
                    for p in f[2]:
                        count += 1
                        if count > self.actor.move:
                            break
                        if self.grid_distance(p, f[1].coords) <= heal_skill.range:
                            logging.debug(self.actor.name + ": Heal target " + f[1].name + "not in range. Moving to heal with skill" + repr(heal_skill.name))
                            return heal_skill.name, f[1], f[2]
            else:
                continue
        logging.debug(self.actor.name + ": Heal targets out of range or healing unneeded.")
        return self.possible_attacks()


    def possible_attacks(self, origin=None):
        possible_moves = []
        if not origin:
            origin = self.actor.coords
        for s in self.actor.skillset:
            if self.skills[s].mp > 0 and self.skills[s].mp > self.actor.mp:
                continue
            if self.skills[s].damage == 0:
                continue
            average = self.skills[s].get_average_damage(self.actor)
            for t in self.enemy_list:
                if self.grid_distance(origin, t["unit"].coords) > 20:
                    continue
                est_damage = 0
                units_affected = 1
                count = 0
                for path_step in t["path"]:
                    count += 1
                    if count > self.actor.move+1:
                        break
                    if self.grid_distance(path_step, t["unit"].coords) <= self.skills[s].range:
                        logging.debug(self.actor.name + ": Possible attack: " + s + " on " + t["unit"].name)
                        est_damage = est_damage + average
                        for r in self.enemy_list:  #check for aoe damage
                            if r == t:  #prevent primary target from being counted twice
                                continue
                            if self.grid_distance(t["unit"].coords, r["unit"].coords) <= self.skills[s].aoe:
                                est_damage = est_damage + average
                                units_affected += 1
                        logging.debug("Estimated damage: " + str(est_damage) + " split between " + str(units_affected) + " units.")
                        break
                if est_damage > 0:
                    possible_moves.append((est_damage, s, t["unit"], t["path"][:-1]))
        return possible_moves


    def prioritize_targets(self, possible_moves):
        if self.actor.ai == "weakest":
            weak_list = []
            for p in possible_moves:
                weak_list.append((p[2].hp, p[2], p[0], p[1], p[3])) #reorganize the list to select based on target hp, not total damage
            weak_list.sort(reverse=True)
            logging.debug(self.actor.name + "with AI: " + self.actor.ai + " move list: " + repr(weak_list))
            return weak_list[0][3], weak_list[0][1], weak_list[0][4]
        else:
            possible_moves.sort(reverse=True)
            logging.debug(self.actor.name + " with AI: " + self.actor.ai + " move list: " + repr(possible_moves))
            return possible_moves[0][1], possible_moves[0][2], possible_moves[0][3]

    def advance(self):
        path = []
        self.enemy_list.sort()  #advance to closest accessible target
        for t in self.enemy_list:
            path = t["path"][0:t['unit'].move]
            if path:
                logging.debug(self.actor.name + " advancing towards " + t["unit"].name)
                break
        if not path:
            logging.debug(self.actor.name + " no accessible targets, moving towards hero 1.")
            path = self.general_move()
        skill = None
        target = None
        return skill, target, path

    def general_move(self):
        path = []
        for i in range(5):
            dist, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (self.battle.hero.coords[1] + (i + 1), self.battle.hero.coords[0]), self.map)
            if path != []:
                break
            dist, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (self.battle.hero.coords[1], self.battle.hero.coords[0] + (i + 1)), self.map)
            if path != []:
                break
            dist, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (self.battle.hero.coords[1] - (i + 1), self.battle.hero.coords[0]), self.map)
            if path != []:
                break
            dist, path = pathfind((self.actor.coords[1], self.actor.coords[0]), (self.battle.hero.coords[1] + 1, self.battle.hero.coords[0] - (i + 1)), self.map)
            if path != []:
                break
        return path

    def grid_distance(self, actor1, actor2):
        return abs(actor1[0] - actor2[0]) + abs(actor1[1] - actor2[1])

    def boss_logic(self):
        allies_of_boss = self.battle.get_allies_of(self.actor)
        if self.actor.hp < 20:
            draintry = self.drain()
            if draintry:
                return draintry
        if self.actor.mp >= 8:
            return "Annihilate", self.actor, []
        if self.battle.hero.hp < 15:
            return self.choose_skill_boss()
        if len(allies_of_boss) < 3 and self.actor.mp > 2 or len(allies_of_boss) < 2 and self.actor.mp > 0:
            if len(allies_of_boss) == 2 and allies_of_boss[1].name == "Lichdrake":
                skill = "Summon Skelesaur"
            elif len(allies_of_boss) == 2 and allies_of_boss[1].name == "Skelesaur":
                skill = "Summon Lichdrake"
            else:
                skill = random.choice(["Summon Skelesaur", "Summon Lichdrake"])
            target = self.find_empty_tile()
            if target:
                return skill, target, []
        return self.choose_skill_boss()

    def find_empty_tile(self, from_tile):
        def test_tile(tile):
            return tile.actor is None and tile.terrain.movable == 1

        bmap = self.battle.bmap
        for i in range(5):
            if test_tile(bmap[self.actor.coords[0]+1+i][self.actor.coords[1]]):
                return (self.actor.coords[0] + 1 + i, self.actor.coords[1])
            if test_tile(bmap[self.actor.coords[0]-1-i][self.actor.coords[1]]):
                return (self.actor.coords[0] - 1 - i, self.actor.coords[1])
            if test_tile(bmap[self.actor.coords[0]][self.actor.coords[1]+1+i]):
                return (self.actor.coords[0], self.actor.coords[1] + 1 + i)
            if test_tile(bmap[self.actor.coords[0]][self.actor.coords[1]-1-i]):
                return (self.actor.coords[0], self.actor.coords[1] - 1 - i)
        return False

    def drain(self):
        heal_skill = ""
        for s in self.actor.skillset:
            if self.skills[s].effects[0]["type"] == "Drain":
                skill_name = s
                heal_skill = self.skills[s]
                if heal_skill.mp > self.actor.mp:
                   return False
        if heal_skill == "":
            return False
        for f in self.friendly_list:
            if f[1] == self.actor:
                continue
            if self.grid_distance(self.actor.coords, f[1].coords) <= heal_skill.range:
                return skill_name, f[1], f[2]
            else:
                count = 0
                for p in f[2]:
                    count += 1
                    if count > self.actor.move:
                        continue
                    if self.grid_distance(p, f[1].coords) <= heal_skill.range:
                        return skill_name, f[1], f[2]
        return False

    def choose_skill_boss(self, nohero=False):
        possible_moves = []
        for s in self.actor.skillset:
            if self.skills[s].mp > self.actor.mp:
                continue
            if nohero == True and self.skills[s].mp > 0:
                continue
            if self.skills[s].damage == 0:
                continue
            average = self.skills[s].get_average_damage(self.actor)
            for t in self.enemy_list:
                if nohero == False and t['unit'] != self.battle.hero:
                    continue
                est_damage = 0
                count = 0
                for p in t['path']:
                    count += 1
                    if count > self.actor.move:
                        break
                    if self.grid_distance(p, t['unit'].coords) <=self.skills[s].range:
                        est_damage = average
                        for r in self.enemy_list:  #check for aoe damage
                            if r == t:  #prevent primary target from being counted twice
                                continue
                            if self.grid_distance(t['unit'].coords, r['unit'].coords) <=self.skills[s].aoe:
                                est_damage += average
                        break
                if est_damage > 0:
                    possible_moves.append((est_damage, t['unit'].hp, s, t['unit'], t['path']))
        possible_moves.sort(reverse=True)
        if possible_moves == [] and nohero is True:
            logging.debug("No targets in range. Advancing.")
            return self.advance()
        if possible_moves == []:
            logging.debug("Hero not in range.")
            return self.choose_skill_boss(True)
        logging.debug("Boss selected:" + possible_moves[0][2] + " on " + repr(possible_moves[0][3]) + "from possible moves: \n" + repr(possible_moves))
        return possible_moves[0][2], possible_moves[0][3], possible_moves[0][4]       #skill and target and path





