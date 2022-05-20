def call_int(x):
    return int(x)


def call_float(x):
    return float(x)


def call_abs(x):
    return abs(x)


def call_min(x, y):
    return min(x, y)


def call_max(x, y):
    return max(x, y)


def call_pow(x, y, z):
    # name change due to optional argument in `pow`
    return pow_mod(x, y, z)

