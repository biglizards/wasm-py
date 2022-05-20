files = [
    "fib", 'fib3',

    # unary functions:
    "not_pyobject",

    # 1. number functions
    "add_pyobject", "subtract_pyobject", "mul_pyobject", "rem_pyobject",
    "tri_pow_pyobject", "bin_pow_pyobject",
    "neg_pyobject", "pos_pyobject", "abs_pyobject", "bool_pyobject", "inv_pyobject",
    "lshift_pyobject", "rshift_pyobject", "and_pyobject", "xor_pyobject", "or_pyobject",
    "int_pyobject", "float_pyobject",
    "floor_div_pyobject", "div_pyobject",
    # 2. sequence functions
    "subscr_pyobject",
    # 3. comparison functions
    "lt_pyobject", "lte_pyobject", "eq_pyobject", "neq_pyobject", "gt_pyobject", "gte_pyobject",
    "is_pyobject",

    # ref_counting
    "py_incref", "py_decref",

    # misc mess
    "new_short",
    "main2",
    "main3",
    "main4",
    "main5",
    "main_long",
    "add_long",
    "get_int_from_short",
    "PyLong_FromLong",
    "PyLong_AsLong", "PyLong_FromDouble",
    "PyTuple_New", "PyTuple_set_item_unchecked", "PyTuple_GetItem", "PyTuple_Size",
    "PyObject_IsTrue",
    "what_the_fuck",
    "pair",
    "first",
    "second",
    "_Py_NoneStruct",  # fun fact: this isn't a file, it's the actual struct
    "return_none",
    "flow_control_example",
    "raise_name_error",

    # exposed long operations
    "long_lt_direct", "long_lte_direct", "long_eq_direct", "long_neq_direct", "long_gt_direct", "long_gte_direct",
    "long_add_direct", "long_sub_direct",

    # for extracting values
    "get_type",

    # float stuff
    "PyFloat_FromDouble", "PyFloat_AsDouble",
    "add_float",

    # builtins
    "builtin_min", "builtin_max"
]


def main():
    print("'[", end='')
    print(', '.join(f'"_{item}"' for item in files), end='')
    print("]'", end='')


if __name__ == '__main__':
    main()
