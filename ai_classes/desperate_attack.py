import redoubtable_ai


class UnitScoreWeightAlly(redoubtable_ai.UnitScoreWeightDefaults):
    def __init__(self):
        redoubtable_ai.UnitScoreWeightAllyDefaults.__init__(self)


class UnitScoreWeightEnemy(redoubtable_ai.UnitScoreWeightEnemyDefaults):
    def __init__(self):
        redoubtable_ai.UnitScoreWeightEnemyDefaults.__init__(self)
        self.hp = 20


class UnitScoreWeightSelf(redoubtable_ai.UnitScoreWeightDefaults):
    def __init__(self):
        redoubtable_ai.UnitScoreWeightDefaults.__init__(self)
        self.hp = 0
        self.mp = 0
        self.attack = 0
        self.defense = 0
        self.move = 0
        self.magic = 0
        self.resistance = 0

        self.position_priority = 5


class AiWeights(redoubtable_ai.AiWeightsDefault):
    def __init__(self, *args, **kwargs):
        redoubtable_ai.AiWeightsDefault.__init__(self, *args, **kwargs)
