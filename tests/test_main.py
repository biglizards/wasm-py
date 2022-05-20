import dis

from generate_code import CodeGenerator
# from src.main_old import func_to_wasm, run_func, Module
from main import compile_func_to_wasm, compile_and_save, compile_multiple, compile_module


def test_lambda_add():
    func = compile_func_to_wasm(
        func=lambda x, y: x+y,
        name='sum'
    )

    assert func(3, 33) == 36


def test_func_add():
    @compile_func_to_wasm
    def add(x, y):
        return x+y

    assert add(3, 33) == 36


def test_pair_swap():
    @compile_func_to_wasm
    def swap(x, y):
        # tests out making and deconstructing tuples
        z = (x, y)
        a = z[0]
        b = z[1]
        return b, a

    assert swap(33, 3) == (3, 33)


def test_undefined_operation():
    # make sure undefined operations correctly crash instead of some kind of undefined behaviour
    @compile_func_to_wasm
    def add_tuples(x):
        a = (x,)
        b = (x,)
        return a + b  # actually, this should work (producing (x, x)) -- it just hasn't been implemented yet

    try:
        add_tuples(3)
        assert False
    except RuntimeError:
        pass


def test_numerical_ops():
    import example_files.numerical_ops
    module = compile_module(example_files.numerical_ops)

    assert module.add(5, 3) == 8
    assert module.add(5.2, 3.4) == 5.2 + 3.4
    assert module.subtract(5, 3) == 2
    assert module.subtract(5.2, 3.4) == 5.2 - 3.4
    assert module.mult(5, 3) == 15
    assert module.mult(5.2, 3.4) == 5.2 * 3.4
    assert module.pow_test(5, 3) == 125
    assert module.pow_test(5.5, 3.2) == 5.5**3.2
    assert module.pow_mod_test(253, 2342, 124) == 25
    assert module.sign_operations(2) == 1
    assert module.divmod(27, 5) == (5.4, 2)
    assert module.divmod(27.1, 5.4) == (27.1 / 5.4, 27.1 % 5.4)
    assert module.bool_test(5) == 1
    assert module.bool_test(0) == -1
    assert module.bool_test(0.0) == -1
    assert module.bool_test(tuple()) == -1  # technically this isn't a numerical op but w/e
    assert module.bitwise_ops(245, 3) == (245 >> 3, 245 << 3, 245 | 3, 245 & 3)


def test_simple_flow():
    @compile_and_save
    def is_three(x):
        if x == 3:
            return 1
        else:
            return 0

    @compile_func_to_wasm
    def is_five(x):
        return 1 if x == 5 else 0

    assert is_three(3)
    assert not is_three(2)

    assert is_five(5)
    assert not is_five(3)


def test_while_loop():
    @compile_and_save
    def efficient_fib(n):
        # a, b = 0, 1
        a = 0
        b = 1
        while n != 0:
            a, b = b, a + b
            n -= 1
        return a

    assert efficient_fib(1) == 1
    assert efficient_fib(5) == 5
    assert efficient_fib(10) == 55
    assert efficient_fib(35) == 9227465

# we don't have these yet
# def test_nested_function():
#     @compile_func_to_wasm
#     def add(x, y):
#         def inner_add(a, b):
#             return a+b
#         return inner_add(x, y)
#
#     assert add(3, 33) == 36


def test_two_functions():
    from example_files.function_calls import add_one, add

    add_one, add = compile_multiple(add_one, add)

    assert add_one(3) == 4

    assert add(3, 33) == 38
    assert add(1, 1) == 4


def test_fib():
    from example_files.fib import fib_python
    fib = compile_func_to_wasm(fib_python, save=True)
    assert fib(35) == 9227465
    bench(fib, 25, n=100)


def test_ambiguous_function_pointer():
    from example_files.function_swap import foo, add_1, add_10
    foo, *_ = compile_multiple(foo, add_1, add_10)

    assert foo(3, 1) == 5
    assert foo(4, 1) == 6
    assert foo(3, 2) == 14
    assert foo(4, 2) == 15


def test_global_mutation():
    from example_files.global_mutation import foo, foo_2, call_foo, swap_foo, counter, set_counter
    call_foo, swap_foo, counter, set_counter, *_ = \
        compile_multiple(call_foo, swap_foo, counter, set_counter, foo, foo_2)

    assert call_foo() == 0
    swap_foo()
    assert call_foo() == 1
    swap_foo()
    assert call_foo() == 0
    swap_foo()
    assert call_foo() == 1

    # counter increments an un-initialised global -- it should throw an error
    try:
        counter()
        assert False
    except RuntimeError:
        pass

    set_counter()
    assert counter() == 1
    assert counter() == 2
    assert counter() == 3


def test_division():
    def do_div(a, b):
        return a / b

    def do_floor_div(a, b):
        return a // b

    div, floor_div = compile_multiple(do_div, do_floor_div)

    assert div(5, 2) == 2.5
    assert floor_div(5, 2) == 2


def test_global_scope():
    from example_files.global_scope_1 import assign_x, delete_x, use_x
    assign_x, delete_x, use_x = compile_multiple(assign_x, delete_x, use_x)

    try:
        use_x(5)
        assert False
    except RuntimeError:
        pass

    assign_x(3)
    assert use_x(5) == 8

    delete_x()
    try:
        use_x(5)
        assert False
    except RuntimeError:
        pass


def test_builtins():
    import example_files.built_in_functions
    module = compile_module(example_files.built_in_functions)

    assert module.call_int(1.1) == 1
    assert module.call_float(1) == 1.0
    assert module.call_abs(-5) == 5
    assert module.call_abs(-5.5) == 5.5
    assert module.call_min(2, 4) == 2
    assert module.call_min(4, 2) == 2
    assert module.call_max(2, 4) == 4
    assert module.call_max(4, 2) == 4


def test_builtin_shadowing():
    from example_files.builtin_shadowing import min_and_max, return_first, return_second, set_first, set_second, \
        del_first, del_second

    min_and_max, _, _, set_first, set_second, del_first, del_second = compile_multiple(
        min_and_max, return_first, return_second, set_first, set_second, del_first, del_second
    )

    assert min_and_max(10, 20) == 10
    assert min_and_max(5, 5) == 5
    assert min_and_max(10, 7) == 7
    assert min_and_max(3, 8) == 3

    set_first()

    assert min_and_max(10, 20) == 10
    assert min_and_max(5, 5) == 5
    assert min_and_max(10, 7) == -1
    assert min_and_max(3, 8) == 3

    set_second()

    # now it always returns the first value
    assert min_and_max(10, 20) == 10
    assert min_and_max(20, 10) == 20
    assert min_and_max(5, 5) == 5
    assert min_and_max(10, 7) == 10
    assert min_and_max(3, 8) == 3

    del_first()

    # now it returns the first value iff it's smaller
    assert min_and_max(10, 20) == 10
    assert min_and_max(20, 10) == -1
    assert min_and_max(5, 5) == 5
    assert min_and_max(10, 7) == -1
    assert min_and_max(3, 8) == 3

    del_second()

    # both builtins are unshadowed now, good
    assert min_and_max(10, 20) == 10
    assert min_and_max(20, 10) == 10
    assert min_and_max(5, 5) == 5
    assert min_and_max(10, 7) == 7
    assert min_and_max(3, 8) == 3


def test_weird_code():
    # try to cause some kind of memory corruption (via double free, or just leaking).
    # this stress test takes several minutes.
    # so far, it always fails to mess anything up, which is a good sign.
    from example_files.cause_memory_corruption import foo, decref_functions, fib_python, sum_of_primes, \
        brute_force_is_prime, use_undefined_global, really_use_it
    decref_functions, foo, fib, sum_of_primes_, _,  use_undefined_global, really_use_it = compile_multiple(
        decref_functions, foo, fib_python, sum_of_primes, brute_force_is_prime, use_undefined_global, really_use_it
    )

    try:
        if use_undefined_global() is None:
            print('warning: undefined things are _still_ None, this should raise an exception by now')
        else:
            assert False
    except RuntimeError:
        pass

    try:
        really_use_it()
        assert False
    except RuntimeError:
        pass

    # we can cause a memory leak by crashing the program repeatedly, but really recovering from a crash is already
    # undefined behaviour, so it's not a huge concern.

    assert foo(5) == 6

    for _ in range(1000):
        decref_functions()
        assert foo(5) == 6

    assert fib(38) == 39088169
    assert sum_of_primes_(20000) == sum_of_primes(20000)

    for _ in range(1000):
        decref_functions()
        assert foo(5) == 6

    assert fib(38) == 39088169
    assert sum_of_primes_(20000) == sum_of_primes(20000)


def bench(f, arg, n=10000):
    import time
    t1 = time.time()
    for _ in range(n):
        pass
    t_base = time.time() - t1
    t2 = time.time()
    for _ in range(n):
        f(arg)
    t = time.time() - t2 - t_base
    print(f'took: {t * 1000:03f}ms')


if __name__ == '__main__':
    # test_lambda_add()
    # test_func_add()
    # test_pair_swap()
    # test_undefined_operation()  # we expect this one to output some error messages
    # test_simple_flow()
    # test_while_loop()
    # test_two_functions()
    # test_fib()
    # test_ambiguous_function_pointer()
    # test_division()
    test_builtins()
    # test_builtin_shadowing()
    # test_weird_code()
    # test_numerical_ops()


import opcode