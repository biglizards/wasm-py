# in this test "foo" is a global function which returns a constant value

def foo():
    return 0


def foo_2():
    return 1


def swap_foo():
    global foo, foo_2
    tmp = foo
    foo = foo_2
    foo_2 = tmp


def call_foo():
    return foo()


def counter():
    global count
    count = count + 1
    return count


def set_counter():
    global count
    count = 0