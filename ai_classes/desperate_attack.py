import redoubtable_ai


class UnitScoreWeightAlly(redoubtable_ai.UnitScoreWeightDefaults):
    def __init__(self):
        redoubtable_ai.UnitScoreWeightDefaults.__init__(self)


class UnitScoreWeightEnemy(redoubtable_ai.UnitScoreWeightEnemyDefaults):
    def __init__(self):
        redoubtable_ai.UnitScoreWeightEnemyDefaults.__init__(self)
        self.hp = -100
        self.total_damage_over_time = -80

        self.is_dead = 5000


class UnitScoreWeightSelf(redoubtable_ai.UnitScoreWeightDefaults):
    def __init__(self):
        redoubtable_ai.UnitScoreWeightDefaults.__init__(self)
        self.preferred_threat_level = 10
        self.is_dead = 0
        self.hp = 0


class AiWeights(redoubtable_ai.AiWeightsDefault):
    def __init__(self, *args, **kwargs):
        redoubtable_ai.AiWeightsDefault.__init__(self, *args, **kwargs)
