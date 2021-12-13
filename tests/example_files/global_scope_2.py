def init(y):
    globals()['x'] = y


def de_init():
    del globals()['x']


def use_x(y):
    return x+y
