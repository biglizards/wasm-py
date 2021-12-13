import dis

from generate_code import CodeGenerator
# from src.main_old import func_to_wasm, run_func, Module
from main import compile_func_to_wasm


def test_lambda_add():
    func = compile_func_to_wasm(
        func=lambda x, y: x+y,
        name='sum'
    )

    assert func(3, 33) == 36


def test_func_add():
    def add(x, y):
        return x+y

    func = compile_func_to_wasm(add)
    assert func(3, 33) == 36


def test_pair_swap():
    def swap(x, y):
        # tests out making and deconstructing tuples
        z = (x, y)
        a = z[0]
        b = z[1]
        return b, a

    ans = compile_func_to_wasm(swap)(33, 3)
    assert ans == (3, 33), ans


def test_undefined_operation():
    def add_tuples(x):
        a = (x,)  # it uses a variable so we can avoid tuple constants
        b = (x,)
        return a + b  # actually, this should work (producing (x, x)) -- it just hasn't been implemented yet

    func = compile_func_to_wasm(add_tuples)
    try:
        func(3)
        assert False
    except RuntimeError:
        pass


def test_simple_flow():
    @compile_func_to_wasm
    def is_three(x):
        if x == 3:
            return 1
        else:
            return 0

    assert is_three(3)
    assert not is_three(2)


def test_while_loop():
    @compile_func_to_wasm
    def efficient_fib(n):
        a, b = 0, 1
        while n:
            a, b = b, a + b
            n -= 1
        return a

    assert efficient_fib(35) == 9227465


def test_nested_function():
    def add(x, y):
        def inner_add(a, b):
            return a+b
        return inner_add(x, y)

    func = compile_func_to_wasm(add)
    assert func(3, 33) == 36


# def test_two_functions():
#     def add_one(x):
#         return x+1
#
#     def add(x, y):
#         return add_one(x) + add_one(y)
#
#     print("add 1")
#     dis.dis(add_one)
#     print("add")
#     dis.dis(add)
#
#     # ok this just straight up does not work
#
#     func_1 = func_to_wasm(
#         code=add_one.__code__,
#         name='add_one'
#     )
#     func_2 = func_to_wasm(
#         code=add.__code__,
#         name='add'
#     )
#
#     mod = Module(func_1, func_2)
#     wasm = mod.compile()
#     assert run_wasm_function(wasm, 'add', 3, 33) == 38


if __name__ == '__main__':
    # test_lambda_add()
    # test_func_add()
    # test_pair_swap()
    # test_undefined_operation()
    test_simple_flow()

