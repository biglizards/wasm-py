def init(y):
    global x
    x = y


def de_init():
    global x
    del x


def use_x(y):
    return x+y
