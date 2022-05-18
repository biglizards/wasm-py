def fib_python(n: int) -> int:
    if n <= 2:
        return 1
    return fib_python(n - 1) + fib_python(n - 2)


def sum_of_primes(n: int):
    i = 1
    total = 0
    while i <= n:
        # is i prime? do a brute force check
        if brute_force_is_prime(i) == 1:
            total += i
        i += 1
    return total


def brute_force_is_prime(n: int) -> int:
    i = 2
    # yeah maybe i should have implemented more than leq, but it's universal so shut up
    while i <= (n - 1):
        if n % i == 0:
            return 0
        i += 1
    return 1
