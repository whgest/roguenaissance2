class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

def add_threat(threat):
    threat_x = threat.coords[0]
    threat_y = threat.coords[1]

    for x in range(50):
        for y in range(25):
            75 - (abs(threat_x - x) + abs(threat_y - y))


from timeit import default_timer as timer

s = timer()
add_threat(Bunch(coords=(12,12)))
e = timer()

print e-s

