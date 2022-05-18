def add_1(x):
    return x + 1


def add_10(x):
    return x + 10


def foo(x, y):
    return (add_1 if y == 1 else add_10)(x + 1)


def undef_foo():
    global foo
    del foo
