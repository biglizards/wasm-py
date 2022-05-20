from inspect import getmembers, isfunction

from generate_code import CodeGenerator
from run_wasm import run_wasm


# for use as a decorator
def compile_and_save(func):
    return compile_func_to_wasm(func, save=True)


def wrapper_wrapper(func_name, instance):
    # in theory this should be the only wrapper, but legacy
    # + this is test suite code so i have lowers standards
    # it takes a PyObject*, recursively extracts its data, and then puts it back into a python object

    def call(name, *args):
        return getattr(instance.exports, name)(*args)

    def extract_int(value):
        # so far: just assume it's a long
        return call('PyLong_AsLong', value)

    def extract_tuple(value):
        # 1. get length of tuple
        # 2. extract each value in turn
        # 3. reconstruct the tuple
        size = call('PyTuple_Size', value)
        return tuple(
            extract(call('PyTuple_GetItem', value, i))
            for i in range(size)
        )

    def extract_bool(value):
        return bool(call('PyLong_AsLong', value))

    def extract_none(value):
        return None

    def extract_float(value):
        return call('PyFloat_AsDouble', value)

    def extract_error(value):
        raise RuntimeError('failed to extract value! Unknown type!')

    extract_map = {1: extract_int, 2: extract_tuple, 3: extract_bool, 4: extract_none, 5: extract_float,
                -1: extract_error}

    def extract(value):
        return extract_map[call('get_type', value)](value)

    def push_int(value):
        return call('PyLong_FromLong', value)

    def push_tuple(value):
        args = [push_arg(item) for item in value]
        tp = call('PyTuple_New', len(value))
        for i, arg in enumerate(args):
            tp = call('PyTuple_set_item_unchecked', arg, tp, i)
        return tp

    def push_bool(value):
        # is it weird to go via long? kinda yes
        return call('bool_pyobject', push_int(value))

    def push_none(value):
        return call('return_none')

    def push_float(value):
        return call('PyFloat_FromDouble', value)

    push_map = {int: push_int, tuple: push_tuple, bool: push_bool, type(None): push_none, float: push_float,
                -1: extract_error}

    def push_arg(arg):
        return push_map[type(arg)](arg)

    def inner(*args):
        # todo: maybe fix that we don't wrap nicely too
        args = [push_arg(arg) for arg in args]
        rv = call(func_name, *args)
        return extract(rv)

    inner.__name__ = func_name

    return inner


def compile_func_to_wasm(func, name=None, save=False):
    if name is None:
        name = func.__name__
    save_name = name if save else None

    # compile the function to WASM
    g = CodeGenerator()
    g.add_to_module(func, name)
    wasm = g.compile(save_name=save_name)

    # use Wasmer (a dependency) to load that WASM into a runtime,
    # which then exposes its functions to Python
    instance = run_wasm(wasm)

    # g.add_to_module also adds a shim which can convert from C types
    # (which is how they're represented after going through Wasmer's interface)
    # to PyObjects, allowing us to treat the function like it was a builtin.
    return wrapper_wrapper(name, instance)


def compile_multiple(*funcs):
    g = CodeGenerator()

    for func in funcs:
        g.add_to_module(func, func.__name__)

    wasm = g.compile(save_name=funcs[0].__name__)
    instance = run_wasm(wasm)

    return [
        wrapper_wrapper(func.__name__, instance)
        for func in funcs
    ]


class Dotdict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def compile_module(mod):
    return Dotdict({
        func.__name__: func for func in
        compile_multiple(*[f for _, f in getmembers(mod, isfunction)])
    })


def main():
    pass


if __name__ == '__main__':
    main()
