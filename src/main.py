from generate_code import CodeGenerator
from run_wasm import run_wasm


# for use as a decorator
def compile_and_save(func):
    return compile_func_to_wasm(func, save=True)


def compile_func_to_wasm(func, name=None, save=False):
    if name is None:
        name = func.__name__

    g = CodeGenerator()
    g.add_to_module(func.__code__, name)

    save_name = name if save else None

    wasm = g.compile(save_name=save_name)
    instance = run_wasm(wasm)

    return getattr(instance.exports, f'__{name}_wrapper')


def compile_multiple(*funcs):
    g = CodeGenerator()

    for func in funcs:
        g.add_to_module(func.__code__, func.__name__)

    wasm = g.compile(save_name=funcs[0].__name__)
    instance = run_wasm(wasm)

    return [
        getattr(instance.exports, f'__{func.__name__}_wrapper')
        for func in funcs
    ]


def main():
    pass


if __name__ == '__main__':
    main()
