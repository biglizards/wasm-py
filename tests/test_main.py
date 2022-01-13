import dis

from generate_code import CodeGenerator
# from src.main_old import func_to_wasm, run_func, Module
from main import compile_func_to_wasm, compile_and_save, compile_multiple


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
    @compile_and_save
    def is_three(x):
        if x == 3:
            return 1
        else:
            return 0

    assert is_three(3)
    assert not is_three(2)


def test_while_loop():
    @compile_and_save
    def efficient_fib(n):
        # a, b = 0, 1
        a = 0
        b = 1
        while n != 0:
            # a, b = b, a + b
            tmp = a
            a = b
            b = b + tmp
            n = n - 1  # n -= 1
        return a

    assert efficient_fib(1) == 1
    assert efficient_fib(5) == 5
    assert efficient_fib(10) == 55
    assert efficient_fib(35) == 9227465


def test_nested_function():
    @compile_func_to_wasm
    def add(x, y):
        def inner_add(a, b):
            return a+b
        return inner_add(x, y)

    assert add(3, 33) == 36


def test_two_functions():
    from example_files.example import add_one, add

    add_one, add = compile_multiple(add_one, add)

    assert add_one(3) == 4

    assert add(3, 33) == 38
    assert add(1, 1) == 4


def test_fib():
    from example_files.fib import fib_python
    fib = compile_func_to_wasm(fib_python, save=True)
    assert fib(35) == 9227465
    bench(fib, 25, n=100)


def bench(f, arg, n=10000):
    import time
    t1 = time.time()
    for _ in range(n):
        pass
    t_base = time.time() - t1
    t2 = time.time()
    for _ in range(n):
        f(arg)
    t = time.time() - t2
    print(f'took: {t * 1000:03f}ms')


if __name__ == '__main__':
    # test_lambda_add()
    # test_func_add()
    # test_pair_swap()
    # test_undefined_operation()
    # test_simple_flow()
    # test_while_loop()
    # test_two_functions()
    test_fib()

import opcode