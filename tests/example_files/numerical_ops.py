def add(x, y):
    return x + y


def subtract(x, y):
    return x - y


def mult(x, y):
    return x * y


def pow_test(x, y):
    return x**y


def pow_mod_test(x, y, z):
    # it's a builtin. Renamed from `pow` since that version takes two arguments.
    return pow_mod(x, y, z)


def sign_operations(x):
    if 0 - x != -x or x != +x:
        return -1
    return 1


def divmod(x, y):
    return x / y, x % y


def bool_test(x):
    if bool(x):
        return 1
    else:
        return -1


def bitwise_ops(x, y):
    return x >> y, x << y, x | y, x & y

