# haha i've used an import, and they said it wouldn't work
from .fib import fib_python, sum_of_primes, brute_force_is_prime


def foo(x):
    return x + 1


def decref_functions():
    # if a function is deallocated that'd be pretty bad
    # this test verifies that doesn't happen
    x = foo
    y = fib_python
    z = sum_of_primes
    f = brute_force_is_prime
    # locals are decref'd at the end of a function
    return None


def use_undefined_global():
    global never_initialised
    return never_initialised


def really_use_it():
    x = use_undefined_global()
    return max(x + 1, x**2)

