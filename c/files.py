files = [
    "fib", 'fib3',
    "add_pyobject", "subtract_pyobject", "subscr_pyobject",
    "leq_pyobject", "eq_pyobject",
    "new_short",
    "main2",
    "main3",
    "main4",
    "main5",
    "main_long",
    "add_long",
    "get_int_from_short",
    "PyLong_FromLong",
    "PyLong_AsLong",
    "PyTuple_New", "PyTuple_set_item_unchecked", "PyTuple_GetItem",
    "what_the_fuck",
    "pair",
    "first",
    "second",
    "_Py_NoneStruct",  # fun fact: this isn't a file, it's the actual struct
    "return_none",
    "flow_control_example",
]


def main():
    print("'[", end='')
    print(', '.join(f'"_{item}"' for item in files), end='')
    print("]'", end='')


if __name__ == '__main__':
    main()
