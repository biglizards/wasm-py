from generate_code import CodeGenerator
from run_wasm import run_wasm


def compile_func_to_wasm(func, name=None):
    if name is None:
        name = func.__name__

    g = CodeGenerator()
    g.add_to_module(func.__code__, name)

    wasm = g.module.compile()
    instance = run_wasm(wasm)

    return getattr(instance.exports, f'__{name}_wrapper')



def main():
    pass


if __name__ == '__main__':
    main()
