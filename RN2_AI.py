import gridmap
import pathfinder
import random
import logging

class RN_AI_Class():
    def __init__(self, battle, e, skills):
        self.skills = skills
        self.battle = battle
        self.e = e
        self.target_list = []
        self.friendly_list = []

    def enemy_turn(self):
        logging.debug("AI turn: " + self.e.name)
        self.target_list, self.friendly_list = self.get_targets()
        if not self.target_list:
            return
        if self.e.ai == "damage":
            skill, target, path = self.possible_attacks()
        elif self.e.ai == "weakest":
            skill, target, path = self.possible_attacks()
        elif self.e.ai == "support":
            skill, target, path = self.heal_allies()
        elif self.e.ai == "aquatic":
            skill, target, path = self.possible_attacks()
        elif self.e.ai == "boss":
            skill, target, path = self.boss_logic()
        else:
            logging.debug(self.e.ai + ": invalid AI.")
            return None, None, []

        logging.debug("Function: enemy_turn returns: " + str([self.e.name, skill, target, path]) + " MP:" + repr(self.e.mp))
        if target is None:
            return skill, None, path
        elif type(target) is tuple:
            return skill, target, path
        else:
            return skill, target.coords, path


    def get_targets(self):
        friendly_list = []
        target_list = []
        aqua = 0
        if self.e.ai == "aquatic":
            aqua = True
        if self.e.ai in ["support", "boss"]:
            for n in self.battle.enemies:
                distance, path = self.pathfind((self.e.coords[1], self.e.coords[0]), (n.coords[1], n.coords[0]))
                friendly_list.append((distance, n, path))
        for h in self.battle.heroes:
            distance, path = self.pathfind((self.e.coords[1], self.e.coords[0]), (h.coords[1], h.coords[0]), aqua)
            target_list.append({"distance": distance, "unit": h, "path": path})
        return target_list, friendly_list

    def heal_allies(self):
        heal_skill = ""
        for s in self.e.skillset:
            if self.skills[s].damage == -1:
                heal_skill =self.skills[s]
                if heal_skill.mp > self.e.mp:
                    logging.debug(self.e.name + ": Not enough MP for heal. MP:" + repr(self.e.mp))
                    return self.possible_attacks()
        if heal_skill == "":
            return self.possible_attacks()
        for f in self.friendly_list:
            if f[1].hp < f[1].maxhp/3:
                if self.grid_distance(self.e.coords, f[1].coords) <= heal_skill.range:
                    logging.debug(self.e.name + ": Heal target " + f[1] + "in range. Healing with skill" + repr(heal_skill.name))
                    return heal_skill.name, f[1], f[2]
                else:
                    count = 0
                    for p in f[2]:
                        count += 1
                        if count > self.e.move:
                            break
                        if self.grid_distance(p, f[1].coords) <= heal_skill.range:
                            logging.debug(self.e.name + ": Heal target " + f[1] + "not in range. Moving to heal with skill" + repr(heal_skill.name))
                            return heal_skill.name, f[1], f[2]
            else:
                continue
        logging.debug(self.e.name + ": Heal targets out of range or healing unneeded.")
        return self.possible_attacks()

    def possible_attacks(self):
        possible_moves = []
        for s in self.e.skillset:
            if self.skills[s].mp > self.e.mp:
                continue
            if self.skills[s].damage == 0:
                continue
            average = (getattr(self.e, self.skills[s].stat)/3) + (self.skills[s].damage[0] * (self.skills[s].damage[1]/2)) #average damage of skill
            for t in self.target_list:
                if self.grid_distance(self.e.coords, t["unit"].coords) > 20:
                    continue
                est_damage = 0
                units_affected = 1
                count = 0
                for path_step in t["path"]:
                    count += 1
                    if count > self.e.move+1:
                        break
                    if self.grid_distance(path_step, t["unit"].coords) <= self.skills[s].range:
                        logging.debug(self.e.name + ": Possible attack: " + s + " on " + t["unit"].name)
                        est_damage = est_damage + average
                        for r in self.target_list:  #check for aoe damage
                            if r == t:  #prevent primary target from being counted twice
                                continue
                            if self.grid_distance(t["unit"].coords, r["unit"].coords) <= self.skills[s].aoe:
                                est_damage = est_damage + average
                                units_affected += 1
                        logging.debug("Estimated damage: " + str(est_damage) + " split between " + str(units_affected) + " units.")
                        break
                if est_damage > 0:
                    possible_moves.append((est_damage, s, t["unit"], t["path"]))
        if not possible_moves:
            logging.debug(self.e.name + ": No possible attacks. Advancing.")
            return self.advance()
        else:
            return self.prioritize_targets(possible_moves)

    def prioritize_targets(self, possible_moves):
        if self.e.ai == "weakest":
            weak_list = []
            for p in possible_moves:
                weak_list.append((p[2].hp, p[2], p[0], p[1], p[3])) #reorganize the list to select based on target hp, not total damage
            weak_list.sort(reverse=True)
            logging.debug(self.e.name + "with AI: " + self.e.ai + " move list: " + repr(weak_list))
            return weak_list[0][3], weak_list[0][1], weak_list[0][4]
        else:
            possible_moves.sort(reverse=True)
            logging.debug(self.e.name + " with AI: " + self.e.ai + " move list: " + repr(possible_moves))
            return possible_moves[0][1], possible_moves[0][2], possible_moves[0][3]

    def advance(self):
        path = []
        self.target_list.sort()  #advance to closest accessible target
        for t in self.target_list:
            path = t["path"]
            if path:
                logging.debug(self.e.name + " advancing towards " + t["unit"].name)
                break
        if not path:
            logging.debug(self.e.name + " no accessible targets, moving towards hero 1.")
            path = self.general_move()
        skill = None
        target = None
        return skill, target, path

    def general_move(self):
        path = []
        for i in range(5):
            dist, path = self.pathfind((self.e.coords[1], self.e.coords[0]), (self.battle.hero.coords[1]+(i+1), self.battle.hero.coords[0]))
            if path != []:
                break
            dist, path = self.pathfind((self.e.coords[1], self.e.coords[0]), (self.battle.hero.coords[1], self.battle.hero.coords[0]+(i+1)))
            if path != []:
                break
            dist, path = self.pathfind((self.e.coords[1], self.e.coords[0]), (self.battle.hero.coords[1]-(i+1), self.battle.hero.coords[0]))
            if path != []:
                break
            dist, path = self.pathfind((self.e.coords[1], self.e.coords[0]), (self.battle.hero.coords[1]+1, self.battle.hero.coords[0]-(i+1)))
            if path != []:
                break
        return path

    def check_bounds(self, coords):
        if coords[1] > 49 or coords[0] > 24 or coords[0] < 0 or coords[1] < 0:
            return True

    def grid_distance(self, actor1, actor2):
        return abs(actor1[0] - actor2[0]) + abs(actor1[1] - actor2[1])

    def pathfind(self, start, end, aquatic=False):   #return true distance, path
        pfmap = gridmap.GridMap(25,50)
        pf = pathfinder.PathFinder(pfmap.successors, pfmap.move_cost, pfmap.move_cost)
        logging.debug("Pathfinding from: " + repr(start) + " " + repr(end))
        if self.check_bounds(start) or self.check_bounds(end):
            logging.debug("Check bounds failed.")
            return 0, []
        # if aquatic == True:
        #     if bmap[end[1]][end[0]][1][0] in [" ", chr(176)]: #bad terrain
        #         return 0, []
        #     for x in range (50):
        #         for y in range (25):
        #             if bmap[x][y][0].actor is not None or bmap[x][y][1][0] not in [chr(247)]:
        #                 pfmap.set_blocked((y,x))
        if aquatic == False:
            if self.battle.bmap[end[1]][end[0]].terrain.movable == 0:
                return 0, []
            for x in range (50):
                for y in range (25):
                    if self.battle.bmap[x][y].actor is not None or self.battle.bmap[x][y].terrain.movable == 0:
                        pfmap.set_blocked((y,x))
        pfmap.set_blocked((start[0], start[1]), False)
        pfmap.set_blocked((end[0], end[1]), False)
        path = list(pf.compute_path(start, end))
        adjusted_path = []
        for p in path:
            adjusted_path.append((p[1], p[0]))
        return len(adjusted_path), adjusted_path

    def boss_logic(self):
        if self.e.hp < 20:
            draintry = self.drain()
            if draintry:
                return draintry
        if self.e.mp >= 8:
            return "Annihilate", self.e, []
        if self.battle.hero.hp < 15:
            return self.choose_skill_boss()
        if len(self.battle.enemies) < 3 and self.e.mp > 2:
            if len(self.battle.enemies) == 2 and self.battle.enemies[1].name == "Lichdrake":
                skill = "Summon Skelesaur"
            elif len(self.battle.enemies) == 2 and self.battle.enemies[1].name == "Skelesaur":
                skill = "Summon Lichdrake"
            else:
                skill = random.choice(["Summon Skelesaur", "Summon Lichdrake"])
            target = self.find_empty_tile()
            if target:
                return skill, target, []
        return self.choose_skill_boss()

    def find_empty_tile(self):
        for i in range(5):
            if self.battle.bmap[self.e.coords[0]+1+i][self.e.coords[1]].actor == None:
                return (self.e.coords[0]+1+i, self.e.coords[1])
            if self.battle.bmap[self.e.coords[0]-1-i][self.e.coords[1]].actor == None:
                return (self.e.coords[0]-1-i, self.e.coords[1])
            if self.battle.bmap[self.e.coords[0]][self.e.coords[1]+1+i].actor == None:
                return (self.e.coords[0], self.e.coords[1]+1+i)
            if self.battle.bmap[self.e.coords[0]][self.e.coords[1]-1-i].actor == None:
                return (self.e.coords[0], self.e.coords[1]-1-i)
        return False

    def drain(self):
        heal_skill = ""
        for s in self.e.skillset:
            if self.skills[s].effect[0]["type"] == "Drain":
                skill_name = s
                heal_skill = self.skills[s]
                if heal_skill.mp > self.e.mp:
                   return False
        if heal_skill == "":
            return False
        for f in self.friendly_list:
            if f[1] == self.e:
                continue
            if self.grid_distance(self.e.coords, f[1].coords) <= heal_skill.range:
                return skill_name, f[1], f[2]
            else:
                count = 0
                for p in f[2]:
                    count += 1
                    if count > self.e.move:
                        continue
                    if self.grid_distance(p, f[1].coords) <= heal_skill.range:
                        return skill_name, f[1], f[2]
        return False

    def choose_skill_boss(self, nohero=False):
        possible_moves = []
        for s in self.e.skillset:
            if self.skills[s].mp > self.e.mp:
                continue
            if nohero == True and self.skills[s].mp > 0:
                continue
            if self.skills[s].damage == 0:
                continue
            average = (getattr(self.e, self.skills[s].stat)/3) + (self.skills[s].damage[0] * (self.skills[s].damage[1]/2)) #average damage of skill
            for t in self.target_list:
                if nohero == False and t['unit'] != self.battle.hero:
                    continue
                est_damage = 0
                count = 0
                for p in t['path']:
                    count += 1
                    if count > self.e.move:
                        break
                    if self.grid_distance(p, t['unit'].coords) <=self.skills[s].range:
                        est_damage = average
                        for r in self.target_list:  #check for aoe damage
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