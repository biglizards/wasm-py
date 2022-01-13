def while_(a, b, c):
    while a():
        b()
    c()


def if_(a, b, c):
    if a():
        b()
    c()


def if_2(a, b, c, d):
    if a():
        b()
    else:
        c()
    d()


def if_3(a, b, c, d, e, f):
    if a():
        b()
    elif c():
        d()
    else:
        e()
    f()


def mini_monster(a, b, c, d, e, f):
    if a():
        b()
    else:
        while c():
            d()
        e()
    f()


def monster(a, b, c, d, e, f):
    if a():
        while b():
            c()
        d()
    else:
        while c():
            d()
        e()
    f()
