def add_one(x):
    return x + 1


def add(x, y):
    return add_one(x) + add_one(y)


def make_add_x(x):
    def add_x(y):
        return x + y
    return add_x
