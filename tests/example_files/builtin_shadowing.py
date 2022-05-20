def min_and_max(x, y):
    # always returns the smaller value... or does it?
    if min(x, y) == x and max(x, y) == y:
        return x
    if min(x, y) == y and max(x, y) == x:
        return y
    return -1


def return_first(x, y):
    return x


def return_second(x, y):
    return y


def set_first():
    global min
    min = return_first


def del_first():
    global min
    del min


def set_second():
    global max
    max = return_second


def del_second():
    global max
    del max
