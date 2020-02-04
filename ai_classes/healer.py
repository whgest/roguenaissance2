import redoubtable_ai


class UnitScoreWeightAlly(redoubtable_ai.UnitScoreWeightAllyDefaults):
    def __init__(self):
        redoubtable_ai.UnitScoreWeightDefaults.__init__(self)
        self.hp = 50


class UnitScoreWeightEnemy(redoubtable_ai.UnitScoreWeightEnemyDefaults):
    def __init__(self):
        redoubtable_ai.UnitScoreWeightEnemyDefaults.__init__(self)


class UnitScoreWeightSelf(redoubtable_ai.UnitScoreWeightSelfDefaults):
    def __init__(self):
        redoubtable_ai.UnitScoreWeightSelfDefaults.__init__(self)
        self.hp = 50


class AiWeights(redoubtable_ai.AiWeightsDefault):
    def __init__(self, *args, **kwargs):
        redoubtable_ai.AiWeightsDefault.__init__(self, *args, **kwargs)
