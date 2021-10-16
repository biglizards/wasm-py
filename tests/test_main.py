import dis

from src.main import func_to_wasm, run_func, Module
from src.run_wasm import run_wasm_function


def test_lambda_add():
    func = func_to_wasm(
        code=(lambda x, y: x+y).__code__,
        name='sum'
    )
    assert run_func(func, 'sum', 3, 33) == 36


def test_func_add():
    def add(x, y):
        return x+y

    func = func_to_wasm(
        code=add.__code__,
        name='add'
    )

    assert run_func(func, 'add', 3, 33) == 36


def test_nested_function():
    def add(x, y):
        def inner_add(a, b):
            return a+b
        return inner_add(x, y)

    func = func_to_wasm(
        code=add.__code__,
        name='add'
    )

    assert run_func(func, 'add', 3, 33) == 36


def test_two_functions():
    def add_one(x):
        return x+1

    def add(x, y):
        return add_one(x) + add_one(y)

    print("add 1")
    dis.dis(add_one)
    print("add")
    dis.dis(add)

    func_1 = func_to_wasm(
        code=add_one.__code__,
        name='add_one'
    )
    func_2 = func_to_wasm(
        code=add.__code__,
        name='add'
    )

    mod = Module(func_1, func_2)
    wasm = mod.compile()
    assert run_wasm_function(wasm, 'add', 3, 33) == 38
