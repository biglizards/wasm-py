def fib_python(n: int):
    if n <= 2:
        return 1
    return fib_python(n - 1) + fib_python(n - 2)
