class DummyCall(object):
    def __call__(self, *args, **kwargs):
        return None


class DummyUi(object):
    def __init__(self):
        pass

    def __getattr__(self, attr):
        return DummyCall()

    def __setattr__(self, attr, val):
        pass
